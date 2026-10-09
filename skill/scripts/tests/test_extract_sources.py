"""Verify input routing and public CLI behavior without live network services."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import sources


class SourceTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def command(self, verb, *args, input=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "adhd_md.py"), verb, *map(str, args)],
                              cwd=self.root, input=input, capture_output=True)

    def test_text_and_stdin_still_preserve_every_character(self):
        raw = "\ufeff# 原文\r\n\r\n保留 30 秒与 0 的例外。\r\n"
        path = self.root / "source.md"
        path.write_bytes(raw.encode("utf-8"))
        self.assertEqual(sources.load_source(str(path))["text"], raw)
        self.assertEqual(sources.load_source("-", stdin_text=raw)["text"], raw)
        self.assertNotIn("origin", sources.load_source(str(path)))

    def test_html_cli_extract_and_read_keep_original_and_provenance(self):
        html = '<html><head><title>配置说明</title></head><body><nav>文档导航</nav><main><h1>配置说明</h1><p>超时 30 秒，0 不超时。</p></main><footer>保留版权说明。</footer></body></html>'
        path = self.root / "source.html"
        path.write_text(html, encoding="utf-8")
        result = self.command("extract", path, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        extracted = json.loads(result.stdout)
        for text in ["超时 30 秒", "保留版权说明", "文档导航"]:
            self.assertIn(text, extracted["text"])
        self.assertEqual(extracted["origin"]["original_html"], html)
        result = self.command("read", path, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        reading = json.loads(result.stdout)
        self.assertEqual(reading["source_text"], extracted["text"])
        self.assertEqual(reading["origin"], extracted["origin"])
        self.assertEqual("".join(c["source"] for c in reading["chunks"]), extracted["text"])
        self.assertEqual(path.read_text(encoding="utf-8"), html)
        result = self.command("extract", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = (self.root / "source.extracted.md").read_text(encoding="utf-8")
        self.assertIn("提取来源：source.html", saved)
        self.assertIn(extracted["text"], saved)

    def test_extract_refuses_source_or_existing_output(self):
        path = self.root / "source.txt"
        path.write_text("保留原文", encoding="utf-8")
        result = self.command("extract", path, "-o", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(path.read_text(encoding="utf-8"), "保留原文")
        target = self.root / "existing.md"
        target.write_text("keep", encoding="utf-8")
        result = self.command("extract", path, "-o", target)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_extract_stdin_and_json_output_conflict(self):
        result = self.command("extract", "-", input="正文\r\n".encode("utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "stdin.extracted.md").read_bytes(), "正文\r\n".encode("utf-8"))
        result = self.command("extract", "-", "--json", "-o", "unused.md", input=b"ok")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "unused.md").exists())

    def test_network_html_and_pdf_are_dispatched_by_response_type(self):
        response = {"body": b"<html><body><p>Full source here.</p></body></html>",
                    "url": "https://example.org/final", "content_type": "text/html", "charset": "utf-8"}
        with patch("extract_web.fetch_url", return_value=response) as fetch:
            result = sources.load_source("https://example.org/first")
        fetch.assert_called_once_with("https://example.org/first", timeout=20)
        self.assertEqual(result["origin"]["location"], response["url"])
        self.assertEqual(result["origin"]["requested_url"], "https://example.org/first")
        response.update(body=b"%PDF-1.4\nexample", content_type="application/octet-stream")
        seen = []

        def fake_pdf(path, **kwargs):
            seen.append(Path(path))
            self.assertEqual(Path(path).read_bytes(), response["body"])
            self.assertEqual(kwargs["source_location"], response["url"])
            return {"text": "PDF body", "source_name": "document.md", "title": "Document",
                    "origin": {"kind": "pdf", "location": response["url"], "method": "fixture", "warnings": []}}

        with patch("extract_web.fetch_url", return_value=response), patch("extract_pdf.extract_pdf", side_effect=fake_pdf):
            self.assertEqual(sources.load_source("https://example.org/file")["text"], "PDF body")
        self.assertFalse(seen[0].exists(), "temporary downloaded PDF must be removed")

    def test_url_plain_text_and_unsupported_media(self):
        response = {"body": b"literal *stars*\r\n", "url": "https://example.org/file.txt",
                    "content_type": "text/plain; charset=utf-8", "charset": "utf-8"}
        with patch("extract_web.fetch_url", return_value=response):
            result = sources.load_source(response["url"])
        self.assertEqual(result["text"], "literal *stars*\r\n")
        self.assertTrue(result["source_name"].endswith(".txt"))
        response["content_type"] = "image/png"
        with patch("extract_web.fetch_url", return_value=response), self.assertRaises(ValueError):
            sources.load_source(response["url"])

    def test_timeout_and_unsupported_scheme_fail_before_fetch(self):
        for timeout in [0, -1, float("nan"), float("inf")]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                sources.load_source("https://example.org", timeout=timeout)
        for source in ["ftp://example.org/a", "file:///etc/passwd", "data://something"]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                sources.load_source(source)
        result = self.command("read", "https://example.org", "--timeout", "nan")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_output_names_cannot_escape_working_directory(self):
        for name in ["../../escape.md", "/tmp/absolute.md", "CON.md", ".md", "<script>.md"]:
            with self.subTest(name=name):
                output = sources.output_path("https://example.org/doc", {"source_name": name})
                self.assertEqual(output.parent, Path("."))
                self.assertTrue(output.name.endswith(".reader.html"))

    def test_pdf_url_output_names_do_not_repeat_extracted_suffix(self):
        result = {"source_name": "manual.extracted.md"}
        self.assertEqual(sources.output_path("https://example.org/manual.pdf", result),
                         Path("manual.reader.html"))
        self.assertEqual(sources.output_path("https://example.org/manual.pdf", result, extracted=True),
                         Path("manual.extracted.md"))


if __name__ == "__main__":
    unittest.main()
