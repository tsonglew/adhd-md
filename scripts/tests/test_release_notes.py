import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("release_notes", Path(__file__).resolve().parents[1] / "release_notes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseNotesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "package.json").write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")

    def notes(self, changelog, tag="v1.2.3"):
        (self.root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        return module.release_notes(self.root, tag)

    def test_only_selected_version_is_published(self):
        self.assertEqual(self.notes("# Changes\n\n## Unreleased\nFuture\n\n## 1.2.3 - 2026-10-14\n\n### 修复\n\n- 保留说明。\n\n## 1.2.2\nOld\n"), "### 修复\n\n- 保留说明。\n")

    def test_rejects_unreleased_empty_and_duplicate_notes(self):
        for text in ("## Unreleased\nPending\n", "## 1.2.3\n\n", "## 1.2.3\nOne\n## 1.2.3\nTwo\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.notes(text)

    def test_rejects_mismatch_and_invalid_tags(self):
        for tag in ("v1.2.4", "1.2.3", "v01.2.3", "v1.2.3-rc.1", "v1.2.3\n", "v1.2.3; echo bad"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.notes("## 1.2.3\nNotes\n", tag)


if __name__ == "__main__":
    unittest.main()
