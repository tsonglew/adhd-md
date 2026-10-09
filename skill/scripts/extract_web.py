"""Bounded HTTP fetching and conservative HTML-to-reading-text extraction.

This module uses only the standard library. It never runs JavaScript or loads
subresources. Visible text outside a semantic main/article region is retained
in an appendix; the complete decoded HTML is also returned for inspection.
"""
from __future__ import annotations

import codecs
from dataclasses import dataclass, field
from html.parser import HTMLParser
from http.client import HTTPException
import math
from pathlib import Path
import re
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_REDIRECTS = 6
_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_HIDDEN = frozenset("head title script style template".split())
_BLOCK = frozenset(("address article aside blockquote body caption dd details dialog div dl dt "
                    "fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr "
                    "li main nav ol p pre section summary table tbody td tfoot th thead tr ul").split())
_SPACE = re.compile(r"[\t\n\r\f ]+")


def _http_url(url: str) -> str:
    if not isinstance(url, str) or not url:
        raise ValueError("请提供完整的 http:// 或 https:// 网页地址。")
    if any(ord(c) < 32 or ord(c) == 127 for c in url) or "\\" in url:
        raise ValueError("网页地址包含控制字符或反斜杠，请复制完整、有效的 URL。")
    try:
        parts = urlsplit(url)
        if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
            raise ValueError("仅支持 http:// 和 https:// 网页地址。")
        if parts.username is not None or parts.password is not None:
            raise ValueError("网页地址不能包含用户名或密码，请使用公开链接或导出的 HTML 文件。")
        port = parts.port
        hostname = parts.hostname.encode("idna").decode("ascii")
        if any(c.isspace() for c in hostname):
            raise ValueError("网页地址的主机名无效。")
        host = "[" + hostname + "]" if ":" in hostname else hostname
        if port is not None:
            host += ":" + str(port)
        return urlunsplit((parts.scheme.lower(), host,
                           quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
                           quote(parts.query, safe="/%?:@!$&'()*+,;=-._~"), ""))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("无效的网页地址：" + str(exc)) from exc


class _SafeRedirects(HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS
    max_repeats = 3

    def __init__(self, deadline=None):
        super().__init__()
        self.deadline = deadline

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib already resolves Location against the current request URL.
        return super().redirect_request(req, fp, code, msg, headers, _http_url(newurl))

    def http_error_302(self, req, fp, code, msg, headers):
        location = headers.get("Location") or headers.get("URI")
        if not location:
            return None
        try:
            if any(ord(c) < 32 or ord(c) == 127 for c in location):
                raise ValueError("网页重定向地址包含控制字符，请使用浏览器中的最终地址。")
            count = getattr(req, "_adhd_redirect_count", 0)
            if count >= self.max_redirections:
                raise ValueError("网页重定向过多，请复制浏览器中的最终地址。")
            destination = _http_url(urljoin(req.full_url, location))
            redirected = self.redirect_request(req, fp, code, msg, headers, destination)
            if redirected is None:
                return None
            redirected._adhd_redirect_count = count + 1
        finally:
            # The default handler reads the entire redirect body before
            # closing it. We do not need that body and must keep it bounded.
            fp.close()
        remaining = self.deadline - time.monotonic() if self.deadline is not None else req.timeout
        if remaining <= 0:
            raise TimeoutError()
        return self.parent.open(redirected, timeout=remaining)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


def fetch_url(url: str, timeout: float = 20) -> dict:
    """Fetch at most 20 MiB, following only validated HTTP(S) redirects."""
    url = _http_url(url)
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("网页下载超时必须是大于 0 的有限秒数。")
    started = time.monotonic()
    request = Request(url, headers={
        "User-Agent": "adhd-md/1.0 (reading-text extractor)",
        "Accept": "text/html, application/xhtml+xml, application/pdf, text/plain;q=0.8, */*;q=0.1",
        "Accept-Encoding": "identity",
    })
    try:
        with build_opener(_SafeRedirects(started + timeout)).open(request, timeout=timeout) as response:
            final_url = _http_url(response.geturl())
            headers = response.headers
            encoding = (headers.get("Content-Encoding") or "identity").lower().strip()
            if encoding not in ("", "identity"):
                raise ValueError("网站忽略了未压缩下载请求，请在浏览器中保存网页或 PDF 后再导入。")
            length = headers.get("Content-Length", "")
            if length.isdigit() and int(length) > MAX_DOWNLOAD_BYTES:
                raise ValueError("下载内容超过 20 MiB，请先保存到本地再处理。")
            parts = []
            size = 0
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError()
                # HTTPResponse.read1 returns after one underlying read, so slow
                # responses cannot reset the complete-download deadline forever.
                raw = getattr(getattr(response, "fp", None), "raw", None)
                connection = getattr(raw, "_sock", None)
                if connection is not None:
                    connection.settimeout(remaining)
                read = getattr(response, "read1", response.read)
                chunk = read(min(65536, MAX_DOWNLOAD_BYTES + 1 - size))
                if time.monotonic() - started > timeout:
                    raise TimeoutError()
                if not chunk:
                    break
                parts.append(chunk)
                size += len(chunk)
                if size > MAX_DOWNLOAD_BYTES:
                    raise ValueError("下载内容超过 20 MiB，请先保存到本地再处理。")
            if length.isdigit() and size < int(length):
                raise ValueError("网页下载不完整，请重试或在浏览器中保存到本地后导入。")
            return {"body": b"".join(parts), "url": final_url,
                    "content_type": headers.get_content_type().lower() if headers.get("Content-Type") else "",
                    "charset": headers.get_content_charset()}
    except HTTPError as exc:
        exc.close()
        if exc.code in (401, 403):
            message = "网站要求登录或拒绝下载，请在已登录的浏览器中保存 HTML 或 PDF 后导入。"
        elif 300 <= exc.code < 400:
            message = "网页重定向过多或重定向地址不受支持，请复制浏览器中的最终地址。"
        else:
            message = "网页下载失败（HTTP {}），请检查地址或稍后重试。".format(exc.code)
        raise ValueError(message) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise ValueError("网页下载超时，请检查网络或先在浏览器中保存到本地。") from exc
    except (URLError, OSError, HTTPException) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise ValueError("网页下载超时，请检查网络或先在浏览器中保存到本地。") from exc
        raise ValueError("无法下载网页，请检查网络、证书和地址，或先保存到本地：{}".format(reason)) from exc


def decode_html(body: bytes, charset: str | None = None) -> str:
    """Decode without replacing or dropping bytes; honor BOM/header/meta hints."""
    if not body:
        raise ValueError("网页为空，请检查地址或导入浏览器保存的 HTML 文件。")
    hints = []
    for signature, encoding in ((codecs.BOM_UTF32_LE, "utf-32"), (codecs.BOM_UTF32_BE, "utf-32"),
                                (codecs.BOM_UTF8, "utf-8-sig"),
                                (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16")):
        if body.startswith(signature):
            hints.append(encoding)
            break
    if charset:
        hints.append(charset)
    prefix = body[:16384].decode("ascii", errors="ignore")
    for meta in re.findall(r"<meta\b[^>]*>", prefix, re.I):
        match = re.search(r"\bcharset\s*=\s*[\"']?\s*([A-Za-z0-9_.:-]+)", meta, re.I)
        if match:
            hints.append(match[1])
    hints.extend(("utf-8", "gb18030"))
    tried = set()
    for encoding in hints:
        encoding = encoding.strip().lower()
        if encoding in ("gb2312", "gbk", "x-gbk", "gb_2312-80"):
            encoding = "gb18030"
        if encoding in tried:
            continue
        tried.add(encoding)
        try:
            result = body.decode(encoding, errors="strict")
        except (LookupError, UnicodeError):
            continue
        # A binary download should not silently turn into a reading document.
        if "\x00" in result:
            continue
        return result.lstrip("\ufeff")
    raise ValueError("无法无损解码网页文字，请在浏览器中另存为 UTF-8 HTML 或复制正文为文本后导入。")


@dataclass(eq=False)
class _Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class _TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        # Repair common omitted closing tags, while respecting nested lists and
        # tables. HTMLParser itself deliberately does not perform this repair.
        if tag in _BLOCK and not any(node.tag == "template" for node in self.stack):
            # </head> is optional HTML syntax. Body content must not inherit
            # head's invisibility when the author omits that closing tag.
            self._close_open({"head"}, {"body"})
        if tag in _BLOCK and tag != "p":
            self._close_open({"p"}, {"body", "html", "table"})
        if tag == "p":
            self._close_open({"p"}, {"body", "html", "table"})
        if tag in _BLOCK:
            self._close_open({"h1", "h2", "h3", "h4", "h5", "h6"}, {"body", "html", "main", "article"})
        if tag == "li":
            self._close_open({"li"}, {"ul", "ol"})
        if tag in ("dt", "dd"):
            self._close_open({"dt", "dd"}, {"dl"})
        if tag == "tr":
            self._close_open({"tr"}, {"table"})
        if tag in ("td", "th"):
            self._close_open({"td", "th"}, {"tr", "table"})
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._close_open({"h1", "h2", "h3", "h4", "h5", "h6"}, {"body", "html"})
        node = _Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            if len(self.stack) >= 200:
                raise ValueError("网页嵌套层级过深，请使用浏览器阅读模式保存正文后导入。")
            self.stack.append(node)

    def _close_open(self, tags, boundaries):
        for index in range(len(self.stack) - 1, 0, -1):
            tag = self.stack[index].tag
            if tag in tags:
                del self.stack[index:]
                return
            if tag in boundaries:
                return

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _hidden(node):
    style = node.attrs.get("style") or ""
    return (node.tag in _HIDDEN or "hidden" in node.attrs or
            bool(re.search(r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*(?:!important\s*)?(?:;|$)", style, re.I)))


def _plain(node):
    if isinstance(node, str):
        return node
    if _hidden(node):
        return ""
    if node.tag == "br":
        return "\n"
    return "".join(_plain(child) for child in node.children)


def _walk(node):
    yield node
    for child in node.children:
        if isinstance(child, _Node):
            yield from _walk(child)


def _clean(text):
    # Do not collapse blank lines: fenced code may depend on every one of them.
    return text.strip()


class _Renderer:
    def __init__(self, base):
        self.base = base
        self.warnings = []

    def warning(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    @staticmethod
    def decorated(inner, left, right):
        """Keep whitespace around inline markup, matching browser text flow."""
        leading = inner[:len(inner) - len(inner.lstrip())]
        trailing = inner[len(inner.rstrip()):]
        return leading + left + inner.strip() + right + trailing

    def destination(self, raw):
        if not raw:
            return ""
        raw = raw.strip()
        if any(ord(c) < 32 or ord(c) == 127 for c in raw) or "\\" in raw:
            self.warning("部分链接含无效字符，已保留文字；请在原始 HTML 中核对链接。")
            return ""
        try:
            resolved = urljoin(self.base, raw)
            parts = urlsplit(resolved)
            if parts.scheme.lower() in ("http", "https"):
                fragment = parts.fragment
                resolved = _http_url(resolved)
                if fragment:
                    resolved += "#" + fragment
            elif parts.scheme.lower() in ("mailto", "tel"):
                pass
            elif not parts.scheme and not parts.netloc:
                # Relative links in a local HTML file stay relative and inert
                # in the offline reader, but remain recoverable in Markdown.
                pass
            else:
                self.warning("部分链接使用不受支持的协议，已保留文字；请在原始 HTML 中核对链接。")
                return ""
            return quote(resolved, safe="/:?#@!$&'*,;=+%~-._")
        except ValueError:
            self.warning("部分链接地址无效，已保留文字；请在原始 HTML 中核对链接。")
            return ""

    def render(self, node, excluded=frozenset()):
        if isinstance(node, str):
            return _SPACE.sub(" ", node)
        if node in excluded or _hidden(node):
            return ""
        tag = node.tag
        if tag == "pre":
            content = _plain(node)
            longest = max((len(m[0]) for m in re.finditer(r"`+", content)), default=0)
            fence = "`" * max(3, longest + 1)
            return "\n\n" + fence + "\n" + content + ("" if content.endswith("\n") else "\n") + fence + "\n\n"
        if tag == "table":
            return self.table(node, excluded)
        inner = "" if tag in ("ul", "ol") else "".join(self.render(child, excluded) for child in node.children)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return "\n\n" + "#" * int(tag[1]) + " " + inner.strip() + "\n\n"
        if tag == "br":
            return "  \n"
        if tag == "hr":
            return "\n\n---\n\n"
        if tag == "img":
            alt = node.attrs.get("alt") or node.attrs.get("title") or "图片（无替代文字）"
            destination = self.destination(node.attrs.get("src"))
            self.warning("图片保留了替代文字和来源链接，图内文字、图表及公式仍需查看原图核对。")
            label = alt.replace("[", "\\[").replace("]", "\\]")
            return "[{}]({})".format(label, destination) if destination else alt
        if tag == "a":
            destination = self.destination(node.attrs.get("href"))
            label = inner if inner.strip() else (node.attrs.get("href") or "")
            if not destination:
                return label
            label = label.replace("[", "\\[").replace("]", "\\]")
            return self.decorated(label, "[", "](" + destination + ")")
        if tag in ("strong", "b") and inner.strip():
            return self.decorated(inner, "**", "**")
        if tag in ("em", "i") and inner.strip():
            return self.decorated(inner, "*", "*")
        if tag in ("sup", "sub") and inner.strip():
            return self.decorated(inner, "^(" if tag == "sup" else "_(", ")")
        if tag == "code" and inner.strip():
            longest = max((len(m[0]) for m in re.finditer(r"`+", inner)), default=0)
            ticks = "`" * max(1, longest + 1)
            return ticks + " " + inner.strip() + " " + ticks
        if tag == "blockquote":
            return "\n\n" + "\n".join("> " + line for line in inner.strip().splitlines()) + "\n\n"
        if tag in ("ul", "ol"):
            lines = []
            step = -1 if tag == "ol" and "reversed" in node.attrs else 1
            default_start = (sum(isinstance(child, _Node) and child.tag == "li"
                                 for child in node.children) if step == -1 else 1)
            try:
                counter = int(node.attrs.get("start", default_start))
            except (TypeError, ValueError):
                counter = default_start
            # Render each item once; retain stray text and wrappers as well.
            for child in node.children:
                if isinstance(child, _Node) and child.tag == "li":
                    if child in excluded or _hidden(child):
                        continue
                    item = "".join(self.render(part, excluded) for part in child.children).strip()
                    if not item:
                        continue
                    try:
                        counter = int(child.attrs.get("value", counter))
                    except (TypeError, ValueError):
                        pass
                    prefix = str(counter) + ". " if tag == "ol" else "- "
                    item_lines = item.splitlines()
                    lines.append(prefix + item_lines[0] + "".join("\n" + " " * len(prefix) + line for line in item_lines[1:]))
                    counter += step
                else:
                    content = self.render(child, excluded).strip()
                    if content:
                        lines.append(content)
            return "\n\n" + "\n".join(lines) + "\n\n"
        if tag in _BLOCK:
            return "\n\n" + inner.strip() + "\n\n" if inner.strip() else ""
        return inner

    def table(self, node, excluded):
        rows = []
        extras = []

        def collect(part):
            if isinstance(part, str):
                if part.strip():
                    extras.append(part.strip())
                return
            if part in excluded or _hidden(part):
                return
            if part.tag == "tr":
                cells = []
                for child in part.children:
                    value = self.render(child, excluded).strip()
                    if isinstance(child, _Node) and child.tag in ("td", "th"):
                        cells.append(re.sub(r"\s+", " ", value).replace("|", "\\|"))
                    elif value:
                        extras.append(value)
                if cells:
                    rows.append(cells)
            elif part.tag in ("table", "thead", "tbody", "tfoot"):
                for child in part.children:
                    collect(child)
            else:
                value = self.render(part, excluded).strip()
                if value:
                    extras.append(value)

        collect(node)
        if not rows:
            return "\n\n" + "\n\n".join(extras) + "\n\n"
        width = max(map(len, rows))
        formatted = ["| " + " | ".join(row + [""] * (width - len(row))) + " |" for row in rows]
        formatted.insert(1, "| " + " | ".join(["---"] * width) + " |")
        if any(part.attrs.get("colspan") or part.attrs.get("rowspan") for part in _walk(node)):
            self.warning("表格含合并单元格，已按行保留文字；请在原网页中核对列对应关系。")
        return "\n\n" + "\n\n".join(extras + ["\n".join(formatted)]) + "\n\n"


def extract_html(html_text: str, source_location: str) -> dict:
    """Return Markdown reading text plus its source metadata and original HTML."""
    parser = _TreeParser()
    try:
        parser.feed(html_text)
        parser.close()
    except (AssertionError, RecursionError) as exc:
        raise ValueError("网页 HTML 结构无法解析，请用浏览器阅读模式保存正文后导入。") from exc
    nodes = list(_walk(parser.root))
    title_node = next((node for node in nodes if node.tag == "title"), None)
    title = _SPACE.sub(" ", "".join(_plain(child) for child in title_node.children)).strip() if title_node else ""
    # Browsers reparent text outside body in malformed documents. Starting at
    # the root also preserves that text and additional accidental body tags;
    # head/title/script/style/template remain explicitly excluded.
    body = parser.root
    renderer = _Renderer(source_location)
    # Honor a document's first safe base URL without ever loading it.
    base = next((node.attrs.get("href") for node in nodes if node.tag == "base" and node.attrs.get("href")), None)
    if base:
        resolved = renderer.destination(base)
        if resolved and urlsplit(resolved).scheme in ("http", "https"):
            renderer.base = resolved
    regions = []

    def select(node):
        if _hidden(node):
            return
        if node.tag in ("article", "main") or node.attrs.get("role") == "main":
            if renderer.render(node).strip():
                regions.append(node)
                return
        for child in node.children:
            if isinstance(child, _Node):
                select(child)

    select(body)
    if regions:
        text = "\n\n".join(renderer.render(node).strip() for node in regions)
        appendix = renderer.render(body, frozenset(regions)).strip()
        if appendix:
            text += "\n\n## 附录：页面其他可见内容\n\n" + appendix
    else:
        text = renderer.render(body).strip()
        renderer.warning("页面没有明确的 main/article 正文区域，已保留全部可见文字；导航等内容可能混在正文中。")
    if not text.strip() or not re.search(r"\w", text, re.UNICODE):
        raise ValueError("网页中没有可提取的正文，可能需要 JavaScript 或登录。请在浏览器中打开并保存渲染后的正文为 HTML/文本再导入。")
    renderer.warning("提取基于下载的 HTML，不执行 JavaScript，也不读取外部样式；动态内容和样式隐藏内容可能与浏览器显示不同。")
    is_url = urlsplit(source_location).scheme.lower() in ("http", "https")
    if not title:
        heading = next((node for node in _walk(body) if node.tag == "h1" and not _hidden(node)), None)
        title = _SPACE.sub(" ", _plain(heading)).strip() if heading else ""
    fallback = urlsplit(source_location).hostname if is_url else Path(source_location).stem
    title = title or fallback or "网页正文"
    basename = re.sub(r"[\x00-\x1f\x7f/\\:*?\"<>|]", "-", title).strip(" .")[:100].rstrip(" .")
    basename = basename or "网页正文"
    return {"text": _clean(text) + "\n", "source_name": basename + ".md", "title": title,
            "origin": {"kind": "web" if is_url else "html", "location": source_location,
                       "method": "stdlib-htmlparser", "warnings": renderer.warnings,
                       "original_html": html_text}}
