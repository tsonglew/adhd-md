#!/usr/bin/env python3
"""从 skill/ 生成自包含单文件版（Tier C：无文件、无 shell 的环境）。

单一真源：内容全部来自 skill/SKILL.md 与 skill/references/，这里只做拼装与
标题降级。不要手改 dist/ 里的产物。

用法：python3 scripts/build_standalone.py [--check]
  --check  只比对产物是否与源同步，不写文件（退出码 1 表示需要重新生成）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skill"
OUT = REPO / "dist" / "adhd-md.standalone.md"

# 附录顺序。examples/ 与 doc-types 不进单文件：体积换收益不划算，
# 单文件的使用场景是「粘进网页版聊天框」。
APPENDIX = [
    ("A", "规则库", "references/rules.md"),
    ("B", "反模式：优化过头", "references/antipatterns.md"),
    ("C", "中文文档专项", "references/cjk.md"),
]

PREAMBLE = """<!-- 本文件由 scripts/build_standalone.py 从 skill/ 生成，请勿手改。 -->

# adhd-md（自包含单文件版）

> **这个版本用于没有命令执行能力的环境**：网页版 LLM，或任何不能跑 shell 的 agent。

下文所有 `python3 .../adhd_md.py` 命令**全部跳过**。改为按附录 A 的规则人工执行，用附录 B 末尾的自检清单自查。

**必须在报告里写明「未做机器校验」。** 假装跑过校验比不校验更糟。

能跑命令的环境请用完整版，带确定性审计与无损校验脚本。
"""


def anchor_of(title: str) -> str:
    a = re.sub(r"[`*\[\]()·、，。：；？！/\\.,:;?!]", "", title)
    return a.strip().lower().replace(" ", "-")


def make_toc(text: str) -> list:
    """从成品的 H2 生成目录。不新写文字，只复用标题。"""
    out, in_fence = [], False
    for line in text.split("\n"):
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        m = re.match(r"^##\s+(.*)$", line)
        if m and not in_fence:
            t = m.group(1).strip()
            out.append(f"- [{t}](#{anchor_of(t)})")
    return out


def demote(md: str, levels: int = 1) -> str:
    """标题降级，最深到 H6。代码块内部不动。"""
    out, in_fence = [], False
    for line in md.split("\n"):
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            out.append(line)
            continue
        m = re.match(r"^(#{1,6})(\s+.*)$", line)
        if m and not in_fence:
            out.append("#" * min(6, len(m.group(1)) + levels) + m.group(2))
        else:
            out.append(line)
    return "\n".join(out)


def strip_frontmatter(md: str) -> tuple[str, str]:
    """返回 (frontmatter 里的 description, 正文)"""
    if not md.startswith("---"):
        return "", md
    end = md.index("\n---", 3)
    fm, body = md[3:end], md[end + 4:]
    desc = ""
    m = re.search(r"^description:\s*(.+)$", fm, re.M)
    if m:
        desc = m.group(1).strip()
    return desc, body.lstrip("\n")


def build() -> str:
    desc, body = strip_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    parts = [PREAMBLE]
    if desc:
        parts.append(f"**什么时候用**：{desc}\n")
    # 全文只保留 PREAMBLE 的一个 H1，其余整体降一级
    parts.append(demote(body, 1))

    for letter, title, rel in APPENDIX:
        src = (SKILL / rel).read_text(encoding="utf-8")
        # 去掉原文件的 H1，用统一的附录标题替代
        src = re.sub(r"^#\s+.*\n+", "", src, count=1)
        parts.append(f"\n---\n\n## 附录 {letter} · {title}\n")
        parts.append(demote(src, 1))

    text = "\n".join(parts)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    toc = make_toc(text)
    marker = "\n下文所有"
    if len(toc) >= 3 and marker in text:
        head, rest = text.split(marker, 1)
        text = head + "\n" + "\n".join(toc) + "\n" + marker + rest

    return text.rstrip("\n") + "\n"


def main() -> int:
    text = build()
    check = "--check" in sys.argv[1:]
    if check:
        if not OUT.is_file():
            print(f"✗ {OUT.relative_to(REPO)} 不存在，跑一次 build_standalone.py")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"✗ {OUT.relative_to(REPO)} 与 skill/ 不同步，重新生成")
            return 1
        print(f"✓ {OUT.relative_to(REPO)} 与源同步")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    kb = len(text.encode("utf-8")) / 1024
    print(f"✓ {OUT.relative_to(REPO)}  {len(text.splitlines())} 行  {kb:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
