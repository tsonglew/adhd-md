"""Behavioral state regressions using the generated HTML's actual JavaScript.

The Node harness supplies only DOM/storage/event primitives. These are not
rendering or browser compatibility tests; visual QA remains a separate check.
"""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import reader
import reading_session


NODE = shutil.which("node")
HARNESS = Path(__file__).with_name("reader_ui_harness.js")


def click(control):
    return {"type": "click", "id": control}


def snapshot():
    return {"type": "snapshot"}


@unittest.skipUnless(NODE, "Node is optional; install it for reader UI state regressions")
class ReaderUIStateTest(unittest.TestCase):
    def setUp(self):
        text = "".join(f"## 第 {number} 节 🧠\r\n\r\n保留第 {number} 节的前提、否定和例外。\r\n\r\n"
                       for number in range(1, 9))
        self.data = reader.build_reading_data(text, "八段 原文.md", chunk_size=900)
        self.assertEqual(len(self.data["chunks"]), 8)
        self.html = reader.render_reader(self.data)

    def exercise(self, operations, **options):
        request = {"html": self.html, "operations": operations, **options}
        result = subprocess.run([NODE, str(HARNESS)], input=json.dumps(request, ensure_ascii=True),
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshots = json.loads(result.stdout)
        for result in snapshots:
            reading_session.validate_session(result["session"], self.data)
        return snapshots

    def offset(self, index):
        return self.data["chunks"][index]["start_offset"]

    def seeded(self, index, *, paused=False):
        data = copy.deepcopy(self.data)
        data["session_imported"] = True
        data["session"]["current"] = dict(data["chunks"][index]["position"])
        data["session"]["resume"] = dict(data["chunks"][index]["position"])
        data["session"]["paused"] = paused
        return data

    def test_review_does_not_replace_resume_and_pause_reload_returns_to_it(self):
        operations = [click("next-button")] * 7 + [snapshot(), {"type": "toc", "index": 1}, snapshot(),
            click("pause-button"), {"type": "reload"}, snapshot(), click("resume-button"), snapshot()]
        reached, reviewed, paused, resumed = self.exercise(operations)
        self.assertEqual(reached["session"]["resume"]["offset"], self.offset(7))
        self.assertEqual(reviewed["session"]["current"]["offset"], self.offset(1))
        self.assertEqual(reviewed["session"]["resume"]["offset"], self.offset(7))
        self.assertFalse(reviewed["resumeHidden"])
        self.assertTrue(paused["session"]["paused"])
        self.assertFalse(paused["pauseHidden"])
        self.assertEqual(paused["session"]["resume"]["offset"], self.offset(7))
        self.assertFalse(resumed["session"]["paused"])
        self.assertEqual(resumed["session"]["current"]["offset"], self.offset(7))

    def test_skipped_section_stays_pending_until_explicit_next_after_return(self):
        skipped, returned, completed = self.exercise([
            click("skip-button"), snapshot(), {"type": "toc", "index": 0}, snapshot(),
            click("next-button"), snapshot(),
        ])
        expected = [[self.offset(0), self.offset(1)]]
        self.assertEqual(skipped["session"]["skipped"], expected)
        self.assertEqual(returned["session"]["skipped"], expected)
        self.assertEqual(returned["session"]["presented"], skipped["session"]["presented"])
        self.assertEqual(completed["session"]["skipped"], [])
        self.assertEqual(completed["session"]["presented"], [[0, self.offset(2)]])

    def test_invalid_import_does_not_change_current_session(self):
        invalid = reading_session.create_session(self.data)
        invalid["source"]["hash"] = "0" * 64
        before, after = self.exercise([
            click("next-button"), click("skip-button"), snapshot(),
            {"type": "fill", "id": "session-json", "value": json.dumps(invalid)},
            click("import-session"), snapshot(),
        ])
        self.assertEqual(after["session"], before["session"])
        self.assertEqual(after["messageError"], "true")
        self.assertIn("当前会话未改变", after["message"])

    def test_manual_import_survives_reload_of_page_with_an_initial_seed(self):
        seed = self.seeded(1, paused=True)
        replacement = self.seeded(5, paused=True)["session"]
        replacement["questions"] = ["保留这次在 Agent 中记录的问题。"]
        imported, reloaded = self.exercise([
            {"type": "fill", "id": "session-json", "value": json.dumps(replacement)},
            click("import-session"), snapshot(), {"type": "reload"}, snapshot(),
        ], html=reader.render_reader(seed))
        self.assertEqual(imported["session"], replacement)
        self.assertEqual(reloaded["session"], replacement)

    def test_legacy_progress_migration_does_not_invent_coverage(self):
        legacy_key = "adhd-md.reader.v1:" + self.data["source_hash"]
        legacy = {"index": 5, "sourceOffset": self.offset(5), "paused": True,
                  "completed": False, "view": "focus", "fontSize": 22, "spacious": True}
        paused, resumed = self.exercise([snapshot(), click("resume-button"), snapshot()],
                                        storage={legacy_key: json.dumps(legacy)})
        self.assertEqual(paused["session"]["current"]["offset"], self.offset(5))
        self.assertEqual(paused["session"]["resume"]["offset"], self.offset(5))
        self.assertEqual(paused["session"]["presented"], [])
        self.assertEqual(paused["session"]["skipped"], [])
        self.assertEqual(resumed["session"]["presented"], [[self.offset(5), self.offset(6)]])

    def test_unavailable_storage_still_allows_json_bookmark_download(self):
        exported, = self.exercise([click("next-button"), click("pause-button"),
                                  click("download-session"), snapshot()], failStorage=True)
        self.assertEqual(exported["storage"], {})
        self.assertIn("无法保存", exported["storageNote"])
        self.assertEqual(exported["session"]["resume"]["offset"], self.offset(1))
        self.assertTrue(exported["session"]["paused"])
        download, = exported["downloads"]
        self.assertEqual(download["name"], "reading-session.json")
        self.assertEqual(json.loads(download["text"]), exported["session"])

    def test_full_view_does_not_mark_all_sections_presented(self):
        before, full, reloaded = self.exercise([snapshot(), {"type": "view", "view": "full"},
                                               snapshot(), {"type": "reload"}, snapshot()])
        self.assertFalse(full["fullHidden"])
        self.assertEqual(before["session"]["presented"], [[0, self.offset(1)]])
        self.assertEqual(full["session"]["presented"], before["session"]["presented"])
        self.assertEqual(reloaded["session"]["presented"], before["session"]["presented"])

    def test_jumping_ahead_and_advancing_does_not_abandon_earlier_resume(self):
        jumped, advanced = self.exercise([click("next-button"), {"type": "toc", "index": 4},
                                         snapshot(), click("next-button"), snapshot()])
        self.assertEqual(jumped["session"]["resume"]["offset"], self.offset(1))
        self.assertEqual(advanced["session"]["current"]["offset"], self.offset(5))
        self.assertEqual(advanced["session"]["resume"]["offset"], self.offset(1))

    def test_ending_after_previewing_last_section_keeps_earlier_resume(self):
        ended, = self.exercise([click("next-button"), {"type": "toc", "index": 7},
                                click("next-button"), snapshot()])
        self.assertTrue(ended["session"]["ended"])
        self.assertEqual(ended["session"]["current"]["offset"], self.offset(7))
        self.assertEqual(ended["session"]["resume"]["offset"], self.offset(1))

    def test_distinct_seeded_pages_keep_their_own_updated_progress(self):
        page_a = reader.render_reader(self.seeded(1))
        page_b = reader.render_reader(self.seeded(4))
        advanced_a, opened_b, returned_a = self.exercise([
            click("next-button"), snapshot(),
            {"type": "navigate", "html": page_b, "pathname": "/b.reader.html"}, snapshot(),
            {"type": "navigate", "html": page_a, "pathname": "/a.reader.html"}, snapshot(),
        ], html=page_a, pathname="/a.reader.html")
        self.assertEqual(advanced_a["session"]["resume"]["offset"], self.offset(2))
        self.assertEqual(opened_b["session"]["resume"]["offset"], self.offset(4))
        self.assertEqual(returned_a["session"], advanced_a["session"])

    def test_invalid_utf8_file_import_leaves_the_session_unchanged(self):
        session = reading_session.create_session(self.data)
        session["questions"] = ["invalid-byte-here"]
        raw = json.dumps(session).encode("utf-8").replace(b"invalid-byte-here", b"\xff")
        before, after = self.exercise([click("next-button"), snapshot(),
                                       {"type": "file", "bytes": list(raw)}, snapshot()])
        self.assertEqual(after["session"], before["session"])
        self.assertEqual(after["messageError"], "true")

    def test_downloaded_continuation_source_matches_bookmark_despite_provenance(self):
        data = copy.deepcopy(self.data)
        data["origin"] = {"kind": "web", "method": "stdlib-htmlparser",
                          "location": "https://example.invalid/article", "warnings": ["图片需回看来源。"]}
        result, = self.exercise([click("download-session-source"), snapshot()], html=reader.render_reader(data))
        download, = result["downloads"]
        self.assertEqual(download["text"], self.data["source_text"])
        recovered = reader.build_reading_data(download["text"], download["name"])
        reading_session.validate_session(result["session"], recovered)


if __name__ == "__main__":
    unittest.main()
