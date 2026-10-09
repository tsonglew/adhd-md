"""Input routing for text, HTML, HTTP(S), and PDF reading sources."""
from __future__ import annotations

import math
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {".md", ".markdown", ".mdown", ".txt", ".text"}
MAX_LOCAL_BYTES = 50 * 1024 * 1024


def is_url(source: str) -> bool:
    return bool(re.match(r"(?i)^https?://", source))


def safe_stem(value: str) -> str:
    value = re.sub(r"[^\w.-]+", "-", value, flags=re.UNICODE).strip(".-")[:80]
    if not value or value.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}:
        value = "document"
    return value


def _validate_text(text: str) -> str:
    if not text.strip("\ufeff \t\r\n"):
        raise ValueError("文档为空，请提供要阅读的正文。")
    if "\x00" in text:
        raise ValueError("文件含二进制内容，请先转换为 UTF-8 文本。")
    return text


def _text_result(text: str, source_name: str) -> dict:
    return {"text": _validate_text(text), "source_name": source_name, "title": None}


def load_source(source: str, *, timeout: float = 20, ocr: str = "auto",
                ocr_lang: str | None = None, stdin_text: str | None = None) -> dict:
    """Extract a source without modifying it or writing output artifacts."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("--timeout 必须是大于 0 的有限秒数。")
    if ocr not in {"auto", "never", "always"}:
        raise ValueError("--ocr 必须是 auto、never 或 always。")
    if source == "-":
        if stdin_text is None:
            raise ValueError("没有取得标准输入正文。")
        return _text_result(stdin_text, "stdin.md")

    if is_url(source):
        from extract_web import decode_html, extract_html, fetch_url

        response = fetch_url(source, timeout=timeout)
        body = response["body"]
        final_url = response["url"]
        content_type = response["content_type"].split(";", 1)[0].strip().lower()
        url_path = unquote(urlsplit(final_url).path)
        suffix = Path(url_path).suffix.lower()
        if body.lstrip().startswith(b"%PDF-") or content_type == "application/pdf":
            from extract_pdf import extract_pdf

            with tempfile.TemporaryDirectory(prefix="adhd-md-source-") as directory:
                pdf = Path(directory) / (safe_stem(Path(url_path).stem) + ".pdf")
                pdf.write_bytes(body)
                result = extract_pdf(pdf, source_location=final_url, ocr=ocr,
                                     ocr_lang=ocr_lang, timeout=timeout)
        elif content_type in {"text/plain", "text/markdown", "text/x-markdown"}:
            text = decode_html(body, response.get("charset"))
            name = safe_stem(Path(url_path).stem) + (".md" if suffix in TEXT_SUFFIXES - {".txt", ".text"} else ".txt")
            result = _text_result(text, name)
            result["origin"] = {"kind": "web", "location": final_url,
                                "method": "HTTP 文本", "warnings": []}
        elif content_type in {"text/html", "application/xhtml+xml", ""} or (
            content_type == "application/octet-stream" and suffix in {".html", ".htm"}
        ):
            result = extract_html(decode_html(body, response.get("charset")), final_url)
        else:
            raise ValueError(f"网址返回了不支持的内容类型：{content_type or '未知'}。请提供网页、文本或 PDF 链接。")
        result["origin"]["requested_url"] = source
        _validate_text(result["text"])
        return result

    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", source):
        raise ValueError("网络来源只支持 http:// 或 https://；本地文件请直接填写路径。")
    path = Path(source)
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES | {".html", ".htm", ".pdf"}:
        raise ValueError("请提供 Markdown、纯文本、HTML、PDF 文件，或 HTTP(S) 网址。")
    if not path.is_file():
        raise ValueError(f"找不到可读取的文件：{path}")
    if path.stat().st_size > MAX_LOCAL_BYTES:
        raise ValueError("文件超过 50 MiB，请先拆分后再提取。")
    if suffix in TEXT_SUFFIXES:
        with path.open(encoding="utf-8", newline="") as handle:
            return _text_result(handle.read(), path.name)
    if suffix == ".pdf":
        from extract_pdf import extract_pdf

        result = extract_pdf(path, source_location=path.name, ocr=ocr,
                             ocr_lang=ocr_lang, timeout=timeout)
    else:
        from extract_web import decode_html, extract_html

        result = extract_html(decode_html(path.read_bytes()), path.resolve().as_uri())
        result["origin"]["location"] = path.name
    _validate_text(result["text"])
    return result


def output_path(source: str, result: dict, *, extracted: bool = False) -> Path:
    suffix = ".extracted.md" if extracted else ".reader.html"
    if source == "-":
        return Path("stdin" + suffix)
    if is_url(source):
        stem = Path(result["source_name"]).stem
        if stem.endswith(".extracted"):
            stem = stem[:-len(".extracted")]
        return Path(safe_stem(stem) + suffix)
    return Path(source).with_suffix(suffix)


def export_markdown(result: dict) -> str:
    """Keep extraction provenance attached when exporting without JSON metadata."""
    origin = result.get("origin")
    if not origin:
        return result["text"]

    def one_line(value):
        return " ".join(str(value).splitlines())

    notes = ["> 提取来源：" + one_line(origin["location"]),
             "> 提取方式：" + one_line(origin["method"])]
    for warning in origin.get("warnings", []):
        notes.append("> 提取说明：" + one_line(warning))
    return "\n>\n".join(notes) + "\n\n" + result["text"]
