"""标准 unittest 入口：`python3 -m unittest discover skill/scripts/tests`

测试本体写在 adhd_md.py 的 SelfTest 里，与实现同文件、同步演进。
这里只做加载，避免两份测试互相漂移。
"""
import importlib.util
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "adhd_md.py"
_spec = importlib.util.spec_from_file_location("adhd_md", _SRC)
adhd_md = importlib.util.module_from_spec(_spec)
sys.modules["adhd_md"] = adhd_md
_spec.loader.exec_module(adhd_md)

SelfTest = adhd_md.SelfTest

if __name__ == "__main__":
    import unittest

    unittest.main()
