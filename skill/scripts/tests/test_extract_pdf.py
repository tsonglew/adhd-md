"""PDF extraction contracts, mocked OCR failures, and real Poppler smoke tests."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract_pdf as pdf


def minimal_pdf(page_texts):
    """Build a tiny valid PDF without an optional PDF-authoring dependency."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    pages = []
    for value in page_texts:
        page_id = len(objects) + 1
        content_id = page_id + 1
        pages.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode())
        escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 16 Tf 30 250 Td ({escaped}) Tj ET".encode("ascii") if value else b""
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(f'{number} 0 R' for number in pages)}] >>".encode()
    return encode_pdf(objects)


def image_only_pdf(images):
    """Embed Poppler-generated RGB PPMs as image-only pages with no text layer."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    pages = []
    for path in images:
        raw = path.read_bytes()
        header = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s", raw)
        if not header:
            raise ValueError("Unexpected PPM fixture header")
        width, height = map(int, header.groups())
        pixels = raw[header.end():]
        if len(pixels) != width * height * 3:
            raise ValueError("Unexpected PPM fixture size")
        page_id = len(objects) + 1
        pages.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /XObject << /Im0 {page_id + 2} 0 R >> >> /Contents {page_id + 1} 0 R >>".encode())
        stream = b"q 300 0 0 300 0 0 cm /Im0 Do Q"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        compressed = zlib.compress(pixels)
        objects.append(f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(compressed)} >>\nstream\n".encode() + compressed + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(f'{number} 0 R' for number in pages)}] >>".encode()
    return encode_pdf(objects)


def encode_pdf(objects):
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(result)


class ExtractPDFTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "原始文档.pdf"
        self.source.write_bytes(minimal_pdf(["Hello" , "World"]))
        self.original = self.source.read_bytes()
        self.text = "Hello\n\fWorld\n\f"
        self.page_count = 2
        self.ocr = {1: "第一页 OCR\n", 2: "第二页 OCR\n", 3: "第三页 OCR\n"}
        self.languages = "List of available languages (2):\neng\nchi_sim\n"
        self.missing_tools = set()
        self.commands = []
        self.temp_files = []
        self.fail_tool = None
        self.timeout_tool = None
        self.skip_image = False
        self.which = patch.object(pdf.shutil, "which", side_effect=self.which_tool).start()
        self.run = patch.object(pdf.subprocess, "run", side_effect=self.run_tool).start()
        self.addCleanup(patch.stopall)

    def which_tool(self, name):
        return None if name in self.missing_tools else "/fake/tools/" + name

    def run_tool(self, args, **kwargs):
        self.commands.append(args)
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertGreater(kwargs["timeout"], 0)
        self.assertEqual(kwargs["env"]["LC_ALL"], "C")
        tool = Path(args[0]).name
        if tool == self.timeout_tool and "--list-langs" not in args:
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])
        if tool == self.fail_tool:
            return subprocess.CompletedProcess(args, 1, b"", b"broken PDF")
        output = b""
        if tool == "pdfinfo":
            self.assertTrue(Path(args[-1]).is_absolute())
            output = f"Pages: {self.page_count}\n".encode()
        elif tool == "pdftotext":
            self.assertTrue(Path(args[-2]).is_absolute())
            self.assertIn("-layout", args)
            self.assertIn("UTF-8", args)
            output = self.text.encode()
        elif tool == "pdftoppm":
            image = Path(args[-1] + ".png")
            self.temp_files.append(image)
            self.assertEqual(args[args.index("-f") + 1], args[args.index("-l") + 1])
            self.assertIn("-singlefile", args)
            if not self.skip_image:
                image.write_bytes(b"PNG fixture for mocked OCR")
        elif tool == "tesseract":
            if "--list-langs" in args:
                output = self.languages.encode()
            else:
                number = int(Path(args[1]).stem.split("-")[-1])
                output = self.ocr[number].encode()
        return subprocess.CompletedProcess(args, 0, output, b"")

    def extract(self, **kwargs):
        result = pdf.extract_pdf(self.source, **kwargs)
        self.assertEqual(self.source.read_bytes(), self.original)
        return result

    def test_text_pages_have_correct_lines_and_source(self):
        result = self.extract()
        self.assertEqual(result["source_name"], "原始文档.extracted.md")
        self.assertEqual(result["origin"]["location"], self.source.name)
        self.assertEqual(result["origin"]["method"], "pdftotext")
        self.assertIn("图片", result["origin"]["warnings"][0])
        lines = result["text"].splitlines()
        for number, page in enumerate(result["origin"]["pages"], 1):
            self.assertEqual(lines[page["start_line"] - 1], f"## 第 {number} 页")
            self.assertEqual(lines[page["start_line"] + 1:page["end_line"]], page["text"].splitlines())
            self.assertEqual(page["status"], "extracted")
        self.assertFalse(any(Path(command[0]).name == "tesseract" for command in self.commands))

    def test_remote_pdf_has_original_source_title(self):
        result = self.extract(source_location="https://example.com/papers/%E8%AF%BB%E4%B9%A6.pdf?download=1")
        self.assertEqual(result["title"], "读书")
        self.assertEqual(result["source_name"], "读书.extracted.md")
        self.assertTrue(result["origin"]["location"].startswith("https://example.com"))

    def test_blank_middle_page_preserved_without_ocr(self):
        self.page_count = 3
        self.text = "First\n\f\fThird\n\f"
        result = self.extract(ocr="never")
        self.assertEqual([p["number"] for p in result["origin"]["pages"]], [1, 2, 3])
        self.assertEqual(result["origin"]["pages"][1]["status"], "missing")
        self.assertIn("未提取", result["origin"]["pages"][1]["text"])
        self.assertEqual(result["origin"]["pages"][2]["text"], "Third")

    def test_blank_last_page_is_not_dropped(self):
        self.text = "First\f\f"
        result = self.extract(ocr="never")
        self.assertEqual(len(result["origin"]["pages"]), 2)
        self.assertEqual(result["origin"]["pages"][1]["status"], "missing")

    def test_auto_ocr_only_textless_page(self):
        self.text = "Hello\n\f\f"
        result = self.extract()
        self.assertEqual(result["origin"]["pages"][0]["method"], "pdftotext")
        self.assertEqual(result["origin"]["pages"][1]["method"], "tesseract")
        self.assertIn("第二页 OCR", result["text"])
        self.assertEqual(result["origin"]["ocr_language"], "chi_sim+eng")
        self.assertEqual(len(self.temp_files), 1)
        self.assertTrue(all(not path.exists() and not path.parent.exists() for path in self.temp_files))

    def test_scan_ocr_auto(self):
        self.text = "\f\f"
        result = self.extract()
        self.assertTrue(all(page["status"] == "ocr_unverified" for page in result["origin"]["pages"]))
        self.assertIn("第一页 OCR", result["text"])

    def test_ocr_always_keeps_original_and_different_ocr(self):
        result = self.extract(ocr="always")
        self.assertIn("Hello", result["text"])
        self.assertIn("第一页 OCR", result["text"])
        page = result["origin"]["pages"][0]
        self.assertEqual(page["original_text"], "Hello")
        self.assertEqual(page["ocr_text"], "第一页 OCR")
        self.assertEqual(page["method"], "pdftotext+tesseract")

    def test_matching_ocr_does_not_duplicate_text(self):
        self.ocr = {1: "Hello\n", 2: "World\n"}
        result = self.extract(ocr="always")
        self.assertEqual(result["text"].count("Hello"), 1)

    def test_empty_ocr_keeps_existing_text(self):
        self.ocr = {1: "", 2: ""}
        result = self.extract(ocr="always")
        self.assertIn("Hello", result["text"])
        self.assertIn("World", result["text"])
        self.assertTrue(any("OCR 未识别" in warning for warning in result["origin"]["warnings"]))

    def test_partial_failed_ocr_keeps_page_placeholder(self):
        self.text = "Hello\n\f\f"
        self.ocr[2] = ""
        result = self.extract()
        self.assertEqual(result["origin"]["pages"][1]["status"], "missing")

    def test_all_blank_never_gives_install_hint(self):
        self.text = "\f\f"
        with self.assertRaisesRegex(ValueError, "brew install"):
            self.extract(ocr="never")

    def test_all_blank_ocr_is_not_empty_success(self):
        self.text = "\f\f"
        self.ocr = {1: "", 2: ""}
        with self.assertRaisesRegex(ValueError, "均未得到"):
            self.extract()

    def test_missing_poppler_is_actionable(self):
        for name in ["pdfinfo", "pdftotext"]:
            with self.subTest(name=name):
                self.missing_tools = {name}
                with self.assertRaisesRegex(ValueError, "poppler-utils"):
                    self.extract()

    def test_missing_ocr_is_actionable_even_with_some_text(self):
        self.text = "Hello\f\f"
        for name in ["pdftoppm", "tesseract"]:
            with self.subTest(name=name):
                self.missing_tools = {name}
                with self.assertRaisesRegex(ValueError, "tesseract-ocr"):
                    self.extract()

    def test_explicit_languages_validate_installed_models(self):
        self.languages = "List of available languages (2):\neng\njpn\n"
        result = self.extract(ocr="always", ocr_lang="jpn+eng")
        self.assertEqual(result["origin"]["ocr_language"], "jpn+eng")
        with self.assertRaisesRegex(ValueError, "缺少语言包"):
            self.extract(ocr="always", ocr_lang="chi_sim+eng")

    def test_invalid_language_cannot_inject_options(self):
        with self.assertRaisesRegex(ValueError, "格式"):
            self.extract(ocr="always", ocr_lang="eng --psm 7")

    def test_english_fallback_is_explicitly_warned(self):
        self.languages = "List of available languages (1):\neng\n"
        result = self.extract(ocr="always")
        self.assertEqual(result["origin"]["ocr_language"], "eng")
        self.assertTrue(any("中文可能无法正确识别" in warning for warning in result["origin"]["warnings"]))

    def test_no_default_language_is_actionable(self):
        self.languages = "List of available languages (1):\njpn\n"
        with self.assertRaisesRegex(ValueError, "默认 OCR 语言包"):
            self.extract(ocr="always")

    def test_invalid_pdf_fails_before_tools(self):
        self.source.write_bytes(b"This is not a PDF")
        with self.assertRaisesRegex(ValueError, "文件头"):
            pdf.extract_pdf(self.source)
        self.assertFalse(self.commands)

    def test_missing_pdf(self):
        with self.assertRaisesRegex(ValueError, "找不到"):
            pdf.extract_pdf(self.source.parent / "missing.pdf")

    def test_page_count_bound_fails_without_truncating(self):
        self.page_count = pdf.MAX_PDF_PAGES + 1
        with self.assertRaisesRegex(ValueError, "不会被截断"):
            self.extract()

    def test_file_size_bound_fails_before_read(self):
        with patch.object(pdf, "MAX_PDF_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "50 MiB"):
                self.extract()

    def test_page_mismatch_fails_without_mislabeling_pages(self):
        self.text = "Hello only one page"
        with self.assertRaisesRegex(ValueError, "分页不一致"):
            self.extract()

    def test_tool_failures_have_actionable_errors(self):
        for tool in ["pdfinfo", "pdftotext", "pdftoppm", "tesseract"]:
            with self.subTest(tool=tool):
                self.fail_tool = tool
                with self.assertRaisesRegex(ValueError, "broken PDF"):
                    self.extract(ocr="always")

    def test_timeouts_are_errors_and_clean_tempfiles(self):
        self.timeout_tool = "tesseract"
        with self.assertRaisesRegex(ValueError, "--timeout"):
            self.extract(ocr="always", timeout=1)
        self.assertTrue(self.temp_files)
        self.assertTrue(all(not path.parent.exists() for path in self.temp_files))

    def test_renderer_must_produce_image(self):
        self.skip_image = True
        with self.assertRaisesRegex(ValueError, "未生成图片"):
            self.extract(ocr="always")

    def test_invalid_mode_and_timeout(self):
        with self.assertRaisesRegex(ValueError, "模式"):
            self.extract(ocr="sometimes")
        for value in [0, -1, float("nan"), float("inf"), "3"]:
            with self.subTest(timeout=value), self.assertRaisesRegex(ValueError, "--timeout"):
                self.extract(timeout=value)

    def test_keep_indentation_and_unreliable_text_layer(self):
        self.text = "  indented\n    table data\f\ufffd\f"
        result = self.extract()
        self.assertIn("  indented\n    table data", result["text"])
        self.assertEqual(result["origin"]["pages"][1]["original_text"], "\ufffd")
        self.assertIn("\ufffd", result["text"])


@unittest.skipUnless(shutil.which("pdfinfo") and shutil.which("pdftotext"), "Poppler is optional; install it for the real PDF smoke test")
class RealPopplerTest(unittest.TestCase):
    def test_real_pdf_text_blank_middle_page_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "-fixture with spaces.pdf"
            original = minimal_pdf(["First page.", "", "Third page."])
            source.write_bytes(original)
            result = pdf.extract_pdf(source, ocr="never")
            pages = result["origin"]["pages"]
            self.assertEqual(len(pages), 3)
            self.assertIn("First page.", pages[0]["text"])
            self.assertEqual(pages[1]["status"], "missing")
            self.assertIn("Third page.", pages[2]["text"])
            self.assertEqual(source.read_bytes(), original)

    @unittest.skipUnless(shutil.which("pdftoppm") and shutil.which("tesseract"), "OCR tools are optional")
    def test_real_ocr_preserves_text_layer(self):
        languages = subprocess.run([shutil.which("tesseract"), "--list-langs"], capture_output=True, check=True, timeout=10)
        if "eng" not in languages.stdout.decode().splitlines():
            self.skipTest("The optional English OCR model is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ocr-fixture.pdf"
            original = minimal_pdf(["HELLO READER"])
            source.write_bytes(original)
            result = pdf.extract_pdf(source, ocr="always", ocr_lang="eng")
            page = result["origin"]["pages"][0]
            self.assertIn("HELLO READER", page["original_text"])
            self.assertIn("HELLO", page["ocr_text"])
            self.assertEqual(page["status"], "ocr_unverified")
            self.assertEqual(source.read_bytes(), original)

    @unittest.skipUnless(shutil.which("pdftoppm") and shutil.which("tesseract"), "OCR tools are optional")
    def test_real_scan_only_pdf_triggers_automatic_ocr_on_every_page(self):
        languages = subprocess.run([shutil.which("tesseract"), "--list-langs"], capture_output=True, check=True, timeout=10)
        if "eng" not in languages.stdout.decode().splitlines():
            self.skipTest("The optional English OCR model is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scan-only.pdf"
            seed = root / "raster-source.pdf"
            markers = ["SCAN ONLY ALPHA", "SCAN ONLY BETA"]
            seed.write_bytes(minimal_pdf(markers))
            subprocess.run([shutil.which("pdftoppm"), "-r", "150", str(seed), str(root / "page")], capture_output=True, check=True, timeout=30)
            original = image_only_pdf(sorted(root.glob("page-*.ppm")))
            source.write_bytes(original)
            text_layer = subprocess.run([shutil.which("pdftotext"), str(source), "-"], capture_output=True, check=True, timeout=30)
            self.assertEqual(text_layer.stdout, b"\f\f", "the fixture must genuinely lack a text layer")
            result = pdf.extract_pdf(source, ocr="auto", ocr_lang="eng")
            pages = result["origin"]["pages"]
            self.assertEqual(len(pages), 2)
            for number, (page, marker) in enumerate(zip(pages, markers), 1):
                self.assertIn(marker, page["ocr_text"])
                self.assertEqual(page["original_text"], "")
                self.assertEqual(page["number"], number)
                self.assertEqual(page["method"], "tesseract")
                self.assertEqual(page["status"], "ocr_unverified")
                self.assertEqual(result["text"].splitlines()[page["start_line"] - 1], f"## 第 {number} 页")
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
