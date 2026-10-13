#!/usr/bin/env python3
"""Validate rule definitions and generate their Markdown representations.

The canonical data lives in skill/references/rule-definitions.json. Explanatory
prose remains hand-maintained; tables are generated and checked for drift.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "skill/references/rule-definitions.json"
RULES_MD = ROOT / "skill/references/rules.md"
RUBRIC_MD = ROOT / "skill/references/rubric.md"
EVIDENCE_MD = ROOT / "skill/references/evidence.md"
RUNTIME_PY = ROOT / "skill/scripts/adhd_md.py"

GROUPS = {
    "S": "骨架", "H": "首屏", "P": "分块", "L": "列表", "W": "句子",
    "A": "行动性", "N": "导航", "T": "排版", "C": "中文专项", "M": "去 AI 味",
    "X": "反模式",
}
STATUS_LABELS = {
    "audit": "脚本检查", "advisory": "仅提示", "format": "自动修复",
    "judge": "人工/模型判断", "gate": "verify 硬门禁",
}
METHOD_LABELS = {"det": "det", "lint": "lint", "judge": "judge", "det/lint": "det/lint", "verify": "verify"}
DIMENSION_ORDER = ["hook", "chunk", "scan", "sentence", "action", "typo", "human"]
LEVEL_LABELS = {1: "light", 2: "standard", 3: "deep"}


class DefinitionError(ValueError):
    pass


def load_definitions() -> dict:
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DefinitionError(f"无法读取规则定义 {DATA.relative_to(ROOT)}：{exc}") from exc
    validate(data)
    return data


def validate(data: dict) -> None:
    if data.get("schema_version") != 1:
        raise DefinitionError("schema_version 必须为 1")
    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSION_ORDER):
        raise DefinitionError("评分维度必须完整且仅包含七个已定义维度")
    if sum(item.get("weight", 0) for item in dimensions.values()) != 100:
        raise DefinitionError("评分维度权重之和必须为 100")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise DefinitionError("rules 必须是非空数组")
    ids: set[str] = set()
    score_ids: set[str] = set()
    finding_owner: dict[str, dict] = {}
    valid_groups = {"S", "H", "P", "L", "W", "A", "N", "T", "C", "M", "X"}
    valid_status = set(STATUS_LABELS)
    valid_automation = set(METHOD_LABELS)
    for rule in rules:
        rid = rule.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"[A-Z][0-9]+", rid):
            raise DefinitionError(f"规则 ID 非法：{rid!r}")
        if rid in ids:
            raise DefinitionError(f"规则 ID 重复：{rid}")
        ids.add(rid)
        if rule.get("group") not in valid_groups or rule.get("group") != rid[0]:
            raise DefinitionError(f"{rid} 的 group 与 ID 不一致")
        if rule.get("axis") not in {"F", "C", "both"}:
            raise DefinitionError(f"{rid} 的 axis 必须为 F、C 或 both")
        if type(rule.get("min_level")) is not int or rule["min_level"] not in (1, 2, 3):
            raise DefinitionError(f"{rid} 的 min_level 必须是 1、2 或 3")
        if rule.get("automation") not in valid_automation:
            raise DefinitionError(f"{rid} 的 automation 非法：{rule.get('automation')!r}")
        if rule.get("status") not in valid_status:
            raise DefinitionError(f"{rid} 的 status 非法：{rule.get('status')!r}")
        if rule.get("evidence_group") not in {"S", "H", "P/L/W", "A", "N", "T", "M", "X"}:
            raise DefinitionError(f"{rid} 的 evidence_group 无效")
        if not isinstance(rule.get("name"), str) or not rule["name"].strip():
            raise DefinitionError(f"{rid} 缺少规则名称")
        if not isinstance(rule.get("threshold"), str):
            raise DefinitionError(f"{rid} 缺少阈值或判据说明")
        if not isinstance(rule.get("scoring"), list):
            raise DefinitionError(f"{rid} 缺少 scoring 声明；没有扣分时也必须显式使用空数组")
        expected_method = {"audit": {"det", "lint", "det/lint"},
                           "advisory": {"lint"}, "format": {"det"},
                           "judge": {"judge"}, "gate": {"verify"}}[rule["status"]]
        if rule["automation"] not in expected_method:
            raise DefinitionError(f"{rid} 的自动化类型 {rule['automation']} 与状态 {rule['status']} 不匹配")
        finding_ids = rule.get("finding_ids", [])
        if rule["status"] in {"audit", "advisory"} and not finding_ids:
            raise DefinitionError(f"{rid} 缺少 finding_ids")
        if rule["status"] not in {"audit", "advisory"} and finding_ids:
            raise DefinitionError(f"{rid} 的状态不产出 finding，却声明了 finding_ids")
        for finding_id in finding_ids:
            if not re.fullmatch(r"[A-Z][0-9]+[a-z]?", finding_id):
                raise DefinitionError(f"{rid} 的 finding ID 非法：{finding_id!r}")
            if finding_id in finding_owner:
                raise DefinitionError(f"finding ID 被多条规则占用：{finding_id}")
            finding_owner[finding_id] = rule
        for component in rule.get("scoring", []):
            cid = component.get("id")
            if not isinstance(cid, str) or not re.fullmatch(r"[A-Z][0-9]+[a-z]?", cid):
                raise DefinitionError(f"{rid} 的评分组件 ID 非法：{cid!r}")
            if cid in score_ids:
                raise DefinitionError(f"评分组件 ID 重复：{cid}")
            score_ids.add(cid)
            dimension = component.get("dimension")
            if dimension != "global" and dimension not in dimensions:
                raise DefinitionError(f"{cid} 的评分维度无效：{dimension!r}")
            if type(component.get("points")) is not int or component["points"] <= 0:
                raise DefinitionError(f"{cid} 的 points 必须为正整数")
            if type(component.get("cap")) is not int or component["cap"] < component["points"]:
                raise DefinitionError(f"{cid} 的 cap 必须不小于 points")
            if component.get("mode") not in {"per_finding", "once"}:
                raise DefinitionError(f"{cid} 的 mode 必须为 per_finding 或 once")
            if not isinstance(component.get("label"), str) or not component["label"].strip():
                raise DefinitionError(f"{cid} 缺少评分说明")
    expected_ids = 86
    if len(ids) != expected_ids:
        raise DefinitionError(f"规则数量为 {len(ids)}，预期 86（78 条正文规则 + 8 条反模式）")
    if data.get("global_score_cap") != 20:
        raise DefinitionError("全局反模式扣分上限必须为 20")
    validate_thresholds(data.get("thresholds", {}))
    validate_runtime_findings(finding_owner)


def validate_runtime_findings(finding_owner: dict[str, dict]) -> None:
    tree = ast.parse(RUNTIME_PY.read_text(encoding="utf-8"))
    audit_node = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "audit"), None)
    if audit_node is None:
        raise DefinitionError("运行时缺少 audit 函数")
    actual: set[str] = set()
    for node in ast.walk(audit_node):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "Finding":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            raise DefinitionError("Finding 调用的规则 ID 必须是字符串常量")
        rid = node.args[0].value
        actual.add(rid)
        if rid not in finding_owner:
            raise DefinitionError(f"运行时 finding {rid} 未在规则源声明")
        if len(node.args) > 3 and isinstance(node.args[3], ast.Constant):
            axis = node.args[3].value
            declared_axis = finding_owner[rid]["axis"]
            if axis != declared_axis:
                raise DefinitionError(f"{rid} 的运行时 axis={axis} 与规则源 {declared_axis} 不一致")
    missing = set(finding_owner) - actual
    if missing:
        raise DefinitionError("规则源声明了但运行时代码没有 Finding：" + ", ".join(sorted(missing)))


def validate_thresholds(thresholds: dict) -> None:
    language = thresholds.get("language", {})
    if set(language) != {"en", "zh"}:
        raise DefinitionError("thresholds.language 必须包含 en 和 zh")
    keys = {"para", "section", "sent_mean", "sent_p90", "tldr", "frag"}
    for lang, values in language.items():
        if set(values) != keys or any(type(v) is not int or v <= 0 for v in values.values()):
            raise DefinitionError(f"{lang} 语言阈值字段缺失或非法")
    limits = thresholds.get("limits", {})
    expected = {
        "H1": {"max_lines", "max_summary_sentences", "max_summary_units"},
        "H2": {"max_items"}, "P1": {"max_sentences"}, "P4": {"max_consecutive_lines"},
        "L1": {"max_depth"}, "L3": {"min_items"}, "L5": {"max_lines"}, "L6": {"max_items"},
        "N1": {"max_lines_without_toc"}, "N3": {"min_h2_sections"},
        "N5": {"max_columns", "max_rows"}, "C3": {"min_units", "min_commas"},
        "C5": {"min_de_count"}, "T2": {"max_bold_ratio", "max_bold_per_paragraph"},
        "X2": {"min_lines_per_heading", "min_plain_prose_sections"},
        "X5": {"max_bold_ratio"}, "M5": {"dashes_per_thousand_han"},
        "M13": {"number_context"}, "M14": {"min_chain_count"}, "S7": {"min_lines"},
    }
    missing = set(expected) - set(limits)
    if missing:
        raise DefinitionError(f"limits 缺少规则参数：{', '.join(sorted(missing))}")
    for rid, fields in expected.items():
        if set(limits[rid]) != fields:
            raise DefinitionError(f"{rid} 参数应为 {sorted(fields)}")
    if set(limits["H1"]["max_summary_units"]) != {"en", "zh"}:
        raise DefinitionError("H1 max_summary_units 必须包含 en 和 zh")

    def positive_numbers(value, path):
        if isinstance(value, dict):
            for child, item in value.items():
                positive_numbers(item, f"{path}.{child}")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if value <= 0:
                raise DefinitionError(f"阈值必须为正数：{path}")
        else:
            raise DefinitionError(f"阈值类型非法：{path}")

    for rid, parameters in limits.items():
        positive_numbers(parameters, rid)


def _table_after_heading(markdown: str, heading: str, table: str) -> str:
    start = markdown.find(heading)
    if start < 0:
        raise DefinitionError(f"找不到文档标题：{heading}")
    next_heading = re.search(r"(?m)^#{1,6} ", markdown[start + len(heading):])
    end = start + len(heading) + next_heading.start() if next_heading else len(markdown)
    section = markdown[start:end]
    lines = section.splitlines()
    replacement = ["<!-- generated:rules:start -->", *table.rstrip().splitlines(), "<!-- generated:rules:end -->"]
    marker_start = next((i for i, line in enumerate(lines) if line == "<!-- generated:rules:start -->"), None)
    if marker_start is not None:
        marker_end = next((i for i in range(marker_start + 1, len(lines))
                           if lines[i] == "<!-- generated:rules:end -->"), None)
        if marker_end is None:
            raise DefinitionError(f"{heading} 的生成标记不成对")
        lines[marker_start:marker_end + 1] = replacement
        after = marker_start + len(replacement)
    else:
        table_start = next((i for i, line in enumerate(lines) if line.startswith("|")), None)
        if table_start is None:
            raise DefinitionError(f"{heading} 下找不到表格")
        table_end = table_start
        while table_end < len(lines) and lines[table_end].startswith("|"):
            table_end += 1
        lines[table_start:table_end] = replacement
        after = table_start + len(replacement)
    while after < len(lines) and lines[after] == "":
        del lines[after]
    if after < len(lines):
        lines.insert(after, "")
    updated_section = "\n".join(lines)
    return markdown[:start] + updated_section.rstrip() + "\n\n" + markdown[end:]


def _escape_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def normalize_heading_boundaries(markdown: str) -> str:
    """Repair boundaries left by older generator versions before replacing tables."""
    return re.sub(r"([^\n])(?=## (?:[A-Z] 组|维度 [1-7]))", r"\1\n\n", markdown)


def render_rule_table(data: dict, group: str) -> str:
    rules = [r for r in data["rules"] if r["group"] == group]
    if group == "X":
        lines = ["| ID | 反模式 | 判据 | 后果 | 评分 | 实现状态 |", "|---|---|---|---|---|---|"]
        for rule in rules:
            row = [rule["id"], rule["name"], rule["threshold"], rule["outcome"],
                   "扣分" if rule.get("scoring") else "不计分", STATUS_LABELS[rule["status"]]]
            lines.append("| " + " | ".join(map(_escape_cell, row)) + " |")
        return "\n".join(lines)
    lines = ["| ID | 规则 | 轴·最低档位 | 自动化 | 实现状态 | 评分 | 判据 |", "|---|---|---|---|---|---|---|"]
    for rule in rules:
        axis = "F/C" if rule["axis"] == "both" else rule["axis"]
        level = f"{axis}·{rule['min_level']} ({LEVEL_LABELS[rule['min_level']]})"
        row = [rule["id"], rule["name"], level, METHOD_LABELS[rule["automation"]],
               STATUS_LABELS[rule["status"]], "扣分" if rule.get("scoring") else "不计分", rule["threshold"]]
        lines.append("| " + " | ".join(map(_escape_cell, row)) + " |")
    return "\n".join(lines)


def render_rules(data: dict, original: str) -> str:
    result = normalize_heading_boundaries(original)
    for group in "SHPLWANTCMX":
        heading = f"## {group} 组"
        result = _table_after_heading(result, heading, render_rule_table(data, group))
    return result


def render_rubric_table(data: dict, dimension: str) -> str:
    components = [c for r in data["rules"] for c in r.get("scoring", [])
                  if c["dimension"] == dimension]
    lines = ["| 命中 | 每次扣分 | 上限 |", "|---|---:|---:|"]
    for component in components:
        cap = "—" if component["cap"] == component["points"] else str(component["cap"])
        lines.append(f"| {_escape_cell(component['label'])}（{component['id']}） | {component['points']} | {cap} |")
    return "\n".join(lines)


def render_x_rubric(data: dict) -> str:
    rows = ["| 反模式 | 扣分 | 谁判定 |", "|---|---:|---|"]
    for rule in data["rules"]:
        if rule["group"] != "X":
            continue
        for component in rule.get("scoring", []):
            who = "脚本" if rule["status"] == "audit" else "模型"
            rows.append(f"| {component['label']} | {component['points']} | {who} |")
        if rule["id"] == "X4":
            rows.append("| X4 删信息 | — | **硬失败，不进评分，直接拒绝写回** |")
    return "\n".join(rows)


def render_rubric(data: dict, original: str) -> str:
    result = normalize_heading_boundaries(original)
    headings = {
        "hook": "## 维度 1 · 首屏结论力", "chunk": "## 维度 2 · 分块粒度",
        "scan": "## 维度 3 · 扫读性", "sentence": "## 维度 4 · 句子负荷",
        "action": "## 维度 5 · 行动性", "typo": "## 维度 6 · 排版一致性",
        "human": "## 维度 7 · 活人感",
    }
    for dimension in DIMENSION_ORDER:
        result = _table_after_heading(result, headings[dimension], render_rubric_table(data, dimension))
    result = _table_after_heading(result, "## X 组 · 全局扣分", render_x_rubric(data))
    return result


def render_evidence_index(data: dict, original: str) -> str:
    start_marker = "<!-- generated:rule-evidence:start -->"
    end_marker = "<!-- generated:rule-evidence:end -->"
    lines = [start_marker, "## 附录 · 规则实现与证据索引", "",
             "每条规则的状态、是否计分和所属机制说明均由 `rule-definitions.json` 生成；证据等级见本文件前文。", "",
             "| ID | 轴 | 最低档位 | 实现状态 | 评分 | 机制分组 |", "|---|---|---:|---|---|---|"]
    for rule in data["rules"]:
        axis = "F/C" if rule["axis"] == "both" else rule["axis"]
        lines.append(f"| {rule['id']} | {axis} | {LEVEL_LABELS[rule['min_level']]} | "
                     f"{STATUS_LABELS[rule['status']]} | {'扣分' if rule.get('scoring') else '不计分'} | "
                     f"{rule['evidence_group']} |")
    lines.append(end_marker)
    generated = "\n".join(lines)
    if start_marker in original or end_marker in original:
        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
        if not pattern.search(original):
            raise DefinitionError("evidence.md 的生成标记不成对")
        return pattern.sub(lambda _: generated, original)
    return original.rstrip() + "\n\n" + generated + "\n"


def expected_files(data: dict) -> dict[Path, str]:
    return {
        RULES_MD: render_rules(data, RULES_MD.read_text(encoding="utf-8")),
        RUBRIC_MD: render_rubric(data, RUBRIC_MD.read_text(encoding="utf-8")),
        EVIDENCE_MD: render_evidence_index(data, EVIDENCE_MD.read_text(encoding="utf-8")),
    }


def main(argv: list[str]) -> int:
    check = "--check" in argv
    try:
        data = load_definitions()
        files = expected_files(data)
    except (DefinitionError, OSError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    drift = []
    for path, expected in files.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual == expected:
            continue
        if check:
            drift.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(expected, encoding="utf-8")
            print(f"已生成：{path.relative_to(ROOT)}")
    if drift:
        print("生成文件与规则源不同步：" + ", ".join(drift), file=sys.stderr)
        print("运行 python3 scripts/build_rules.py 更新生成表格。", file=sys.stderr)
        return 1
    if check:
        print("✓ 规则定义、规则表、评分表和证据索引同步")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
