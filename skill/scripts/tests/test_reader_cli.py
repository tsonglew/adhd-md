"""Exercise the public read command, including output and source protection."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "adhd_md.py"


class ReaderCLITest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "已有文档.md"
        self.original = "# 继续阅读\r\n\r\n超时默认 30 秒。设为 0 不超时。\r\n".encode("utf-8")
        self.source.write_bytes(self.original)

    def run_read(self, *args, input=None):
        return subprocess.run(
            [sys.executable, str(TOOL), "read", *map(str, args)],
            cwd=self.root, input=input, capture_output=True,
        )

    def test_default_html_preserves_source_and_embedded_text(self):
        result = self.run_read(self.source)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.source.with_suffix(".reader.html").read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", page.lower())
        self.assertNotIn("__ADHD_READER_DATA__", page)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_json_is_machine_readable_and_preserves_crlf(self):
        result = self.run_read(self.source, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["source_text"].encode("utf-8"), self.original)
        self.assertEqual("".join(c["source"] for c in data["chunks"]), data["source_text"])
        self.assertFalse(self.source.with_suffix(".reader.html").exists())

    def test_existing_output_is_not_overwritten(self):
        target = self.root / "existing.html"
        target.write_text("keep me", encoding="utf-8")
        result = self.run_read(self.source, "-o", target)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep me")

    def test_source_cannot_be_output(self):
        result = self.run_read(self.source, "-o", self.source)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_symlink_output_is_not_followed(self):
        target = self.root / "linked.html"
        target.symlink_to(self.source)
        result = self.run_read(self.source, "-o", target)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_stdin_supports_pasted_text(self):
        result = self.run_read("-", "--json", input=self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["source_text"].encode("utf-8"), self.original)

    def test_json_and_output_are_mutually_exclusive(self):
        target = self.root / "unused.html"
        result = self.run_read(self.source, "--json", "-o", target)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(target.exists())

    def test_bad_input_gives_actionable_error_without_traceback(self):
        for name, value in [("empty.md", b" \r\n"), ("encoded.txt", b"\xff"),
                            ("binary.md", b"a\x00b"), ("page.pdf", b"%PDF")]:
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(value)
                result = self.run_read(path)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"read:", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertFalse(path.with_suffix(".reader.html").exists())

    def test_missing_input(self):
        result = self.run_read(self.root / "missing.md")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_invalid_chunk_size(self):
        result = self.run_read(self.source, "--chunk-size", "0")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
