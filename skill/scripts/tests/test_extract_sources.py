"""Verify input routing and public CLI behavior without live network services."""
import io
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

    def test_stdin_limit_is_byte_based_and_never_truncates(self):
        self.assertEqual(sources.read_stdin(io.BytesIO(b"12345678"), max_bytes=8), "12345678")
        with self.assertRaisesRegex(ValueError, "超过 0 MiB.*未读取为部分文档"):
            sources.read_stdin(io.BytesIO(b"123456789"), max_bytes=8)
        with self.assertRaisesRegex(ValueError, "超过 0 MiB.*未读取为部分文档"):
            sources.read_stdin(io.StringIO("界" * 3), max_bytes=8)
        with patch.object(sources, "MAX_LOCAL_BYTES", 8), self.assertRaisesRegex(ValueError, "标准输入超过"):
            sources.load_source("-", stdin_text="123456789")

    def test_empty_source_refuses_read_and_extract_without_partial_output(self):
        source = self.root / "empty.md"
        source.write_bytes(b"")
        for command, output in (("read", self.root / "empty.reader.html"),
                                ("extract", self.root / "empty.extracted.md")):
            with self.subTest(command=command):
                result = self.command(command, source)
                self.assertEqual(result.returncode, 2)
                self.assertIn("文档为空", result.stderr.decode("utf-8"))
                self.assertFalse(output.exists())

    def test_local_html_links_never_read_link_targets_or_fetch_images(self):
        source = self.root / "page.html"
        next_page = self.root / "next.html"
        image = self.root / "chart.png"
        source.write_text('<main><a href="next.html#section">Next</a><img src="chart.png" alt="Chart">'
                          '<img src="https://example.org/track.png" alt="Remote"></main>',
                          encoding="utf-8")
        next_page.write_text("must not be read", encoding="utf-8")
        image.write_bytes(b"must not be read as an image")
        real_read_bytes = Path.read_bytes
        read_paths = []

        def guarded_read_bytes(path):
            read_paths.append(path.resolve())
            if path.resolve() != source.resolve():
                raise AssertionError(f"unexpected read of linked resource: {path}")
            return real_read_bytes(path)

        with patch.object(Path, "read_bytes", guarded_read_bytes), patch("extract_web.fetch_url") as fetch:
            result = sources.load_source(str(source))

        fetch.assert_not_called()
        self.assertEqual(read_paths, [source.resolve()])
        self.assertIn("[Next](next.html#section)", result["text"])
        self.assertIn("[Chart](chart.png)", result["text"])
        self.assertIn("[Remote](https://example.org/track.png)", result["text"])
        exported = sources.export_markdown(result)
        for target in ("next.html#section", "chart.png", "https://example.org/track.png"):
            self.assertIn(target, exported)

        cli_result = self.command("extract", source)
        self.assertEqual(cli_result.returncode, 0, cli_result.stderr)
        saved = (self.root / "page.extracted.md").read_text(encoding="utf-8")
        for target in ("next.html#section", "chart.png", "https://example.org/track.png"):
            self.assertIn(target, saved)

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
