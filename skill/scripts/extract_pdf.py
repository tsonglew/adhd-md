"""Local PDF extraction with optional, explicitly marked OCR.

Only Python's standard library is used. Poppler supplies pdfinfo/pdftotext and,
when OCR is needed, pdftoppm; Tesseract supplies OCR. The input PDF is never
modified or uploaded. Text extraction cannot preserve figures or guarantee PDF
reading order, so every result retains its source and page-level provenance.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unicodedata
from urllib.parse import unquote, urlsplit


MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_PDF_PAGES = 500
_POPPLER_INSTALL = "macOS: brew install poppler；Ubuntu/Debian: sudo apt install poppler-utils"
_OCR_INSTALL = (
    "macOS: brew install poppler tesseract tesseract-lang；"
    "Ubuntu/Debian: sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng"
)
_PDF_WARNING = "PDF 提取无法保证阅读顺序，也不会保留全部图片、图表、公式及版面；请按页码对照原始 PDF。"
_OCR_WARNING = "OCR 是机器识别结果，可能漏字、错字或打乱阅读顺序，尤其是表格和公式；请对照原始 PDF 核对。"


def _run(args: list[str], timeout: float, description: str):
    """Run tools without a shell, with bounded time and stable pdfinfo labels."""
    try:
        result = subprocess.run(
            args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, check=False, shell=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"{description} 超时（每次调用上限 {timeout:g} 秒）；请提高 --timeout 或先拆分 PDF。") from exc
    except OSError as exc:
        raise ValueError(f"无法运行 {description}：{exc}") from exc
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()[:500]
        raise ValueError(f"{description} 失败（退出码 {result.returncode}）：{detail or '请检查 PDF 是否损坏或需要密码。'}")
    return result


def _tool(name: str, *, ocr: bool = False) -> str:
    path = shutil.which(name)
    if not path:
        hint = _OCR_INSTALL if ocr else _POPPLER_INSTALL
        raise ValueError(f"PDF {'OCR ' if ocr else ''}需要 {name}，请先安装。{hint}")
    return path


def _decode(result, warnings: list[str], label: str) -> str:
    text = result.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if "\ufffd" in text:
        warnings.append(f"{label} 含无法解码的字符，请对照原 PDF 核对。")
    diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
    if diagnostic:
        warnings.append(f"{label} 工具提示：{diagnostic[:500]}")
    return text


def _usable(text: str) -> bool:
    # Accept CJK and mathematical symbols, but not blank/control-only output.
    return any(char != "\ufffd" and (char.isalnum() or unicodedata.category(char).startswith("S")) for char in text)


def _language(tesseract: str, requested: str | None, timeout: float, warnings: list[str]) -> str:
    listing = _run([tesseract, "--list-langs"], timeout, "读取 Tesseract 语言包")
    available = {
        line.strip() for line in listing.stdout.decode("utf-8", errors="replace").splitlines()
        if re.fullmatch(r"[A-Za-z0-9_/-]+", line.strip())
    }
    if requested:
        if not re.fullmatch(r"[A-Za-z0-9_/-]+(?:\+[A-Za-z0-9_/-]+)*", requested):
            raise ValueError("--ocr-lang 格式不正确；例如 chi_sim+eng 或 eng。")
        missing = [lang for lang in requested.split("+") if lang not in available]
        if missing:
            raise ValueError(f"Tesseract 缺少语言包：{', '.join(missing)}。{_OCR_INSTALL}；运行 tesseract --list-langs 查看已安装语言。")
        return requested
    if {"chi_sim", "eng"}.issubset(available):
        return "chi_sim+eng"
    if "eng" in available:
        warnings.append("缺少简体中文 OCR 语言包 chi_sim，本次仅使用 eng，中文可能无法正确识别；请安装中文语言包后用 --ocr-lang chi_sim+eng 重新提取。" + _OCR_INSTALL)
        return "eng"
    raise ValueError(f"Tesseract 缺少默认 OCR 语言包 eng（推荐同时安装 chi_sim）。{_OCR_INSTALL}；也可用 --ocr-lang 指定已安装语言。")


def _title(path: Path, source_location: str | None) -> tuple[str, str]:
    name = path.name
    if source_location and urlsplit(source_location).scheme in {"http", "https"}:
        name = unquote(urlsplit(source_location).path.rsplit("/", 1)[-1]) or name
    name = " ".join(name.split()).replace("/", "_").replace("\\", "_")
    stem = name[:-4] if name.lower().endswith(".pdf") else name
    stem = stem or "PDF 文档"
    return stem, stem + ".extracted.md"


def extract_pdf(path, *, source_location=None, ocr="auto", ocr_lang=None, timeout=30) -> dict:
    """Extract a PDF into Markdown plus provenance; raise ValueError on failure.

    ``ocr`` is auto/never/always. Auto OCRs pages lacking usable text; always
    keeps the original text layer as well when OCR produces different text.
    ``timeout`` limits each subprocess. Blank pages retain explicit placeholders
    instead of shifting subsequent page numbers. Pages use statuses extracted,
    ocr_unverified or missing, and inclusive one-based Markdown line positions.
    """
    if ocr not in {"auto", "never", "always"}:
        raise ValueError("PDF OCR 模式必须是 auto、never 或 always。")
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("--timeout 必须是大于 0 的有限秒数。")
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"找不到 PDF 文件：{source}")
    if source.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF 超过 50 MiB；请先拆分 PDF 再提取，原文不会被截断。")
    with source.open("rb") as handle:
        if b"%PDF-" not in handle.read(1024):
            raise ValueError("输入不是有效的 PDF 文件（缺少 PDF 文件头）。")

    pdfinfo = _tool("pdfinfo")
    pdftotext = _tool("pdftotext")
    warnings = [_PDF_WARNING]
    info = _decode(_run([pdfinfo, "-enc", "UTF-8", str(source)], timeout, "读取 PDF 页数"), warnings, "PDF 信息")
    count_match = re.search(r"^Pages:\s*(\d+)\s*$", info, re.MULTILINE)
    if not count_match:
        raise ValueError("无法确定 PDF 页数；请检查 PDF 是否损坏或需要密码，并升级 Poppler 后重试。")
    page_count = int(count_match.group(1))
    if not 1 <= page_count <= MAX_PDF_PAGES:
        raise ValueError(f"PDF 页数必须为 1–{MAX_PDF_PAGES}，当前为 {page_count}；请先拆分 PDF，原文不会被截断。")
    extracted = _decode(_run(
        [pdftotext, "-layout", "-enc", "UTF-8", "-eol", "unix", str(source), "-"],
        timeout, "提取 PDF 文本",
    ), warnings, "PDF 文本")
    text_pages = extracted.split("\f")
    if len(text_pages) > 1 and not text_pages[-1].strip():
        text_pages.pop()  # Poppler emits a final delimiter, including blank pages.
    if len(text_pages) != page_count:
        raise ValueError(f"PDF 页数与文本分页不一致（{page_count} 页 / {len(text_pages)} 段）；请升级 Poppler 或拆分 PDF 后重试，避免页码错位。")
    text_pages = [text.rstrip("\n") for text in text_pages]
    need_ocr = [index for index, text in enumerate(text_pages) if ocr == "always" or (ocr == "auto" and not _usable(text))]

    language = None
    ocr_pages = {}
    if need_ocr:
        pdftoppm = _tool("pdftoppm", ocr=True)
        tesseract = _tool("tesseract", ocr=True)
        language = _language(tesseract, ocr_lang, timeout, warnings)
        warnings.append(_OCR_WARNING)
        with tempfile.TemporaryDirectory(prefix="adhd-md-pdf-") as directory:
            for index in need_ocr:
                page_number = index + 1
                prefix = Path(directory) / f"page-{page_number}"
                rendered = _run([
                    pdftoppm, "-f", str(page_number), "-l", str(page_number),
                    "-singlefile", "-r", "180", "-scale-to", "3500", "-png",
                    str(source), str(prefix),
                ], timeout, f"渲染 PDF 第 {page_number} 页")
                _decode(rendered, warnings, f"渲染第 {page_number} 页")
                image = prefix.with_suffix(".png")
                if not image.is_file():
                    raise ValueError(f"PDF 第 {page_number} 页渲染未生成图片，无法继续 OCR。")
                recognized = _run([tesseract, str(image), "stdout", "-l", language], timeout, f"OCR 第 {page_number} 页")
                ocr_pages[index] = _decode(recognized, warnings, f"OCR 第 {page_number} 页").rstrip("\n\f")
                image.unlink()  # Do not retain hundreds of page images until exit.

    if not any(_usable(text) for text in [*text_pages, *ocr_pages.values()]):
        if ocr == "never":
            raise ValueError("PDF 没有可提取的文本；请移除 --ocr never，安装 OCR 工具后重试。" + _OCR_INSTALL)
        raise ValueError("PDF 文本提取和 OCR 均未得到可阅读内容；请检查原文件是否空白、选择正确的 --ocr-lang，或使用更清晰的扫描件。")

    title, source_name = _title(source, source_location)
    lines = [f"# {title}", ""]
    pages = []
    for index, original in enumerate(text_pages):
        page_number = index + 1
        recognized = ocr_pages.get(index)
        original_usable = _usable(original)
        recognized_usable = recognized is not None and _usable(recognized)
        method = "pdftotext" if original_usable else "none"
        status = "extracted" if original_usable else "missing"
        content = original
        if recognized is not None:
            method = "pdftotext+tesseract" if original.strip() else "tesseract"
            if recognized_usable:
                status = "ocr_unverified"
                if original.strip() and original != recognized:
                    content = f"### 原 PDF 文本层\n\n{original}\n\n### OCR 识别文本（待核对）\n\n{recognized}"
                else:
                    content = f"[OCR 识别文本，待核对]\n\n{recognized}"
            else:
                warnings.append(f"第 {page_number} 页 OCR 未识别到可阅读文本，请核对原 PDF。")
                if recognized and recognized != original:
                    content += f"\n\n[OCR 未得到可靠正文，以下为识别输出]\n\n{recognized}"
        if not original_usable and not recognized_usable:
            warnings.append(f"第 {page_number} 页未提取到可阅读正文（可能为空白页、图片或识别失败）；页码已保留，请核对原 PDF。")
            content += ("\n\n" if content else "") + "[本页未提取到可阅读正文；可能为空白页或包含未识别的图片／文字，请查看原 PDF。]"
        start_line = len(lines) + 1
        page_lines = [f"## 第 {page_number} 页", "", *content.split("\n")]
        lines.extend(page_lines)
        end_line = len(lines)
        lines.append("")
        page = {"number": page_number, "text": content, "method": method, "status": status,
                "start_line": start_line, "end_line": end_line}
        if recognized is not None:
            page.update({"original_text": original, "ocr_text": recognized, "ocr_language": language})
        pages.append(page)
    return {
        "text": "\n".join(lines), "source_name": source_name, "title": title,
        "origin": {"kind": "pdf", "location": source_location or source.name,
                   "method": "pdftotext+tesseract" if need_ocr else "pdftotext",
                   "warnings": warnings, "pages": pages, "ocr_language": language},
    }
