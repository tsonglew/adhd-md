"""Portable bookmarks survive the public CLI and HTML handoff without rewriting sources."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "adhd_md.py"


class ReaderSessionCLITest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "原文.md"
        self.original = "# 开头 🧠\r\n\r\n第一段。继续原文。\r\n\r\n## 次节\r\n\r\n第二段。条件不能丢。\r\n".encode("utf-8")
        self.source.write_bytes(self.original)
        self.data = json.loads(self.run_read("--json").stdout)
        self.bookmark = self.root / "书签.json"

    def run_read(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "read", str(self.source), *map(str, args)],
                              capture_output=True, cwd=self.root)

    def write_bookmark(self, session):
        self.bookmark.write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")

    def test_chat_bookmark_imports_into_json_and_html(self):
        session = self.data["session"]
        second = self.data["chunks"][1]
        session["resume"] = second["position"]
        session["skipped"] = [[0, second["start_offset"]]]
        session["questions"] = ["条件是什么？ </script><script>bad()</script>"]
        session["paused"] = True
        self.write_bookmark(session)
        result = self.run_read("--session", self.bookmark, "--json", "--chunk-size", "8")
        self.assertEqual(result.returncode, 0, result.stderr)
        imported = json.loads(result.stdout)
        self.assertEqual(imported["session"], session)
        self.assertTrue(imported["session_imported"])
        output = self.root / "恢复.html"
        result = self.run_read("--session", self.bookmark, "-o", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = output.read_text(encoding="utf-8")
        self.assertNotIn("<script>bad()</script>", page)
        self.assertNotIn("__ADHD_SESSION_SCRIPT__", page)
        self.assertIn("AdhdReadingSession", page)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_changed_source_rejects_without_creating_output(self):
        self.write_bookmark(self.data["session"])
        self.source.write_bytes(self.original + "\r\n新增内容".encode("utf-8"))
        result = self.run_read("--session", self.bookmark)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertFalse(self.source.with_suffix(".reader.html").exists())
        self.assertEqual(json.loads(self.bookmark.read_text()), self.data["session"])

    def test_bad_bookmark_does_not_touch_existing_output(self):
        output = self.root / "keep.html"
        output.write_text("keep", encoding="utf-8")
        for text in ("not json", '{"schema":"adhd-md-session"}', "[" * 2000):
            with self.subTest(text=text[:30]):
                self.bookmark.write_text(text)
                result = self.run_read("--session", self.bookmark, "-o", output)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(output.read_text(), "keep")

    def test_missing_or_oversized_bookmark_fails_cleanly(self):
        for oversized in (False, True):
            if oversized:
                self.bookmark.write_bytes(b" " * (1024 * 1024 + 1))
            result = self.run_read("--session", self.bookmark, "--json")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
