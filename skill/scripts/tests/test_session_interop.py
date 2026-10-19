"""Check portable reading bookmarks across Python and the browser's JavaScript.

The cases model interruption, skipped reading, changed chunk sizes, and damaged
bookmarks. Node runs only the pure session module; no browser or network is used.
"""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import reader
import reading_session


NODE = shutil.which("node")
JS_MODULE = SCRIPTS.parent / "assets" / "reader-session.js"
NODE_RUNNER = r"""
const api = require(process.argv[1]);
const requests = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const results = requests.map(request => {
  try {
    let value;
    if (request.operation === 'create') value = api.create(request.data);
    else if (request.operation === 'validate') value = api.validate(request.session, request.data);
    else if (request.operation === 'parse') value = api.parse(request.text, request.data);
    else throw new Error('unsupported test operation');
    return {ok: true, value};
  } catch (error) {
    return {ok: false, error: error.message};
  }
});
process.stdout.write(JSON.stringify(results));
"""


@unittest.skipUnless(NODE, "Node is optional; install it for Python/browser session interoperability tests")
class SessionInteropTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.text = (
            "# 开始 🧠\r\n\r\n"
            + "先核对配置，0 表示不超时，但生产环境不建议这样用。" * 6
            + "\r\n\r\n## 暂时跳过\r\n\r\n"
            + "遇到错误先保留日志，不要直接覆盖配置。" * 6
            + "\r\n\r\n## 回来继续 🚀\r\n\r\n"
            + "第二次重试前仍须核对条件。保留原文中的例外与单位。" * 6
            + "\r\n"
        )
        self.data = reader.build_reading_data(self.text, "资料/已有 文档.md", chunk_size=70)
        self.skip_index = self.text.index("## 暂时跳过")
        self.return_index = self.text.index("## 回来继续")

    def js(self, *requests):
        result = subprocess.run(
            [NODE, "-e", NODE_RUNNER, str(JS_MODULE)],
            input=json.dumps(requests, ensure_ascii=True),
            text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def read_in_python(self, text):
        path = self.root / "阅读 书签.json"
        path.write_bytes(text.encode("utf-8"))
        return reading_session.read_session(path, self.data)

    def position(self, scalar_index):
        return {
            "offset": len(self.text[:scalar_index].encode("utf-16-le")) // 2,
            "anchor": self.text[scalar_index:scalar_index + 64],
        }

    def interrupted_session(self):
        session = reading_session.create_session(self.data)
        start = self.position(self.skip_index)["offset"]
        end = self.position(self.return_index)["offset"]
        length = session["source"]["length"]
        session.update({
            "current": self.position(self.return_index),
            "resume": self.position(self.skip_index),
            # Out-of-order adjacent ranges are valid and must normalize alike.
            "presented": [[end, length], [5, start], [0, 5]],
            "skipped": [[start, end]],
            "questions": ["这里的 0 是否仍表示不超时？", "\r\n保留 🧠 和原文里的条件。\r\n",
                          '原文里的 {"version": 1, "version": 2} 只是待澄清示例。'],
            "paused": True,
        })
        return session

    def test_fresh_bookmark_matches_across_languages_and_keeps_unicode_anchors(self):
        for source in (self.text, "🧠" * 70 + "\r\n尾部", ""):
            with self.subTest(source=source[:12]):
                data = reader.build_reading_data(source, "资料 🧠.md", chunk_size=30)
                expected = reading_session.create_session(data)
                result = self.js({"operation": "create", "data": data})[0]
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["value"], expected)
                self.assertEqual(expected["source"]["length"], len(source.encode("utf-16-le")) // 2)
                self.assertEqual(expected["current"]["anchor"], source[:64])
                self.assertEqual(reading_session.validate_session(result["value"], data), expected)

    def test_interrupted_reading_roundtrip_preserves_skips_questions_and_crlf(self):
        original = self.interrupted_session()
        untouched = copy.deepcopy(original)
        expected = reading_session.validate_session(original, self.data)
        start = self.position(self.skip_index)["offset"]
        end = self.position(self.return_index)["offset"]
        self.assertEqual(expected["presented"], [[0, start], [end, expected["source"]["length"]]])
        self.assertEqual(expected["skipped"], [[start, end]])
        self.assertIn("\r\n", expected["resume"]["anchor"])
        results = self.js(
            {"operation": "validate", "session": original, "data": self.data},
            {"operation": "parse", "text": json.dumps(original, ensure_ascii=False), "data": self.data},
        )
        for result in results:
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["value"], expected)
            self.assertEqual(self.read_in_python(json.dumps(result["value"], ensure_ascii=False)), expected)
        self.assertEqual(original, untouched)
        self.assertEqual(expected["questions"], original["questions"])
        self.assertTrue(expected["paused"])
        self.assertFalse(expected["ended"])

    def test_rechunking_retains_source_position_and_pending_ranges(self):
        session = reading_session.validate_session(self.interrupted_session(), self.data)
        reshaped = reader.build_reading_data(self.text, self.data["source_name"], chunk_size=1000)
        self.assertNotEqual(len(self.data["chunks"]), len(reshaped["chunks"]))
        self.assertEqual(reading_session.validate_session(session, reshaped), session)
        result = self.js({"operation": "validate", "session": session, "data": reshaped})[0]
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["value"], session)
        # The same source location can belong to a different displayed chunk.
        indices = []
        for data in (self.data, reshaped):
            containing = [chunk for chunk in data["chunks"]
                          if chunk["start_offset"] <= session["current"]["offset"] < chunk["end_offset"]]
            self.assertEqual(len(containing), 1)
            indices.append(containing[0]["index"])
        self.assertNotEqual(indices[0], indices[1])

    def test_same_content_can_move_without_losing_its_bookmark(self):
        session = self.interrupted_session()
        renamed = reader.build_reading_data(self.text, "新目录/已搬走 文档.md", chunk_size=150)
        expected = reading_session.validate_session(session, renamed)
        result = self.js({"operation": "validate", "session": session, "data": renamed})[0]
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["value"], expected)
        self.assertEqual(expected["source"]["name"], renamed["source_name"])
        self.assertEqual(expected["source"]["hash"], session["source"]["hash"])
        self.assertEqual(expected["resume"], session["resume"])

    def test_changed_source_is_rejected_even_when_length_and_anchors_match(self):
        session = reading_session.create_session(self.data)
        # Change a late condition outside either 64-character bookmark anchor.
        changed = self.text[:200] + ("否" if self.text[200] != "否" else "是") + self.text[201:]
        data = reader.build_reading_data(changed, self.data["source_name"])
        self.assertEqual(data["source_text"][:64], self.text[:64])
        self.assertEqual(len(changed.encode("utf-16-le")), len(self.text.encode("utf-16-le")))
        with self.assertRaises(ValueError):
            reading_session.validate_session(session, data)
        result = self.js({"operation": "validate", "session": session, "data": data})[0]
        self.assertFalse(result["ok"])

    def test_damaged_bookmarks_are_rejected_by_both_languages(self):
        base = reading_session.create_session(self.data)
        length = base["source"]["length"]
        mutations = [
            ("schema", ("schema",), "another-format"),
            ("version", ("version",), 2),
            ("boolean-version", ("version",), True),
            ("hash", ("source", "hash"), "0" * 64),
            ("length", ("source", "length"), length + 1),
            ("boolean-length", ("source", "length"), True),
            ("current-anchor", ("current", "anchor"), "别的文档"),
            ("resume-anchor", ("resume", "anchor"), ""),
            ("negative-offset", ("current", "offset"), -1),
            ("past-end-offset", ("current", "offset"), length + 1),
            ("fraction-offset", ("current", "offset"), 0.5),
            ("boolean-offset", ("current", "offset"), False),
            ("split-emoji-offset", ("current", "offset"), 6),
            ("split-emoji-range", ("presented",), [[0, 6], [6, 7]]),
            ("empty-range", ("presented",), [[0, 0]]),
            ("reversed-range", ("presented",), [[7, 0]]),
            ("overlapping-ranges", ("presented",), [[0, 7], [5, 10]]),
            ("range-past-end", ("skipped",), [[0, length + 1]]),
            ("question-length", ("questions",), ["🧠" * 1001]),
            ("question-type", ("questions",), [None]),
            ("paused-type", ("paused",), 1),
            ("ended-type", ("ended",), "false"),
            ("unknown-root-field", ("run_command",), "echo should-never-run"),
            ("unknown-source-field", ("source", "url"), "https://example.invalid"),
            ("unknown-position-field", ("resume", "chunk"), 1),
        ]
        damaged = []
        for label, path, value in mutations:
            session = copy.deepcopy(base)
            target = session
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            damaged.append((label, session))
        cross_overlap = copy.deepcopy(base)
        cross_overlap.update(presented=[[0, 10]], skipped=[[5, 12]])
        damaged.append(("presented-skipped-overlap", cross_overlap))
        results = self.js(*({"operation": "validate", "session": session, "data": self.data}
                            for _, session in damaged))
        for (label, session), result in zip(damaged, results):
            with self.subTest(case=label):
                with self.assertRaises(ValueError):
                    reading_session.validate_session(session, self.data)
                self.assertFalse(result["ok"], result)

    def test_whitespace_only_questions_have_one_contract(self):
        values = ["", " \t\r\n", "\ufeff", "\x85", "\x1c", "\u2003", "\ufeff\x85 "]
        sessions = []
        for value in values:
            session = reading_session.create_session(self.data)
            session["questions"] = [value]
            sessions.append(session)
        results = self.js(*({"operation": "validate", "session": session, "data": self.data}
                            for session in sessions))
        for question, session, result in zip(values, sessions, results):
            with self.subTest(question=repr(question)):
                with self.assertRaises(ValueError):
                    reading_session.validate_session(session, self.data)
                self.assertFalse(result["ok"], result)

    def test_parse_rejects_duplicate_fields_and_invalid_json_in_both_languages(self):
        session = reading_session.create_session(self.data)
        valid = json.dumps(session, ensure_ascii=False)
        texts = {
            "duplicate-root": '{"version": 1,' + valid[1:],
            "duplicate-nested": valid.replace('"current": {', '"current": {"offset": 0,', 1),
            "duplicate-escaped-key": '{"\\u0076ersion": 1,' + valid[1:],
            "decimal-version": valid.replace('"version": 1', '"version": 1.0', 1),
            "exponent-version": valid.replace('"version": 1', '"version": 1e0', 1),
            "nonstandard-constant": valid.replace('"version": 1', '"version": NaN', 1),
            "truncated": valid[:-1],
            "fenced-json": "```json\n" + valid + "\n```",
            "oversized": valid + " " * (1024 * 1024),
        }
        results = self.js(*({"operation": "parse", "text": text, "data": self.data}
                            for text in texts.values()))
        for (label, text), result in zip(texts.items(), results):
            with self.subTest(case=label):
                with self.assertRaises(ValueError):
                    self.read_in_python(text)
                self.assertFalse(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
