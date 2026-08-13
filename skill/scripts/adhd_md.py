#!/usr/bin/env python3
"""adhd-md 的确定性工具层：审计、格式修复、无损校验。

设计原则：能用规则算准的事情不交给模型。
纯标准库，单文件，Python 3.9+。

子命令：
  audit   评分 + 逐条 findings
  fmt     确定性格式修复（默认只做零风险项）
  verify  无损校验门禁（format 档可证明无损）
  report  改前改后分数对比
  init    生成文档骨架
  selftest 自检
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "0.1.0"

# ---------------------------------------------------------------- 字符与阈值

CJK = r"㐀-䶿一-鿿豈-﫿぀-ヿ"
CJK_RE = re.compile(f"[{CJK}]")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’-]*")
EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff☀-⛿✀-➿\U0001f1e6-\U0001f1ff]"
)
# 单义排版符号不算 emoji：字形单色稳定、语义唯一、表格里比文字更快扫。
# 与已排除的箭头（→ ←）同类。带变体选择符 U+FE0F 时按 emoji 呈现，仍然算。
TYPO_MARKS = "✓✔✗✘"
EMOJI_RE = re.compile(
    f"(?![{TYPO_MARKS}](?!️))"
    "[\U0001f000-\U0001faff☀-⛿✀-➿\U0001f1e6-\U0001f1ff]"
)

TH = {
    "en": dict(para=80, section=200, sent_mean=20, sent_p90=30, tldr=120, frag=25),
    "zh": dict(para=160, section=400, sent_mean=45, sent_p90=70, tldr=120, frag=40),
}

DIMS = {
    "hook": ("首屏结论力", 18),
    "chunk": ("分块粒度", 18),
    "scan": ("扫读性", 13),
    "sentence": ("句子负荷", 13),
    "action": ("行动性", 12),
    "typo": ("排版一致性", 13),
    "human": ("活人感", 13),
}

# rule -> (dim, 每次扣分, 上限)
DEDUCT = {
    "H1": ("hook", 60, 60),
    "H2": ("hook", 15, 15),
    "P1": ("chunk", 8, 60),
    "P4": ("chunk", 10, 30),
    "S3": ("chunk", 10, 40),
    "N1": ("scan", 20, 20),
    "L3": ("scan", 12, 12),
    "L1": ("scan", 10, 30),
    "N5": ("scan", 8, 24),
    "L5": ("scan", 4, 20),
    "N2": ("scan", 5, 20),
    "N6": ("scan", 4, 12),
    "W1m": ("sentence", 15, 50),
    "W1x": ("sentence", 8, 32),
    "W4": ("sentence", 8, 24),
    "C3": ("sentence", 8, 32),
    "W6": ("sentence", 2, 16),
    "C5": ("sentence", 3, 12),
    "A4": ("action", 6, 24),
    "T1": ("typo", 8, 32),
    "T2d": ("typo", 20, 20),
    "T2p": ("typo", 3, 15),
    "S1": ("typo", 10, 30),
    "S2": ("typo", 10, 10),
    "C1": ("typo", 1, 15),
    "C2": ("typo", 2, 16),
    "C8": ("typo", 3, 15),
    "T4": ("typo", 5, 5),
    "T7": ("typo", 5, 5),
    "T8": ("typo", 5, 15),
    "M1": ("human", 10, 40),
    "M3": ("human", 5, 20),
    "M4": ("human", 4, 24),
    "M5": ("human", 3, 18),
    "M6": ("human", 3, 18),
    "M7": ("human", 8, 24),
    "M8": ("human", 5, 25),
    "M9": ("human", 8, 32),
}

# 全局扣分（X 组），最多 20
X_DEDUCT = {"X1p": 8, "X1c": 5, "X2": 8, "X5": 6}
X_CAP = 20

# 仅在指定 level 及以上生效
MIN_LEVEL = {"C5": 3}

# 脚本判不了、必须模型补的规则
JUDGE_ONLY = [
    "S4", "S5", "S6", "S7", "S8", "H3", "H4", "P2", "P5", "L2", "L4", "L7",
    "W2", "W3", "W5", "W7", "W8", "W9", "A1", "A2", "A3", "A5", "A6",
    "N4", "T3", "T5", "C4", "X3", "X6", "X7", "X8",
]

BACKREF = [
    "如上所述", "如前所述", "见下文", "见上文", "前面提到", "上文提到", "综上所述",
    "as mentioned above", "as described above", "see above", "see below",
]
FILLER = [
    "基本上", "事实上", "众所周知", "不难看出",
    "其实", "总的来说", "在某种程度上",
    "basically", "actually", "needless to say",
]

# ── M 组：模型腔（去 AI 味）
#
# 规则集受 human-writing skill（MIT）的中文写作约定启发，但**只保留在技术文档里
# 确实增加阅读成本的部分**，并且做了两处放宽：
#   1. 破折号不硬禁 —— 它是标准中文标点，AI 味在于密度，所以改成密度规则
#   2. 冒号只禁「抬价式」引导语，不禁 `参数：` 这类标签冒号（技术文档需要）
#
# 每条都写明它为什么是阅读成本，不是单纯的文风洁癖。

# M1 翻案腔：先立一个读者本来没有的误解，再推翻它给下文抬价。
# 读者要先装载错误前提、再卸掉，白付一次工作记忆
M_PIVOT = [
    re.compile(r"(?:并)?不是[^。！？\n]{1,40}[，、]?而是"),
    re.compile(r"并非[^。！？\n]{1,40}而是"),
    re.compile(r"不在于[^。！？\n]{1,40}而在于"),
    re.compile(r"与其说[^。！？\n]{1,40}(?:不如|倒不如)"),
    re.compile(r"(?:看似|表面上?)[^。！？\n]{1,40}(?:其实|实际上?|实则)"),
    re.compile(r"(?:总|一直|都)?以为[^。！？\n]{2,40}(?:其实|才发现|才明白|才知道)"),
    re.compile(r"[^，。！？\n]{1,12}不重要[，,](?:重要|要紧)的是"),
    re.compile(r"(?:答案)?恰恰相反"),
    re.compile(r"回头(?:看|一看)?才(?:发现|明白|知道)"),
    re.compile(r"\bit(?:'s| is) not (?:just )?[^.!?\n]{1,40}[,;] it(?:'s| is)\b", re.I),
    re.compile(r"\bthe real (?:question|problem|issue) is\b", re.I),
]

# M2 同构排比三连。只提示不扣分：正则分不清「修辞排比」和「技术枚举」，
# `--toc`、`--join-cjk`、`--strip-emoji` 三个 flag 并列是好写法（见 L2），
# 「为什么出发，为什么放弃，为什么害怕」才是要改的。这个区分只有模型能做。
M_ANAPHORA = re.compile(
    r"([^，。！？、\n]{2,6})[^，。！？、\n]{0,10}[，、]\1[^，。！？、\n]{0,10}[，、]\1"
)

# M3 抽象名词配具体动词抒情：句子没有主语能负责，读者无法核对
M_LYRIC = re.compile(
    r"(时间|岁月|时光|记忆|焦虑|孤独|命运|时代|情绪|喧嚣)[^。，！？\n]{0,4}"
    r"(保管|磨平|抹平|显出|沉淀|吞没|抚平|雕刻|标注|收纳|发酵|落下)"
)

# M4 动词名词化：把动作藏进名词，读者要多解一层才知道谁做了什么
M_NOMINAL = [
    re.compile(r"进行(?:了|一次|一场|着)?[^。，！？\n]{0,10}"
               r"(?:调整|优化|升级|分析|讨论|梳理|复盘|迭代|尝试|思考|规划|排查)"),
    re.compile(r"实现了?[^。，！？\n]{0,14}的?[^。，！？\n]{0,6}(?:提升|增长|突破|转变|落地)"),
    re.compile(r"完成了?对[^。，！？\n]{0,16}的"),
    re.compile(r"起到了?[^。，！？\n]{0,12}的?作用"),
    re.compile(r"具有[^。，！？\n]{0,10}(?:意义|价值)"),
]

# M6 抬价式冒号：`核心是：` 这类引导语先宣布重要性再给货，等于把一句话说两遍。
# 字段标签冒号（`参数：` `结论：` `例外：`）不算 —— 技术文档需要它定位
M_HINT_COLON = re.compile(
    r"(一句话(?:总结|说)?|核心(?:是|在于)|关键(?:是|在于)|"
    r"简单说|划重点|敲重点|真相(?:是|只有一个)?)\s*[：:]"
)

# M7 硬停词：宣布「我要说重点了」，本身不携带信息
M_STOP = ["说白了", "说穿了", "先说结论", "不吹不黑", "客观来说"]

# M8 洞察路标：用词announce深度，实际内容没变深
M_ROADSIGN = [
    "更微妙的是", "还有一层", "只说对了一半", "值得注意的是", "需要指出的是",
    "从某种意义上说", "归根结底", "不可否认", "更深层次",
    "it is worth noting", "it should be noted", "in essence", "at its core",
]

# M9 商业与模型黑话：抬价词，替换成普通说法后信息量不变
M_JARGON = [
    "赋能", "抓手", "闭环", "底层逻辑", "顶层设计", "降本增效", "全链路",
    "组合拳", "技术底座", "认知跃迁", "能力沉淀", "拉通", "价值释放",
    "内容矩阵", "结构性机会", "深层逻辑", "打开想象空间", "生态位",
    "leverage", "synergy", "holistic", "seamless", "game-chang", "cutting-edge",
    "delve into", "unlock the",
]

# M5 破折号密度。破折号是标准中文标点，问题在密度：
# 手写技术文档中位数约 5/千字，模型生成常在 15 以上
M_DASH_RE = re.compile(r"——|—(?!—)|–")
M_DASH_PER_KILO = 8

# M10 借喻包装抽象概念。误报率高（`git 仓库` 是本义），只提示不扣分
M_METAPHOR = re.compile(r"(仓库|抽屉|温度|坍塌|浪潮|钥匙|底座|土壤|齿轮|坐标系|容器)")

# 引用一个句式不等于使用它。规则文档里写「不是 A 而是 B」当反面例子，
# 不该被判成犯了这条规则。M 组扫描前把「」『』里的内容挖掉
M_QUOTED_RE = re.compile(r"[「『][^」』\n]{0,40}[」』]")

SHELL_PROMPT_RE = re.compile(r"^\s*[$>]\s+\S")
BAD_LINK_TEXT = {
    "here", "click here", "this", "this link", "link", "read more", "more",
    "点击这里", "这里", "详见", "链接", "点我",
}
STEP_HINT = re.compile(
    r"(步骤|安装|快速开始|上手|部署|配置流程|steps?|install|quick ?start|getting started|setup)",
    re.I,
)
ORDER_HINT = re.compile(r"^\s*(第[一二三四五六七八九十]+步|然后|接着|首先|最后|first|then|next|finally)", re.I)
TLDR_RE = re.compile(r"(tl;?dr|摘要|结论|一句话|速览|at a glance|summary)", re.I)
# 背景铺垫开头。短不等于是结论 —— 这类开头再短也不算首屏结论。
BG_OPENER = re.compile(
    r"^\s*(随着|近年来|近几年|这几年|众所周知|在当今|当今|长期以来|一直以来|首先|"
    r"本文(将|会|介绍|讲)|我们(都)?知道|如今|"
    # 会议/日志类元信息开头：讲的是「什么时候谁在场」，不是结论
    r"今天|昨天|前天|上午|下午|晚上|刚才|本次会议|这次会|会议记录|参会|与会|"
    r"as (the|our|more)|in recent years|over the (past|last)|nowadays|traditionally|"
    r"this (doc|document|article|guide) (will |)(describe|introduce|cover|explain)|"
    r"(today|yesterday|this (morning|afternoon))[, ])",
    re.I,
)

# ---------------------------------------------------------------- 块解析

FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})\s*(\S*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
UL_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
OL_RE = re.compile(r"^(\s*)(\d+)([.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^\s*>")
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
HTML_RE = re.compile(r"^\s*</?[A-Za-z][^>]*>")


@dataclass
class Block:
    kind: str
    start: int  # 1-indexed 起始行
    lines: list
    info: dict = field(default_factory=dict)

    @property
    def end(self):
        return self.start + len(self.lines) - 1

    @property
    def text(self):
        return "\n".join(self.lines)


def parse_blocks(lines):
    """把行序列切成块。kind 取值：frontmatter/code/heading/hr/table/quote/list/html/para"""
    blocks = []
    i = 0
    n = len(lines)

    if n and lines[0].strip() == "---":
        j = 1
        while j < n and lines[j].strip() != "---":
            j += 1
        if j < n:
            blocks.append(Block("frontmatter", 1, lines[: j + 1]))
            i = j + 1

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = FENCE_OPEN.match(line)
        if m:
            fence = m.group(2)
            lang = m.group(3)
            j = i + 1
            while j < n and not re.match(r"^\s*" + fence[0] + "{" + str(len(fence)) + ",}\\s*$", lines[j]):
                j += 1
            end = min(j, n - 1)
            blocks.append(Block("code", i + 1, lines[i : end + 1], {"lang": lang, "closed": j < n}))
            i = end + 1
            continue

        m = HEADING_RE.match(line)
        if m:
            blocks.append(Block("heading", i + 1, [line], {"level": len(m.group(1)), "title": m.group(2).strip()}))
            i += 1
            continue

        if HR_RE.match(line):
            blocks.append(Block("hr", i + 1, [line]))
            i += 1
            continue

        if "|" in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]) and "|" in lines[i + 1]:
            j = i
            while j < n and "|" in lines[j] and lines[j].strip():
                j += 1
            rows = lines[i:j]
            cols = max(len([c for c in r.strip().strip("|").split("|")]) for r in rows)
            blocks.append(Block("table", i + 1, rows, {"cols": cols, "rows": len(rows) - 2}))
            i = j
            continue

        if QUOTE_RE.match(line):
            j = i
            while j < n and (QUOTE_RE.match(lines[j]) or (lines[j].strip() and not _is_block_start(lines[j]))):
                j += 1
            blocks.append(Block("quote", i + 1, lines[i:j]))
            i = j
            continue

        if UL_RE.match(line) or OL_RE.match(line):
            j = i
            items = []
            while j < n:
                cur = lines[j]
                if not cur.strip():
                    if j + 1 < n and (UL_RE.match(lines[j + 1]) or OL_RE.match(lines[j + 1]) or lines[j + 1].startswith(("  ", "\t"))):
                        j += 1
                        continue
                    break
                mm = UL_RE.match(cur) or OL_RE.match(cur)
                if mm:
                    items.append(j)
                elif cur.startswith((" ", "\t")):
                    pass
                elif _is_block_start(cur):
                    break
                j += 1
            blocks.append(Block("list", i + 1, lines[i:j], {"items": [k - i for k in items]}))
            i = j
            continue

        if HTML_RE.match(line):
            blocks.append(Block("html", i + 1, [line]))
            i += 1
            continue

        j = i
        while j < n and lines[j].strip() and not _is_block_start(lines[j], skip_para=True):
            j += 1
        blocks.append(Block("para", i + 1, lines[i:j]))
        i = j

    return blocks


def _is_block_start(line, skip_para=False):
    if HEADING_RE.match(line) or HR_RE.match(line) or FENCE_OPEN.match(line):
        return True
    if UL_RE.match(line) or OL_RE.match(line) or QUOTE_RE.match(line):
        return True
    if not skip_para and HTML_RE.match(line):
        return True
    return False


# ---------------------------------------------------------------- 文本抽取

INLINE_CODE_RE = re.compile(r"`+[^`\n]*?`+")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]*)[^)]*\)")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
EMPH_RE = re.compile(r"[*_~]{1,3}")


def strip_inline(text, keep_code=False):
    """剥掉行内标记，保留可读文字。链接保留文字丢 URL。"""
    t = LINK_RE.sub(lambda m: m.group(1), text)
    if not keep_code:
        t = INLINE_CODE_RE.sub(" ", t)
    t = HTML_TAG_RE.sub("", t)
    t = EMPH_RE.sub("", t)
    return t


def prose_of(block, keep_code=False):
    """块的可读正文。代码块与 frontmatter 返回空。

    keep_code=False（审计用）：行内代码不算正文，否则 `npm install` 会被当成两个词，
    把句长与字数统计抬高。
    keep_code=True（校验用）：保留行内代码内容，这样把裸标识符包成 `code`
    不会被误判成丢词。
    """
    if block.kind in ("code", "frontmatter", "hr"):
        return ""
    if block.kind == "heading":
        return strip_inline(block.info["title"], keep_code)
    if block.kind == "list":
        out = []
        for ln in block.lines:
            m = UL_RE.match(ln) or OL_RE.match(ln)
            out.append(strip_inline(m.group(len(m.groups())) if m else ln.strip(), keep_code))
        return "\n".join(out)
    if block.kind == "quote":
        return strip_inline("\n".join(re.sub(r"^\s*>\s?", "", l) for l in block.lines), keep_code)
    if block.kind == "table":
        cells = []
        for r in block.lines:
            if TABLE_SEP_RE.match(r):
                continue
            cells += [strip_inline(c.strip(), keep_code) for c in r.strip().strip("|").split("|")]
        return " ".join(c for c in cells if c)
    return strip_inline(block.text, keep_code)


def count_units(text):
    """返回 (CJK 字数, 拉丁词数)"""
    return len(CJK_RE.findall(text)), len(LATIN_WORD_RE.findall(text))


def detect_lang(blocks):
    cjk = lat = 0
    for b in blocks:
        c, l = count_units(prose_of(b))
        cjk += c
        lat += l
    total = cjk + lat
    if total == 0:
        return "en"
    return "zh" if cjk / total > 0.30 else "en"


def units(text, lang):
    cjk, lat = count_units(text)
    return cjk if lang == "zh" else lat


ZH_SENT_END = "。！？；…"


def split_sentences(text, lang):
    text = text.strip()
    if not text:
        return []
    if lang == "zh":
        parts = re.split(f"(?<=[{ZH_SENT_END}])|\n+", text)
    else:
        parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z\"'(\[])|\n{2,}|\n(?=[-*#])", text)
    return [p.strip() for p in parts if p and p.strip()]


# ---------------------------------------------------------------- 审计

@dataclass
class Finding:
    rule: str
    line: int
    msg: str
    axis: str          # F / C
    advisory: bool = False


AXIS = {
    "S1": "F", "S2": "F", "S3": "F", "P1": "F", "P4": "F", "L1": "F", "L3": "F",
    "L5": "F", "N1": "F", "N5": "F", "T1": "F", "T2d": "F", "T2p": "F", "T4": "F",
    "T7": "F", "T8": "F", "C1": "F", "C2": "F", "C8": "F", "A4": "F", "X1p": "F", "X1c": "F",
    "X2": "F", "X5": "F",
    "H1": "C", "H2": "C", "W1m": "C", "W1x": "C", "W4": "C", "W6": "C",
    "C3": "C", "C5": "C", "N2": "C", "N6": "C", "C7": "C", "W2": "C",
    "M1": "C", "M2": "C", "M3": "C", "M4": "C", "M6": "C", "M7": "C",
    "M8": "C", "M9": "C", "M10": "C",
    "M5": "F",
}


class Doc:
    def __init__(self, text, path="<stdin>"):
        self.path = path
        self.raw = text
        self.lines = text.split("\n")
        if self.lines and self.lines[-1] == "":
            self.lines = self.lines[:-1]
        self.blocks = parse_blocks(self.lines)
        self.lang = detect_lang(self.blocks)
        self.th = TH[self.lang]

    def body_blocks(self):
        return [b for b in self.blocks if b.kind != "frontmatter"]


def audit(doc, level=2, emoji="none"):
    f = []
    lang, th = doc.lang, doc.th
    blocks = doc.body_blocks()
    headings = [b for b in blocks if b.kind == "heading"]
    prose_all = "\n".join(prose_of(b) for b in blocks if b.kind != "heading")

    # --- S 骨架
    prev = 0
    for b in headings:
        lv = b.info["level"]
        if prev and lv > prev + 1:
            f.append(Finding("S1", b.start, f"标题从 H{prev} 跳到 H{lv}", "F"))
        prev = lv
    h1 = [b for b in headings if b.info["level"] == 1]
    if len(h1) != 1:
        f.append(Finding("S2", h1[1].start if len(h1) > 1 else 1, f"H1 数量为 {len(h1)}，应为 1", "F"))

    # 章节长度：两个标题之间的正文量
    acc, acc_line = 0, 1
    for b in blocks:
        if b.kind == "heading":
            if acc > th["section"]:
                f.append(Finding("S3", acc_line, f"章节正文 {acc} 超过上限 {th['section']}", "F"))
            acc, acc_line = 0, b.start
        else:
            acc += units(prose_of(b), lang)
    if acc > th["section"]:
        f.append(Finding("S3", acc_line, f"章节正文 {acc} 超过上限 {th['section']}", "F"))

    # --- H 首屏
    # 首屏 = 第一个 H2 之前的内容（标题本身若是 TL;DR 类则继续往下算）
    lead = []
    for b in blocks:
        if b.kind == "heading" and b.info["level"] >= 2:
            if not TLDR_RE.search(b.info["title"]):
                break
        if b.start > 25:
            break
        lead.append(b)

    lead_text = "\n".join(b.text for b in lead)
    has_tldr = bool(TLDR_RE.search(lead_text))
    tldr_block = None
    if not has_tldr:
        for b in lead:
            if b.kind in ("heading", "hr", "code"):
                continue
            if b.kind == "list":
                if _is_toc(b):
                    continue  # 目录不是 TL;DR，跳过继续找
                if len(b.info.get("items", [])) <= 5:
                    has_tldr, tldr_block = True, b
                break
            if b.kind in ("para", "quote"):
                p = prose_of(b)
                if BG_OPENER.match(p):
                    continue  # 背景铺垫不算结论，继续看下一块
                if len(split_sentences(p, lang)) <= 3 and units(p, lang) <= (80 if lang == "zh" else 40):
                    has_tldr, tldr_block = True, b
                # 第一段不是结论就判失败，不再往后找
                break

    if not has_tldr:
        f.append(Finding("H1", 1, "前 15 行没有结论 / TL;DR，读者不知道要不要读下去", "C"))
    else:
        for b in lead:
            if b.kind == "list" and not _is_toc(b) and len(b.info.get("items", [])) > 5:
                f.append(Finding("H2", b.start, f"首屏要点 {len(b.info['items'])} 条，超过 5 条", "C"))
                break
            if b.kind == "para" and units(prose_of(b), lang) > th["tldr"] and TLDR_RE.search(lead_text):
                f.append(Finding("H2", b.start, f"TL;DR {units(prose_of(b), lang)} 超过 {th['tldr']}", "C"))
                break

    # --- P 分块
    for b in blocks:
        if b.kind not in ("para", "quote"):
            continue
        p = prose_of(b)
        sents = split_sentences(p, lang)
        u = units(p, lang)
        if len(sents) > 3 or u > th["para"]:
            f.append(Finding("P1", b.start, f"段落 {len(sents)} 句 / {u} 单位，上限 3 句 / {th['para']}", "F"))
        if len(b.lines) > 6:
            f.append(Finding("P4", b.start, f"连续 {len(b.lines)} 行无空行无标记", "F"))

    # --- L 列表
    for b in blocks:
        if b.kind != "list" or _is_toc(b):
            continue
        depths = set()
        for idx in b.info.get("items", []):
            ln = b.lines[idx]
            m = UL_RE.match(ln) or OL_RE.match(ln)
            indent = len(m.group(1).replace("\t", "    "))
            depths.add(indent // 2)
        if depths and max(depths) >= 2:
            f.append(Finding("L1", b.start, f"列表嵌套 {max(depths) + 1} 层，上限 2 层", "F"))
        items = b.info.get("items", [])
        for k, idx in enumerate(items):
            nxt = items[k + 1] if k + 1 < len(items) else len(b.lines)
            span = [l for l in b.lines[idx:nxt] if l.strip()]
            if len(span) > 2:
                f.append(Finding("L5", b.start + idx, f"列表项占 {len(span)} 行，超过 2 行", "F"))
        if len(items) > 7:
            f.append(Finding("L6", b.start, f"列表 {len(items)} 项，建议分组", "F", advisory=True))
        # L3：像步骤却用了无序列表
        if items and UL_RE.match(b.lines[items[0]]) and len(items) >= 3:
            ctx = _nearest_heading(blocks, b)
            body = "\n".join(b.lines)
            if (ctx and STEP_HINT.search(ctx)) or ORDER_HINT.search(body):
                f.append(Finding("L3", b.start, "看起来是操作步骤，应改成有序列表或复选框", "F"))

    # --- W / C 句子
    # 只统计正文句子。列表项、表格单元格、标题不是「句子」，混进来会把均值稀释掉。
    # 逐块遍历而不是先拼成一坨：行号必须落在真实位置，落到 L1 等于没给定位。
    lens = []
    for b in blocks:
        if b.kind not in ("para", "quote"):
            continue
        # 段落内的换行是软换行，不是句子边界。按 75 字硬折行的中文段落
        # 若把换行当边界，一句话会被算成三句，P1 全是误报。
        flat = re.sub(r"\n+", "" if lang == "zh" else " ", prose_of(b))
        for s in split_sentences(flat, lang):
            u = units(s, lang)
            if u <= 0:
                continue
            lens.append(u)
            if u > th["sent_p90"]:
                f.append(Finding("W1x", b.start, f"单句 {u} 超过上限 {th['sent_p90']}", "C"))
            if lang == "zh":
                commas = s.count("，") + s.count(",")
                if u > 45 and commas >= 4:
                    f.append(Finding("C3", b.start, f"一逗到底：{u} 字 {commas} 个逗号", "C"))
                if level >= 3 and s.count("的") >= 3:
                    f.append(Finding("C5", b.start, "单句「的」≥3，修饰层层套嵌", "C"))
    if lens:
        mean = sum(lens) / len(lens)
        if mean > th["sent_mean"]:
            over = (mean - th["sent_mean"]) / th["sent_mean"]
            for _ in range(int(over / 0.10) + (1 if over % 0.10 else 0)):
                f.append(Finding("W1m", 1, f"均句长 {mean:.1f} 超过上限 {th['sent_mean']}", "C"))

    # 回扫指令与填充词：逐行扫，一处一条，行号准确
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        for off, ln in enumerate(b.lines):
            low = strip_inline(ln).lower()
            for w in BACKREF:
                for _ in re.finditer(re.escape(w.lower()), low):
                    f.append(Finding("W4", b.start + off, f"回扫指令「{w}」，就地重述代替", "C"))
            for w in FILLER:
                for _ in re.finditer(re.escape(w.lower()), low):
                    f.append(Finding("W6", b.start + off, f"填充词「{w}」可删", "C"))

    if lang == "zh":
        for b in blocks:
            if b.kind in ("code", "frontmatter"):
                continue
            for off, ln in enumerate(b.lines):
                body = _protect(ln)[0]
                if re.search(f"[{CJK}][A-Za-z0-9]|[A-Za-z0-9][{CJK}]", body):
                    f.append(Finding("C1", b.start + off, "中英文之间缺空格", "F"))
                if re.search(f"[{CJK}][,;:!?]|[{CJK}]\\.(?![A-Za-z0-9])", body):
                    f.append(Finding("C2", b.start + off, "中文段落里出现半角标点", "F"))

        # C8 句中软换行。中文没有空格分词，多数渲染器会把软换行渲染成一个空格，
        # 于是句子中间凭空多出一个空格。一个段落报一次就够，不逐行刷。
        for b in blocks:
            if b.kind != "para" or len(b.lines) < 2:
                continue
            for off, ln in enumerate(b.lines[:-1]):
                s = ln.rstrip()
                # 行尾是字或字母数字 → 断在词句中间。断在标点后（逗号顿号等）从宽处理
                if s and (CJK_RE.match(s[-1]) or s[-1].isalnum()):
                    f.append(Finding("C8", b.start + off, "句中软换行，中文渲染会多出一个空格", "F"))
                    break

    # --- M 组 模型腔（去 AI 味）
    dash_hits = []
    metaphor_seen = False
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        for off, ln in enumerate(b.lines):
            # 行内代码与「」引用都算「在谈论这个句式」，不算在用它
            vis = M_QUOTED_RE.sub("  ", _protect(ln)[0])
            low = vis.lower()
            line = b.start + off
            for pat in M_PIVOT:
                for _ in pat.finditer(vis):
                    f.append(Finding("M1", line, "翻案腔：先立误解再推翻。直接从正面下判断", "C"))
            if M_ANAPHORA.search(vis) and not re.search(r"[`（(/]", vis):
                f.append(Finding("M2", line, "疑似同构排比三连，修辞性的留两项；技术枚举忽略",
                                 "C", advisory=True))
            for m in M_LYRIC.finditer(vis):
                f.append(Finding("M3", line, f"抽象名词配具体动词抒情：{m.group(0)}", "C"))
            for pat in M_NOMINAL:
                for m in pat.finditer(vis):
                    f.append(Finding("M4", line, f"动词名词化：{m.group(0)}", "C"))
            for m in M_HINT_COLON.finditer(vis):
                f.append(Finding("M6", line, f"抬价式冒号：{m.group(0).strip()}", "C"))
            for w in M_STOP:
                if w in vis:
                    f.append(Finding("M7", line, f"硬停词「{w}」，本身不携带信息", "C"))
            for w in M_ROADSIGN:
                if w.lower() in low:
                    f.append(Finding("M8", line, f"洞察路标「{w}」，内容没变深", "C"))
            for w in M_JARGON:
                if w.lower() in low:
                    f.append(Finding("M9", line, f"黑话「{w}」，换普通说法信息量不变", "C"))
            # M5 只数行文里的破折号。列表项里的 `事项 —— 负责人 —— 期限` 是字段分隔，
            # 表格里的 — 常表示「无 / 不适用」，都不是行文节奏问题
            if b.kind in ("para", "quote"):
                dash_hits += [line] * len(M_DASH_RE.findall(vis))
            if not metaphor_seen and M_METAPHOR.search(vis):
                metaphor_seen = True
                f.append(Finding("M10", line, "借喻可能在包装抽象概念，写本义则忽略", "C", advisory=True))

    # M5 破折号密度。按汉字数给预算，超出的逐处报。只统计正文段落，理由见上
    han_all = len(CJK_RE.findall(prose_all))
    dash_budget = max(3, han_all * M_DASH_PER_KILO // 1000)
    for line in dash_hits[dash_budget:]:
        f.append(Finding("M5", line,
                         f"破折号超出预算：全文 {len(dash_hits)} 个，预算 {dash_budget}"
                         f"（{M_DASH_PER_KILO}/千字）", "F"))

    # --- A 行动性
    for b in blocks:
        if b.kind == "code":
            for off, ln in enumerate(b.lines[1:-1] if b.info.get("closed") else b.lines[1:], start=1):
                if SHELL_PROMPT_RE.match(ln):
                    f.append(Finding("A4", b.start + off, "命令带 $ / > 提示符，复制会出错", "F"))

    # --- N 导航
    if len(doc.lines) > 80 and not _has_toc(blocks):
        f.append(Finding("N1", 1, f"{len(doc.lines)} 行文档没有目录", "F"))
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        for off, ln in enumerate(b.lines):
            # 用 _protect 剥掉行内代码：文档里写 `![]()` 作为例子不该被当成真链接
            vis = _protect(ln)[0]
            for m in LINK_RE.finditer(vis):
                txt = m.group(1).strip().lower()
                if m.group(0).startswith("!"):
                    if not txt:
                        f.append(Finding("N6", b.start + off, "图片缺 alt 文本", "C"))
                    continue
                if txt in BAD_LINK_TEXT or len(txt) < 2:
                    f.append(Finding("N2", b.start + off, f"链接文本无意义：「{m.group(1)}」", "C"))
            for m in re.finditer(r"(?<![(<\w])https?://\S+", vis):
                f.append(Finding("N2", b.start + off, "裸 URL，应给有意义的链接文本", "C"))
        if b.kind == "table":
            if b.info["cols"] > 5 or b.info["rows"] > 10:
                f.append(Finding("N5", b.start, f"表格 {b.info['cols']} 列 {b.info['rows']} 行，超过 5×10", "F"))

    # --- T 排版
    for b in blocks:
        if b.kind == "code" and not b.info.get("lang"):
            f.append(Finding("T1", b.start, "代码块缺语言标签", "F"))
        if b.kind == "html" and not re.match(r"\s*</?(details|summary|br)\b", b.lines[0]):
            f.append(Finding("T8", b.start, "裸 HTML 标签", "F"))

    bold_chars = sum(len(m.group(1)) for m in re.finditer(r"\*\*([^*]+)\*\*", prose_all_raw(blocks)))
    total_chars = max(1, len(re.sub(r"\s", "", prose_all)))
    ratio = bold_chars / total_chars
    if ratio > 0.08:
        f.append(Finding("T2d", 1, f"加粗密度 {ratio:.0%}，上限 8%", "F"))
    for b in blocks:
        if b.kind in ("para", "quote"):
            c = len(re.findall(r"\*\*[^*]+\*\*", b.text))
            if c > 2:
                f.append(Finding("T2p", b.start, f"单段加粗 {c} 处，上限 2 处", "F"))

    for off, ln in enumerate(doc.lines, start=1):
        if re.search(r"[ \t]+$", ln) and not re.search(r"(?<!\s) {2}$", ln):
            f.append(Finding("T4", off, "行尾多余空白", "F"))
            break
    if not doc.raw.endswith("\n") or doc.raw.endswith("\n\n"):
        f.append(Finding("T4", len(doc.lines), "文件末尾换行不规范", "F"))

    for b in blocks:
        if b.kind != "list":
            continue
        nums = []
        for idx in b.info.get("items", []):
            m = OL_RE.match(b.lines[idx])
            if m and len(m.group(1)) == 0:
                nums.append(int(m.group(2)))
        if len(nums) > 1 and nums != list(range(nums[0], nums[0] + len(nums))):
            f.append(Finding("T7", b.start, f"有序列表序号非递增：{nums}", "F"))

    # --- X 反模式
    prose_no_head = "\n".join(prose_of(b) for b in blocks if b.kind not in ("heading", "code"))
    if EMOJI_RE.search(prose_no_head):
        f.append(Finding("X1p", 1, "正文出现 emoji", "F"))
    # 代码块里的 emoji 是示例（比如反模式文档在演示「emoji 汤」长什么样），不算违规
    n_emoji = len(EMOJI_RE.findall("\n".join(b.text for b in blocks if b.kind != "code")))
    if emoji == "none" and n_emoji:
        f.append(Finding("X1c", 1, f"共 {n_emoji} 个 emoji，默认策略为零 emoji", "F"))
    elif n_emoji > max(1, len(headings)):
        f.append(Finding("X1c", 1, f"emoji {n_emoji} 个超过章节数 {len(headings)}", "F"))
    if headings and len(doc.lines) / len(headings) < 5:
        f.append(Finding("X2", 1, f"平均每 {len(doc.lines) / len(headings):.1f} 行一个标题，碎片化", "F"))
    # 碎片化只看纯正文章节。含代码块或复选框的短章节是合法的步骤结构，
    # 不是「把叙述剁碎」—— 运维手册每步一节恰恰是对的。
    prose_secs = []
    cur, structured = 0, False
    started = False
    for b in blocks:
        if b.kind == "heading":
            if started and not structured:
                prose_secs.append(cur)
            cur, structured, started = 0, False, True
            continue
        if b.kind == "code" or (b.kind == "list" and re.search(r"^\s*[-*+]\s+\[[ xX]\]", b.text, re.M)):
            structured = True
        cur += units(prose_of(b), lang)
    if started and not structured:
        prose_secs.append(cur)
    if len(prose_secs) >= 3 and sum(prose_secs) / len(prose_secs) < th["frag"]:
        f.append(Finding("X2", 1, f"纯正文章节平均 {sum(prose_secs) / len(prose_secs):.0f} 单位，"
                                  f"低于 {th['frag']}，碎片化", "F"))
    if ratio > 0.12:
        f.append(Finding("X5", 1, f"加粗密度 {ratio:.0%} 超过 12%", "F"))

    return [x for x in f if MIN_LEVEL.get(x.rule, 1) <= level]


def prose_all_raw(blocks):
    return "\n".join(b.text for b in blocks if b.kind not in ("code", "frontmatter"))


def _nearest_heading(blocks, target):
    last = None
    for b in blocks:
        if b is target:
            return last
        if b.kind == "heading":
            last = b.info["title"]
    return last


def _is_toc(b):
    """目录块：列表里至少两项指向 #锚点。目录是导航，不是要点列表，也不是 TL;DR。"""
    return b.kind == "list" and sum(1 for l in b.lines if re.search(r"\]\(#", l)) >= 2


def _has_toc(blocks):
    return any(_is_toc(b) for b in blocks[:12])


def _line_of(doc, needle):
    for i, ln in enumerate(doc.lines, start=1):
        if needle and needle in ln:
            return i
    return 1


# ---------------------------------------------------------------- 评分

def score(findings, det_only=True):
    hits = {}
    for f in findings:
        if f.advisory or f.rule not in DEDUCT:
            continue
        hits.setdefault(f.rule, 0)
        hits[f.rule] += 1

    dim_ded = {k: 0.0 for k in DIMS}
    for rule, n in hits.items():
        dim, per, cap = DEDUCT[rule]
        dim_ded[dim] += min(per * n, cap)

    dims = {}
    for k, (label, w) in DIMS.items():
        dims[k] = dict(label=label, weight=w, score=max(0.0, 100.0 - dim_ded[k]))

    x_total = 0
    x_hits = {}
    for f in findings:
        if f.rule in X_DEDUCT and f.rule not in x_hits:
            x_hits[f.rule] = X_DEDUCT[f.rule]
    x_total = min(X_CAP, sum(x_hits.values()))

    weighted = sum(d["score"] * d["weight"] for d in dims.values()) / 100.0
    total = max(0.0, min(100.0, weighted - x_total))

    return dict(
        total=round(total, 1),
        band=band(total),
        dims={k: dict(v, score=round(v["score"], 1)) for k, v in dims.items()},
        x_deduct=x_total,
        x_hits=x_hits,
        unscored=JUDGE_ONLY if det_only else [],
        det_only=det_only,
    )


def band(total):
    for lo, name in ((90, "优"), (80, "好"), (60, "可用但吃力"), (40, "需重构")):
        if total >= lo:
            return name
    return "差"


# ---------------------------------------------------------------- 格式修复

def _protect(line):
    """抽出不可改动的片段（行内代码 / URL / HTML / 链接目标），返回 (占位后的文本, 片段表)"""
    keep = []

    def sub(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"

    pat = re.compile(r"`+[^`\n]*?`+|\]\([^)]*\)|</?[A-Za-z][^>]*>|(?<![(\w])https?://\S+")
    return pat.sub(sub, line), keep


def _restore(line, keep):
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], line)


def fix_cjk_spacing(line):
    body, keep = _protect(line)
    body = re.sub(f"([{CJK}])([A-Za-z0-9])", r"\1 \2", body)
    body = re.sub(f"([A-Za-z0-9])([{CJK}])", r"\1 \2", body)
    body = re.sub(r" {2,}", " ", body)
    return _restore(body, keep)


HALF2FULL = {",": "，", ";": "；", ":": "：", "!": "！", "?": "？"}


def fix_cjk_punct(line):
    body, keep = _protect(line)

    def rep(m):
        return m.group(1) + HALF2FULL[m.group(2)]

    body = re.sub(f"([{CJK}])([,;:!?])(?=\\s|$|[{CJK}])", rep, body)
    body = re.sub(f"([{CJK}])\\.(?=\\s|$)", r"\1。", body)
    return _restore(body, keep)


def renumber_lists(lines, blocks):
    out = list(lines)
    for b in blocks:
        if b.kind != "list":
            continue
        counters = {}
        for idx in b.info.get("items", []):
            ln = b.lines[idx]
            m = OL_RE.match(ln)
            if not m:
                continue
            indent = len(m.group(1).replace("\t", "    "))
            counters[indent] = counters.get(indent, 0) + 1
            for k in list(counters):
                if k > indent:
                    del counters[k]
            new = f"{m.group(1)}{counters[indent]}{m.group(3)} {m.group(4)}"
            out[b.start - 1 + idx] = new
    return out


def fix_blank_lines(lines, blocks):
    """块之间保证恰好一个空行，压缩连续空行。代码块内部不动。"""
    protected = set()
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            for k in range(b.start, b.end + 1):
                protected.add(k)

    out = []
    prev_blank = False
    for i, ln in enumerate(lines, start=1):
        if i in protected:
            out.append(ln)
            prev_blank = False
            continue
        if not ln.strip():
            if not prev_blank:
                out.append("")
            prev_blank = True
            continue
        need_blank = False
        if out and out[-1].strip():
            if HEADING_RE.match(ln) or HR_RE.match(ln) or (FENCE_OPEN.match(ln) and ("```" in ln or "~~~" in ln)):
                need_blank = True
            elif (UL_RE.match(ln) or OL_RE.match(ln)) and not (UL_RE.match(out[-1]) or OL_RE.match(out[-1]) or out[-1].startswith((" ", "\t"))):
                need_blank = True
            elif HEADING_RE.match(out[-1]):
                need_blank = True
        if need_blank:
            out.append("")
        out.append(ln)
        prev_blank = False
    while out and not out[-1].strip():
        out.pop()
    return out


def fix_trailing(lines, blocks):
    protected = set()
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            for k in range(b.start, b.end + 1):
                protected.add(k)
    out = []
    for i, ln in enumerate(lines, start=1):
        if i in protected:
            out.append(ln)
            continue
        stripped = ln.rstrip()
        hard_break = re.search(r"\S {2,}$", ln) and i < len(lines) and lines[i : i + 1] and lines[i].strip()
        out.append(stripped + "  " if hard_break else stripped)
    return out


def build_toc(blocks):
    items = []
    for b in blocks:
        if b.kind == "heading" and b.info["level"] == 2:
            title = strip_inline(b.info["title"])
            anchor = re.sub(r"[^\w一-鿿 -]", "", title.lower()).strip().replace(" ", "-")
            items.append(f"- [{title}](#{anchor})")
    return items


def fmt(text, toc=False, join_cjk=False, strip_emoji=False):
    doc = Doc(text)
    lines = doc.lines
    lines = fix_trailing(lines, doc.blocks)

    doc2 = Doc("\n".join(lines) + "\n")
    lines = renumber_lists(lines, doc2.blocks)

    doc3 = Doc("\n".join(lines) + "\n")
    protected = set()
    for b in doc3.blocks:
        if b.kind in ("code", "frontmatter"):
            for k in range(b.start, b.end + 1):
                protected.add(k)

    if doc.lang == "zh":
        lines = [
            ln if i in protected else fix_cjk_punct(fix_cjk_spacing(ln))
            for i, ln in enumerate(lines, start=1)
        ]
    if strip_emoji:
        lines = [ln if i in protected else EMOJI_RE.sub("", ln).rstrip() for i, ln in enumerate(lines, start=1)]

    doc4 = Doc("\n".join(lines) + "\n")
    if join_cjk and doc.lang == "zh":
        merged, i = [], 0
        for b in doc4.blocks:
            if b.kind == "para" and len(b.lines) > 1:
                joined = ""
                for ln in b.lines:
                    s = ln.strip()
                    if joined and not CJK_RE.search(joined[-1:]):
                        joined += " " + s
                    else:
                        joined += s
                merged.append((b.start, b.end, [joined]))
        for start, end, repl in reversed(merged):
            lines[start - 1 : end] = repl

    doc5 = Doc("\n".join(lines) + "\n")
    lines = fix_blank_lines(lines, doc5.blocks)

    if toc:
        doc6 = Doc("\n".join(lines) + "\n")
        if not _has_toc(doc6.blocks):
            items = build_toc(doc6.blocks)
            if len(items) >= 3:
                insert_at = None
                for b in doc6.blocks:
                    if b.kind == "heading" and b.info["level"] == 2:
                        insert_at = b.start - 1
                        break
                if insert_at:
                    lines[insert_at:insert_at] = items + [""]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 校验

PUNCT_FOLD = str.maketrans({
    "，": ",", "。": ".", "；": ";", "：": ":", "！": "!", "？": "?",
    "（": "(", "）": ")", "「": '"', "」": '"', "、": ",", "…": "...",
    "“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "－": "-",
})


def code_blocks_of(text):
    doc = Doc(text)
    out = []
    for b in doc.blocks:
        if b.kind == "code":
            inner = b.lines[1:-1] if b.info.get("closed") and len(b.lines) > 1 else b.lines[1:]
            out.append("\n".join(l.rstrip() for l in inner).strip())
    return out


def strip_toc_block(blocks):
    keep = []
    for b in blocks[:12]:
        if b.kind == "list" and sum(1 for l in b.lines if re.search(r"\]\(#", l)) >= 2:
            keep.append(id(b))
    return keep


def _tokenize(t):
    """CJK 逐字成 token，拉丁/数字按词成 token。

    必须逐字符扫描，不能先 split 再判断：`另外Node18以下` 是一个 chunk，
    加空格后变成三个 chunk，若按 chunk 判断会得出不同的 token 序列，
    让 C1 空格修复被误判成内容丢失。
    """
    tokens, buf = [], []

    def flush():
        if buf:
            w = "".join(buf).strip("._-/").lower()
            if w:
                tokens.append(w)
            buf.clear()

    for ch in t:
        if CJK_RE.match(ch):
            flush()
            tokens.append(ch)
        elif ch.isalnum() or ch in "._-/":
            buf.append(ch)
        else:
            flush()
    flush()
    return tokens


def normalize_prose(text):
    """归一化成 token 序列，用于 format 档的无损硬比对。"""
    doc = Doc(text)
    skip = set(strip_toc_block(doc.blocks))
    parts = []
    for b in doc.blocks:
        if b.kind in ("code", "frontmatter", "hr") or id(b) in skip:
            continue
        parts.append(prose_of(b, keep_code=True))
    return _tokenize("\n".join(parts).translate(PUNCT_FOLD))


IDENT_RE = re.compile(r"\b(?:[A-Za-z_][A-Za-z0-9_]*(?:[._-][A-Za-z0-9_]+)+|[a-z]+[A-Z][A-Za-z0-9]*|[A-Z]{2,}[A-Z0-9_]*)\b")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|ms|s|m|h|GB|MB|KB|px|个|次|秒|分钟|小时|天|倍|条|行|列)?", re.I)
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
INLINE_SPAN_RE = re.compile(r"`([^`\n]+)`")


def extract_invariants(text):
    return dict(
        code=code_blocks_of(text),
        inline=sorted(set(m.group(1).strip() for m in INLINE_SPAN_RE.finditer(text))),
        urls=sorted(set(URL_RE.findall(text))),
        nums=sorted(set(m.group(0).replace(" ", "") for m in NUM_RE.finditer(strip_code(text)))),
        idents=sorted(set(IDENT_RE.findall(strip_code(text)))),
    )


def strip_code(text):
    doc = Doc(text)
    out = []
    for b in doc.blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        out.append(b.text)
    return "\n".join(out)


def verify(old, new, scope="both"):
    """返回 (ok, 报告 dict)"""
    rep = {"scope": scope, "hard_failures": [], "warnings": [], "ok": True}

    old_code, new_code = code_blocks_of(old), code_blocks_of(new)
    missing_code = [c for c in old_code if c and c not in new_code]
    if missing_code:
        rep["hard_failures"].append({
            "kind": "code_block_missing",
            "count": len(missing_code),
            "sample": missing_code[0][:120],
        })

    if scope == "format":
        # 比多重集，不比序列。块重排（S5 结论前置）是合法的 format 操作，
        # 会改变 token 顺序但不改变 token 集合。删词 → missing，新写 → extra。
        a, b = normalize_prose(old), normalize_prose(new)
        ca, cb = Counter(a), Counter(b)
        missing, extra = ca - cb, cb - ca
        if missing:
            rep["hard_failures"].append({
                "kind": "prose_tokens_missing",
                "count": sum(missing.values()),
                "items": [w for w, _ in missing.most_common(20)],
                "hint": "这些词从正文里消失了。format 档不许删词。",
            })
        if extra:
            rep["hard_failures"].append({
                "kind": "prose_tokens_added",
                "count": sum(extra.values()),
                "items": [w for w, _ in extra.most_common(20)],
                "hint": "这些词是新写的。format 档不许新增措辞，改用 scope=content。",
            })
        if not missing and not extra and a != b:
            rep["warnings"].append({
                "kind": "blocks_reordered",
                "hint": "检测到块重排。检查被搬动的块里有没有「这个方案」「上述」「它」这类悬空指代。",
            })
    else:
        oi, ni = extract_invariants(old), extract_invariants(new)
        new_text = new
        for key in ("urls", "idents", "nums", "inline"):
            missing = [x for x in oi[key] if x not in new_text]
            if missing:
                bucket = "hard_failures" if key in ("urls", "idents", "inline") else "warnings"
                rep[bucket].append({"kind": f"{key}_missing", "count": len(missing), "items": missing[:12]})

    rep["ok"] = not rep["hard_failures"]
    return rep["ok"], rep


# ---------------------------------------------------------------- 骨架

SKELETONS = {
    "readme": """# 项目名

一句话说清这是什么、给谁用。

## 能干什么

- 能力一，写结果不写实现
- 能力二
- 能力三

## 装 + 跑（约 N 分钟）

1. 装依赖：`...`
2. 跑起来：`...`
3. 验证：`...`

## 常用场景

### 场景一

命令 + 预期输出。

## 配置

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--foo` | `bar` | ... |

## 出错了看这里

**症状** → 原因 → 解法。
""",
    "tutorial": """# 做出 X（约 N 分钟）

读完你能做到什么：一句话。

**前置条件**

- 版本要求
- 需要的账号 / 权限

## 第 1 步 · 动词开头

做什么，然后：

```bash
命令
```

预期看到：`...`

## 做完了

怎么验证成功。下一步去哪。
""",
    "reference": """# 模块名

一句话职责。

## 速查表

| 接口 | 用途 | 常用参数 |
|---|---|---|
| `fn()` | ... | ... |

## `fn(args)`

一句话作用。

**参数**

| 名称 | 类型 | 默认 | 说明 |
|---|---|---|---|

**返回**：...

```js
// 最小示例
```

**常见错误**：...
""",
    "adr": """# 决定：我们选 X（不选 Y）

**状态**：已采纳 · YYYY-MM-DD

## 结论

一句话说清选了什么。

## 为什么

- 理由一
- 理由二

## 放弃了什么

| 备选 | 放弃原因 |
|---|---|

## 代价

接受了哪些坏处。这节不许省。

## 什么情况下要重新考虑

触发条件。
""",
    "runbook": """# 处理 X 故障

## 先做这个

最能止血的一步。

```bash
命令
```

## 确认是这个故障

- 症状一
- 症状二

## 处理步骤

- [ ] 步骤一 —— 验证：...
- [ ] 步骤二 —— 验证：...

## 没好？升级

找谁、怎么找、给什么信息。

## 事后

要清理什么、复盘记什么。
""",
    "notes": """# 会议主题 · YYYY-MM-DD

## 结论与待办

- [ ] 事项 —— 负责人 —— 期限

## 决定了什么

- 决定一

## 还没定

- 悬而未决 —— 谁来推进

<details>
<summary>讨论过程</summary>

原始记录放这里，不删。

</details>
""",
}


# ---------------------------------------------------------------- 输出

def render_audit(path, doc, findings, sc, scope="both"):
    lines = [f"# {path}", ""]
    if sc["det_only"]:
        # 不给档位。det-only 把 31 条模型规则按满分算，报「优」会误导。
        lines.append(f"脚本分 **{sc['total']}** / 100")
        lines.append("")
        lines.append(f"> 这不是最终分。{len(sc['unscored'])} 条需模型判断的规则按满分计入，"
                     "补上之后只会更低，不会更高。")
    else:
        lines.append(f"总分 **{sc['total']}** / 100 —— {sc['band']}")
    lines.append("")
    lines.append(f"语言 `{doc.lang}` · {len(doc.lines)} 行 · {len(doc.blocks)} 块")
    lines.append("")
    lines.append("| 维度 | 权重 | 得分 |")
    lines.append("|---|---|---|")
    for k, v in sc["dims"].items():
        lines.append(f"| {v['label']} | {v['weight']}% | {v['score']} |")
    if sc["x_hits"]:
        lines.append("")
        lines.append(f"反模式扣分 **−{sc['x_deduct']}**：" + "、".join(sc["x_hits"]))
    lines.append("")

    shown = [f for f in findings if scope == "both" or f.axis == ("F" if scope == "format" else "C")]
    if shown:
        lines.append(f"## 待改 {len(shown)} 处")
        lines.append("")
        groups = {}
        for f in shown:
            groups.setdefault(f.rule, []).append(f)
        for rule in sorted(groups, key=lambda r: -len(groups[r])):
            g = groups[rule]
            head = f"- **{rule}** ({AXIS.get(rule, '?')} 轴) × {len(g)} —— {g[0].msg}"
            lines.append(head)
            for f in g[:3]:
                lines.append(f"  - `{path}:{f.line}`")
            if len(g) > 3:
                lines.append(f"  - …另 {len(g) - 3} 处")
    else:
        lines.append("没有脚本可判定的问题。")

    if sc["unscored"]:
        lines.append("")
        lines.append("## 需模型判断（脚本未评分）")
        lines.append("")
        lines.append("、".join(sc["unscored"]))
    return "\n".join(lines) + "\n"


def read(p):
    return sys.stdin.read() if p == "-" else Path(p).read_text(encoding="utf-8")


# ---------------------------------------------------------------- CLI

def cmd_audit(a):
    worst = 0
    payload = []
    for p in a.files:
        text = read(p)
        doc = Doc(text, p)
        findings = audit(doc, level=a.level, emoji=a.emoji)
        sc = score(findings, det_only=True)
        worst = max(worst, 100 - sc["total"])
        if a.json:
            payload.append(dict(
                path=p, lang=doc.lang, lines=len(doc.lines), score=sc,
                findings=[dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis,
                               advisory=f.advisory) for f in findings],
            ))
        else:
            print(render_audit(p, doc, findings, sc, a.scope))
    if a.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], ensure_ascii=False, indent=2))
    if a.min_score is not None and (100 - worst) < a.min_score:
        return 1
    return 0


def cmd_fmt(a):
    changed = 0
    for p in a.files:
        old = read(p)
        new = fmt(old, toc=a.toc, join_cjk=a.join_cjk, strip_emoji=a.strip_emoji)
        if new == old:
            continue
        changed += 1
        if a.check:
            print(f"需要格式修复：{p}")
        elif a.write:
            Path(p).write_text(new, encoding="utf-8")
            print(f"已修复：{p}")
        else:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile=f"{p} (原)", tofile=f"{p} (fmt)"))
    if not changed:
        print("格式已规范，无需修改。")
    return 1 if (a.check and changed) else 0


def cmd_verify(a):
    ok, rep = verify(read(a.old), read(a.new), a.scope)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"scope={a.scope} → {'通过' if ok else '失败'}")
        for h in rep["hard_failures"]:
            print(f"  [硬失败] {h['kind']}: {json.dumps(h, ensure_ascii=False)[:400]}")
        for w in rep["warnings"]:
            print(f"  [警告] {w['kind']}: {json.dumps(w, ensure_ascii=False)[:300]}")
    return 0 if ok else 3


def cmd_report(a):
    rows = []
    for label, p in (("before", a.old), ("after", a.new)):
        doc = Doc(read(p), p)
        f = audit(doc, level=a.level, emoji=a.emoji)
        rows.append((label, doc, f, score(f, det_only=True)))
    (_, _, fb, sb), (_, _, fa, sa) = rows
    ok, vrep = verify(read(a.old), read(a.new), a.scope)

    print(f"脚本分  {sb['total']} → {sa['total']}  ({sa['total'] - sb['total']:+.1f})")
    print()
    print("| 维度 | before | after | delta |")
    print("|---|---|---|---|")
    for k, v in DIMS.items():
        b, x = sb["dims"][k]["score"], sa["dims"][k]["score"]
        print(f"| {v[0]} | {b} | {x} | {x - b:+.1f} |")
    print()
    print(f"反模式扣分  −{sb['x_deduct']} → −{sa['x_deduct']}"
          + ("  ✗ after 必须为 0" if sa["x_deduct"] else ""))
    print(f"findings    {len(fb)} → {len(fa)}")
    print(f"verify({a.scope})  {'通过' if ok else '失败'}")
    if not ok:
        for h in vrep["hard_failures"]:
            print(f"  [硬失败] {h['kind']}")
    if sa["x_deduct"] or not ok:
        return 1
    return 0


def cmd_init(a):
    print(SKELETONS[a.type], end="")
    return 0


def cmd_selftest(a):
    import unittest
    sys.argv = sys.argv[:1]
    suite = unittest.TestLoader().loadTestsFromNames(["__main__.SelfTest"])
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if res.wasSuccessful() else 1


import unittest  # noqa: E402  自检用，放末尾避免影响启动


class SelfTest(unittest.TestCase):
    def test_lang(self):
        self.assertEqual(Doc("# Hello\n\nplain english text here\n").lang, "en")
        self.assertEqual(Doc("# 标题\n\n这是一段中文正文\n").lang, "zh")

    def test_cjk_spacing(self):
        self.assertEqual(fix_cjk_spacing("用npm装好后运行3次"), "用 npm 装好后运行 3 次")
        self.assertEqual(fix_cjk_spacing("装好（约 2 分钟）"), "装好（约 2 分钟）")
        self.assertEqual(fix_cjk_spacing("跑 `npm install` 就行"), "跑 `npm install` 就行")

    def test_cjk_punct(self):
        self.assertEqual(fix_cjk_punct("注意: 这里有坑, 小心"), "注意： 这里有坑， 小心")
        self.assertEqual(fix_cjk_punct("见 README.md 说明"), "见 README.md 说明")

    def test_fmt_idempotent(self):
        src = "#标题\n# 标题\n\n\n\n用npm装,然后跑\n```\ncode  \n```\n1. a\n1. b\n1. c\n"
        once = fmt(src)
        self.assertEqual(fmt(once), once, "fmt 必须幂等")

    def test_fmt_preserves_code(self):
        src = "# T\n\n```python\nx = 1  # 保留中文注释,和空格  \n```\n"
        self.assertIn("x = 1  # 保留中文注释,和空格  ", fmt(src))

    def test_renumber(self):
        src = "# T\n\n1. a\n1. b\n1. c\n"
        out = fmt(src)
        self.assertIn("1. a", out)
        self.assertIn("2. b", out)
        self.assertIn("3. c", out)

    def test_verify_format_ok(self):
        old = "# T\n\n这是第一句，这是第二句。\n"
        new = "# T\n\n这是第一句，这是第二句。\n"
        ok, _ = verify(old, new, "format")
        self.assertTrue(ok)

    def test_verify_format_catches_deletion(self):
        old = "# T\n\n超时默认 30 秒。生产环境别设成 0。\n"
        new = "# T\n\n超时默认 30 秒。\n"
        ok, rep = verify(old, new, "format")
        self.assertFalse(ok)
        self.assertEqual(rep["hard_failures"][0]["kind"], "prose_tokens_missing")

    def test_verify_format_allows_reorder(self):
        # S5 结论前置：整块搬移，token 集合不变
        old = "# T\n\n## 背景\n\n项目从去年开始。\n\n## 结论\n\n性能快了十三倍。\n"
        new = "# T\n\n## 结论\n\n性能快了十三倍。\n\n## 背景\n\n项目从去年开始。\n"
        ok, rep = verify(old, new, "format")
        self.assertTrue(ok, rep)
        self.assertEqual(rep["warnings"][0]["kind"], "blocks_reordered")

    def test_verify_format_allows_backticking(self):
        # 把裸标识符包成行内代码是 format 操作，不是丢词
        old = "# T\n\n用 maxEntries 选项改，默认 500。\n"
        new = "# T\n\n用 `maxEntries` 选项改，默认 500。\n"
        ok, rep = verify(old, new, "format")
        self.assertTrue(ok, rep)

    def test_audit_ignores_inline_code_in_metrics(self):
        # 行内代码不该抬高句长统计
        with_code = Doc("# T\n\n结论。\n\n## 细节\n\n跑 `npm install --save-dev some-package` 就行。\n")
        self.assertNotIn("W1x", {f.rule for f in audit(with_code)})
        old = "# T\n\n超时默认 30 秒。\n"
        new = "# T\n\n## TL;DR\n\n超时默认 30 秒，改不动就看这节。\n"
        ok, rep = verify(old, new, "format")
        self.assertFalse(ok)
        self.assertIn("prose_tokens_added", {h["kind"] for h in rep["hard_failures"]})

    def test_verify_format_allows_restructure(self):
        old = "# T\n\n支持三种模式：只改格式、只改内容、两者都改。\n"
        new = "# T\n\n支持三种模式：\n\n- 只改格式\n- 只改内容\n- 两者都改\n"
        ok, rep = verify(old, new, "format")
        self.assertTrue(ok, rep)

    def test_verify_format_tolerates_cjk_spacing(self):
        # C1 空格修复与 C2 标点规范都不算内容改动
        old = "# T\n\n另外Node18以下不兼容,参数是ttl、maxSize和strategy.\n"
        new = "# T\n\n另外 Node18 以下不兼容，参数是 ttl、maxSize 和 strategy。\n"
        ok, rep = verify(old, new, "format")
        self.assertTrue(ok, rep)

    def test_fmt_output_passes_format_verify(self):
        src = ("# 缓存模块\n\n缓存默认开启,关掉要改配置并重启,另外Node18以下不兼容。\n"
               "参数有3个,分别是ttl、maxSize和strategy。\n\n1. 装依赖\n1. 改配置\n1. 起服务\n")
        out = fmt(src)
        ok, rep = verify(src, out, "format")
        self.assertTrue(ok, rep)

    def test_verify_content_invariants(self):
        old = "# T\n\n用 `--timeout` 改，默认 30 秒。见 https://x.dev/docs\n"
        new = "# T\n\n默认超时 30 秒。\n"
        ok, rep = verify(old, new, "content")
        self.assertFalse(ok)
        kinds = {h["kind"] for h in rep["hard_failures"]}
        self.assertIn("urls_missing", kinds)

    def test_verify_code_block_loss(self):
        old = "# T\n\n```bash\nnpm i\n```\n"
        new = "# T\n\n装依赖即可。\n"
        ok, rep = verify(old, new, "content")
        self.assertFalse(ok)
        self.assertIn("code_block_missing", {h["kind"] for h in rep["hard_failures"]})

    def test_audit_flags_wall_of_text(self):
        para = "这是一个很长的段落。" * 12
        d = Doc(f"# T\n\n{para}\n")
        rules = {f.rule for f in audit(d)}
        self.assertIn("P1", rules)

    def test_audit_flags_missing_tldr(self):
        body = "\n\n".join(["随着业务不断发展，我们遇到了越来越多的问题，需要一个系统性的解决方案来应对。"] * 4)
        d = Doc(f"# 标题\n\n{body}\n")
        self.assertIn("H1", {f.rule for f in audit(d)})

    def test_tldr_not_faked_by_later_short_para(self):
        # 文档中段的短句不能算首屏结论
        src = ("# 缓存模块\n\n随着业务发展，我们遇到了性能问题，"
               "于是引入了缓存，它的目标是降低数据库压力。\n\n## 使用方式\n\n装好就能用。\n")
        self.assertIn("H1", {f.rule for f in audit(Doc(src))})

    def test_tldr_accepted_when_present(self):
        src = "# 缓存模块\n\n缓存默认开启，把数据库压力降到三分之一。\n\n## 使用方式\n\n装好就能用。\n"
        self.assertNotIn("H1", {f.rule for f in audit(Doc(src))})

    def test_long_sentence_flagged_per_sentence(self):
        # 一个超长句不能被短句均值掩盖
        long_s = "这是一个非常长的句子" * 9 + "。"
        d = Doc(f"# T\n\n结论在这里。\n\n## 细节\n\n{long_s}\n\n- 短项\n- 短项\n- 短项\n")
        self.assertIn("W1x", {f.rule for f in audit(d)})

    def test_list_items_dont_dilute_sentence_stats(self):
        many_short = "\n".join(f"- 第 {i} 项" for i in range(20))
        long_s = "这是一个非常长的句子" * 9 + "。"
        d = Doc(f"# T\n\n结论。\n\n## 细节\n\n{long_s}\n\n{many_short}\n")
        rules = {f.rule for f in audit(d)}
        self.assertIn("W1x", rules)

    def test_audit_flags_fence_and_prompt(self):
        d = Doc("# T\n\n```\n$ npm install\n```\n")
        rules = {f.rule for f in audit(d)}
        self.assertIn("T1", rules)
        self.assertIn("A4", rules)

    def test_audit_flags_emoji(self):
        d = Doc("# T 🚀\n\n先 📦 装依赖，再跑起来。\n")
        rules = {f.rule for f in audit(d)}
        self.assertIn("X1p", rules)

    def test_score_range(self):
        d = Doc("# T\n\n短句。\n")
        sc = score(audit(d))
        self.assertTrue(0 <= sc["total"] <= 100)

    def test_score_penalizes_bad_doc(self):
        good = Doc("# T\n\n一句话结论。\n\n## 怎么做\n\n1. 第一步\n2. 第二步\n")
        bad = Doc("# T\n\n" + "随着业务发展，我们需要在这里写一段很长的话，"
                  "而且一逗到底，不换行，不分段，读起来非常吃力，" * 6 + "\n")
        self.assertGreater(score(audit(good))["total"], score(audit(bad))["total"])

    def test_table_and_nesting(self):
        d = Doc("# T\n\n- a\n  - b\n    - c\n")
        self.assertIn("L1", {f.rule for f in audit(d)})

    def test_backref_detected(self):
        d = Doc("# T\n\n如上所述，这个配置要改。\n")
        self.assertIn("W4", {f.rule for f in audit(d)})

    def test_findings_have_real_line_numbers(self):
        # 行号落到 L1 等于没定位。除了整篇级规则（W1m/S2/N1/X*），都必须指到实处
        src = ("# T\n\n结论。\n\n## 一\n\n这里有个填充词，基本上就是废话。\n\n"
               "## 二\n\n如上所述，这个配置要改。\n")
        whole_doc = {"W1m", "S2", "N1", "X1p", "X1c", "X2", "X5", "T2d", "T4"}
        for fd in audit(Doc(src)):
            if fd.rule not in whole_doc:
                self.assertGreater(fd.line, 1, f"{fd.rule} 行号是 {fd.line}")

    def test_backref_counted_once_per_occurrence(self):
        src = "# T\n\n结论。\n\n## 一\n\n如上所述，改配置。\n\n## 二\n\n如上所述，再改一次。\n"
        hits = [fd for fd in audit(Doc(src)) if fd.rule == "W4"]
        self.assertEqual(len(hits), 2)
        self.assertNotEqual(hits[0].line, hits[1].line)

    def test_emoji_in_code_block_is_example_not_violation(self):
        src = "# T\n\n结论。\n\n## 反面例子\n\n```markdown\n## 🚀 快速开始\n先 📦 装依赖\n```\n"
        rules = {fd.rule for fd in audit(Doc(src))}
        self.assertNotIn("X1p", rules)
        self.assertNotIn("X1c", rules)

    def test_c3_message_reports_actual_comma_count(self):
        s = "这个功能默认是关闭的" + "，如果你想打开它就得先改配置" * 4 + "。"
        hits = [fd for fd in audit(Doc(f"# T\n\n结论。\n\n## 细节\n\n{s}\n")) if fd.rule == "C3"]
        self.assertTrue(hits, "C3 未触发，检查测试串长度")
        self.assertIn("4 个逗号", hits[0].msg)

    def test_m_group_catches_ai_tells(self):
        cases = {
            "M1": "这个功能不是为了省事，而是为了少出错。",
            "M3": "时间会保管那些被忽略的细节。",
            "M4": "我们对配置进行了优化，实现了性能的提升。",
            "M6": "核心是：先改配置再重启。",
            "M7": "说白了就是缓存没生效。",
            "M8": "值得注意的是，这个配置只在启动时读一次。",
            "M9": "这套方案能赋能业务团队，打通全链路闭环。",
        }
        for rule, sentence in cases.items():
            d = Doc(f"# T\n\n结论。\n\n## 细节\n\n{sentence}\n")
            self.assertIn(rule, {fd.rule for fd in audit(d)}, f"{rule} 没抓到：{sentence}")

    def test_m_group_leaves_plain_writing_alone(self):
        plain = ("# T\n\n缓存默认开启。\n\n## 细节\n\n"
                 "关掉缓存要改配置并重启。重启会中断正在处理的请求，建议低峰期操作。\n"
                 "参数有三个，分别是 ttl、maxEntries 和 strategy。\n")
        hits = [fd.rule for fd in audit(Doc(plain)) if fd.rule.startswith("M") and not fd.advisory]
        self.assertEqual(hits, [], f"误报：{hits}")

    def test_m5_dash_is_density_not_ban(self):
        # 少量破折号是标准中文标点，不该报
        few = "# T\n\n结论。\n\n## 细节\n\n" + "这是一句普通的话，里面有个破折号 —— 就一个。\n" * 2
        self.assertNotIn("M5", {fd.rule for fd in audit(Doc(few))})
        # 密度过高才报
        many = "# T\n\n结论。\n\n## 细节\n\n" + "短句 —— 又一个破折号。\n" * 12
        self.assertIn("M5", {fd.rule for fd in audit(Doc(many))})

    def test_m_group_ignores_quoted_patterns(self):
        # 规则文档引用禁用句式当反面例子，不该被判成犯规
        doc = ("# T\n\n结论。\n\n## 规则\n\n"
               "不要写「不是 A 而是 B」这种翻案腔，也不要用「值得注意的是」当路标。\n"
               "`核心是：` 这类抬价冒号同理。\n")
        hits = [fd.rule for fd in audit(Doc(doc)) if fd.rule.startswith("M") and not fd.advisory]
        self.assertEqual(hits, [], f"引用被当成使用：{hits}")
        # 真的在用就要报
        used = "# T\n\n结论。\n\n## 细节\n\n这个功能不是为了省事，而是为了少出错。\n"
        self.assertIn("M1", {fd.rule for fd in audit(Doc(used))})

    def test_m5_counts_prose_dashes_only(self):
        # 列表项里做字段分隔的破折号不算行文节奏问题（doc-types 的会议记录模板就这么写）
        checklist = "# T\n\n结论。\n\n## 待办\n\n" + "".join(
            f"- [ ] 事项 {i} —— 负责人 —— 期限\n" for i in range(8))
        self.assertNotIn("M5", {fd.rule for fd in audit(Doc(checklist))})

    def test_m6_allows_field_label_colon(self):
        # 「结论：」「参数：」是字段标签，不是抬价冒号
        d = Doc("# T\n\n结论。\n\n## 细节\n\n结论：通过。参数：三个。\n")
        self.assertNotIn("M6", {fd.rule for fd in audit(d)})

    def test_soft_wrap_is_not_a_sentence_boundary(self):
        # 按 75 字硬折行的中文段落：一句话不能被算成三句
        wrapped = ("# T\n\n结论。\n\n## 细节\n\n"
                   "这是一句被硬折行的中文长句，\n它在文件里占了三行，\n但语义上只是一句话。\n")
        rules = {fd.rule for fd in audit(Doc(wrapped))}
        self.assertNotIn("P1", rules, "软换行被当成句子边界了")

    def test_c8_flags_mid_sentence_soft_wrap(self):
        # 断在字中间要报
        bad = "# T\n\n结论。\n\n## 细节\n\n这是一句被硬折行的中文长句它在文件里\n占了两行但语义上只是一句话。\n"
        self.assertIn("C8", {fd.rule for fd in audit(Doc(bad))})
        # 一行一句不报
        ok = "# T\n\n结论。\n\n## 细节\n\n这是第一句话。\n这是第二句话。\n"
        self.assertNotIn("C8", {fd.rule for fd in audit(Doc(ok))})

    def test_typographic_marks_are_not_emoji(self):
        # 表格里的 ✓ / ✗ 是排版符号，不是 emoji 汤
        ok_doc = Doc("# T\n\n结论。\n\n## 表\n\n| 项 | 状态 |\n|---|---|\n| a | ✓ |\n| b | ✗ |\n")
        rules = {fd.rule for fd in audit(ok_doc)}
        self.assertNotIn("X1p", rules)
        self.assertNotIn("X1c", rules)
        # 真 emoji 照样抓
        bad = Doc("# T\n\n结论。\n\n## 节\n\n先 📦 装依赖 🚀\n")
        self.assertIn("X1p", {fd.rule for fd in audit(bad)})

    def test_own_toc_output_is_not_flagged(self):
        """fmt --toc 生成的目录不能被自己的 H2/L6 规则当成要点列表报出来。"""
        src = "# T\n\n一句话结论。\n\n" + "\n\n".join(
            f"## 第 {i} 节\n\n这一节讲清楚一件事，写得不长但够用。" for i in range(1, 11))
        out = fmt(src + "\n", toc=True)
        self.assertIn("](#", out, "没生成目录")
        rules = {fd.rule for fd in audit(Doc(out))}
        self.assertNotIn("H2", rules)
        self.assertNotIn("L6", rules)
        self.assertNotIn("N1", rules)

    def test_init_skeletons_parse(self):
        for name, body in SKELETONS.items():
            d = Doc(body)
            self.assertTrue(d.blocks, name)
            self.assertEqual(fmt(body), fmt(fmt(body)), f"{name} 骨架 fmt 不幂等")

    def test_examples_corpus(self):
        """示例语料是回归门禁：after 必须分数上升、无反模式扣分、verify 通过。"""
        ex = Path(__file__).resolve().parent.parent / "references" / "examples"
        if not ex.is_dir():
            self.skipTest("examples 目录不存在")
        cases = {
            "01-zh-notes": ("both", 3, 95),
            "02-zh-readme": ("format", 2, 95),
            "03-en-runbook": ("both", 2, 95),
            # 04 是 format+light，写不了 TL;DR，88 分就是正确结果
            "04-en-reference": ("format", 1, 85),
        }
        for name, (scope, level, floor) in cases.items():
            bf, af = ex / f"{name}.before.md", ex / f"{name}.after.md"
            self.assertTrue(bf.is_file() and af.is_file(), f"{name} 缺文件")
            before, after = bf.read_text(encoding="utf-8"), af.read_text(encoding="utf-8")
            sb = score(audit(Doc(before), level=level))
            sa = score(audit(Doc(after), level=level))
            self.assertGreater(sa["total"], sb["total"], f"{name} 分数没提升")
            self.assertGreaterEqual(sa["total"], floor, f"{name} after 低于 {floor}")
            self.assertEqual(sa["x_deduct"], 0, f"{name} after 有反模式扣分 {sa['x_hits']}")
            ok, rep = verify(before, after, scope)
            self.assertTrue(ok, f"{name} verify({scope}) 失败：{rep['hard_failures']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adhd-md", description="Markdown 的 ADHD 友好化工具层")
    ap.add_argument("--version", action="version", version=VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = dict(level=dict(type=int, choices=[1, 2, 3], default=2,
                            help="1=light 2=standard 3=deep"),
                  emoji=dict(choices=["none", "minimal"], default="none"))

    p = sub.add_parser("audit", help="评分 + findings")
    p.add_argument("files", nargs="+")
    p.add_argument("--json", action="store_true")
    p.add_argument("--scope", choices=["format", "content", "both"], default="both",
                   help="只列出该轴可改的 findings")
    p.add_argument("--min-score", type=float, help="低于此分退出码 1，用于 CI")
    p.add_argument("--level", **common["level"])
    p.add_argument("--emoji", **common["emoji"])
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("fmt", help="确定性格式修复")
    p.add_argument("files", nargs="+")
    p.add_argument("--write", action="store_true", help="写回文件（默认打印 diff）")
    p.add_argument("--check", action="store_true", help="只检查，需修复则退出码 1")
    p.add_argument("--toc", action="store_true", help="缺目录时按已有标题生成")
    p.add_argument("--join-cjk", action="store_true", help="合并中文段落内的软换行")
    p.add_argument("--strip-emoji", action="store_true", help="删除 emoji（会改动字符，非无损）")
    p.set_defaults(fn=cmd_fmt)

    p = sub.add_parser("verify", help="无损校验门禁")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--scope", choices=["format", "content", "both"], default="both")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("report", help="改前改后对比")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--scope", choices=["format", "content", "both"], default="both")
    p.add_argument("--level", **common["level"])
    p.add_argument("--emoji", **common["emoji"])
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("init", help="生成文档骨架")
    p.add_argument("--type", required=True, choices=sorted(SKELETONS))
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("selftest", help="自检")
    p.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
