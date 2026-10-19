"""Portable reading sessions, validated against the exact source document.

Offsets and half-open ranges use UTF-16 code units so Python and browsers share
one position format. Anchors retain up to 64 Unicode code points from a valid
source boundary. A session records navigation, not comprehension.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


SCHEMA = "adhd-md-session"
VERSION = 1
MAX_SESSION_BYTES = 1024 * 1024
MAX_SOURCE_NAME = 4096
MAX_RANGES = 10000
MAX_QUESTIONS = 100
MAX_QUESTION_LENGTH = 1000
ANCHOR_LENGTH = 64
_FIELDS = {"schema", "version", "source", "current", "resume", "presented",
           "skipped", "questions", "paused", "ended"}
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_SURROGATE = re.compile(r"[\ud800-\udfff]")


def _error(message: str) -> ValueError:
    return ValueError("阅读书签：" + message)


def _object(value, fields: set[str], label: str) -> dict:
    if type(value) is not dict:
        raise _error(f"{label} 必须是 JSON 对象。")
    if set(value) != fields:
        raise _error(f"{label} 字段不完整或包含不支持的字段。")
    return value


def _string(value, maximum: int, label: str, *, nonblank: bool = False) -> str:
    if type(value) is not str or len(value) > maximum or _SURROGATE.search(value):
        raise _error(f"{label} 必须是最多 {maximum} 个 Unicode 字符的有效字符串。")
    # Match the browser validator: Python whitespace plus ECMAScript's FEFF.
    if nonblank and all(character.isspace() or character == "\ufeff" for character in value):
        raise _error(f"{label} 不能为空或只有空白。")
    return value


def _integer(value, minimum: int, maximum: int, label: str) -> int:
    # bool is an int subclass, but is never a valid source position or version.
    if type(value) is not int or not minimum <= value <= maximum:
        raise _error(f"{label} 必须是 {minimum}–{maximum} 之间的整数。")
    return value


def _source(data: dict) -> tuple[str, dict]:
    if type(data) is not dict or type(data.get("source_text")) is not str:
        raise _error("当前文档缺少有效的原文数据。")
    text = data["source_text"]
    if _SURROGATE.search(text):
        raise _error("当前原文含无效的 Unicode 字符。")
    name = _string(data.get("source_name"), MAX_SOURCE_NAME, "当前来源名称")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if data.get("source_hash") != digest:
        raise _error("当前文档的内容哈希与原文不一致，请重新生成阅读数据。")
    length = len(text.encode("utf-16-le")) // 2
    return text, {"name": name, "hash": digest, "length": length}


def _indices_at_offsets(text: str, requested: set[int]) -> dict[int, int]:
    """Resolve requested UTF-16 boundaries in one scan, without a per-char map."""
    ordered = sorted(requested)
    if not ordered:
        return {}
    found = {}
    cursor = 0
    target = 0
    for index, character in enumerate(text):
        if ordered[target] == cursor:
            found[cursor] = index
            target += 1
            if target == len(ordered):
                return found
        cursor += 2 if ord(character) > 0xFFFF else 1
        if ordered[target] < cursor:
            raise _error("位置或范围端点落在 Unicode 字符中间；请重新定位后导出书签。")
    if target < len(ordered) and ordered[target] == cursor:
        found[cursor] = len(text)
        target += 1
    if target != len(ordered):
        raise _error("位置或范围端点超出原文。")
    return found


def _ranges(value, length: int, label: str) -> list[list[int]]:
    if type(value) is not list or len(value) > MAX_RANGES:
        raise _error(f"{label} 必须是最多 {MAX_RANGES} 项的数组。")
    checked = []
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise _error(f"{label} 的每项必须是 [起点, 终点] 数组。")
        start = _integer(item[0], 0, length, label + "起点")
        end = _integer(item[1], 0, length, label + "终点")
        if start >= end:
            raise _error(f"{label} 的起点必须小于终点。")
        checked.append([start, end])
    checked.sort()
    merged = []
    for start, end in checked:
        if merged and start < merged[-1][1]:
            raise _error(f"{label} 含重叠范围。")
        if merged and start == merged[-1][1]:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    return merged


def create_session(data: dict) -> dict:
    """Create a fresh session, including for an empty source at offset zero."""
    text, source = _source(data)
    position = {"offset": 0, "anchor": text[:ANCHOR_LENGTH]}
    return {"schema": SCHEMA, "version": VERSION, "source": source,
            "current": dict(position), "resume": dict(position),
            "presented": [], "skipped": [], "questions": [],
            "paused": False, "ended": False}


def validate_session(session, data: dict) -> dict:
    """Return a fresh normalized session, rejecting mismatched or unsafe input.

    Adjacent ranges are merged; overlapping ranges, including overlaps between
    presented and skipped, are rejected. Source names may change. Hashes,
    lengths and both exact source anchors must match the current document.
    """
    session = _object(session, _FIELDS, "书签")
    if type(session["schema"]) is not str or session["schema"] != SCHEMA:
        raise _error("不支持此书签格式，需要 adhd-md-session。")
    if type(session["version"]) is not int or session["version"] != VERSION:
        raise _error("不支持此书签版本，当前仅支持版本 1。")
    text, expected_source = _source(data)
    source = _object(session["source"], {"name", "hash", "length"}, "来源")
    _string(source["name"], MAX_SOURCE_NAME, "来源名称")
    if type(source["hash"]) is not str or not _HASH.fullmatch(source["hash"]):
        raise _error("来源哈希必须是 64 位小写 SHA-256 字符串。")
    if type(source["length"]) is not int or source["length"] < 0:
        raise _error("来源长度必须是非负整数。")
    if source["hash"] != expected_source["hash"] or source["length"] != expected_source["length"]:
        raise _error("书签与当前原文不匹配（内容哈希或 UTF-16 长度不同）；请使用对应版本的原文，首版不自动跨版本定位。")
    length = expected_source["length"]
    positions = {}
    requested = set()
    for key in ("current", "resume"):
        position = _object(session[key], {"offset", "anchor"}, key + " 位置")
        offset = _integer(position["offset"], 0, length, key + " 位置")
        anchor = _string(position["anchor"], ANCHOR_LENGTH, key + " 原文锚点")
        positions[key] = {"offset": offset, "anchor": anchor}
        requested.add(offset)
    # Validate all original endpoints before merging, so adjacent ranges cannot
    # hide a boundary that cuts an astral Unicode character in half.
    for key in ("presented", "skipped"):
        value = session[key]
        if type(value) is not list or len(value) > MAX_RANGES:
            raise _error(f"{key} 必须是最多 {MAX_RANGES} 项的数组。")
        for item in value:
            if type(item) is not list or len(item) != 2:
                raise _error(f"{key} 的每项必须是 [起点, 终点] 数组。")
            requested.update(_integer(endpoint, 0, length, key + " 范围端点") for endpoint in item)
    presented = _ranges(session["presented"], length, "已带读范围")
    skipped = _ranges(session["skipped"], length, "跳过范围")
    left = right = 0
    while left < len(presented) and right < len(skipped):
        first, second = presented[left], skipped[right]
        if max(first[0], second[0]) < min(first[1], second[1]):
            raise _error("已带读范围与跳过范围重叠，不能将跳过内容计为已带读。")
        if first[1] <= second[1]:
            left += 1
        else:
            right += 1
    indices = _indices_at_offsets(text, requested)
    for key, position in positions.items():
        index = indices[position["offset"]]
        if position["anchor"] != text[index:index + ANCHOR_LENGTH]:
            raise _error(f"{key} 的原文锚点与当前位置不一致，请核对书签和原文。")
    questions = session["questions"]
    if type(questions) is not list or len(questions) > MAX_QUESTIONS:
        raise _error(f"待澄清问题必须是最多 {MAX_QUESTIONS} 项的数组。")
    questions = [_string(question, MAX_QUESTION_LENGTH, "待澄清问题", nonblank=True) for question in questions]
    for key in ("paused", "ended"):
        if type(session[key]) is not bool:
            raise _error(f"{key} 必须是 true 或 false。")
    return {"schema": SCHEMA, "version": VERSION, "source": expected_source,
            **positions, "presented": presented, "skipped": skipped,
            "questions": questions, "paused": session["paused"], "ended": session["ended"]}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _error("JSON 含重复字段。")
        result[key] = value
    return result


def _invalid_constant(value):
    raise _error("JSON 不允许 NaN 或 Infinity。")


def read_session(path, data: dict) -> dict:
    """Read at most 1 MiB of strict UTF-8 JSON and validate its full session."""
    try:
        with Path(path).open("rb") as handle:
            raw = handle.read(MAX_SESSION_BYTES + 1)
    except OSError as exc:
        raise _error(f"无法读取书签文件：{exc}") from exc
    if len(raw) > MAX_SESSION_BYTES:
        raise _error("书签文件超过 1 MiB，请使用完整且大小合规的书签；不会截断导入。")
    try:
        session = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise _error("书签不是有效的 UTF-8 JSON；请只保存 JSON，不要包含 Markdown 代码围栏。") from exc
    except ValueError as exc:
        if str(exc).startswith("阅读书签："):
            raise
        raise _error("书签 JSON 包含无效或过大的数值。") from exc
    return validate_session(session, data)
