#!/usr/bin/env python3
"""adhd-md 的确定性工具层：审计、格式修复、部分不变量检查。

设计原则：能用规则算准的事情不交给模型。
纯标准库，Python 3.9+。阅读页生成器位于同目录 reader.py。

子命令：
  audit   评分 + 逐条 findings
  fmt     确定性格式修复（默认只做零风险项）
  verify  检查正文 token 与部分内容不变量
  report  改前改后分数对比
  init    生成文档骨架
  read    生成离线阅读页或陪读分段数据，保留原文
  extract 自动提取网页或 PDF 正文
  selftest 自检
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import stat
import sys
import tempfile
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

RULES_PATH = Path(__file__).resolve().parents[1] / "references" / "rule-definitions.json"
try:
    RULE_DATA = json.loads(RULES_PATH.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise RuntimeError(f"无法读取规则定义 {RULES_PATH}: {exc}") from exc

RULES = RULE_DATA["rules"]
RULE_BY_ID = {rule["id"]: rule for rule in RULES}
TH = RULE_DATA["thresholds"]["language"]
RULE_LIMITS = RULE_DATA["thresholds"]["limits"]
LEVEL_LABELS = {1: "light", 2: "standard", 3: "deep"}
DIMS = {key: (item["label"], item["weight"]) for key, item in RULE_DATA["dimensions"].items()}
SCORE_COMPONENTS = {
    component["id"]: {**component, "rule_id": rule["id"], "status": rule["status"]}
    for rule in RULES for component in rule.get("scoring", [])
}
DEDUCT = {
    cid: (item["dimension"], item["points"], item["cap"])
    for cid, item in SCORE_COMPONENTS.items() if item["dimension"] != "global"
}
X_DEDUCT = {
    cid: item["points"] for cid, item in SCORE_COMPONENTS.items()
    if item["dimension"] == "global"
}
X_CAP = RULE_DATA["global_score_cap"]

AXIS = {}
MIN_LEVEL = {}
for _rule in RULES:
    for _finding_id in _rule.get("finding_ids", [_rule["id"]]):
        AXIS[_finding_id] = _rule["axis"]
        MIN_LEVEL[_finding_id] = _rule["min_level"]
    AXIS.setdefault(_rule["id"], _rule["axis"])
    MIN_LEVEL.setdefault(_rule["id"], _rule["min_level"])

# 兼容原有调用方；完整评分时这些规则可由模型传入 findings。
JUDGE_ONLY = [rule["id"] for rule in RULES if rule["status"] == "judge"]

BACKREF = [
    "如上所述", "如前所述", "见下文", "见上文", "前面提到", "上文提到", "综上所述",
    "as mentioned above", "as described above", "see above", "see below",
]
FILLER = [
    "基本上", "事实上", "众所周知", "不难看出",
    "其实", "总的来说", "在某种程度上",
    "basically", "actually", "needless to say",
]

# ── M 组：去 AI 味
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

# M6 预告式冒号：`核心是：` 这类引导语先宣布重要性再给货，等于把一句话说两遍。
# 字段标签冒号（`参数：` `结论：` `例外：`）不算 —— 技术文档需要它定位
M_HINT_COLON = re.compile(
    r"(一句话(?:总结|说)?|核心(?:是|在于)|关键(?:是|在于)|"
    r"简单说|划重点|敲重点|真相(?:是|只有一个)?)\s*[：:]"
)

# M7 开场空话：宣布「我要说重点了」，本身不携带信息
M_STOP = ["说白了", "说穿了", "先说结论", "不吹不黑", "客观来说"]

# M8 装深刻：用词承诺深度，实际内容没变深
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
M_DASH_PER_KILO = RULE_LIMITS["M5"]["dashes_per_thousand_han"]

# M10 借喻包装抽象概念。误报率高（`git 仓库` 是本义），只提示不扣分
M_METAPHOR = re.compile(r"(仓库|抽屉|温度|坍塌|浪潮|钥匙|底座|土壤|齿轮|坐标系|容器)")

# ── M11-M14 中文广告腔。借鉴 academic-humanizer 的 Layer 2（MIT），
# 按技术文档改造：它管学术论文的 prove/novelty，我们管中文文档的
# 「显著提升 / 大量 / 此外连续 / 随着…从而…」

# M11 空泛量词与模糊量词：没有数字的量词和程度副词，量化或删。
# 「大量测试」「各种场景」「性能比较稳定」→ 换成数字和边界
M11_VAGUE = [
    re.compile(r"(?:大量|各种|众多|各类|一系列|多样的)[^。！？\n]{0,14}"),
    re.compile(r"(?:比较|相对|较为|有点|稍微|相当|颇为)(?:好|快|稳|稳定|简单|复杂|高|低|大|小|明显|容易|难)"),
]

# M12 连续连接词开头：一个段落里连续两句以「此外 / 而且 / 同时 / 另外」开头，
# 逻辑不靠连接词硬缝，靠句子本身
M12_OPENER = re.compile(
    r"[。！？](此外|而且|同时|另外|除此之外|另一方面)[^。！？]{1,40}[。！？](?:此外|而且|同时|另外|除此之外|另一方面)"
)

# M13 广告宣称：没有数字支撑的「显著提升 / 大幅降低 / 彻底解决 / 业界首创」。
# 句子里 10 字内带数字（显著提升 40%）时不报
M13_CLAIM = re.compile(
    r"(?:显著|大幅|明显|极大)(?:提升|提高|优化|改善|增强|降低|减少|节省|加快)|"
    r"彻底(?:解决|修复|根治)|完美(?:解决|支持|适配)|"
    r"(?:业界|国内|全球)(?:领先|首创|一流)|(?:首个|首创|最强|最优|革命性|颠覆)"
)

# M14 从句堆叠：单句 ≥2 个逻辑连接词（随着…，从而…，进而…），
# 和 C3 一逗到底是亲戚，但抓的是「连接词链」而不是逗号数量
M14_CHAIN = re.compile(r"(?:随着|从而|进而|与此同时|在此基础上|由此|使得|以便)")


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


def _is_escaped(text, index):
    slashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        slashes += 1
        index -= 1
    return slashes % 2 == 1


def _inline_code_spans(text):
    """Return matched inline-code spans, honoring the opening backtick count."""
    spans = []
    i = 0
    while i < len(text):
        if text[i] != "`" or _is_escaped(text, i):
            i += 1
            continue
        run_end = i + 1
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        run_size = run_end - i
        cursor = run_end
        close = None
        while cursor < len(text):
            tick = text.find("`", cursor)
            if tick < 0:
                break
            end = tick + 1
            while end < len(text) and text[end] == "`":
                end += 1
            if end - tick == run_size and not _is_escaped(text, tick):
                close = end
                break
            cursor = end
        if close is None:
            i = run_end
            continue
        spans.append((i, close))
        i = close
    return spans


def _mask_ranges(text, spans):
    chars = list(text)
    for start, end in spans:
        chars[start:end] = [" "] * (end - start)
    return "".join(chars)


def _markdown_links_for_lint(text):
    """Find inline Markdown links/images without treating code examples as links."""
    links = []
    i = 0
    while i < len(text):
        image = (text[i] == "!" and i + 1 < len(text) and text[i + 1] == "["
                 and not _is_escaped(text, i))
        if image:
            start, open_bracket = i, i + 1
        elif text[i] == "[" and not _is_escaped(text, i):
            start, open_bracket = i, i
        else:
            i += 1
            continue

        depth = 1
        cursor = open_bracket + 1
        label_end = None
        while cursor < len(text):
            char = text[cursor]
            if char == "\\" and cursor + 1 < len(text):
                cursor += 2
                continue
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    label_end = cursor
                    break
            cursor += 1
        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            i = open_bracket + 1
            continue

        depth = 1
        cursor = label_end + 2
        while cursor < len(text):
            char = text[cursor]
            if char == "\\" and cursor + 1 < len(text):
                cursor += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    links.append({
                        "start": start,
                        "end": cursor + 1,
                        "image": image,
                        "label_start": open_bracket + 1,
                        "label_end": label_end,
                    })
                    i = cursor + 1
                    break
            cursor += 1
        else:
            i = open_bracket + 1
    return links


def _link_label_text(text):
    def preserve_code(match):
        value = match.group(0)
        ticks = len(re.match(r"`+", value).group(0))
        return value[ticks:-ticks]

    label = INLINE_CODE_RE.sub(preserve_code, text)
    label = re.sub(r"\\([\\`*_{}\[\]()#+\-.!<>|~])", r"\1", label)
    return re.sub(r"\s+", " ", EMPH_RE.sub("", label)).strip()


def strip_inline(text, keep_code=False):
    """剥掉行内标记，保留可读文字。链接保留文字丢 URL。"""
    t = LINK_RE.sub(lambda m: m.group(1), text)
    if not keep_code:
        t = INLINE_CODE_RE.sub(" ", t)
    t = AUTOLINK_RE.sub(lambda m: m.group(1), t)
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

    if len(doc.lines) > RULE_LIMITS["S7"]["min_lines"]:
        f.append(Finding("S7", 1, f"全文 {len(doc.lines)} 行，超过 {RULE_LIMITS['S7']['min_lines']} 行；可评估拆分", "F", advisory=True))

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

    h2s = [b for b in headings if b.info["level"] == 2]
    if len(h2s) >= RULE_LIMITS["N3"]["min_h2_sections"]:
        hrs = [b for b in blocks if b.kind == "hr"]
        for previous, current in zip(h2s, h2s[1:]):
            if not any(previous.end < hr.start < current.start for hr in hrs):
                f.append(Finding("N3", current.start, "两个大节之间没有分割线，可按文档节奏添加", "F", advisory=True))

    # --- H 首屏
    # 首屏 = 第一个 H2 之前的内容（标题本身若是 TL;DR 类则继续往下算）
    lead = []
    for b in blocks:
        if b.kind == "heading" and b.info["level"] >= 2:
            if not TLDR_RE.search(b.info["title"]):
                break
        if b.start > RULE_LIMITS["H1"]["max_lines"]:
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
                if len(b.info.get("items", [])) <= RULE_LIMITS["H2"]["max_items"]:
                    has_tldr, tldr_block = True, b
                break
            if b.kind in ("para", "quote"):
                p = prose_of(b)
                if BG_OPENER.match(p):
                    continue  # 背景铺垫不算结论，继续看下一块
                if (len(split_sentences(p, lang)) <= RULE_LIMITS["H1"]["max_summary_sentences"]
                        and units(p, lang) <= RULE_LIMITS["H1"]["max_summary_units"][lang]):
                    has_tldr, tldr_block = True, b
                # 第一段不是结论就判失败，不再往后找
                break

    if not has_tldr:
        f.append(Finding("H1", 1, f"前 {RULE_LIMITS['H1']['max_lines']} 行没有结论 / TL;DR，读者不知道要不要读下去", "C"))
    else:
        for b in lead:
            if (b.kind == "list" and not _is_toc(b)
                    and len(b.info.get("items", [])) > RULE_LIMITS["H2"]["max_items"]):
                f.append(Finding("H2", b.start, f"首屏要点 {len(b.info['items'])} 条，超过 {RULE_LIMITS['H2']['max_items']} 条", "C"))
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
        if len(sents) > RULE_LIMITS["P1"]["max_sentences"] or u > th["para"]:
            f.append(Finding("P1", b.start, f"段落 {len(sents)} 句 / {u} 单位，上限 {RULE_LIMITS['P1']['max_sentences']} 句 / {th['para']}", "F"))
        if len(b.lines) > RULE_LIMITS["P4"]["max_consecutive_lines"]:
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
        if depths and max(depths) + 1 > RULE_LIMITS["L1"]["max_depth"]:
            f.append(Finding("L1", b.start, f"列表嵌套 {max(depths) + 1} 层，上限 {RULE_LIMITS['L1']['max_depth']} 层", "F"))
        items = b.info.get("items", [])
        for k, idx in enumerate(items):
            nxt = items[k + 1] if k + 1 < len(items) else len(b.lines)
            span = [l for l in b.lines[idx:nxt] if l.strip()]
            if len(span) > RULE_LIMITS["L5"]["max_lines"]:
                f.append(Finding("L5", b.start + idx, f"列表项占 {len(span)} 行，超过 {RULE_LIMITS['L5']['max_lines']} 行", "F"))
        if len(items) > RULE_LIMITS["L6"]["max_items"]:
            f.append(Finding("L6", b.start, f"列表 {len(items)} 项，建议分组", "F", advisory=True))
        # L3：像步骤却用了无序列表
        if items and UL_RE.match(b.lines[items[0]]) and len(items) >= RULE_LIMITS["L3"]["min_items"]:
            ctx = _nearest_heading(blocks, b)
            body = "\n".join(b.lines)
            if (ctx and STEP_HINT.search(ctx)) or ORDER_HINT.search(body):
                f.append(Finding("L3", b.start, "看起来是操作步骤，应改成有序列表或复选框", "F"))

    if lang == "zh":
        list_endings = []
        for b in blocks:
            if b.kind != "list" or _is_toc(b):
                continue
            for idx in b.info.get("items", []):
                item = strip_inline(b.lines[idx]).strip()
                if item:
                    list_endings.append((b.start + idx, bool(re.search(r"[。.!！?？；;]$", item))))
        if any(marked for _, marked in list_endings) and any(not marked for _, marked in list_endings):
            line = next(line for line, marked in list_endings if marked)
            f.append(Finding("C6", line, "中文列表项句末标点不一致，建议全文统一", "F", advisory=True))

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
                if u > RULE_LIMITS["C3"]["min_units"] and commas >= RULE_LIMITS["C3"]["min_commas"]:
                    f.append(Finding("C3", b.start, f"一逗到底：{u} 字 {commas} 个逗号", "C"))
                if s.count("的") >= RULE_LIMITS["C5"]["min_de_count"]:
                    f.append(Finding("C5", b.start, f"单句「的」≥{RULE_LIMITS['C5']['min_de_count']}，修饰层层套嵌", "C"))
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

    # --- M 组 去 AI 味
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
                f.append(Finding("M6", line, f"预告式冒号：{m.group(0).strip()}", "C"))
            for w in M_STOP:
                if w in vis:
                    f.append(Finding("M7", line, f"开场空话「{w}」，本身不携带信息", "C"))
            for w in M_ROADSIGN:
                if w.lower() in low:
                    f.append(Finding("M8", line, f"「{w}」这类装深刻的话，内容没变深", "C"))
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
            if lang == "zh":
                shell_words = sorted(set(re.findall(r"进行|实现|相关|方面|的问题|工作", vis)))
                if shell_words:
                    f.append(Finding("C7", line, f"虚词壳「{'、'.join(shell_words)}」可改成具体动词或删掉", "C", advisory=True))

    # M5 破折号密度。按汉字数给预算，超出的逐处报。只统计正文段落，理由见上
    han_all = len(CJK_RE.findall(prose_all))
    dash_budget = max(3, han_all * M_DASH_PER_KILO // 1000)
    for line in dash_hits[dash_budget:]:
        f.append(Finding("M5", line,
                         f"破折号超出预算：全文 {len(dash_hits)} 个，预算 {dash_budget}"
                         f"（{M_DASH_PER_KILO}/千字）", "F"))

    # M11-M14 中文广告腔。逐句扫正文段落；行号落在句子的真实位置
    for b in blocks:
        if b.kind not in ("para", "quote"):
            continue
        flat = re.sub(r"\n+", "", prose_of(b))
        for sent in split_sentences(flat, lang):
            if lang != "zh":
                continue
            for pat in M11_VAGUE:
                for m in pat.finditer(sent):
                    f.append(Finding("M11", b.start, f"空泛量词/模糊量词「{m.group(0)[:18]}」，换成数字或删", "C"))
            for m in M13_CLAIM.finditer(sent):
                # 句内 10 字内带数字 → 有依据，放行
                context = RULE_LIMITS["M13"]["number_context"]
                span = sent[max(0, m.start() - context): m.end() + context]
                if not re.search(r"\d", span):
                    f.append(Finding("M13", b.start, f"广告宣称「{m.group(0)}」没有数字支撑，换成具体数字", "C"))
            chains = M14_CHAIN.findall(sent)
            if len(chains) >= RULE_LIMITS["M14"]["min_chain_count"]:
                f.append(Finding("M14", b.start, f"从句堆叠：{len(chains)} 个逻辑连接词（{'/'.join(set(chains))}），拆成短句", "C"))

    # M12 连续连接词开头（跨行扫）
    for b in blocks:
        if b.kind != "para":
            continue
        flat = re.sub(r"\n+", "", prose_of(b))
        if M12_OPENER.search(flat):
            f.append(Finding("M12", b.start, "连续句子以「此外/而且/同时/另外」开头，让逻辑自己说", "C"))

    # --- A 行动性
    for b in blocks:
        if b.kind == "code":
            for off, ln in enumerate(b.lines[1:-1] if b.info.get("closed") else b.lines[1:], start=1):
                if SHELL_PROMPT_RE.match(ln):
                    f.append(Finding("A4", b.start + off, "命令带 $ / > 提示符，复制会出错", "F"))

    # --- N 导航
    if len(doc.lines) > RULE_LIMITS["N1"]["max_lines_without_toc"] and not _has_toc(blocks):
        f.append(Finding("N1", 1, f"{len(doc.lines)} 行文档没有目录", "F"))
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        for off, ln in enumerate(b.lines):
            if REFERENCE_LINK_RE.match(ln):
                continue  # 引用式链接定义不是裸 URL，也不在此处判断 alt 文本
            code_spans = _inline_code_spans(ln)
            vis = _mask_ranges(ln, code_spans)
            vis = HTML_TAG_RE.sub(lambda m: " " * len(m.group(0)), vis)
            links = _markdown_links_for_lint(vis)
            line_no = b.start + off
            for link in links:
                label = _link_label_text(ln[link["label_start"]:link["label_end"]])
                if link["image"]:
                    if not label:
                        f.append(Finding("N6", line_no, "图片缺 alt 文本", "C"))
                    continue
                if label.casefold() in BAD_LINK_TEXT or len(label) < 2:
                    f.append(Finding("N2", line_no, f"链接文本无意义：「{label}」", "C"))

            unlinked = _mask_ranges(vis, [(item["start"], item["end"]) for item in links])
            for match in URL_RE.finditer(unlinked):
                if match.group(0).rstrip(".,;:!?，。；：！？、"):
                    f.append(Finding("N2", line_no, "裸 URL，应给有意义的链接文本", "C"))
        if b.kind == "table":
            if (b.info["cols"] > RULE_LIMITS["N5"]["max_columns"]
                    or b.info["rows"] > RULE_LIMITS["N5"]["max_rows"]):
                f.append(Finding("N5", b.start, f"表格 {b.info['cols']} 列 {b.info['rows']} 行，超过 {RULE_LIMITS['N5']['max_columns']}×{RULE_LIMITS['N5']['max_rows']}", "F"))

    # --- T 排版
    for b in blocks:
        if b.kind == "code" and not b.info.get("lang"):
            f.append(Finding("T1", b.start, "代码块缺语言标签", "F"))
        if b.kind == "html" and not re.match(r"\s*</?(details|summary|br)\b", b.lines[0]):
            f.append(Finding("T8", b.start, "裸 HTML 标签", "F"))
        if b.kind not in ("code", "frontmatter"):
            for off, ln in enumerate(b.lines):
                label = re.match(r"^\s*(?:[-*+]\s+)?(?:\*\*)?(注意|警告|危险|warning|caution)(?:\*\*)?\s*[:：]", ln, re.I)
                canonical = re.match(r"^\s*>\s*\*\*(注意|警告|危险|warning|caution)\*\*\s*[:：]", ln, re.I)
                if label and not canonical:
                    f.append(Finding("T5", b.start + off, "提示/警告标签应统一为 `> **注意**` 或 `> **警告**`", "F", advisory=True))
                    break

    bold_stats = [bold_metrics(b) for b in blocks]
    bold_chars = sum(item[0] for item in bold_stats)
    total_chars = max(1, sum(item[1] for item in bold_stats))
    ratio = bold_chars / total_chars
    if ratio > RULE_LIMITS["T2"]["max_bold_ratio"]:
        f.append(Finding("T2d", 1, f"加粗密度 {ratio:.1%}，上限 {RULE_LIMITS['T2']['max_bold_ratio']:.0%}", "F"))
    for b in blocks:
        if b.kind in ("para", "quote"):
            c = bold_metrics(b)[2]
            if c > RULE_LIMITS["T2"]["max_bold_per_paragraph"]:
                f.append(Finding("T2p", b.start, f"单段加粗 {c} 处，上限 {RULE_LIMITS['T2']['max_bold_per_paragraph']} 处", "F"))

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
    if headings and len(doc.lines) / len(headings) < RULE_LIMITS["X2"]["min_lines_per_heading"]:
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
    if (len(prose_secs) >= RULE_LIMITS["X2"]["min_plain_prose_sections"]
            and sum(prose_secs) / len(prose_secs) < th["frag"]):
        f.append(Finding("X2", 1, f"纯正文章节平均 {sum(prose_secs) / len(prose_secs):.0f} 单位，"
                                  f"低于 {th['frag']}，碎片化", "F"))
    if ratio > RULE_LIMITS["X5"]["max_bold_ratio"]:
        f.append(Finding("X5", 1, f"加粗密度 {ratio:.1%} 超过 {RULE_LIMITS['X5']['max_bold_ratio']:.0%}", "F"))

    return [x for x in f if MIN_LEVEL.get(x.rule, 1) <= level]


def bold_metrics(block):
    """Count strong emphasis and visible prose in the same block-local domain.

    Code, link destinations and escaped delimiters cannot open emphasis. Headings
    are excluded on both sides of the density ratio, as they are not body prose.
    This is a conservative Markdown subset, not a complete delimiter parser.
    """
    if block.kind in ("heading", "code", "frontmatter", "hr", "html"):
        return 0, 0, 0
    text = _mask_ranges(block.text, _inline_code_spans(block.text))
    links = _markdown_links_for_lint(text)
    for start, end in sorted([(a, b) for x in links for a, b in
                              ((x["start"], x["label_start"]), (x["label_end"], x["end"]))],
                             reverse=True):
        text = text[:start] + text[end:]
    text = AUTOLINK_RE.sub(" ", text)
    text = HTML_TAG_RE.sub("", text)
    # Retain escaped punctuation as visible characters without making it syntax.
    text = "".join(("Ａ" if char == "*" else "Ｂ")
                   if char in "*_" and _is_escaped(text, index) else char
                   for index, char in enumerate(text))
    matches = list(re.finditer(r"(?<!\*)\*\*(?!\s)(.+?)(?<!\s)\*\*(?!\*)|"
                               r"(?<![\w_])__(?!\s)(.+?)(?<!\s)__(?![\w_])", text, re.S))
    def visible(value):
        return len(re.sub(r"\s", "", strip_inline(value)))
    return sum(visible(m[1] or m[2]) for m in matches), visible(text), len(matches)


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

def rule_in_scope(rule, scope):
    return scope == "both" or rule["axis"] == "both" or rule["axis"] == ("F" if scope == "format" else "C")


def coverage_summary(level=2, scope="both", findings=None):
    """Counts rule definitions, not findings. Scope changes this view only."""
    applicable = [rule for rule in RULES if rule["min_level"] <= level and rule_in_scope(rule, scope)]
    counts = {
        "applicable": len(applicable),
        "script_checked": sum(rule["status"] == "audit" for rule in applicable),
        "hint_only": sum(rule["status"] == "advisory" for rule in applicable),
        "judge_only": sum(rule["status"] == "judge" for rule in applicable),
        "format_only": sum(rule["status"] == "format" for rule in applicable),
        "hard_gate": sum(rule["status"] == "gate" for rule in applicable),
        "unimplemented": sum(rule["status"] not in {"audit", "advisory", "judge", "format", "gate"}
                              for rule in applicable),
    }
    counts["rule_ids"] = {
        "script_checked": [rule["id"] for rule in applicable if rule["status"] == "audit"],
        "hint_only": [rule["id"] for rule in applicable if rule["status"] == "advisory"],
        "judge_only": [rule["id"] for rule in applicable if rule["status"] == "judge"],
        "format_only": [rule["id"] for rule in applicable if rule["status"] == "format"],
        "hard_gate": [rule["id"] for rule in applicable if rule["status"] == "gate"],
        "unimplemented": [rule["id"] for rule in applicable
                          if rule["status"] not in {"audit", "advisory", "judge", "format", "gate"}],
    }
    counts["script_scored"] = sum(
        rule["status"] == "audit" and bool(rule.get("scoring")) for rule in applicable
    )
    if findings is not None:
        shown = [finding for finding in findings
                 if scope == "both" or finding.axis == ("F" if scope == "format" else "C")]
        counts["findings"] = len(shown)
        counts["advisory_findings"] = sum(finding.advisory for finding in shown)
    counts["scope"] = scope
    counts["level"] = level
    return counts


def score(findings, det_only=True, level=2, scope="both"):
    hits = {}
    for finding in findings:
        if finding.advisory:
            continue
        component = SCORE_COMPONENTS.get(finding.rule)
        if component is None or (det_only and component["status"] != "audit"):
            continue
        hits[finding.rule] = hits.get(finding.rule, 0) + 1

    dim_ded = {key: 0.0 for key in DIMS}
    global_hits = {}
    for component_id, count in hits.items():
        component = SCORE_COMPONENTS[component_id]
        if component["dimension"] == "global":
            global_hits[component_id] = component["points"]
            continue
        multiplier = 1 if component["mode"] == "once" else count
        dim_ded[component["dimension"]] += min(component["points"] * multiplier, component["cap"])

    dims = {}
    for key, (label, weight) in DIMS.items():
        dims[key] = dict(label=label, weight=weight, score=max(0.0, 100.0 - dim_ded[key]))

    x_deduct = min(X_CAP, sum(global_hits.values()))
    weighted = sum(item["score"] * item["weight"] for item in dims.values()) / 100.0
    total = max(0.0, min(100.0, weighted - x_deduct))
    unscored = [rule["id"] for rule in RULES
                if rule["status"] == "judge" and rule["min_level"] <= level
                and rule_in_scope(rule, scope)] if det_only else []
    return dict(
        total=round(total, 1),
        band=None if det_only else band(total),
        dims={key: dict(item, score=round(item["score"], 1)) for key, item in dims.items()},
        x_deduct=x_deduct,
        x_hits=global_hits,
        unscored=unscored,
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
    leading = re.match(r"^[ \t]*", line).group(0)
    content = line[len(leading):]
    trailing = re.search(r" {2,}$", line)
    suffix = trailing.group(0) if trailing else ""
    content = content[:-len(suffix)] if suffix else content
    body, keep = _protect(content)
    body = re.sub(f"([{CJK}])([A-Za-z0-9])", r"\1 \2", body)
    body = re.sub(f"([A-Za-z0-9])([{CJK}])", r"\1 \2", body)
    body = re.sub(r" {2,}", " ", body)
    return leading + _restore(body, keep) + suffix


HALF2FULL = {",": "，", ";": "；", ":": "：", "!": "！", "?": "？"}


def fix_cjk_punct(line):
    body, keep = _protect(line)

    def rep(m):
        return m.group(1) + HALF2FULL[m.group(2)]

    body = re.sub(f"([{CJK}])([,;:!?])(?=\\s|$|[{CJK}])", rep, body)
    body = re.sub(f"([{CJK}])\\.(?=\\s|$)", r"\1。", body)
    return _restore(body, keep)


def renumber_lists(lines, blocks, protected_lines=None):
    out = list(lines)
    protected_lines = set(protected_lines or ())
    for b in blocks:
        if b.kind != "list":
            continue
        counters = {}
        for idx in b.info.get("items", []):
            if b.start + idx in protected_lines:
                continue
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


def _remove_quote_prefixes(line, count=None):
    rest = line
    removed = 0
    while count is None or removed < count:
        match = re.match(r"^ {0,3}>[ \t]?", rest)
        if not match:
            break
        rest = rest[match.end():]
        removed += 1
    return rest, removed


def _fence_opener(line):
    rest, quote_count = _remove_quote_prefixes(line)
    list_item = re.match(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+", rest)
    if list_item:
        rest = rest[list_item.end():]
    match = FENCE_OPEN.match(rest)
    return (match, quote_count) if match else (None, quote_count)


def fenced_code_ranges(lines):
    """Locate fenced code at top level and inside simple list / quote containers."""
    ranges = []
    active = None
    for index, line in enumerate(lines):
        if active is None:
            match, quote_count = _fence_opener(line)
            if match:
                active = (index, match.group(2)[0], len(match.group(2)), quote_count)
            continue

        start, marker, size, quote_count = active
        candidate = line
        if quote_count:
            candidate, removed = _remove_quote_prefixes(line, quote_count)
            if removed != quote_count:
                continue
        if re.match(r"^\s*" + re.escape(marker) + "{" + str(size) + r",}\s*$", candidate):
            ranges.append((start + 1, index + 1, True))
            active = None
    if active is not None:
        start, _, _, _ = active
        ranges.append((start + 1, len(lines), False))
    return ranges


def protected_markdown_lines(lines, blocks=None):
    """One-based lines that formatting must preserve byte-for-byte."""
    if blocks is None:
        blocks = parse_blocks(lines)
    protected = set()
    for block in blocks:
        if block.kind in ("code", "frontmatter"):
            protected.update(range(block.start, block.end + 1))
    for start, end, _closed in fenced_code_ranges(lines):
        protected.update(range(start, end + 1))

    # Indented code and ambiguous nested continuation lines are left intact.
    for index, line in enumerate(lines, start=1):
        if line.strip() and re.match(r"^(?: {4,}|\t)", line):
            protected.add(index)
        elif not line.strip() and index > 1 and index < len(lines):
            if index - 1 in protected and re.match(r"^(?: {4,}|\t)", lines[index]):
                protected.add(index)

    if lines and lines[0].strip() == "---" and not any(
        i > 1 and line.strip() == "---" for i, line in enumerate(lines, start=1)
    ):
        protected.update(range(1, len(lines) + 1))
    return protected


def fix_blank_lines(lines, blocks, protected_lines=None):
    """块之间保证恰好一个空行，压缩连续空行。代码块内部不动。"""
    protected = set(protected_lines or ())
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


def fix_trailing(lines, blocks, protected_lines=None):
    protected = set(protected_lines or ())
    for b in blocks:
        if b.kind in ("code", "frontmatter"):
            for k in range(b.start, b.end + 1):
                protected.add(k)
    out = []
    for i, ln in enumerate(lines, start=1):
        if i in protected:
            out.append(ln)
            continue
        hard_break = re.search(r"\S {2,}$", ln)
        out.append(ln if hard_break else ln.rstrip())
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
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n")
    if has_mixed_line_endings(text):
        return text
    newline = "\r\n" if crlf_count else "\n"
    has_final_newline = text.endswith(("\n", "\r"))
    text = text.replace("\r\n", "\n")
    doc = Doc(text)
    lines = doc.lines
    protected = protected_markdown_lines(lines, doc.blocks)
    lines = fix_trailing(lines, doc.blocks, protected)

    doc2 = Doc("\n".join(lines) + "\n")
    protected = protected_markdown_lines(lines, doc2.blocks)
    lines = renumber_lists(lines, doc2.blocks, protected)

    doc3 = Doc("\n".join(lines) + "\n")
    protected = protected_markdown_lines(lines, doc3.blocks)

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
            if b.kind == "para" and len(b.lines) > 1 and not any(
                line_no in protected for line_no in range(b.start, b.end + 1)
            ):
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
    protected = protected_markdown_lines(lines, doc5.blocks)
    lines = fix_blank_lines(lines, doc5.blocks, protected)

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

    output = "\n".join(lines)
    if has_final_newline and output:
        output += "\n"
    return output.replace("\n", newline)


def has_mixed_line_endings(text):
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n")
    bare_cr = "\r" in text.replace("\r\n", "")
    return bare_cr or (crlf_count > 0 and lf_count != crlf_count)


# ---------------------------------------------------------------- 校验

PUNCT_FOLD = str.maketrans({
    "，": ",", "。": ".", "；": ";", "：": ":", "！": "!", "？": "?",
    "（": "(", "）": ")", "「": '"', "」": '"', "、": ",", "…": "...",
    "“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "－": "-",
})


def code_blocks_of(text):
    return [item["value"] for item in code_block_records(text)]


def indented_code_ranges(lines, excluded=None):
    excluded = set(excluded or ())
    ranges = []
    index = 0
    while index < len(lines):
        line_no = index + 1
        if line_no in excluded or not re.match(r"^(?: {4,}|\t)", lines[index]) or not lines[index].strip():
            index += 1
            continue
        start = index
        end = index
        probe = index + 1
        while probe < len(lines):
            current_no = probe + 1
            current = lines[probe]
            if current_no in excluded:
                break
            if re.match(r"^(?: {4,}|\t)", current) and current.strip():
                end = probe
                probe += 1
                continue
            if not current.strip():
                next_indented = probe + 1 < len(lines) and re.match(
                    r"^(?: {4,}|\t)\S", lines[probe + 1]
                )
                if next_indented and probe + 2 not in excluded:
                    end = probe
                    probe += 1
                    continue
            break
        ranges.append((start + 1, end + 1))
        index = end + 1
    return ranges


def code_block_records(text):
    doc = Doc(text)
    lines = doc.lines
    frontmatter = set()
    for block in doc.blocks:
        if block.kind == "frontmatter":
            frontmatter.update(range(block.start, block.end + 1))

    records, excluded = [], set(frontmatter)
    for start, end, closed in fenced_code_ranges(lines):
        if start in frontmatter:
            continue
        # start/end 是 1-based 行号；切片起点正好是 opener 后一行的 0-based 索引。
        inner_start = start
        inner_end = end - 1 if closed else end
        body = "\n".join(lines[inner_start:inner_end])
        opener, _ = _fence_opener(lines[start - 1])
        info = opener.group(3).strip() if opener else ""
        records.append({
            "value": body, "line": start, "end_line": end,
            "kind": "fenced", "language": info,
        })
        excluded.update(range(start, end + 1))

    for start, end in indented_code_ranges(lines, excluded):
        body = "\n".join(lines[start - 1:end])
        records.append({
            "value": body, "line": start, "end_line": end,
            "kind": "indented", "language": "",
        })
        excluded.update(range(start, end + 1))
    return records


TOC_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[([^\]]+)\]\(#([^)]+)\)\s*$")


def heading_anchor(title):
    return re.sub(r"[^\w一-鿿 -]", "", strip_inline(title).lower()).strip().replace(" ", "-")


def strip_toc_block(blocks):
    """只豁免每行都指向现有 H2、且标签与标题相符的列表目录。"""
    headings = {
        heading_anchor(b.info["title"]): strip_inline(b.info["title"])
        for b in blocks if b.kind == "heading" and b.info["level"] == 2
    }
    keep = []
    for b in blocks[:12]:
        if b.kind != "list":
            continue
        rows = [line for line in b.lines if line.strip()]
        matches = [TOC_ITEM_RE.match(line) for line in rows]
        if len(rows) >= 2 and all(matches) and all(
            headings.get(match.group(2)) == match.group(1) for match in matches
        ):
            keep.append(id(b))
    return keep


def _tokenize(t, preserve_punctuation=False):
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

    punctuation = set(",.;:!?()\"'")
    for ch in t:
        if preserve_punctuation and ch in punctuation:
            flush()
            tokens.append(f"␟{ch}")
        elif CJK_RE.match(ch):
            flush()
            tokens.append(ch)
        elif ch.isalnum() or ch in "._-/":
            buf.append(ch)
        else:
            flush()
    flush()
    return tokens


NUM_UNIT_PATTERN = (
    r"%|milliseconds?|msecs?|seconds?|secs?|minutes?|mins?|hours?|days?|weeks?|months?|years?|"
    r"ms|s|m|h|d|GB|MB|KB|TB|GiB|MiB|KiB|px|个|次|秒|分钟|小时|天|倍|条|行|列"
)
NUMBER_UNIT_GAP_RE = re.compile(
    rf"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)\s+({NUM_UNIT_PATTERN})(?![A-Za-z0-9_])",
    re.I,
)


def normalize_number_unit_spacing(text):
    """数字与同一单位之间的空白可变；数值和单位本身仍逐字比较。"""
    return NUMBER_UNIT_GAP_RE.sub(r"\1\2", text)


def normalize_prose(text):
    """归一化成 token 序列，供 format 档进行 token 计数与顺序比较。"""
    doc = Doc(text)
    skip = set(strip_toc_block(doc.blocks))
    parts = []
    for b in doc.blocks:
        if b.kind in ("code", "frontmatter", "hr") or id(b) in skip:
            continue
        parts.append(prose_of(b, keep_code=True))
    return _tokenize(normalize_number_unit_spacing("\n".join(parts)).translate(PUNCT_FOLD))


def normalize_prose_with_lines(text):
    doc = Doc(text)
    skip = set(strip_toc_block(doc.blocks))
    tokens, lines = [], []
    for block in doc.blocks:
        if block.kind in ("code", "frontmatter", "hr") or id(block) in skip:
            continue
        current = _tokenize(normalize_number_unit_spacing(
            prose_of(block, keep_code=True)
        ).translate(PUNCT_FOLD))
        tokens.extend(current)
        lines.extend([block.start] * len(current))
    return tokens, lines


def format_fragments(text):
    """返回参与 format 校验的有序 Markdown 块、token 序列与源行。"""
    doc = Doc(text)
    skipped = set(strip_toc_block(doc.blocks))
    fragments = []
    for block in doc.blocks:
        if block.kind in ("code", "frontmatter", "hr") or id(block) in skipped:
            continue
        content = prose_of(block, keep_code=True)
        tokens = tuple(_tokenize(
            normalize_number_unit_spacing(content).translate(PUNCT_FOLD),
            preserve_punctuation=True,
        ))
        if tokens:
            fragments.append({
                "kind": block.kind,
                "tokens": tokens,
                "line": block.start,
                "text": content[:160],
            })
    return fragments


def compare_fragment_order(old, new):
    """只允许完整、唯一且未改写的原块重排；其余等词频换序需人工判断。"""
    old_fragments, new_fragments = format_fragments(old), format_fragments(new)
    signature = lambda fragment: (fragment["kind"], fragment["tokens"])
    old_counts = Counter(signature(fragment) for fragment in old_fragments)
    new_counts = Counter(signature(fragment) for fragment in new_fragments)
    if old_counts != new_counts:
        return "unmapped", []
    repeated = [tokens for tokens, count in old_counts.items() if count > 1]
    if repeated:
        return "ambiguous", []
    old_positions = {signature(fragment): index for index, fragment in enumerate(old_fragments)}
    mapping = []
    for new_index, fragment in enumerate(new_fragments):
        old_index = old_positions[signature(fragment)]
        mapping.append({
            "old_index": old_index,
            "new_index": new_index,
            "old_line": old_fragments[old_index]["line"],
            "new_line": fragment["line"],
            "kind": fragment["kind"],
        })
    if [item["old_index"] for item in mapping] == list(range(len(old_fragments))):
        return "unchanged", mapping
    return "mapped_reorder", mapping


REFERENCE_LINK_RE = re.compile(r"(?m)^\s*\[[^\]]+\]:\s*\S+")
REFERENCE_USE_RE = re.compile(r"\[[^\]]+\]\[[^\]]*\]")
HTML_MARKUP_RE = re.compile(r"</?[A-Za-z][^>]*>|<!--")
LINK_DEST_RE = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))")
AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+|mailto:[^>\s]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})>", re.I)


def frontmatter_of(text):
    """返回开头闭合的 YAML frontmatter 原文；没有则返回 None。"""
    blocks = Doc(text).blocks
    if blocks and blocks[0].kind == "frontmatter":
        return blocks[0].text
    return None


def link_target_records(text):
    """提取链接目标及源位置；目录生成项、代码和元数据不算正文链接。"""
    doc = Doc(text)
    protected = set()
    toc_blocks = set(strip_toc_block(doc.blocks))
    for block in doc.blocks:
        if block.kind in ("code", "frontmatter"):
            protected.update(range(block.start, block.end + 1))
        elif id(block) in toc_blocks:
            protected.update(range(block.start, block.end + 1))
    targets = []
    for line_no, line in enumerate(doc.lines, start=1):
        if line_no in protected:
            continue
        visible = INLINE_CODE_RE.sub("", line)
        link_spans = []
        for match in AUTOLINK_RE.finditer(visible):
            targets.append({"value": match.group(1), "line": line_no, "source": "autolink"})
            link_spans.append(match.span())
        for match in LINK_DEST_RE.finditer(visible):
            targets.append({
                "value": match.group(1) or match.group(2),
                "line": line_no,
                "source": "markdown_link",
            })
            link_spans.append(match.span())
        for match in URL_RE.finditer(visible):
            if not any(start <= match.start() and match.end() <= end for start, end in link_spans):
                targets.append({
                    "value": match.group(0).rstrip(".,;:!?"),
                    "line": line_no,
                    "source": "bare_url",
                })
    return targets


def link_destinations(text):
    """提取常见单行 Markdown 链接和图片目标，保留重复次数。"""
    return [item["value"] for item in link_target_records(text)]


def verification_uncertainties(text):
    """Return unsupported Markdown constructs with 1-based source locations."""
    doc = Doc(text)
    issues = []
    if has_mixed_line_endings(text):
        issues.append({
            "kind": "mixed_line_endings",
            "line": 1,
            "hint": "檔案混用不同換行符；格式化器保留原文，統一換行前需人工確認。",
        })
    protected = set()
    for block in doc.blocks:
        if block.kind in ("code", "frontmatter"):
            protected.update(range(block.start, block.end + 1))
        if block.kind == "code" and not block.info.get("closed"):
            issues.append({
                "kind": "unclosed_fence",
                "line": block.start,
                "hint": "围栏未闭合，后续内容可能被当成代码；保留原文并人工核对。",
            })

    if doc.lines and doc.lines[0].strip() == "---" and not any(
        i > 1 and line.strip() == "---" for i, line in enumerate(doc.lines, start=1)
    ):
        issues.append({
            "kind": "unclosed_frontmatter",
            "line": 1,
            "hint": "YAML frontmatter 未闭合，校验器无法确认元数据边界。",
        })

    for line_no, line in enumerate(doc.lines, start=1):
        if line_no in protected or not line.strip():
            continue
        visible = AUTOLINK_RE.sub("", INLINE_CODE_RE.sub("", line))
        if re.match(r"^(?: {4,}|\t)\S", line):
            issues.append({
                "kind": "indented_code_or_nested_block",
                "line": line_no,
                "hint": "四空格缩进可能是代码或嵌套块；当前解析器无法可靠区分。",
            })
        if REFERENCE_LINK_RE.match(visible) or REFERENCE_USE_RE.search(visible):
            issues.append({
                "kind": "reference_link",
                "line": line_no,
                "hint": "引用式链接暂不在自动校验范围内；检查标签与目标是否仍对应。",
            })
        if HTML_MARKUP_RE.search(visible):
            issues.append({
                "kind": "raw_html",
                "line": line_no,
                "hint": "原始 HTML 的显示与结构不由 Markdown 校验器解析；保留原样并人工核对。",
            })
    valid_tocs = set(strip_toc_block(doc.blocks))
    for block in doc.blocks:
        if block.kind == "list" and any(re.search(r"\]\(#", line) for line in block.lines):
            if id(block) not in valid_tocs:
                issues.append({
                    "kind": "toc_not_matching_headings",
                    "line": block.start,
                    "hint": "目录链接必须逐项匹配现有 H2 标题；其他锚点列表需要人工核对。",
                })
    return issues


def reused_fold_wrapper_lines(source, target):
    """只认可 summary 逐字复用唯一原 H2 的标准 details 外壳。"""
    source_headings = Counter(
        strip_inline(block.info["title"], keep_code=True).strip()
        for block in Doc(source).blocks
        if block.kind == "heading" and block.info["level"] == 2
    )
    lines = Doc(target).lines
    allowed = set()
    summary_re = re.compile(r"^\s*<summary>(.*?)</summary>\s*$")
    for index, line in enumerate(lines):
        if line.strip() != "<details>" or index + 2 >= len(lines):
            continue
        summary = summary_re.match(lines[index + 1])
        if not summary:
            continue
        title = strip_inline(summary.group(1), keep_code=True).strip()
        if source_headings[title] != 1:
            continue
        close = next((pos for pos in range(index + 2, len(lines))
                      if lines[pos].strip() == "</details>"), None)
        if close is None or any(lines[pos].strip() == "<details>"
                                for pos in range(index + 2, close)):
            continue
        allowed.update((index + 1, index + 2, close + 1))
    return allowed


IDENT_RE = re.compile(r"\b(?:[A-Za-z_][A-Za-z0-9_]*(?:[._-][A-Za-z0-9_]+)+|[a-z]+[A-Z][A-Za-z0-9]*|[A-Z]{2,}[A-Z0-9_]*)\b")
OPTION_RE = re.compile(r"(?<![\w-])--?[A-Za-z][A-Za-z0-9_-]*(?:=[^\s,;，；]+)?")
PATH_RE = re.compile(
    r"(?<![A-Za-z0-9:/])(?:\.\.?/|[A-Za-z0-9_.~-]+/)[A-Za-z0-9_.~/-]*(?:#[A-Za-z0-9_-]+)?"
    r"|(?<![A-Za-z0-9:/])[A-Za-z0-9_.~-]+\.(?:md|markdown|html?|css|m?js|cjs|ts|tsx|jsx|json|ya?ml|toml|sh|py|png|jpe?g|svg|pdf|txt|zip)(?:#[A-Za-z0-9_-]+)?",
    re.I,
)
PERMISSION_RE = re.compile(
    r"(?i)(?<!\w)(?:permissions?|scopes?|roles?|权限|角色|范围)\s*(?:[:=：]|为|是)\s*"
    r"([A-Za-z0-9_.,/| -]+?)(?=\s*(?:[。！？；;\n]|$))"
)
CHMOD_RE = re.compile(r"(?i)\b(?:chmod|mode)\s+(0?[0-7]{3,4})\b")
NUM_RE = re.compile(
    rf"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)\s*({NUM_UNIT_PATTERN})?(?![A-Za-z0-9_])",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
INLINE_SPAN_RE = re.compile(r"`([^`\n]+)`")
PRESENCE_ONLY_IDENTIFIERS = {
    "API", "CLI", "URL", "HTTP", "HTTPS", "HTML", "JSON", "PDF",
    "ID", "UI", "UX", "CPU", "GPU",
}


def _prose_records(text, include_code=False):
    """可见正文行及原行号；围栏、缩进代码、元数据和生成目录不入正文源。"""
    doc = Doc(text)
    excluded = set()
    for block in doc.blocks:
        if block.kind == "frontmatter":
            excluded.update(range(block.start, block.end + 1))
    code = code_block_records(text)
    for block in code:
        excluded.update(range(block["line"], block["end_line"] + 1))
    for block_id in strip_toc_block(doc.blocks):
        block = next((item for item in doc.blocks if id(item) == block_id), None)
        if block:
            excluded.update(range(block.start, block.end + 1))
    records = [
        {"text": line, "line": line_no, "source": "prose"}
        for line_no, line in enumerate(doc.lines, start=1)
        if line_no not in excluded and line.strip()
    ]
    if include_code:
        for block in code:
            first_line = block["line"] if block["kind"] == "indented" else block["line"] + 1
            for offset, line in enumerate(block["value"].split("\n")):
                if line.strip():
                    records.append({"text": line, "line": first_line + offset, "source": "code"})
    return records


def extract_invariants(text, include_code=False):
    """保留来源、类型和重复次数，供 verify 做精确多重集比较。"""
    prose = _prose_records(text, include_code=include_code)
    inline, literals, numbers = [], [], []
    seen_identifiers = set()
    for source in prose:
        line = source["text"]
        if source["source"] == "prose":
            for match in INLINE_SPAN_RE.finditer(line):
                inline.append({"value": match.group(1), "line": source["line"], "type": "inline"})

        # 只比较内容，不把 Markdown 的反引号当字面量的一部分。
        visible = INLINE_SPAN_RE.sub(lambda match: match.group(1), line) if source["source"] == "prose" else line
        literal_visible = URL_RE.sub(" ", visible)
        occupied = []
        for kind, pattern in (("option", OPTION_RE), ("path", PATH_RE)):
            for match in pattern.finditer(literal_visible):
                literals.append({"type": kind, "value": match.group(0), "line": source["line"]})
                occupied.append(match.span())
        for match in PERMISSION_RE.finditer(literal_visible):
            value = re.sub(r"\s*([,，/|])\s*", r"\1", match.group(1).strip())
            literals.append({"type": "permission", "value": value, "line": source["line"]})
        for match in CHMOD_RE.finditer(literal_visible):
            literals.append({"type": "permission_mode", "value": match.group(1), "line": source["line"]})
            occupied.append(match.span(1))

        # URL 与链接目标由独立提取器检查，避免把域名片段重复当标识符。
        without_urls = literal_visible
        for match in IDENT_RE.finditer(without_urls):
            if not any(start <= match.start() and match.end() <= end for start, end in occupied):
                key = match.group(0)
                if key.casefold() in {"ms", "s", "m", "h", "gb", "mb", "kb", "px"}:
                    continue
                if (source["source"] == "code" or key not in PRESENCE_ONLY_IDENTIFIERS
                        or key not in seen_identifiers):
                    literals.append({"type": "identifier", "value": key, "line": source["line"]})
                    seen_identifiers.add(key)
        if source["source"] == "prose":
            numeric_source = re.sub(r"^\s*\d+[.)]\s+", "", literal_visible)
            for match in NUM_RE.finditer(numeric_source):
                value = re.sub(r"\s+", "", match.group(0))
                numbers.append({"value": value, "line": source["line"], "type": "number"})

    return {
        "code": code_block_records(text),
        "links": link_target_records(text),
        "inline": inline,
        "literals": literals,
        "numbers": numbers,
        "prose": prose,
    }


def _record_key(record, fields):
    return tuple(record[field] for field in fields)


def _counter_records(records, fields):
    counts = Counter()
    lines = {}
    for record in records:
        key = _record_key(record, fields)
        counts[key] += 1
        lines.setdefault(key, []).append(record["line"])
    return counts, lines


def _diff_records(old_records, new_records, fields, type_field=None):
    old_counts, old_lines = _counter_records(old_records, fields)
    new_counts, new_lines = _counter_records(new_records, fields)
    missing = old_counts - new_counts
    added = new_counts - old_counts

    def describe(counter, source_lines, new_side=False):
        result = []
        for key, count in counter.most_common(12):
            item = dict(zip(fields, key))
            item["count"] = count
            if type_field and type_field not in item:
                item[type_field] = key[0]
            item["lines"] = source_lines.get(key, [])[:12]
            result.append(item)
        return result

    return describe(missing, old_lines), describe(added, new_lines)


def _literal_count(text, value):
    """按完整字面量计数；字母、数字和下划线边界不能匹配更长标识符。"""
    if not value:
        return 0
    count, offset = 0, 0
    word = lambda char: char.isalnum() or char == "_"
    while True:
        index = text.find(value, offset)
        if index < 0:
            return count
        end = index + len(value)
        left_ok = index == 0 or not (word(value[0]) and word(text[index - 1]))
        right_ok = end == len(text) or not (word(value[-1]) and word(text[end]))
        if left_ok and right_ok:
            count += 1
            offset = end
        else:
            offset = index + 1


def _inline_literal_losses(old_records, new_records):
    old_counts, old_lines = _counter_records(old_records, ("value",))
    new_text = "\n".join(record["text"] for record in new_records)
    missing = []
    for (value,), old_count in old_counts.items():
        found = _literal_count(new_text, value)
        if found < old_count:
            missing.append({
                "type": "inline", "value": value,
                "count": old_count - found,
                "old_count": old_count, "new_count": found,
                "old_lines": old_lines[(value,)][:12],
            })
    return missing


def strip_code(text):
    doc = Doc(text)
    out = []
    for b in doc.blocks:
        if b.kind in ("code", "frontmatter"):
            continue
        out.append(b.text)
    return "\n".join(out)


def verify(old, new, scope="both"):
    """返回 (ok, 报告 dict)。ok 仅在 status=pass 时为 True。"""
    rep = {
        "scope": scope,
        "status": "pass",
        "hard_failures": [],
        "warnings": [],
        "unknowns": [],
        "ok": True,
    }

    if old == new:
        rep["identical"] = True
        return True, rep

    for side, text in (("old", old), ("new", new)):
        allowed_fold_lines = reused_fold_wrapper_lines(old, new) if side == "new" else set()
        for issue in verification_uncertainties(text):
            if issue["kind"] == "raw_html" and issue["line"] in allowed_fold_lines:
                continue
            rep["unknowns"].append({"side": side, **issue})

    old_inv = extract_invariants(old)
    # 新增内容可以进入代码块；旧内容中的受保护值仍可在其新来源中匹配。
    new_inv = extract_invariants(new, include_code=True)
    missing_code, added_code = _diff_records(
        old_inv["code"], new_inv["code"], ("value",)
    )
    if missing_code or (scope == "format" and added_code):
        rep["hard_failures"].append({
            "kind": "code_block_missing",
            "count": sum(item["count"] for item in missing_code)
                     + (sum(item["count"] for item in added_code) if scope == "format" else 0),
            "missing": [{**item, "value": item["value"][:160]} for item in missing_code],
            "added": [{**item, "value": item["value"][:160]} for item in added_code],
            "hint": "原有代码块正文及其重复次数都必须保留。",
        })

    missing_links, added_links = _diff_records(
        old_inv["links"], new_inv["links"], ("value",)
    )
    if missing_links or (scope == "format" and added_links):
        rep["hard_failures"].append({
            "kind": "link_targets_changed",
            "missing": missing_links,
            "added": added_links,
            "hint": "格式整理应保留 Markdown 链接和图片的目标地址。",
        })

    old_frontmatter, new_frontmatter = frontmatter_of(old), frontmatter_of(new)
    if old_frontmatter != new_frontmatter:
        if scope == "format":
            rep["hard_failures"].append({
                "kind": "frontmatter_changed",
                "old": old_frontmatter,
                "new": new_frontmatter,
                "hint": "format 模式不改元数据；回退后另行审阅。",
            })
        else:
            rep["warnings"].append({
                "kind": "frontmatter_changed",
                "old": old_frontmatter,
                "new": new_frontmatter,
                "old_line": 1 if old_frontmatter is not None else None,
                "new_line": 1 if new_frontmatter is not None else None,
                "hint": "元数据变化已允许，但需单独核对字段、值和消费者兼容性。",
            })

    # 内容改写也必须保留原文中的精确字面值。新加反引号可以改变包装，
    # 但选项、路径、权限值和大小写敏感标识符按来源正文查找完整值及次数。
    missing_inline = _inline_literal_losses(old_inv["inline"], new_inv["prose"])
    if missing_inline:
        rep["hard_failures"].append({
            "kind": "inline_literals_missing",
            "count": sum(item["count"] for item in missing_inline),
            "items": missing_inline[:12],
            "hint": "原有行内代码值必须逐项保留；可以增加或移除反引号，但不能改掉字面内容。",
        })

    missing_literals, added_literals = _diff_records(
        old_inv["literals"], new_inv["literals"], ("type", "value")
    )
    if missing_literals:
        rep["hard_failures"].append({
            "kind": "protected_literals_missing",
            "count": sum(item["count"] for item in missing_literals),
            "missing": missing_literals,
            "added": added_literals,
            "hint": "选项、路径、权限值和大小写敏感标识符必须按类型及次数保留。",
        })

    missing_numbers, added_numbers = _diff_records(
        old_inv["numbers"], new_inv["numbers"], ("value",)
    )
    if missing_numbers:
        finding = {
            "kind": "numeric_literals_changed",
            "count": sum(item["count"] for item in missing_numbers),
            "missing": missing_numbers,
            "added": added_numbers,
            "hint": "仅忽略数字与单位之间的空白；数值或单位变化需要明确审阅。",
        }
        if scope == "format":
            rep["hard_failures"].append(finding)
        else:
            rep["warnings"].append(finding)

    if scope == "format":
        # 比多重集，不比序列。块重排（S5 结论前置）是合法的 format 操作，
        # 会改变 token 顺序但不改变 token 集合。删词 → missing，新写 → extra。
        a, b = normalize_prose(old), normalize_prose(new)
        ca, cb = Counter(a), Counter(b)
        missing, extra = ca - cb, cb - ca
        old_tokens, old_lines = normalize_prose_with_lines(old)
        new_tokens, new_lines = normalize_prose_with_lines(new)
        old_positions, new_positions = {}, {}
        for token, line in zip(old_tokens, old_lines):
            old_positions.setdefault(token, []).append(line)
        for token, line in zip(new_tokens, new_lines):
            new_positions.setdefault(token, []).append(line)
        if missing:
            rep["hard_failures"].append({
                "kind": "prose_tokens_missing",
                "count": sum(missing.values()),
                "items": [w for w, _ in missing.most_common(20)],
                "missing": [
                    {"value": word, "count": count, "old_lines": old_positions.get(word, [])[:12]}
                    for word, count in missing.most_common(20)
                ],
                "hint": "这些词从正文里消失了。format 档不许删词。",
            })
        if extra:
            rep["hard_failures"].append({
                "kind": "prose_tokens_added",
                "count": sum(extra.values()),
                "items": [w for w, _ in extra.most_common(20)],
                "added": [
                    {"value": word, "count": count, "new_lines": new_positions.get(word, [])[:12]}
                    for word, count in extra.most_common(20)
                ],
                "hint": "这些词是新写的。format 档不许新增措辞，改用 scope=content。",
            })
        if not missing and not extra and a != b:
            mismatch = next((i for i, (before, after) in enumerate(zip(old_tokens, new_tokens))
                             if before != after), min(len(old_tokens), len(new_tokens)))
            line = new_lines[mismatch] if mismatch < len(new_lines) else (new_lines[-1] if new_lines else 1)
            mapping, movements = compare_fragment_order(old, new)
            if mapping == "mapped_reorder":
                rep.setdefault("notes", []).append({
                    "kind": "blocks_reordered",
                    "moves": [move for move in movements if move["old_index"] != move["new_index"]],
                    "hint": "只匹配到未改写的完整块。仍要检查「这个方案」「上述」「它」等指代是否失去对象。",
                })
            else:
                if mapping == "ambiguous":
                    kind = "ambiguous_fragment_mapping"
                    hint = "重复块无法唯一映射；请人工确认移动的是哪一份原文。"
                else:
                    kind = "token_order_changed"
                    hint = "词序变化不对应未改写的完整块移动；可能改动了句内条件、对象或否定关系。"
                rep["warnings"].append({
                    "kind": "blocks_reordered",
                    "hint": "检查块移动和指代关系；无法确定时保留原文并人工复核。",
                })
                rep["unknowns"].append({
                    "side": "new",
                    "kind": kind,
                    "line": line,
                    "hint": hint,
                })
    rep["status"] = (
        "fail" if rep["hard_failures"]
        else "unknown" if rep["unknowns"] or rep["warnings"]
        else "pass"
    )
    rep["ok"] = rep["status"] == "pass"
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

def render_audit(path, doc, findings, sc, scope="both", level=2):
    lines = [f"# {path}", ""]
    if sc["det_only"]:
        # 不给档位。脚本分未包含人工判断，报「优」会误导。
        lines.append(f"脚本分 **{sc['total']}** / 100")
        lines.append("")
        lines.append(f"> 这不是最终分。全文有 {len(sc['unscored'])} 条规则尚需模型判断，脚本暂按未命中计分；"
                     "这不表示通过，补上判断后分数可能下降。")
    else:
        lines.append(f"总分 **{sc['total']}** / 100 —— {sc['band']}")
    lines.append("")
    lines.append(f"语言 `{doc.lang}` · {len(doc.lines)} 行 · {len(doc.blocks)} 块")
    lines.append("")
    coverage = coverage_summary(level, scope, findings)
    lines.append(f"规则覆盖（{LEVEL_LABELS[level]} · {scope}）：适用 {coverage['applicable']} 条；"
                 f"脚本检查 {coverage['script_checked']}（可计分 {coverage['script_scored']}）；"
                 f"仅提示 {coverage['hint_only']}；需判断 {coverage['judge_only']}；"
                 f"仅自动修复 {coverage['format_only']}；硬门禁 {coverage['hard_gate']}。")
    lines.append("scope 只过滤 findings 列表与覆盖统计；脚本分始终按全文所有适用轴计算。"
                 "提示项没有分值，未判定项也不等于通过。")
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
        lines.append(f"## Findings {len(shown)} 条")
        lines.append("")
        groups = {}
        for f in shown:
            groups.setdefault(f.rule, []).append(f)
        for rule in sorted(groups, key=lambda r: -len(groups[r])):
            g = groups[rule]
            advisory_note = "（仅提示，不扣分）" if g[0].advisory else ""
            head = f"- **{rule}** ({AXIS.get(rule, '?')} 轴){advisory_note} × {len(g)} —— {g[0].msg}"
            lines.append(head)
            for f in g[:3]:
                lines.append(f"  - `{path}:{f.line}`")
            if len(g) > 3:
                lines.append(f"  - …另 {len(g) - 3} 处")
    else:
        lines.append("所选范围没有 findings；这不代表人工判断项通过。")

    if sc["unscored"]:
        lines.append("")
        lines.append("## 需模型判断（脚本未评分）")
        lines.append("")
        lines.append("、".join(sc["unscored"]))
    return "\n".join(lines) + "\n"


def read(p):
    if p == "-":
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        text = stream.read()
        return text.decode("utf-8") if isinstance(text, bytes) else text
    with open(p, "r", encoding="utf-8", newline="") as stream:
        return stream.read()


class WriteRefused(RuntimeError):
    """A safe write cannot be guaranteed for this path or source encoding."""


class ConcurrentWrite(WriteRefused):
    """The original path or its bytes changed while formatting was in progress."""


def _stat_fingerprint(info):
    return (
        info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
        info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
    )


def read_write_snapshot(path):
    """Read UTF-8 bytes without following links and retain identity for a later CAS check."""
    path = os.fspath(path)
    before = os.lstat(path)
    if stat.S_ISLNK(before.st_mode):
        raise WriteRefused("拒绝写入符号链接；请指定其实际文件路径")
    if not stat.S_ISREG(before.st_mode):
        raise WriteRefused("目标不是普通文件")
    if before.st_nlink != 1:
        raise WriteRefused("拒绝写入硬链接文件，以免破坏共享文件关系")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_dev != before.st_dev
                or info.st_ino != before.st_ino or info.st_nlink != 1):
            raise ConcurrentWrite("文件在读取期间被替换或建立了硬链接")
        data = stream.read()

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WriteRefused("只支持 UTF-8 文本；原文件未改动") from exc
    return {"text": text, "bytes": data, "stat": info,
            "fingerprint": _stat_fingerprint(info)}


def atomic_write_text(path, text, expected):
    """Stage beside the target, recheck its snapshot, then atomically replace it."""
    destination = Path(path)
    temporary = None
    try:
        data = text.encode("utf-8")
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{destination.name}.", suffix=".tmp",
            dir=str(destination.parent), delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

            source_info = expected["stat"]
            staged_info = os.fstat(stream.fileno())
            if (source_info.st_uid, source_info.st_gid) != (staged_info.st_uid, staged_info.st_gid):
                chown = getattr(os, "fchown", None)
                if chown is None:
                    raise WriteRefused("无法保留原文件所有者和组")
                chown(stream.fileno(), source_info.st_uid, source_info.st_gid)
            os.fchmod(stream.fileno(), stat.S_IMODE(source_info.st_mode))
            os.fsync(stream.fileno())

        current = read_write_snapshot(path)
        if (current["fingerprint"] != expected["fingerprint"]
                or current["bytes"] != expected["bytes"]):
            raise ConcurrentWrite("文件在读取后被修改或替换；拒绝覆盖")

        os.replace(temporary, destination)
        temporary = None

        # Make the rename durable where directory fsync is supported.
        try:
            directory_fd = os.open(
                str(destination.parent),
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------- CLI

def cmd_audit(a):
    worst = 0
    payload = []
    for p in a.files:
        text = read(p)
        doc = Doc(text, p)
        findings = audit(doc, level=a.level, emoji=a.emoji)
        sc = score(findings, det_only=True, level=a.level)
        worst = max(worst, 100 - sc["total"])
        shown = [f for f in findings if a.scope == "both" or f.axis == ("F" if a.scope == "format" else "C")]
        if a.json:
            payload.append(dict(
                schema_version=2, path=p, lang=doc.lang, lines=len(doc.lines), scope=a.scope,
                level=a.level, score=sc, coverage=coverage_summary(a.level, a.scope, findings),
                scope_behavior="findings 和 coverage 按 scope 展示；score 始终覆盖全文所有适用轴",
                findings=[dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis,
                               advisory=f.advisory) for f in findings],
                shown_findings=[dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis,
                                     advisory=f.advisory) for f in shown],
            ))
        else:
            print(render_audit(p, doc, findings, sc, a.scope, a.level))
    if a.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], ensure_ascii=False, indent=2))
    if a.min_score is not None and (100 - worst) < a.min_score:
        return 1
    return 0


def cmd_fmt(a):
    changed = 0
    blocked_status = 0
    for p in a.files:
        snapshot = None
        try:
            if a.write:
                snapshot = read_write_snapshot(p)
                old = snapshot["text"]
            else:
                old = read(p)
        except (OSError, WriteRefused, UnicodeError) as exc:
            blocked_status = max(blocked_status, 3)
            print(f"拒绝写回：{p}（{exc}）")
            continue
        new = fmt(old, toc=a.toc, join_cjk=a.join_cjk, strip_emoji=a.strip_emoji)
        if has_mixed_line_endings(old):
            blocked_status = max(blocked_status, 4)
            print(f"無法格式化：{p}（混合換行符，保留原檔）")
            continue
        if new == old:
            continue
        changed += 1
        if a.check:
            print(f"需要格式修复：{p}")
        elif a.write:
            if not a.strip_emoji:
                ok, rep = verify(old, new, "format")
                if not ok:
                    status = rep["status"]
                    code = 3 if status == "fail" else 4
                    blocked_status = max(blocked_status, code)
                    print(f"拒绝写回：{p}（校验{ {'fail': '失败', 'unknown': '无法判断'}[status] }）")
                    for item in rep["hard_failures"] + rep["unknowns"]:
                        line = f":{item['line']}" if "line" in item else ""
                        print(f"  {item['kind']}{line}: {item.get('hint', '')}")
                    continue
            try:
                atomic_write_text(p, new, snapshot)
            except ConcurrentWrite as exc:
                blocked_status = max(blocked_status, 3)
                print(f"拒绝写回：{p}（{exc}）")
                continue
            except (OSError, WriteRefused, UnicodeError) as exc:
                blocked_status = max(blocked_status, 3)
                print(f"写回失败：{p}（{exc}；原文件保持不变）")
                continue
            print(f"{'已写入（有损）' if a.strip_emoji else '已修复'}：{p}")
        else:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile=f"{p} (原)", tofile=f"{p} (fmt)"))
    if not changed:
        print("格式已规范，无需修改。")
    return blocked_status or (1 if (a.check and changed) else 0)


def cmd_verify(a):
    ok, rep = verify(read(a.old), read(a.new), a.scope)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        label = {"pass": "通过", "fail": "失败", "unknown": "无法判断"}[rep["status"]]
        print(f"scope={a.scope} → {label}")
        for h in rep["hard_failures"]:
            print(f"  [硬失败] {h['kind']}: {json.dumps(h, ensure_ascii=False)[:400]}")
        for w in rep["warnings"]:
            print(f"  [警告] {w['kind']}: {json.dumps(w, ensure_ascii=False)[:300]}")
        for u in rep["unknowns"]:
            where = f"{u.get('side', 'new')}:{u['line']}" if "line" in u else u.get("side", "")
            print(f"  [无法判断] {u['kind']} {where}: {u['hint']}")
        for note in rep.get("notes", []):
            print(f"  [提示] {note['kind']}: {note['hint']}")
    return 0 if rep["status"] == "pass" else 3 if rep["status"] == "fail" else 4


def cmd_report(a):
    rows = []
    for label, p in (("before", a.old), ("after", a.new)):
        doc = Doc(read(p), p)
        f = audit(doc, level=a.level, emoji=a.emoji)
        scoped = [item for item in f
                  if a.scope == "both" or item.axis == ("F" if a.scope == "format" else "C")]
        rows.append((label, doc, f, scoped, score(f, det_only=True, level=a.level),
                     coverage_summary(a.level, a.scope, f)))
    (lb, db, fb, sfb, sb, cb), (la, da, fa, sfa, sa, ca) = rows
    ok, vrep = verify(read(a.old), read(a.new), a.scope)

    if a.json:
        payload = {
            "schema_version": 2,
            "scope": a.scope,
            "level": a.level,
            "scope_behavior": "findings 和 coverage 按 scope 展示；score 始终覆盖全文所有适用轴",
            "before": {
                "path": a.old, "lang": db.lang, "lines": len(db.lines), "score": sb,
                "coverage": cb,
                "findings": [dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis, advisory=f.advisory) for f in fb],
                "shown_findings": [dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis, advisory=f.advisory) for f in sfb],
            },
            "after": {
                "path": a.new, "lang": da.lang, "lines": len(da.lines), "score": sa,
                "coverage": ca,
                "findings": [dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis, advisory=f.advisory) for f in fa],
                "shown_findings": [dict(rule=f.rule, line=f.line, msg=f.msg, axis=f.axis, advisory=f.advisory) for f in sfa],
            },
            "verify": vrep,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if vrep["status"] == "unknown":
            return 4
        return 1 if sa["x_deduct"] or not ok else 0

    print(f"脚本分  {sb['total']} → {sa['total']}  ({sa['total'] - sb['total']:+.1f})")
    print(f"规则覆盖（{LEVEL_LABELS[a.level]} · {a.scope}）：适用 {cb['applicable']} 条；"
          f"脚本检查 {cb['script_checked']}（可计分 {cb['script_scored']}）；"
          f"仅提示 {cb['hint_only']}；需判断 {cb['judge_only']}；"
          f"仅自动修复 {cb['format_only']}；硬门禁 {cb['hard_gate']}。")
    print("scope 只过滤 findings 展示与覆盖统计；脚本分始终按全文所有适用轴计算。"
          "提示项不扣分，人工判断项未判定不等于通过。")
    print()
    print("| 维度 | before | after | delta |")
    print("|---|---|---|---|")
    for k, v in DIMS.items():
        b, x = sb["dims"][k]["score"], sa["dims"][k]["score"]
        print(f"| {v[0]} | {b} | {x} | {x - b:+.1f} |")
    print()
    print(f"反模式扣分  −{sb['x_deduct']} → −{sa['x_deduct']}"
          + ("  ✗ after 必须为 0" if sa["x_deduct"] else ""))
    print(f"findings({a.scope})  {len(sfb)} → {len(sfa)}；全文 {len(fb)} → {len(fa)}")
    verify_label = {"pass": "通过", "fail": "失败", "unknown": "无法判断"}[vrep["status"]]
    if vrep.get("warnings") and vrep["status"] == "pass":
        verify_label += "（有警告）"
    print(f"verify({a.scope})  {verify_label}")
    if not ok:
        for h in vrep["hard_failures"]:
            print(f"  [硬失败] {h['kind']}")
        for u in vrep["unknowns"]:
            print(f"  [无法判断] {u['kind']}")
    for warning in vrep.get("warnings", []):
        print(f"  [警告] {warning['kind']}: {warning.get('hint', '')}")
    for note in vrep.get("notes", []):
        print(f"  [提示] {note['kind']}: {note['hint']}")
    if vrep["status"] == "unknown":
        return 4
    if sa["x_deduct"] or not ok:
        return 1
    return 0


def cmd_init(a):
    print(SKELETONS[a.type], end="")
    return 0


def _source_command(a, *, extracted=False):
    from sources import export_markdown, load_source, output_path, read_stdin

    command = "extract" if extracted else "read"
    if a.json and a.output:
        print(f"{command}: --json 输出到标准输出，不能同时指定 --output。", file=sys.stderr)
        return 2
    try:
        original = None
        if a.file == "-":
            stream = getattr(sys.stdin, "buffer", sys.stdin)
            original = read_stdin(stream)
        result = load_source(a.file, timeout=a.timeout, ocr=a.ocr,
                             ocr_lang=a.ocr_lang, stdin_text=original)
        if extracted:
            data = result
            content = export_markdown(result)
        else:
            from reader import build_reading_data, render_reader

            data = build_reading_data(result["text"], result["source_name"], chunk_size=a.chunk_size)
            if result.get("title"):
                data["title"] = result["title"]
            if result.get("origin"):
                data["origin"] = result["origin"]
            content = None
        if a.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        output = Path(a.output) if a.output else output_path(a.file, result, extracted=extracted)
        if not extracted:
            content = render_reader(data)
        # Exclusive creation also refuses symlinks and hardlinks to existing files.
        with output.open("x", encoding="utf-8", newline="") as handle:
            handle.write(content)
        if extracted:
            print(f"已提取正文：{output.resolve()}")
        else:
            print(f"已生成阅读页：{output.resolve()}（{len(data['chunks'])} 段）")
            print("用浏览器打开即可阅读；原文保持不变。")
        for warning in result.get("origin", {}).get("warnings", []):
            print(f"{command}: {warning}", file=sys.stderr)
        return 0
    except FileExistsError:
        print(f"{command}: 输出文件已存在；请用 -o 指定新文件名。", file=sys.stderr)
    except UnicodeError:
        print(f"{command}: 无法解码正文；Markdown / 文本文件请使用 UTF-8 编码。", file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"{command}: {exc}", file=sys.stderr)
    return 2


def cmd_read(a):
    return _source_command(a)


def cmd_extract(a):
    return _source_command(a, extracted=True)


def cmd_selftest(a):
    import unittest
    sys.argv = sys.argv[:1]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(SelfTest)
    suite.addTests(loader.discover(str(Path(__file__).parent / "tests"), pattern="test_reader*.py"))
    suite.addTests(loader.discover(str(Path(__file__).parent / "tests"), pattern="test_extract*.py"))
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if res.wasSuccessful() else 1


import unittest  # noqa: E402  自检用，放末尾避免影响启动


class SelfTest(unittest.TestCase):
    def test_bold_ignores_code_and_destinations(self):
        for literal in ("`x ** 2`", "``x ** 2 ` y``", r"\*\*literal\*\*",
                        "[label](https://example.test/**path**)"):
            with self.subTest(literal=literal):
                doc = Doc("# Title\n\n" + literal + " ordinary prose.\n\nMore prose.\n")
                self.assertFalse({"T2d", "T2p", "X5"} & {f.rule for f in audit(doc)})

    def test_bold_metrics_same_visible_domain(self):
        for text in ("**alpha beta**", "__alpha beta__", "**[alpha beta](https://example.test)**"):
            block = Doc(text + "\n").blocks[0]
            bold, total, count = bold_metrics(block)
            self.assertEqual(bold, 9)
            self.assertLessEqual(bold, total)
            self.assertEqual(count, 1)
        doc = Doc("# **Heading**\n\nplain body\n")
        self.assertFalse({"T2d", "X5"} & {f.rule for f in audit(doc)})

    def test_bold_does_not_pair_across_blocks(self):
        doc = Doc("# Title\n\n**unclosed paragraph\n\nother paragraph**\n")
        self.assertFalse({"T2d", "X5"} & {f.rule for f in audit(doc)})

    def test_bold_paragraph_count_ignores_literals(self):
        block = Doc("`x ** 2` then **real** prose.\n").blocks[0]
        self.assertEqual(bold_metrics(block)[0], 4)
        self.assertEqual(bold_metrics(block)[2], 1)
        doc = Doc("# Title\n\n`**a** **b** **c**` **real**\n")
        self.assertNotIn("T2p", {f.rule for f in audit(doc)})
        doc = Doc("# Title\n\n**a** **b** **c**\n")
        self.assertIn("T2p", {f.rule for f in audit(doc)})

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

    def test_fmt_preserves_indented_python_and_string_value(self):
        import ast

        src = "# T\r\n\r\n    if True:\r\n        result = \"中文,示例\"  \r\n\r\n说明,继续。\r\n"
        expected = "# T\r\n\r\n    if True:\r\n        result = \"中文,示例\"  \r\n\r\n说明，继续。\r\n"
        out = fmt(src)
        self.assertEqual(out, expected)
        tree = ast.parse("if True:\n    result = \"中文,示例\"\n")
        self.assertEqual(tree.body[0].body[0].value.value, "中文,示例")

    def test_fmt_preserves_list_continuation_indent_and_tab_code(self):
        src = "# T\n\n- 项目\n  续Node18\n\tif True:\n\t\tresult = \"中文,示例\"  \n"
        expected = "# T\n\n- 项目\n  续 Node18\n\tif True:\n\t\tresult = \"中文,示例\"  \n"
        self.assertEqual(fmt(src), expected)

    def test_fmt_protects_nested_fences_and_shorter_inner_fence(self):
        src = (
            "# T\n\n"
            "- 列表项\n"
            "  ````python\n"
            "  if True:\n"
            "      result = \"中文,示例\"\n"
            "  ```shorter marker\n"
            "  ````\n\n"
            "> ````python\n"
            "> if True:\n"
            ">     result = \"中文,示例\"\n"
            "> ```shorter marker\n"
            "> ````\n"
        )
        out = fmt(src)
        for line in (
            '      result = "中文,示例"',
            "  ```shorter marker",
            '>     result = "中文,示例"',
            "> ```shorter marker",
        ):
            self.assertIn(line, out)
        self.assertEqual(fmt(out), out)

    def test_fmt_preserves_hard_break_spaces_and_unclosed_fence(self):
        hard_break = "# T\n\n第一行  \n第二行\n"
        self.assertIn("第一行  \n第二行", fmt(hard_break))
        unclosed = "# T\n\n```python\nvalue = \"中文,示例\"  \n"
        self.assertIn('value = "中文,示例"  ', fmt(unclosed))

    def test_fmt_preserves_inline_commands_paths_versions_and_urls(self):
        src = (
            "# T\n\n运行 `python -m test, --path=/tmp/a,`，版本 `Node18.1.2`，"
            "访问 https://example.com/a?x=1,y=2。\n"
        )
        self.assertEqual(fmt(src), src)

    def test_fmt_write_preserves_crlf_bytes(self):
        import contextlib
        import io
        import tempfile

        source = "# T\r\n\r\n中文,文字\r\n".encode("utf-8")
        expected = "# T\r\n\r\n中文，文字\r\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "doc.md"
            path.write_bytes(source)
            os.chmod(path, 0o640)
            before_stat = path.stat()
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["fmt", str(path), "--write"])
            self.assertEqual(result, 0)
            self.assertEqual(path.read_bytes(), expected)
            after_stat = path.stat()
            self.assertEqual(stat.S_IMODE(after_stat.st_mode), 0o640)
            self.assertNotEqual(after_stat.st_ino, before_stat.st_ino)
            self.assertEqual(list(Path(root).glob(".doc.md.*.tmp")), [])

    def test_fmt_write_refuses_symlink_and_hardlink_targets(self):
        import contextlib
        import io
        import tempfile

        source = "# T\n\n中文,内容\n"
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "target.md"
            target.write_text(source, encoding="utf-8")
            link = Path(root) / "linked.md"
            link.symlink_to(target)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["fmt", str(link), "--write"])
            self.assertEqual(result, 3)
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), source)
            self.assertIn("符号链接", output.getvalue())

            hardlink = Path(root) / "hardlinked.md"
            os.link(target, hardlink)
            with contextlib.redirect_stdout(output := io.StringIO()):
                result = main(["fmt", str(target), "--write"])
            self.assertEqual(result, 3)
            self.assertEqual(target.read_text(encoding="utf-8"), source)
            self.assertEqual(hardlink.read_text(encoding="utf-8"), source)
            self.assertIn("硬链接", output.getvalue())
            self.assertEqual(list(Path(root).glob(".*.tmp")), [])

    def test_fmt_write_multi_file_failure_is_atomic_per_file(self):
        import contextlib
        import io
        import tempfile

        source = "# T\n\n中文,内容\n"
        with tempfile.TemporaryDirectory() as root:
            good = Path(root) / "good.md"
            target = Path(root) / "target.md"
            link = Path(root) / "linked.md"
            good.write_text(source, encoding="utf-8")
            target.write_text(source, encoding="utf-8")
            link.symlink_to(target)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["fmt", str(good), str(link), "--write"])
            self.assertEqual(result, 3)
            self.assertIn("中文，内容", good.read_text(encoding="utf-8"))
            self.assertEqual(target.read_text(encoding="utf-8"), source)
            self.assertIn("已修复", output.getvalue())
            self.assertIn("拒绝写回", output.getvalue())
            self.assertEqual(list(Path(root).glob(".*.tmp")), [])

    def test_fmt_write_rejects_non_utf8_without_touching_bytes(self):
        import contextlib
        import io
        import tempfile

        raw = b"# T\n\n\xff,content\n"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "invalid.md"
            path.write_bytes(raw)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["fmt", str(path), "--write"])
            self.assertEqual(result, 3)
            self.assertEqual(path.read_bytes(), raw)
            self.assertIn("UTF-8", output.getvalue())

    def test_fmt_write_detects_concurrent_edits_and_cleans_temp(self):
        import contextlib
        import io
        import tempfile
        from unittest import mock

        source = "# T\n\n中文,内容\n"
        external_edit = "# T\n\n外部编辑内容\n"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "doc.md"
            path.write_text(source, encoding="utf-8")
            real_fmt = fmt

            def edit_after_read(text, **kwargs):
                path.write_text(external_edit, encoding="utf-8")
                return real_fmt(text, **kwargs)

            output = io.StringIO()
            with mock.patch.object(sys.modules[__name__], "fmt", side_effect=edit_after_read):
                with contextlib.redirect_stdout(output):
                    result = main(["fmt", str(path), "--write"])
            self.assertEqual(result, 3)
            self.assertEqual(path.read_text(encoding="utf-8"), external_edit)
            self.assertIn("被修改", output.getvalue())
            self.assertEqual(list(Path(root).glob(".doc.md.*.tmp")), [])

    def test_fmt_write_failure_keeps_original_and_cleans_temp(self):
        import contextlib
        import io
        import tempfile
        from unittest import mock

        source = "# T\n\n中文,内容\n"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "doc.md"
            path.write_text(source, encoding="utf-8")
            for operation in ("fsync", "replace"):
                with self.subTest(operation=operation):
                    output = io.StringIO()
                    with mock.patch.object(os, operation, side_effect=PermissionError("injected")):
                        with contextlib.redirect_stdout(output):
                            result = main(["fmt", str(path), "--write"])
                    self.assertEqual(result, 3)
                    self.assertEqual(path.read_text(encoding="utf-8"), source)
                    self.assertIn("原文件保持不变", output.getvalue())
                    self.assertEqual(list(Path(root).glob(".doc.md.*.tmp")), [])

    def test_fmt_write_strip_emoji_uses_explicit_lossy_path(self):
        import contextlib
        import io
        import tempfile

        source = "# T\n\nKeep this 😀\n"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "doc.md"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["fmt", str(path), "--write", "--strip-emoji"])
            self.assertEqual(result, 0)
            self.assertNotIn("😀", path.read_text(encoding="utf-8"))
            self.assertIn("已写入（有损）", output.getvalue())

    def test_fmt_leaves_mixed_line_endings_unknown(self):
        mixed = "# T\r\n\n中文,文字\n"
        self.assertEqual(fmt(mixed), mixed)
        ok, rep = verify(mixed, mixed.replace("中文,文字", "中文，文字"), "format")
        self.assertFalse(ok)
        self.assertEqual(rep["status"], "unknown")
        self.assertTrue(any(u["kind"] == "mixed_line_endings" and u["line"] == 1
                            for u in rep["unknowns"]))

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
        self.assertIn("prose_tokens_missing", {h["kind"] for h in rep["hard_failures"]})

    def test_verify_format_allows_reorder(self):
        # 标题和段落作为未改写的完整块移动时可以通过，并保留指代提醒。
        old = "# T\n\n## 背景\n\n项目从去年开始。\n\n## 结论\n\n性能快了十三倍。\n"
        new = "# T\n\n## 结论\n\n性能快了十三倍。\n\n## 背景\n\n项目从去年开始。\n"
        ok, rep = verify(old, new, "format")
        self.assertTrue(ok, rep)
        self.assertEqual(rep["status"], "pass")
        self.assertEqual(rep["notes"][0]["kind"], "blocks_reordered")
        self.assertTrue(rep["notes"][0]["moves"])

    def test_verify_format_rejects_sentence_and_list_reordering(self):
        old = "# T\n\n允许甲，禁止乙。\n"
        changed = "# T\n\n禁止甲，允许乙。\n"
        ok, rep = verify(old, changed, "format")
        self.assertFalse(ok, rep)
        self.assertEqual(rep["status"], "unknown")
        self.assertEqual(rep["unknowns"][0]["kind"], "token_order_changed")
        self.assertIn("完整块移动", rep["unknowns"][0]["hint"])

        old = "# T\n\n- 先校验\n- 再保存\n"
        changed = "# T\n\n- 再保存\n- 先校验\n"
        ok, rep = verify(old, changed, "format")
        self.assertFalse(ok, rep)
        self.assertEqual(rep["status"], "unknown")

    def test_verify_format_marks_repeated_fragment_mapping_ambiguous(self):
        old = "# T\n\n相同段落。\n\n其他内容。\n\n相同段落。\n"
        new = "# T\n\n其他内容。\n\n相同段落。\n\n相同段落。\n"
        ok, rep = verify(old, new, "format")
        self.assertFalse(ok, rep)
        self.assertEqual(rep["status"], "unknown")
        self.assertEqual(rep["unknowns"][0]["kind"], "ambiguous_fragment_mapping")

        old = "# T\n\n## Setup\n\nFirst.\n\n## Setup\n\nSecond.\n"
        new = "# T\n\n## Setup\n\nSecond.\n\n## Setup\n\nFirst.\n"
        ok, rep = verify(old, new, "format")
        self.assertFalse(ok, rep)
        self.assertEqual(rep["status"], "unknown")
        self.assertEqual(rep["unknowns"][0]["kind"], "ambiguous_fragment_mapping")

    def test_verify_raw_html_unknown_has_source_line(self):
        old = "# T\n\n<details>\n<summary>旧标题</summary>\n原文。\n</details>\n"
        new = old.replace("原文。", "原文！")
        ok, rep = verify(old, new, "format")
        self.assertFalse(ok)
        self.assertEqual(rep["status"], "unknown")
        self.assertTrue(any(u["kind"] == "raw_html" and u["line"] == 3
                            for u in rep["unknowns"]))

    def test_verify_allows_fold_with_unique_reused_heading(self):
        old = "# T\n\n## Options\n\nOriginal text.\n"
        folded = "# T\n\n<details>\n<summary>Options</summary>\nOriginal text.\n</details>\n"
        ok, rep = verify(old, folded, "format")
        self.assertTrue(ok, rep)
        self.assertEqual(rep["status"], "pass")

        hidden = folded.replace("Original text.\n", "")
        ok, rep = verify(old, hidden, "format")
        self.assertFalse(ok, rep)
        self.assertEqual(rep["status"], "fail")
        self.assertIn("prose_tokens_missing", {h["kind"] for h in rep["hard_failures"]})

        duplicate = "# T\n\n## Options\n\nA.\n\n## Options\n\nB.\n"
        ambiguous = "# T\n\n<details>\n<summary>Options</summary>\nA.\n</details>\n"
        ok, rep = verify(duplicate, ambiguous, "format")
        self.assertFalse(ok, rep)
        self.assertNotEqual(rep["status"], "pass")

    def test_fmt_write_refuses_unknown_without_changing_source(self):
        import contextlib
        import io
        import tempfile

        source = "# 标题\n\n<details>\n\n中文,内容\n\n</details>"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "doc.md"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["fmt", str(path), "--write"])
            self.assertEqual(code, 4)
            self.assertEqual(path.read_text(encoding="utf-8"), source)
            self.assertIn("拒绝写回", output.getvalue())

    def test_verify_json_adds_tri_state_without_legacy_success(self):
        import contextlib
        import io
        import tempfile

        old = "# T\n\n允许甲，禁止乙。\n"
        new = "# T\n\n禁止甲，允许乙。\n"
        with tempfile.TemporaryDirectory() as root:
            before, after = Path(root) / "before.md", Path(root) / "after.md"
            before.write_text(old, encoding="utf-8")
            after.write_text(new, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["verify", str(before), str(after), "--scope=format", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 4)
        self.assertEqual(payload["status"], "unknown")
        self.assertFalse(payload["ok"])
        self.assertTrue({"scope", "hard_failures", "warnings", "ok"}.issubset(payload))
        with tempfile.TemporaryDirectory() as root:
            before, after = Path(root) / "before.md", Path(root) / "after.md"
            before.write_text(old, encoding="utf-8")
            after.write_text(new, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["verify", str(before), str(after), "--scope=format"])
        self.assertEqual(code, 4)
        self.assertIn("无法判断", output.getvalue())
        self.assertNotIn("→ 通过", output.getvalue())

    def test_verify_format_protects_frontmatter_and_link_targets(self):
        old = "---\ntitle: Before\n---\n\n[guide](next.html#start)\n"
        changed_meta = old.replace("title: Before", "title: After")
        ok, rep = verify(old, changed_meta, "format")
        self.assertFalse(ok)
        self.assertIn("frontmatter_changed", {h["kind"] for h in rep["hard_failures"]})

        for scope in ("content", "both"):
            ok, rep = verify(old, changed_meta, scope)
            self.assertFalse(ok)
            self.assertEqual(rep["status"], "unknown")
            warning = next(w for w in rep["warnings"] if w["kind"] == "frontmatter_changed")
            self.assertIn("title: Before", warning["old"])
            self.assertIn("title: After", warning["new"])

        changed_link = old.replace("next.html#start", "other.html#start")
        ok, rep = verify(old, changed_link, "content")
        self.assertFalse(ok)
        self.assertIn("link_targets_changed", {h["kind"] for h in rep["hard_failures"]})

        meta_with_body_format = old.replace("[guide](next.html#start)", "**[guide](next.html#start)**")
        ok, rep = verify(old, meta_with_body_format, "format")
        self.assertTrue(ok, rep)

        bare = "# T\n\nSee https://grafana.internal/d/payments\n"
        linked = "# T\n\nSee [dashboard](https://grafana.internal/d/payments)\n"
        ok, rep = verify(bare, linked, "both")
        self.assertTrue(ok, rep)

        autolink = "# T\n\nSee <https://example.com/a>\n"
        inline_link = "# T\n\nSee [https://example.com/a](https://example.com/a)\n"
        ok, rep = verify(autolink, inline_link, "format")
        self.assertTrue(ok, rep)

    def test_verify_link_target_counts_and_scope_addition_policy(self):
        old = "# T\n\nSee [one](https://docs.example/a) and [two](https://docs.example/a).\n"
        new = "# T\n\nSee [one](https://docs.example/a).\n"
        for scope in ("format", "content", "both"):
            with self.subTest(scope=scope):
                ok, rep = verify(old, new, scope)
                self.assertFalse(ok)
                finding = next(h for h in rep["hard_failures"] if h["kind"] == "link_targets_changed")
                self.assertEqual(finding["missing"][0]["count"], 1)
                self.assertEqual(finding["missing"][0]["lines"], [3, 3])

        old = "# T\n\nRead the manual.\n"
        new = "# T\n\nRead the [manual](https://docs.example/manual).\n"
        self.assertTrue(verify(old, new, "content")[0])
        self.assertTrue(verify(old, new, "both")[0])
        self.assertFalse(verify(old, new, "format")[0])

    def test_verify_generated_toc_matches_existing_headings(self):
        old = "# T\n\n" + "\n\n".join(
            f"## 第 {i} 节\n\n第 {i} 节的正文。" for i in range(1, 4)
        ) + "\n"
        generated = fmt(old, toc=True)
        ok, rep = verify(old, generated, "format")
        self.assertTrue(ok, rep)

        fake = generated.replace("[第 1 节](#第-1-节)", "[伪目录](#made-up)")
        ok, rep = verify(old, fake, "format")
        self.assertFalse(ok)
        self.assertNotEqual(rep["status"], "pass")
        self.assertTrue(any(u["kind"] == "toc_not_matching_headings" for u in rep["unknowns"]))

    def test_verification_supported_syntax_matrix(self):
        cases = [
            ("heading", "# T\n\n## Setup\n", "# T\n\n### Setup\n",
             "# T\n\n### Install\n"),
            ("paragraph", "# T\n\nUse the worker now.\n",
             "# T\n\nUse the **worker** now.\n", "# T\n\nUse the server now.\n"),
            ("fenced code", "# T\n\n```sh\necho ok\n```\n",
             "# T\n\n```sh\necho ok\n```\n\n", "# T\n\n```sh\necho no\n```\n"),
            ("list", "# T\n\n- first\n- second\n", "# T\n\n* first\n* second\n",
             "# T\n\n- first\n- third\n"),
            ("quote", "# T\n\n> Read this.\n", "# T\n\n> Read this.\n\n",
             "# T\n\n> Ignore this.\n"),
            ("table", "# T\n\n| Key | Value |\n| --- | --- |\n| ttl | 7 days |\n",
             "# T\n\n| Key | Value |\n| :--- | ---: |\n| ttl | 7 days |\n",
             "# T\n\n| Key | Value |\n| --- | --- |\n| ttl | 8 days |\n"),
        ]
        for label, before, allowed, out_of_bounds in cases:
            with self.subTest(syntax=label, sample="allowed"):
                ok, rep = verify(before, allowed, "format")
                self.assertTrue(ok, rep)
            with self.subTest(syntax=label, sample="out-of-bounds"):
                ok, rep = verify(before, out_of_bounds, "format")
                self.assertFalse(ok, rep)
                self.assertEqual(rep["status"], "fail")

        folded = "# T\n\n<details>\n<summary>Options</summary>\nOriginal text.\n</details>\n"
        ok, unchanged = verify(folded, folded, "format")
        self.assertTrue(ok, unchanged)
        ok, changed = verify(folded, folded.replace("Original text.", "Original text!"), "format")
        self.assertFalse(ok)
        self.assertEqual(changed["status"], "unknown")

        indented = "# T\n\n    x = 1\n"
        ok, changed = verify(indented, indented + "\n", "format")
        self.assertFalse(ok)
        self.assertEqual(changed["status"], "unknown")

        reference = "# T\n\nRead [the guide][guide].\n\n[guide]: guide.md\n"
        ok, changed = verify(reference, reference.replace("Read", "**Read**"), "format")
        self.assertFalse(ok)
        self.assertEqual(changed["status"], "unknown")

        unclosed = "# T\n\n## Code\n\n```python\nprint(1)\n"
        ok, changed = verify(unclosed, unclosed.replace("## Code", "### Code"), "format")
        self.assertFalse(ok)
        self.assertEqual(changed["status"], "unknown")
        self.assertTrue(any(u["kind"] == "unclosed_fence" and u["line"] == 5
                            for u in changed["unknowns"]))

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

    def test_audit_finds_bad_links_empty_alt_and_bare_urls(self):
        src = (
            "# Links\n\n"
            "Read [here](https://example.com/a\\(draft\\)).\n"
            "![  ](images/chart\\(draft\\).png)\n"
            "网址：https://example.com/裸链(演示)。\n\n"
            "Code: `[here](https://example.com)` and `![ ](image.png)`; "
            "also <https://example.com/autolink>.\n\n"
            "```md\n[here](https://example.com)\n![ ](image.png)\n``\n"
            "\n[guide]: https://example.com/reference\n"
        )
        hits = [(finding.rule, finding.line) for finding in audit(Doc(src))
                if finding.rule in {"N2", "N6"}]
        self.assertEqual(hits, [("N2", 3), ("N6", 4), ("N2", 5)])

    def test_audit_ignores_meaningful_links_autolinks_and_code_examples(self):
        src = (
            "# Links\n\n"
            "Read the [deployment guide](https://example.com/guide\\(blue\\)).\n"
            "![架构示意图](images/architecture\\(v2\\).png)\n"
            "Autolink: <https://example.com/reference>.\n"
            "Inline examples: `[here](https://example.com)` and `https://example.com`.\n\n"
            "```md\n[here](https://example.com)\n![ ](image.png)\nhttps://example.com\n```\n"
            "\n[guide]: https://example.com/reference\n"
        )
        hits = [finding for finding in audit(Doc(src)) if finding.rule in {"N2", "N6"}]
        self.assertEqual(hits, [])

    def test_rule_hints_report_without_changing_score(self):
        src = (
            "# 规则提示\n\n结论：检查文档写法。\n\n## 第一节\n\n"
            "注意：先进行检查。\n\n"
            "## 第二节\n\n"
            "- 第一项。\n- 第二项\n"
        )
        hits = [finding for finding in audit(Doc(src), level=2)
                if finding.rule in {"N3", "T5", "C6", "C7"}]
        self.assertEqual({finding.rule for finding in hits}, {"N3", "T5", "C6", "C7"})
        self.assertTrue(all(finding.advisory for finding in hits))
        self.assertEqual(score(hits)["total"], 100.0)

        long_doc = "# Long\n\n結論。\n\n" + "正文內容。\n" * 600
        self.assertIn("S7", {finding.rule for finding in audit(Doc(long_doc), level=3)})

    def test_rule_level_scope_coverage_matrix(self):
        expected = {
            "format": [(24, 16, 2, 3, 2, 1), (39, 23, 4, 9, 2, 1), (41, 23, 5, 10, 2, 1)],
            "content": [(2, 0, 0, 1, 0, 1), (37, 19, 3, 14, 0, 1), (46, 20, 3, 22, 0, 1)],
            "both": [(25, 16, 2, 4, 2, 1), (75, 42, 7, 23, 2, 1), (86, 43, 8, 32, 2, 1)],
        }
        for scope, rows in expected.items():
            for level, wanted in enumerate(rows, start=1):
                with self.subTest(scope=scope, level=level):
                    coverage = coverage_summary(level, scope)
                    got = (coverage["applicable"], coverage["script_checked"], coverage["hint_only"],
                           coverage["judge_only"], coverage["format_only"], coverage["hard_gate"])
                    self.assertEqual(got, wanted)
                    self.assertEqual(coverage["unimplemented"], 0)

    def test_audit_scope_preserves_full_score_and_json_compatibility(self):
        import contextlib
        import io
        import tempfile

        src = ("# Demo 🚀\n\n结论。\n\n## 第一节\n\n这部分进行测试。\n"
               "\n## 第二节\n\n还有正常内容。\n")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.md"
            path.write_text(src, encoding="utf-8")
            outputs = {}
            for scope in ("format", "content"):
                args = type("Args", (), dict(files=[str(path)], level=2, emoji="none",
                                              min_score=None, json=True, scope=scope))()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(cmd_audit(args), 0)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload["schema_version"], 2)
                self.assertIsNone(payload["score"]["band"])
                self.assertIn("findings", payload)  # legacy, all-axis findings remain available
                self.assertTrue(all(f["axis"] == ("F" if scope == "format" else "C")
                                    for f in payload["shown_findings"]))
                outputs[scope] = payload
            self.assertEqual(outputs["format"]["score"], outputs["content"]["score"])
            self.assertEqual(outputs["format"]["coverage"]["scope"], "format")
            self.assertEqual(outputs["content"]["coverage"]["scope"], "content")

    def test_report_text_json_match_audit_and_surface_verify_warnings(self):
        import contextlib
        import io
        import tempfile

        base = ("# Demo\n\n结论。\n\n## 第一节\n\n这段正文提供足够多的信息，便于读者快速理解配置并继续操作。\n\n"
                "读者可以先查看本节的关键条件。\n\n"
                "完成后再核对实际输出。\n\n"
                "- [ ] 核对配置\n\n"
                "## 第二节\n\n这里说明运行条件和检查方法，读者可以直接核对执行结果。\n\n"
                "每个步骤都可以在本地重复。\n\n"
                "失败时先检查配置值。\n\n"
                "- [ ] 核对环境\n\n"
                "## 第三节\n\n最后列出限制和后续步骤，帮助读者恢复阅读并完成任务。\n\n"
                "相关边界写在本节中。\n\n"
                "读者可以据此决定下一步。\n\n"
                "- [ ] 记录结果\n")
        with tempfile.TemporaryDirectory() as temp:
            old = Path(temp) / "before.md"
            new = Path(temp) / "after.md"
            old.write_text(base, encoding="utf-8")
            new.write_text(base, encoding="utf-8")
            audit_args = type("Args", (), dict(files=[str(new)], level=2, emoji="none",
                                                min_score=None, json=True, scope="format"))()
            audit_output = io.StringIO()
            with contextlib.redirect_stdout(audit_output):
                cmd_audit(audit_args)
            audit_payload = json.loads(audit_output.getvalue())

            report_output = io.StringIO()
            with contextlib.redirect_stdout(report_output):
                code = main(["report", str(old), str(new), "--scope", "format", "--json"])
            self.assertEqual(code, 0)
            report_payload = json.loads(report_output.getvalue())
            self.assertEqual(report_payload["after"]["score"], audit_payload["score"])
            self.assertEqual(report_payload["after"]["coverage"], audit_payload["coverage"])

            old.write_text("# TTL\n\n默认有效期为 30 秒。\n", encoding="utf-8")
            new.write_text("# TTL\n\n默认有效期为 30 分钟。\n", encoding="utf-8")
            text_output = io.StringIO()
            with contextlib.redirect_stdout(text_output):
                code = main(["report", str(old), str(new), "--scope", "content"])
            self.assertEqual(code, 4)
            self.assertIn("[警告] numeric_literals_changed", text_output.getvalue())
            self.assertIn("无法判断", text_output.getvalue())

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

    def test_verify_no_false_num_warning_on_spaced_cjk(self):
        # 「2 分钟」归一成「2分钟」后要能在带空格的原文里找到，否则每篇中文文档都误报
        old = "# T\n\n装好约 2 分钟，共 71 条规则。\n"
        new = "# T\n\n装好约 2 分钟。\n\n## 规则\n\n共 71 条规则。\n"
        ok, rep = verify(old, new, "content")
        self.assertTrue(ok, rep["hard_failures"])
        self.assertEqual(rep["warnings"], [], f"数字误报：{rep['warnings']}")
        # 真丢了要报
        ok2, rep2 = verify(old, "# T\n\n装好很快。\n", "content")
        self.assertFalse(ok2)
        self.assertEqual(rep2["status"], "unknown")
        numeric = next(w for w in rep2["warnings"] if w["kind"] == "numeric_literals_changed")
        self.assertEqual(numeric["missing"][0]["value"], "2分钟")
        self.assertEqual(numeric["missing"][0]["lines"], [3])

    def test_verify_content_invariants(self):
        old = "# T\n\n用 `--timeout` 改，默认 30 秒。见 https://x.dev/docs\n"
        new = "# T\n\n默认超时 30 秒。\n"
        ok, rep = verify(old, new, "content")
        self.assertFalse(ok)
        kinds = {h["kind"] for h in rep["hard_failures"]}
        self.assertIn("link_targets_changed", kinds)

    def test_verify_typed_literals_reject_replacements_in_every_scope(self):
        cases = [
            ("domain", "文档见 https://docs.old.dev/start。", "文档见 https://docs.new.dev/start。",
             "link_targets_changed"),
            ("relative path", "配置在 ../config/app.yaml。", "配置在 ../config/prod.yaml。",
             "protected_literals_missing"),
            ("option prefix", "运行 `--timeout`。", "运行 `--timeoutExtra`。",
             "protected_literals_missing"),
            ("permission", "权限：read, write。", "权限：read, admin。",
             "protected_literals_missing"),
            ("case-sensitive identifier", "选项是 maxEntries。", "选项是 maxentries。",
             "protected_literals_missing"),
        ]
        for name, before, after, expected in cases:
            with self.subTest(name=name):
                old, new = f"# T\n\n{before}\n", f"# T\n\n{after}\n"
                for scope in ("format", "content", "both"):
                    ok, rep = verify(old, new, scope)
                    self.assertFalse(ok, (scope, rep))
                    finding = next(h for h in rep["hard_failures"] if h["kind"] == expected)
                    self.assertTrue(finding.get("missing"), finding)
                    self.assertTrue(finding["missing"][0].get("lines") or
                                    finding["missing"][0].get("old_lines"), finding)

    def test_verify_repeated_code_and_inline_values_keep_counts(self):
        code = "```bash\nprintf 'ok'\n```"
        old = f"# T\n\n{code}\n\n{code}\n"
        new = f"# T\n\n{code}\n"
        for scope in ("format", "content", "both"):
            with self.subTest(scope=scope):
                ok, rep = verify(old, new, scope)
                self.assertFalse(ok)
                finding = next(h for h in rep["hard_failures"] if h["kind"] == "code_block_missing")
                self.assertEqual(finding["missing"][0]["count"], 1)
                self.assertEqual(finding["missing"][0]["lines"], [3, 7])

        old = "# T\n\n`maxEntries` 与 `maxEntries` 都要保留。\n"
        new = "# T\n\n`maxEntries` 要保留。\n"
        ok, rep = verify(old, new, "content")
        self.assertFalse(ok)
        finding = next(h for h in rep["hard_failures"] if h["kind"] == "inline_literals_missing")
        self.assertEqual(finding["items"][0]["count"], 1)
        self.assertEqual(finding["items"][0]["old_lines"], [3, 3])

        old = "# T\n\nmaxEntries appears twice: maxEntries.\n"
        new = "# T\n\nmaxEntries appears once.\n"
        ok, rep = verify(old, new, "content")
        self.assertFalse(ok)
        finding = next(h for h in rep["hard_failures"] if h["kind"] == "protected_literals_missing")
        self.assertEqual(finding["missing"][0]["type"], "identifier")
        self.assertEqual(finding["missing"][0]["value"], "maxEntries")
        self.assertEqual(finding["missing"][0]["count"], 1)

    def test_verify_allows_backticks_and_moving_literal_into_code(self):
        old = "# T\n\n用 maxEntries 选项；命令是 `--timeout`。\n"
        wrapped = "# T\n\n用 `maxEntries` 选项；命令是 `--timeout`。\n"
        self.assertTrue(verify(old, wrapped, "format")[0])

        old = "# T\n\n执行 `--timeout` 并访问 ../config/app.yaml。\n"
        new = "# T\n\n执行下面的命令：\n\n```sh\ncli --timeout\n```\n\n配置在 ../config/app.yaml。\n"
        for scope in ("content", "both"):
            with self.subTest(scope=scope):
                ok, rep = verify(old, new, scope)
                self.assertTrue(ok, rep)

    def test_verify_numeric_units_and_scope_policy(self):
        old = "# T\n\n限制为 2 MB。\n"
        self.assertTrue(verify(old, "# T\n\n限制为 2MB。\n", "format")[0])
        changed_unit = "# T\n\n限制为 2 GB。\n"
        ok, rep = verify(old, changed_unit, "format")
        self.assertFalse(ok)
        finding = next(h for h in rep["hard_failures"] if h["kind"] == "numeric_literals_changed")
        self.assertEqual(finding["missing"][0]["value"], "2MB")
        self.assertEqual(finding["added"][0]["value"], "2GB")

        ok, rep = verify(old, changed_unit, "content")
        self.assertFalse(ok)
        self.assertEqual(rep["status"], "unknown")
        self.assertEqual(rep["warnings"][0]["kind"], "numeric_literals_changed")

        old = "# T\n\n请求最多等待 30 seconds。\n"
        new = "# T\n\n请求最多等待 30 minutes。\n"
        ok, rep = verify(old, new, "both")
        self.assertFalse(ok)
        self.assertEqual(rep["status"], "unknown")
        self.assertEqual(rep["warnings"][0]["missing"][0]["value"], "30seconds")
        self.assertEqual(rep["warnings"][0]["added"][0]["value"], "30minutes")

    def test_verify_reports_cli_status_codes_for_fail_and_unknown(self):
        import contextlib
        import io
        import tempfile
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as temp:
            old = Path(temp) / "old.md"
            new = Path(temp) / "new.md"
            old.write_text("# T\n\n`--timeout`\n", encoding="utf-8")
            new.write_text("# T\n\n`--timeoutExtra`\n", encoding="utf-8")
            args = SimpleNamespace(old=str(old), new=str(new), scope="content", json=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cmd_verify(args), 3)
            old.write_text("# T\n\n<details>\n<summary>Options</summary>\nOriginal.\n</details>\n",
                           encoding="utf-8")
            new.write_text("# T\n\n<details>\n<summary>Options</summary>\nOriginal!\n</details>\n",
                           encoding="utf-8")
            args.scope = "format"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cmd_verify(args), 4)
            old.write_text("# T\n\n## A\n\nAlpha.\n\n## B\n\nBeta.\n", encoding="utf-8")
            new.write_text("# T\n\n## B\n\nBeta.\n\n## A\n\nAlpha.\n", encoding="utf-8")
            args.scope = "format"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(cmd_verify(args), 0)
            self.assertIn("[提示] blocks_reordered", output.getvalue())
            self.assertIn("指代", output.getvalue())

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

    def test_score_matches_independent_weight_caps_and_global_cap(self):
        two_paragraph_hits = [Finding("P1", line, "手算样例", "F") for line in (2, 4)]
        score_two = score(two_paragraph_hits)
        self.assertEqual(score_two["dims"]["chunk"]["score"], 84.0)
        self.assertEqual(score_two["total"], 97.1)  # 100 - 16 × 18%

        many_paragraph_hits = [Finding("P1", line, "手算封顶", "F") for line in range(10)]
        score_capped = score(many_paragraph_hits)
        self.assertEqual(score_capped["dims"]["chunk"]["score"], 40.0)
        self.assertEqual(score_capped["total"], 89.2)  # 100 - 60 × 18%

        global_hits = [Finding(rule, 1, "手算全局扣分", "F") for rule in
                       ("X1p", "X1c", "X2", "X5", "X3", "X6")]
        score_global = score(global_hits, det_only=False)
        self.assertEqual(score_global["x_hits"], {
            "X1p": 8, "X1c": 5, "X2": 8, "X5": 6, "X3": 5, "X6": 5,
        })
        self.assertEqual(score_global["x_deduct"], 20)
        self.assertEqual(score_global["total"], 80.0)

    def test_full_score_includes_model_findings_and_band_boundaries(self):
        model_hit = [Finding("H3", 1, "手工判断", "C")]
        self.assertEqual(score(model_hit, det_only=True, level=3)["total"], 100.0)
        complete = score(model_hit, det_only=False, level=3)
        self.assertEqual(complete["total"], 97.3)
        self.assertEqual(complete["band"], "优")
        self.assertIn("H3", score(model_hit, det_only=True, level=3)["unscored"])
        self.assertEqual(
            [band(value) for value in (90, 89.9, 80, 79.9, 60, 59.9, 40, 39.9)],
            ["优", "好", "好", "可用但吃力", "可用但吃力", "需重构", "需重构", "差"],
        )

    def test_deep_rule_is_filtered_by_source_level(self):
        src = "# 标题\n\n结论。\n\n## 细节\n\n这是的的的测试句。\n"
        by_level = {
            level: {finding.rule for finding in audit(Doc(src), level=level)}
            for level in (1, 2, 3)
        }
        self.assertNotIn("C5", by_level[1])
        self.assertNotIn("C5", by_level[2])
        self.assertIn("C5", by_level[3])

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

    def test_m11_14_catch_chinese_advertising(self):
        # 中文广告腔：空泛量词、连续连接词、无数字宣称、从句堆叠
        cases = {
            "M11": "我们进行了大量的实验测试，验证了方案的有效性。",
            "M12": "方案A更快。此外它更简单。此外它还能扩展。",
            "M13": "该方案显著提升了整体性能。",
            "M14": "随着数据量增长，从而需要更多算力，进而推高成本。",
        }
        for rule, sentence in cases.items():
            d = Doc(f"# T\n\n结论。\n\n## 细节\n\n{sentence}\n")
            self.assertIn(rule, {fd.rule for fd in audit(d)}, f"{rule} 没抓到：{sentence}")

    def test_m13_allows_number_backed_claims(self):
        d = Doc("# T\n\n结论。\n\n## 细节\n\n处理时间显著提升 40%。\n")
        self.assertNotIn("M13", {fd.rule for fd in audit(d)})

    def test_m11_12_14_no_false_positive_on_plain_chinese(self):
        plain = ("# T\n\n结论。\n\n## 细节\n\n"
                 "缓存默认开启，关掉要改配置并重启。重启会中断正在处理的请求，建议低峰期操作。\n"
                 "参数有三个：ttl、maxEntries 和 strategy。相对上一版，默认值没变。\n"
                 "处理结果通过 API 返回，同时写入日志。\n")
        hits = [fd.rule for fd in audit(Doc(plain)) if fd.rule in ("M11", "M12", "M13", "M14")]
        self.assertEqual(hits, [], f"误报：{hits}")

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
               "`核心是：` 这类预告式冒号同理。\n")
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
        # 「结论：」「参数：」是字段标签，不是预告式冒号
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
        """示例语料是回归门禁：核对评分与预期的 verify 三态。"""
        ex = Path(__file__).resolve().parent.parent / "references" / "examples"
        if not ex.is_dir():
            self.skipTest("examples 目录不存在")
        cases = {
            "01-zh-notes": ("both", 3, 95, "unknown"),  # 含原始 details HTML
            "02-zh-readme": ("format", 2, 95, "unknown"),  # 有顺序变化
            "03-en-runbook": ("both", 2, 95, "pass"),
            # 04 是 format+light，写不了 TL;DR，88 分就是正确结果
            "04-en-reference": ("format", 1, 85, "pass"),
        }
        for name, (scope, level, floor, expected_status) in cases.items():
            bf, af = ex / f"{name}.before.md", ex / f"{name}.after.md"
            self.assertTrue(bf.is_file() and af.is_file(), f"{name} 缺文件")
            before, after = bf.read_text(encoding="utf-8"), af.read_text(encoding="utf-8")
            sb = score(audit(Doc(before), level=level))
            sa = score(audit(Doc(after), level=level))
            self.assertGreater(sa["total"], sb["total"], f"{name} 分数没提升")
            self.assertGreaterEqual(sa["total"], floor, f"{name} after 低于 {floor}")
            self.assertEqual(sa["x_deduct"], 0, f"{name} after 有反模式扣分 {sa['x_hits']}")
            ok, rep = verify(before, after, scope)
            self.assertEqual(rep["status"], expected_status,
                             f"{name} verify({scope}) 状态异常：{rep}")
            self.assertEqual(ok, expected_status == "pass")


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

    p = sub.add_parser("verify", help="检查已支持的不变量；返回通过、失败或无法判断")
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
    p.add_argument("--json", action="store_true", help="以 JSON 输出 before/after、覆盖率和 verify 结果")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("init", help="生成文档骨架")
    p.add_argument("--type", required=True, choices=sorted(SKELETONS))
    p.set_defaults(fn=cmd_init)

    def source_arguments(parser, output_help):
        parser.add_argument("file", help="Markdown / 文本 / HTML / PDF 文件，或 HTTP(S) 网址；- 读取标准输入")
        parser.add_argument("-o", "--output", help=output_help)
        parser.add_argument("--timeout", type=float, default=20, help="网页请求整体及每次 PDF/OCR 工具调用的超时秒数；不限制本地解析（默认 20）")
        parser.add_argument("--ocr", choices=["auto", "never", "always"], default="auto", help="PDF OCR：无文字页自动识别 / 不识别 / 所有页识别")
        parser.add_argument("--ocr-lang", help="Tesseract 语言，如 chi_sim+eng；默认使用已安装的中英文语言")

    p = sub.add_parser("read", help="自动提取并生成离线阅读页，或输出陪读分段 JSON")
    source_arguments(p, "HTML 输出路径（默认 <原名>.reader.html，不覆盖已有文件）")
    p.add_argument("--chunk-size", type=int, default=900, help="每段目标字符数，完整代码块等可以超出（默认 900）")
    p.add_argument("--json", action="store_true", help="只输出原文、分段和源位置，供 AI 陪读使用")
    p.set_defaults(fn=cmd_read)

    p = sub.add_parser("extract", help="自动提取网页 / PDF 正文，保存 Markdown 或输出 JSON")
    source_arguments(p, "Markdown 输出路径（默认 <原名>.extracted.md，不覆盖已有文件）")
    p.add_argument("--json", action="store_true", help="输出正文和提取来源信息，不写文件")
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("selftest", help="自检")
    p.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
