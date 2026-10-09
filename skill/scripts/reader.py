"""Lossless reading chunks and a small, safe offline Markdown renderer.

The source is never rewritten. Chunk boundaries are offsets into the original
string; Markdown rendering is only a reading aid, with the original available
alongside it. This intentionally supports a small subset, not arbitrary HTML.
"""
from __future__ import annotations

import bisect
import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*)$")
_LIST = re.compile(r"^( {0,3})([-+*]|[0-9]{1,9}[.)])(?:[ \t]+|$)(.*)$")
_QUOTE = re.compile(r"^ {0,3}>[ \t]?(.*)$")
_RULE = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_SENTENCE = re.compile(r'''(?:[。！？]+[”’」』）》）]*|[.!?]+["')\]]*(?=\s|$))[ \t\r\n]*''')
_INLINE = re.compile(
    r"(?P<code>(?P<ticks>`+)(?P<codebody>.+?)(?P=ticks))"
    r"|(?P<link>!?\[[^\]\n]*\]\((?:[^()\n]|\([^()\n]*\))*\))"
    r"|(?P<strong>\*\*(?=\S)(?:.+?\S|\S)\*\*|__(?=\S)(?:.+?\S|\S)__)"
    r"|(?P<em>\*(?=\S)(?:[^*\n]*?\S|\S)\*|(?<!\w)_(?=\S)(?:[^_\n]*?\S|\S)_(?!\w))"
    r"|(?P<auto><(?:https?://|mailto:)[^<>\s]+>)",
    re.DOTALL,
)


@dataclass
class _Block:
    kind: str
    source: str
    start: int


def _line_text(line: str) -> str:
    return line.rstrip("\r\n")


def _fence(line: str):
    match = _FENCE.match(_line_text(line))
    if match and (match[1][0] != "`" or "`" not in match[2]):
        return match
    return None


def _closing_fence(line: str, opener: str) -> bool:
    return bool(re.fullmatch(r" {0,3}" + re.escape(opener[0]) + "{" + str(len(opener)) + r",}[ \t]*", _line_text(line)))


def _cells(line: str) -> list[str]:
    """Split unescaped table pipes; keep pipe escapes available to the reader."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line)]


def _table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or "|" not in lines[index]:
        return False
    cells = _cells(lines[index + 1])
    return bool(cells) and len(cells) == len(_cells(lines[index])) and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells
    )


def _scan_blocks(text: str) -> list[_Block]:
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    blocks = []
    i = 0
    while i < len(lines):
        start = i
        line = _line_text(lines[i])
        if not line.strip():
            kind = "blank"
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
        elif i == 0 and line.lstrip("\ufeff") == "---" and any(
            _line_text(value) in ("---", "...") for value in lines[1:]
        ):
            kind = "frontmatter"
            i += 1
            while i < len(lines) and _line_text(lines[i]) not in ("---", "..."):
                i += 1
            i += 1
        elif _fence(line):
            kind = "fence"
            opener = _fence(line)[1]
            i += 1
            while i < len(lines):
                close = _closing_fence(lines[i], opener)
                i += 1
                if close:
                    break
        elif _HEADING.match(line):
            kind = "heading"
            i += 1
        elif _table_start(lines, i):
            kind = "table"
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                i += 1
        elif i + 1 < len(lines) and _SETEXT.match(_line_text(lines[i + 1])):
            kind = "heading"
            i += 2
        elif _RULE.match(line):
            kind = "rule"
            i += 1
        elif line.startswith(("    ", "\t")):
            kind = "indented_code"
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith(("    ", "\t"))):
                i += 1
        elif _LIST.match(line):
            kind = "list"
            i += 1
            while i < len(lines):
                current = _line_text(lines[i])
                if not current.strip():
                    # A blank line belongs to a loose list only when the next
                    # meaningful line is another item or an indented body.
                    ahead = i + 1
                    while ahead < len(lines) and not lines[ahead].strip():
                        ahead += 1
                    if ahead >= len(lines) or not (
                        _LIST.match(_line_text(lines[ahead])) or lines[ahead].startswith((" ", "\t"))
                    ):
                        break
                    i = ahead
                    continue
                if not current.startswith((" ", "\t")) and (
                    _HEADING.match(current) or _QUOTE.match(current) or _fence(current) or _RULE.match(current)
                ):
                    break
                i += 1
        elif _QUOTE.match(line):
            kind = "quote"
            i += 1
            while i < len(lines) and lines[i].strip():
                current = _line_text(lines[i])
                if not _QUOTE.match(current) and (
                    _HEADING.match(current) or _fence(current) or _LIST.match(current) or _RULE.match(current)
                ):
                    break
                i += 1
        else:
            kind = "paragraph"
            i += 1
            while i < len(lines) and lines[i].strip():
                current = _line_text(lines[i])
                if (
                    _HEADING.match(current) or _fence(current) or _LIST.match(current)
                    or _QUOTE.match(current) or _RULE.match(current) or _table_start(lines, i)
                    or (i + 1 < len(lines) and _SETEXT.match(_line_text(lines[i + 1])))
                ):
                    break
                i += 1
        blocks.append(_Block(kind, text[offsets[start]:offsets[i]], offsets[start]))
    return blocks


def _heading(block: _Block) -> tuple[int, str]:
    lines = block.source.splitlines()
    match = _HEADING.match(lines[0])
    if match:
        return len(match[1]), re.sub(r"[ \t]+#+[ \t]*$", "", match[2]).strip()
    return (1 if lines[-1].lstrip().startswith("=") else 2), lines[0].strip()


def _plain_title(value: str) -> str:
    def plain(match):
        token = match[0]
        if match.group("code"):
            return match.group("codebody")
        if match.group("link"):
            start = 2 if token.startswith("!") else 1
            return token[start:token.index("](")]
        if match.group("strong"):
            return token[2:-2]
        if match.group("em"):
            return token[1:-1]
        return token[1:-1]
    return _INLINE.sub(plain, value).strip()


def _plain_blocks(text: str) -> list[_Block]:
    blocks = []
    offset = 0
    for line in text.splitlines(keepends=True):
        kind = "paragraph" if line.strip() else "blank"
        if blocks and blocks[-1].kind == kind:
            blocks[-1].source += line
        else:
            blocks.append(_Block(kind, line, offset))
        offset += len(line)
    return blocks


def _paragraph_pieces(block: _Block, target: int) -> list[_Block]:
    if block.kind != "paragraph" or len(block.source) <= target:
        return [block]
    # Do not break an inline code span, emphasis, image or link at punctuation.
    protected = [(match.start(), match.end()) for match in _INLINE.finditer(block.source)]
    boundaries = [match.end() for match in _SENTENCE.finditer(block.source)
                  if not any(left < match.end() < right for left, right in protected)]
    if not boundaries or boundaries[-1] != len(block.source):
        boundaries.append(len(block.source))
    pieces = []
    start = 0
    previous = 0
    for end in boundaries:
        if end - start > target and previous > start:
            pieces.append(_Block("paragraph", block.source[start:previous], block.start + start))
            start = previous
        previous = end
    if start < len(block.source):
        pieces.append(_Block("paragraph", block.source[start:], block.start + start))
    return pieces


def _safe_url(destination: str):
    destination = html.unescape(destination).strip()
    if not destination or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in destination):
        return None
    try:
        parsed = urlsplit(destination)
    except ValueError:
        return None
    if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
        return destination
    if parsed.scheme.lower() == "mailto" and parsed.path:
        return destination
    return None


def _link(label: str, destination: str) -> str:
    safe = _safe_url(destination)
    if safe:
        return '<a href="{}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">{}</a>'.format(
            html.escape(safe, quote=True), label
        )
    return '<span class="reader-inert-link">{} ({})</span>'.format(label, html.escape(destination))


def _inline(text: str, depth: int = 0) -> str:
    if depth > 12:
        return html.escape(text)
    output = []
    cursor = 0
    for match in _INLINE.finditer(text):
        output.append(html.escape(text[cursor:match.start()]))
        token = match[0]
        if match.group("code"):
            output.append("<code>" + html.escape(match.group("codebody")) + "</code>")
        elif match.group("link"):
            bracket = token.index("](")
            label = token[2:bracket] if token.startswith("!") else token[1:bracket]
            destination = token[bracket + 2:-1].strip()
            parsed = re.fullmatch(r'''(?:<([^>\n]*)>|(\S+?))(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?''', destination)
            if parsed:
                destination = parsed[1] if parsed[1] is not None else parsed[2]
            label_html = _inline(label, depth + 1)
            if token.startswith("!"):
                # Images never request remote resources. An explicit link is
                # available for safe schemes; raw source retains every detail.
                output.append('<span class="reader-image">[图片：' + label_html + " · " + _link("查看链接", destination) + "]</span>")
            else:
                output.append(_link(label_html, destination))
        elif match.group("strong"):
            output.append("<strong>" + _inline(token[2:-2], depth + 1) + "</strong>")
        elif match.group("em"):
            output.append("<em>" + _inline(token[1:-1], depth + 1) + "</em>")
        else:
            output.append(_link(html.escape(token[1:-1]), token[1:-1]))
        cursor = match.end()
    output.append(html.escape(text[cursor:]))
    return "".join(output)


def _render_list(source: str, depth: int) -> str:
    lines = source.splitlines(keepends=True)
    result = []
    group = None
    item_lines = []
    item_value = ""
    content_indent = 0
    base_indent = len(_LIST.match(_line_text(lines[0]))[1])

    def finish_item():
        if item_lines:
            result.append("<li" + item_value + ">" + _render_markdown("".join(item_lines), depth + 1) + "</li>")
            item_lines.clear()

    for line in lines:
        match = _LIST.match(_line_text(line))
        if match and len(match[1]) == base_indent:
            finish_item()
            new_group = "ol" if match[2][0].isdigit() else "ul"
            item_value = ' value="{}"'.format(int(match[2][:-1])) if new_group == "ol" else ""
            if group != new_group:
                if group:
                    result.append("</" + group + ">")
                group = new_group
                start = ' start="{}"'.format(int(match[2][:-1])) if group == "ol" else ""
                result.append("<" + group + start + ">")
            content_indent = match.start(3)
            ending = line[len(_line_text(line)):]
            item_lines.append(match[3] + ending)
        else:
            indentation = len(line) - len(line.lstrip(" "))
            item_lines.append(line[min(indentation, content_indent):])
    finish_item()
    if group:
        result.append("</" + group + ">")
    return "".join(result)


def _render_markdown(source: str, depth: int = 0) -> str:
    if depth > 12:
        return "<pre>" + html.escape(source) + "</pre>"
    output = []
    for block in _scan_blocks(source):
        lines = block.source.splitlines(keepends=True)
        if block.kind == "blank":
            continue
        if block.kind == "heading":
            level, title = _heading(block)
            output.append("<h{0}>{1}</h{0}>".format(level, _inline(title)))
        elif block.kind in ("fence", "indented_code", "frontmatter"):
            if block.kind == "fence":
                opener = _fence(lines[0])[1]
                end = len(lines) - 1 if len(lines) > 1 and _closing_fence(lines[-1], opener) else len(lines)
                body = "".join(lines[1:end])
            elif block.kind == "indented_code":
                body = "".join(line[1:] if line.startswith("\t") else line[4:] if line.startswith("    ") else line for line in lines)
            else:
                body = block.source
            output.append("<pre><code>" + html.escape(body) + "</code></pre>")
        elif block.kind == "table":
            rows = [_cells(line) for line in lines]
            output.append('<div class="reader-table"><table><thead><tr>' + "".join("<th>" + _inline(cell) + "</th>" for cell in rows[0]) + "</tr></thead><tbody>")
            for row in rows[2:]:
                output.append("<tr>" + "".join("<td>" + _inline(cell) + "</td>" for cell in row) + "</tr>")
            output.append("</tbody></table></div>")
        elif block.kind == "list":
            output.append(_render_list(block.source, depth))
        elif block.kind == "quote":
            body = "".join(re.sub(r"^ {0,3}>[ \t]?", "", line) for line in lines)
            output.append("<blockquote>" + _render_markdown(body, depth + 1) + "</blockquote>")
        elif block.kind == "rule":
            output.append("<hr>")
        else:
            output.append("<p>" + _inline(block.source.strip()) + "</p>")
    return "\n".join(output)


def build_reading_data(text: str, source_name: str, chunk_size: int = 900) -> dict:
    """Prepare lossless reading chunks; chunk_size is a soft character target.

    Sentences and structural blocks may exceed the target. start_line/end_line
    are inclusive and can overlap when a paragraph is split on a single line.
    Whitespace-only input still produces a chunk, so concatenation always works.
    """
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    is_plain = Path(source_name).suffix.lower() in (".txt", ".text")
    blocks = _plain_blocks(text) if is_plain else _scan_blocks(text)
    fallback = Path(source_name).stem or source_name or "未命名文档"
    title = next((_plain_title(_heading(block)[1]) for block in blocks if block.kind == "heading"), fallback)
    title = title or fallback
    line_starts = [0]
    for line in text.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))
    chunks = []
    current = []
    current_length = 0
    has_body = False
    section_title = title
    chunk_title = title

    def flush():
        nonlocal current_length, has_body
        if not current:
            return
        source = "".join(piece.source for piece in current)
        offset = current[0].start
        chunks.append({
            "index": len(chunks),
            "title": chunk_title,
            "start_line": bisect.bisect_right(line_starts, offset),
            "end_line": bisect.bisect_right(line_starts, offset + len(source) - 1),
            "source": source,
            "html": ('<p class="reader-plain">' + html.escape(source) + '</p>') if is_plain else _render_markdown(source),
        })
        current.clear()
        current_length = 0
        has_body = False

    for block in blocks:
        for piece in _paragraph_pieces(block, chunk_size):
            if piece.kind == "heading":
                if has_body:
                    flush()
                section_title = _plain_title(_heading(piece)[1]) or section_title
                if not has_body:
                    chunk_title = section_title
            elif piece.kind != "blank" and has_body and current_length + len(piece.source) > chunk_size:
                flush()
            if not current:
                chunk_title = section_title
            current.append(piece)
            current_length += len(piece.source)
            has_body = has_body or piece.kind not in ("blank", "heading")
    flush()
    return {
        "title": title,
        "source_name": source_name,
        "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_text": text,
        "chunks": chunks,
    }


def render_reader(data: dict) -> str:
    """Embed data in the packaged, self-contained reader without script escape."""
    template = Path(__file__).resolve().parents[1] / "assets" / "reader.html"
    with template.open(encoding="utf-8", newline="") as handle:
        page = handle.read()
    marker = "__ADHD_READER_DATA__"
    if page.count(marker) != 1:
        raise ValueError("reader.html must contain exactly one reading-data marker")
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for character, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        serialized = serialized.replace(character, escaped)
    return page.replace(marker, serialized)
