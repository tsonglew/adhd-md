"""Exact-source, portable reading sessions and Python/browser offset parity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import reading_session as sessions
import reader


def source_data(text, name="中文😀.md"):
    return {"source_text": text, "source_name": name,
            "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def position(text, offset):
    prefix = text.encode("utf-16-le")[:offset * 2].decode("utf-16-le")
    return {"offset": offset, "anchor": text[len(prefix):len(prefix) + 64]}


class ReadingSessionTest(unittest.TestCase):
    def setUp(self):
        self.text = "中😀文\r\n第一句。🧠第二句。\r\n"
        self.data = source_data(self.text)
        self.session = sessions.create_session(self.data)

    def rejected(self, mutate, pattern=None):
        candidate = copy.deepcopy(self.session)
        mutate(candidate)
        with self.assertRaisesRegex(ValueError, pattern or "阅读书签："):
            sessions.validate_session(candidate, self.data)

    def test_initial_session_uses_utf16_and_independent_positions(self):
        self.assertEqual(self.session["source"]["length"], len(self.text) + 2)
        self.assertEqual(self.session["source"]["hash"], self.data["source_hash"])
        self.assertEqual(self.session["current"], position(self.text, 0))
        self.assertEqual(self.session["resume"], position(self.text, 0))
        self.assertIsNot(self.session["current"], self.session["resume"])
        self.assertEqual(self.session["presented"], [])
        self.assertFalse(self.session["paused"])
        self.assertFalse(self.session["ended"])

    def test_anchor_counts_unicode_codepoints_not_utf16_units(self):
        text = "😀" * 70 + "中文"
        data = source_data(text)
        session = sessions.create_session(data)
        self.assertEqual(session["current"]["anchor"], "😀" * 64)
        session["current"] = position(text, 2)
        self.assertEqual(sessions.validate_session(session, data)["current"], position(text, 2))

    def test_empty_source_and_eof_positions_are_valid(self):
        data = source_data("")
        empty = sessions.create_session(data)
        self.assertEqual(empty["source"]["length"], 0)
        self.assertEqual(empty["current"], {"offset": 0, "anchor": ""})
        self.assertEqual(sessions.validate_session(empty, data), empty)
        length = self.session["source"]["length"]
        self.session["current"] = self.session["resume"] = {"offset": length, "anchor": ""}
        self.assertEqual(sessions.validate_session(self.session, self.data)["resume"]["offset"], length)

    def test_normalization_renames_source_sorts_ranges_without_mutation(self):
        self.session["source"]["name"] = "旧名.md"
        self.session["presented"] = [[4, 6], [0, 1], [1, 4]]
        self.session["skipped"] = [[6, 7]]
        self.session["questions"] = ["  原文这里是什么意思？  "]
        original = copy.deepcopy(self.session)
        actual = sessions.validate_session(self.session, self.data)
        self.assertEqual(self.session, original)
        self.assertEqual(actual["source"]["name"], self.data["source_name"])
        self.assertEqual(actual["presented"], [[0, 6]])
        self.assertEqual(actual["skipped"], [[6, 7]])
        self.assertEqual(actual["questions"], original["questions"])
        actual["current"]["offset"] = 99
        actual["questions"].append("新的问题")
        self.assertEqual(self.session, original)

    def test_hash_or_length_mismatch_rejects_even_with_plausible_anchor(self):
        self.rejected(lambda s: s["source"].update(hash="0" * 64), "原文不匹配")
        self.rejected(lambda s: s["source"].update(length=1234), "原文不匹配")
        changed = source_data(self.text + "新增正文")
        with self.assertRaisesRegex(ValueError, "原文不匹配"):
            sessions.validate_session(self.session, changed)

    def test_only_schema_and_integer_version_one_are_supported(self):
        for value in (None, "session", 1, True):
            with self.subTest(schema=value):
                self.rejected(lambda s: s.update(schema=value), "格式")
        for value in (0, 2, -1, "1", True, 1.0, None):
            with self.subTest(version=value):
                self.rejected(lambda s: s.update(version=value), "版本")

    def test_required_and_unknown_fields_reject_at_each_object_level(self):
        for value in (None, [], "{}", 1):
            with self.subTest(root=value), self.assertRaisesRegex(ValueError, "JSON 对象"):
                sessions.validate_session(value, self.data)
        for key in self.session:
            with self.subTest(missing=key):
                self.rejected(lambda s: s.pop(key), "字段")
        self.rejected(lambda s: s.update(unrecognized=True), "字段")
        for key in ("source", "current", "resume"):
            with self.subTest(nested=key):
                self.rejected(lambda s: s[key].update(unrecognized=1), "字段")
                self.rejected(lambda s: s.update({key: []}), "JSON 对象")

    def test_source_field_types_and_bounds(self):
        for name in (None, 1, True, "a" * 4097, "\ud800"):
            with self.subTest(name=str(name)[:30]):
                self.rejected(lambda s: s["source"].update(name=name), "来源名称")
        self.session["source"]["name"] = "😀" * 4096
        self.assertEqual(sessions.validate_session(self.session, self.data)["source"]["name"], self.data["source_name"])
        for digest in (True, "", "a" * 63, "A" * 64, "g" * 64, "a" * 64 + "\n"):
            with self.subTest(hash=digest):
                self.rejected(lambda s: s["source"].update(hash=digest), "来源哈希")
        for length in (-1, True, 1.0, "1", None):
            with self.subTest(length=length):
                self.rejected(lambda s: s["source"].update(length=length), "来源长度")

    def test_positions_reject_bad_types_out_of_range_and_surrogate_midpoint(self):
        for key in ("current", "resume"):
            for offset in (-1, self.session["source"]["length"] + 1, True, 1.0, "1", None, 2):
                with self.subTest(key=key, offset=offset):
                    self.rejected(lambda s: s[key].update(offset=offset))
            self.session[key] = position(self.text, 3)
        self.assertEqual(sessions.validate_session(self.session, self.data)["current"]["offset"], 3)

    def test_anchor_must_match_exact_source_and_cannot_be_truncated(self):
        for anchor in ("", "不对应", "a" * 65, "\ud800", None, [], True):
            with self.subTest(anchor=anchor):
                self.rejected(lambda s: s["current"].update(anchor=anchor))
        text = "字" * 100
        data = source_data(text)
        session = sessions.create_session(data)
        session["current"]["anchor"] = "字" * 63
        with self.assertRaisesRegex(ValueError, "锚点"):
            sessions.validate_session(session, data)

    def test_range_shapes_types_and_bounds(self):
        for key in ("presented", "skipped"):
            for ranges in (None, {}, (), [[0]], [[0, 1, 2]], [(0, 1)], [[False, 1]],
                           [[0, 1.0]], [[-1, 1]], [[0, 999]], [[3, 1]], [[1, 1]]):
                with self.subTest(key=key, ranges=ranges):
                    self.rejected(lambda s: s.update({key: ranges}))

    def test_range_count_is_bounded_before_normalization(self):
        for key in ("presented", "skipped"):
            with self.subTest(key=key):
                self.rejected(lambda s: s.update({key: [[0, 1]] * 10001}), "10000")
        data = source_data("x" * 10000)
        session = sessions.create_session(data)
        session["presented"] = [[index, index + 1] for index in range(10000)]
        self.assertEqual(sessions.validate_session(session, data)["presented"], [[0, 10000]])

    def test_overlaps_within_or_across_lists_are_rejected(self):
        for key in ("presented", "skipped"):
            with self.subTest(key=key):
                self.rejected(lambda s: s.update({key: [[0, 4], [3, 6]]}), "重叠")
                self.rejected(lambda s: s.update({key: [[0, 1], [0, 1]]}), "重叠")
        self.rejected(lambda s: s.update(presented=[[0, 4]], skipped=[[3, 6]]), "已带读范围与跳过范围重叠")

    def test_adjacent_merge_cannot_hide_invalid_utf16_boundary(self):
        self.rejected(lambda s: s.update(presented=[[0, 2], [2, 4]]), "Unicode 字符中间")
        self.rejected(lambda s: s.update(skipped=[[1, 2]]), "Unicode 字符中间")

    def test_questions_are_bounded_strings_and_never_invented(self):
        for questions in (None, {}, (), [None], [True], [""], [" \n\t　"], ["\ufeff"], ["\x85"], ["\x1c"], ["\ud800"],
                          ["x" * 1001], ["问题"] * 101):
            with self.subTest(questions=str(questions)[:30]):
                self.rejected(lambda s: s.update(questions=questions))
        self.session["questions"] = ["😀" * 1000] * 100
        self.assertEqual(sessions.validate_session(self.session, self.data)["questions"], self.session["questions"])

    def test_paused_and_ended_require_boolean_values(self):
        for key in ("paused", "ended"):
            for value in (None, 0, 1, "true", []):
                with self.subTest(key=key, value=value):
                    self.rejected(lambda s: s.update({key: value}), "true 或 false")
        self.session.update(paused=True, ended=True)
        self.assertEqual(sessions.validate_session(self.session, self.data), self.session)

    def test_chunk_offsets_and_positions_partition_utf16_source(self):
        data = reader.build_reading_data(self.text, "test.md", chunk_size=7)
        cursor = 0
        for chunk in data["chunks"]:
            self.assertEqual(chunk["start_offset"], cursor)
            self.assertEqual(chunk["position"], position(self.text, cursor))
            cursor += len(chunk["source"].encode("utf-16-le")) // 2
            self.assertEqual(chunk["end_offset"], cursor)
        self.assertEqual(cursor, data["session"]["source"]["length"])
        self.assertEqual(data["session"], sessions.create_session(data))

    def test_rechunking_preserves_session_positions_without_index_mapping(self):
        text = "# 中文😀\r\n\r\n" + "🧠这是一段内容。还要保留条件。\r\n\r\n" * 20
        small = reader.build_reading_data(text, "small.md", chunk_size=30)
        large = reader.build_reading_data(text, "large.md", chunk_size=200)
        session = small["session"]
        session["current"] = copy.deepcopy(small["chunks"][3]["position"])
        session["resume"] = copy.deepcopy(small["chunks"][6]["position"])
        session["presented"] = [[0, small["chunks"][6]["start_offset"]]]
        session["paused"] = True
        actual = sessions.validate_session(session, large)
        self.assertNotEqual(len(small["chunks"]), len(large["chunks"]))
        self.assertEqual(actual["current"], session["current"])
        self.assertEqual(actual["resume"], session["resume"])
        self.assertEqual(actual["source"]["name"], "large.md")

    def test_reader_supports_direct_file_loading_without_scripts_on_sys_path(self):
        script = """import importlib.util, sys
spec = importlib.util.spec_from_file_location('isolated_reader', sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
data = module.build_reading_data('中文😀', 'source.md')
assert data['session']['source']['length'] == 4
assert data['chunks'][0]['end_offset'] == 4
"""
        result = subprocess.run([sys.executable, "-I", "-c", script, str(SCRIPTS / "reader.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class ReadSessionFileTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "book.json"
        self.data = source_data("中文😀\r\n下一段。")
        self.session = sessions.create_session(self.data)

    def read(self, raw):
        self.path.write_bytes(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
        return sessions.read_session(self.path, self.data)

    def test_utf8_json_roundtrip_and_exact_size_limit(self):
        raw = json.dumps(self.session, ensure_ascii=False).encode("utf-8")
        self.assertEqual(self.read(raw), self.session)
        self.assertEqual(self.read(raw + b" " * (sessions.MAX_SESSION_BYTES - len(raw))), self.session)
        with self.assertRaisesRegex(ValueError, "超过 1 MiB"):
            self.read(raw + b" " * (sessions.MAX_SESSION_BYTES + 1 - len(raw)))

    def test_fenced_invalid_encoded_and_truncated_json_rejected(self):
        raw = json.dumps(self.session, ensure_ascii=False)
        for invalid in ("```json\n" + raw + "\n```", raw[:-1], "", b"\xff", "\ufeff" + raw):
            with self.subTest(prefix=str(invalid)[:30]), self.assertRaisesRegex(ValueError, "UTF-8 JSON"):
                self.read(invalid)
        # JSON implementations may reject nesting while parsing or accept the
        # array first; neither path may accept it as a reading session.
        with self.assertRaisesRegex(ValueError, "阅读书签："):
            self.read("[" * 2000 + "]" * 2000)

    def test_duplicate_fields_and_nonfinite_numbers_rejected(self):
        raw = json.dumps(self.session)
        for invalid in ('{"schema":"adhd-md-session",' + raw[1:],
                        raw.replace('"offset": 0', '"offset": 0, "offset": 0', 1)):
            with self.subTest(duplicate=invalid[:80]), self.assertRaisesRegex(ValueError, "重复字段"):
                self.read(invalid)
        for value in ("NaN", "Infinity", "-Infinity"):
            invalid = raw.replace('"version": 1', '"version": ' + value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "NaN 或 Infinity"):
                self.read(invalid)

    def test_json_with_wrong_source_or_missing_file_has_readable_error(self):
        self.session["source"]["hash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "原文不匹配"):
            self.read(json.dumps(self.session))
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, "无法读取书签文件"):
            sessions.read_session(self.path, self.data)


if __name__ == "__main__":
    unittest.main()
