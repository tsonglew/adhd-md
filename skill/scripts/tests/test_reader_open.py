"""Opening a generated reader is optional and never changes generation success."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import webbrowser


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import adhd_md


class ReaderOpenTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "已有 文档.md"
        self.original = "# 继续阅读\n\n超时默认 30 秒；0 表示不超时。\n"
        self.source.write_text(self.original, encoding="utf-8")

    def run_read(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = adhd_md.main(["read", *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_default_does_not_open_browser(self):
        with patch.object(adhd_md.webbrowser, "open") as open_browser:
            code, stdout, stderr = self.run_read(self.source)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.source.with_suffix(".reader.html").exists())
        open_browser.assert_not_called()

    def test_open_runs_once_after_complete_write_with_escaped_file_uri(self):
        output = self.root / "阅读 空间.html"

        def inspect_written_page(uri):
            self.assertEqual(uri, output.resolve().as_uri())
            self.assertIn("%20", uri)
            self.assertNotIn("阅读", uri)
            page = output.read_text(encoding="utf-8")
            self.assertTrue(page.rstrip().endswith("</html>"))
            self.assertIn(self.original.splitlines()[-1], page)
            return True

        with patch.object(adhd_md.webbrowser, "open", side_effect=inspect_written_page) as open_browser:
            code, stdout, stderr = self.run_read(self.source, "-o", output, "--open")
        self.assertEqual(code, 0, stderr)
        open_browser.assert_called_once_with(output.resolve().as_uri())
        self.assertEqual(stderr, "")
        self.assertIn(str(output.resolve()), stdout)
        self.assertEqual(self.source.read_text(encoding="utf-8"), self.original)

    def test_headless_false_result_preserves_success_and_output_path(self):
        output = self.source.with_suffix(".reader.html")
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(adhd_md.webbrowser, "open", return_value=False) as open_browser:
            code, stdout, stderr = self.run_read(self.source, "--open")
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())
        self.assertIn(str(output.resolve()), stdout)
        self.assertIn(str(output.resolve()), stderr)
        self.assertIn("警告", stderr)
        self.assertIn("手动打开", stderr)
        open_browser.assert_called_once_with(output.resolve().as_uri())

    def test_browser_errors_warn_without_failing_generated_page(self):
        for number, failure in enumerate((OSError("unavailable"),
                                           FileNotFoundError("missing browser"),
                                           webbrowser.Error("no browser"))):
            with self.subTest(failure=type(failure).__name__):
                output = self.root / f"output-{number}.html"
                with patch.object(adhd_md.webbrowser, "open", side_effect=failure) as open_browser:
                    code, stdout, stderr = self.run_read(self.source, "-o", output, "--open")
                self.assertEqual(code, 0)
                self.assertTrue(output.exists())
                self.assertIn(str(output.resolve()), stdout)
                self.assertIn(str(output.resolve()), stderr)
                self.assertIn("警告", stderr)
                self.assertNotIn("Traceback", stderr)
                open_browser.assert_called_once_with(output.resolve().as_uri())

    def test_json_open_conflict_precedes_any_input_read_or_write(self):
        original_files = set(self.root.iterdir())
        for source in (self.source, "-", "https://example.invalid/article"):
            with self.subTest(source=source), \
                    patch("sources.load_source") as load_source, \
                    patch("sources.read_stdin") as read_stdin, \
                    patch.object(adhd_md.webbrowser, "open") as open_browser:
                code, stdout, stderr = self.run_read(source, "--json", "--open")
                self.assertEqual(code, 2)
                self.assertEqual(stdout, "")
                self.assertIn("不能同时指定 --open", stderr)
                load_source.assert_not_called()
                read_stdin.assert_not_called()
                open_browser.assert_not_called()
                self.assertEqual(set(self.root.iterdir()), original_files)

    def test_existing_output_is_preserved_and_never_opened(self):
        output = self.root / "existing.html"
        output.write_text("keep me", encoding="utf-8")
        with patch.object(adhd_md.webbrowser, "open") as open_browser:
            code, stdout, stderr = self.run_read(self.source, "-o", output, "--open")
        self.assertEqual(code, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep me")
        self.assertIn("已存在", stderr)
        open_browser.assert_not_called()

    def test_extraction_failure_never_opens_browser_or_creates_output(self):
        output = self.root / "failed.html"
        with patch("sources.load_source", side_effect=ValueError("无法提取正文")), \
                patch.object(adhd_md.webbrowser, "open") as open_browser:
            code, stdout, stderr = self.run_read(self.source, "-o", output, "--open")
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())
        self.assertIn("无法提取正文", stderr)
        open_browser.assert_not_called()

    def test_output_write_failure_never_opens_browser(self):
        output = self.root / "missing-directory" / "reader.html"
        with patch.object(adhd_md.webbrowser, "open") as open_browser:
            code, stdout, stderr = self.run_read(self.source, "-o", output, "--open")
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())
        open_browser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
