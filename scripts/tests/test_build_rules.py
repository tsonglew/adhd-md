import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import build_rules  # noqa: E402


class BuildRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(build_rules.DATA.read_text(encoding="utf-8"))

    def test_rejects_missing_id(self):
        data = copy.deepcopy(self.data)
        data["rules"][0]["id"] = ""
        with self.assertRaisesRegex(build_rules.DefinitionError, "ID 非法"):
            build_rules.validate(data)

    def test_rejects_duplicate_id(self):
        data = copy.deepcopy(self.data)
        data["rules"].append(copy.deepcopy(data["rules"][0]))
        with self.assertRaisesRegex(build_rules.DefinitionError, "ID 重复"):
            build_rules.validate(data)

    def test_rejects_invalid_level(self):
        data = copy.deepcopy(self.data)
        data["rules"][0]["min_level"] = 4
        with self.assertRaisesRegex(build_rules.DefinitionError, "min_level"):
            build_rules.validate(data)

    def test_check_fails_on_generated_table_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            refs = root / "skill/references"
            scripts = root / "skill/scripts"
            refs.mkdir(parents=True)
            scripts.mkdir(parents=True)
            data_path = refs / "rule-definitions.json"
            rules_path = refs / "rules.md"
            rubric_path = refs / "rubric.md"
            evidence_path = refs / "evidence.md"
            runtime_path = scripts / "adhd_md.py"
            data_path.write_text(build_rules.DATA.read_text(encoding="utf-8"), encoding="utf-8")
            runtime_path.write_text(build_rules.RUNTIME_PY.read_text(encoding="utf-8"), encoding="utf-8")
            rules_path.write_text(build_rules.RULES_MD.read_text(encoding="utf-8"), encoding="utf-8")
            rubric_path.write_text(build_rules.RUBRIC_MD.read_text(encoding="utf-8"), encoding="utf-8")
            evidence_path.write_text(build_rules.EVIDENCE_MD.read_text(encoding="utf-8"), encoding="utf-8")
            replacements = {
                "ROOT": root,
                "DATA": data_path,
                "RULES_MD": rules_path,
                "RUBRIC_MD": rubric_path,
                "EVIDENCE_MD": evidence_path,
                "RUNTIME_PY": runtime_path,
            }
            output = io.StringIO()
            with mock.patch.multiple(build_rules, **replacements):
                expected = build_rules.expected_files(self.data)
                for path, content in expected.items():
                    path.write_text(content, encoding="utf-8")
                rules_path.write_text(
                    rules_path.read_text(encoding="utf-8").replace("| ID | 规则 |", "| ID | 手工漂移 |", 1),
                    encoding="utf-8",
                )
                with contextlib.redirect_stderr(output):
                    result = build_rules.main(["--check"])
            self.assertEqual(result, 1)
            self.assertIn("skill/references/rules.md", output.getvalue())


if __name__ == "__main__":
    unittest.main()
