---
name: adhd-md
description: 把 Markdown 文档改造成 ADHD 友好、可扫读的版本，可选择只改格式、只改内容或两者兼改，并用脚本校验没有丢信息。Use when the user asks to make a document ADHD-friendly, more skimmable, or easier to read; when they say 文档太长看不下去 / 排版太密 / 全是大段文字 / 帮我把这个文档改得好读一点 / 优化一下排版; or asks to audit, lint, or restructure Markdown for readability. Triggers include ADHD friendly, ADHD 友好, 注意力友好, 可扫读, skimmable, wall of text, 文字墙, 大段文字, 改排版, 重排文档, make this readable.
---

# adhd-md

把 Markdown 改造成 ADHD 友好的样子：结论前置、段落切碎、句子变短、动作明确、噪音归零。

**铁律：只重排信息，绝不删信息。** 篇幅太长就折叠或移到附录，不许删。违反这条，其他做得再好都是失败。

## 什么时候用

用户给了一个 Markdown 文件（或一段 Markdown），希望它更好读、更好扫、更适合注意力容易断的人。

不适用的情况：
- 输入不是 Markdown（先转换，或直接拒绝）
- 用户要的是**内容审查**（事实核查、逻辑校对）—— 那不是这个 skill
- 用户要的是**翻译**或**扩写** —— 都不是

## 两个参数

### scope：改什么

| 值 | 边界 | 用户会怎么说 |
|---|---|---|
| `format` | 正文词序列逐字不变，只动标记、空白、块顺序 | 只改格式 / 只调样式 / 别动我的字 / 排版优化 |
| `content` | 只改措辞与信息组织，不碰排版风格 | 只改内容 / 句子太长 / 帮我改写 |
| `both`（默认） | 全都改 | 优化一下 / 改成 ADHD 友好 |

划线判据：**搬移已有块算 format，写出新句子算 content。**

把结论段整块搬到开头 = format。新写一段 TL;DR = content。

### level：改多狠

| 值 | 适用 | 会做什么 |
|---|---|---|
| `light` | 规范、合同、API 文档，怕动 | 只做零风险项，不重排顺序 |
| `standard`（默认） | README、教程、设计文档 | 拆段、列表化、改标题、写 TL;DR、块重排 |
| `deep` | 会议记录、长文、堆积的笔记 | 全量重构骨架、渐进披露、生成 checklist |

用户没说就用 `both` + `standard`，并在报告开头一句话说明用了什么档，让人能反悔。

## 工作流

### 第 0 步 · 决定写哪里

```bash
git -C <文档所在仓库> status --porcelain <文件>
```

- 仓库干净 → **原地改**，用户用 `git diff` 审阅
- 有未提交改动，或不在 git 里 → 写到 `<原名>.adhd.md`，并告诉用户为什么

绝不在有未提交改动的文件上原地覆盖。

### 第 1 步 · 审计

```bash
python3 <skill>/scripts/adhd_md.py audit 文件.md --level 2
```

拿到脚本分、逐条 findings（带 `文件:行`）、以及需要你判断的规则清单。

**先读输出再动手。** 不要凭印象改 —— 脚本已经把能算准的都算了。

### 第 2 步 · 确定性格式修复

```bash
python3 <skill>/scripts/adhd_md.py fmt --write 文件.md
```

零风险、不需要你判断：行尾空白、有序列表序号、块间空行、中英文间距、中文标点。

`scope=content` 时跳过这一步。

可选开关：`--toc`（按已有标题生成目录）、`--join-cjk`（合并中文软换行）、`--strip-emoji`（删 emoji，注意这会改动字符）。

### 第 3 步 · 你来改

读 `references/rules.md`，按 scope 过滤出生效的规则子集，逐条改。

顺序：**先 content 再 format**。措辞定了，排版决策才稳。

改之前必读：
- `references/rules.md` —— 规则全表，含阈值
- `references/antipatterns.md` —— 八种过度优化，**这个必读**
- `references/cjk.md` —— 文档是中文时读
- `references/doc-types.md` —— 只在 `level=deep` 需要重排骨架时读

### 第 4 步 · 校验

```bash
python3 <skill>/scripts/adhd_md.py verify 原文.md 新文.md --scope=format
python3 <skill>/scripts/adhd_md.py report 原文.md 新文.md --scope=<scope>
```

`scope=format` 时 verify 是**硬门禁**：token 序列必须完全一致。不通过就回退，不许放行。

`scope=content` 或 `both` 时 verify 检查不变量：代码块、行内代码、URL、标识符、数字。任何硬失败都要修到通过。

原地改时先留一份原文到临时文件，否则没法 verify：

```bash
cp 文件.md /tmp/adhd-orig.md   # 改之前
```

### 第 5 步 · 报告

必须包含四项：

1. 用了什么 scope 与 level
2. 脚本分 before → after，逐维度 delta
3. verify 结论（通过 / 失败及原因）
4. **你改了什么、以及故意没改什么**

反模式扣分（X 组）after 必须为 0。不为 0 说明你是靠过度格式化换分数，回退重来。

**AI 味（M 组）命中数只许下降，不许上升。** 你改写内容时最容易顺手写出「不是 A 而是 B」「值得注意的是」，等于用一套问题换掉另一套。改完对比 `audit` 的活人感维度。

## 三种 scope 的 do / don't

### scope=format

**能做**：在已有句界拆段 · 并列句转列表（复用原词）· 加粗已有关键术语 · 补空行分割线 · 代码块补语言标签 · 标题层级修正 · 列表降嵌套 · `<details>` 折叠（summary 复用已有标题文字）· 由已有标题生成 TOC · 块顺序重排 · 中英文间距与标点规范

**不能做**：改任何一个词 · 新写 TL;DR · 改写标题措辞 · 补时间预估 · 补下一步动作 · 删填充词

**块重排的陷阱**：把结论块搬到开头后，扫一遍被搬走的块里有没有「这个方案」「上述配置」「它」这类**悬空指代**。修指代要改词，属于 content —— 所以 `scope=format` 下检出悬空指代时，**放弃这次搬移**，在报告里记「需 content 权限才能安全前置」。

### scope=content

**能做**：长句拆短 · 被动改主动 · 结论前置改写 · 新写 TL;DR · 标题改成结论式 · 补时间预估与下一步 · 术语首现解释 · 删填充词与虚词壳 · 拆括号插入语 · 消灭「如上所述」· **洗掉 AI 味**（翻案腔、预告式冒号、装深刻的话、黑话、名词化）

**不能做**：改排版风格（不新增标题层级、不改列表形态、不动折叠结构）· 也不能借「精简」之名删约束条件、单位、版本号、例外情况

### scope=both

先 content 再 format，最后统一 verify。默认档。

## 没有 shell 的宿主怎么办

拿不到 Bash / 命令执行时：

1. 跳过 audit / fmt / verify，按 `references/rules.md` 人工过一遍
2. 用 `references/antipatterns.md` 末尾的自检清单逐条自查
3. **在报告里明确写「未做机器校验」** —— 不许假装跑过脚本

假装跑过校验，比不校验更糟。

## 输出契约

改完给用户的报告，照这个格式：

```markdown
## 改完了：<文件名>

**scope** `both` · **level** `standard` · 写到 `原地`（git 干净）

脚本分 62.4 → 88.1（+25.7）

| 维度 | before | after |
|---|---|---|
| 首屏结论力 | 40 | 100 |
| …… | | |

**verify(both)** 通过 —— 代码块、URL、标识符、数字全部保全

**改了什么**
- 把最后一段的结论整块搬到开头（format）
- 12 个超长句拆成 28 句（content）
- 3 处「如上所述」就地重述（content）

**故意没改**
- `## API 参数` 一节保持原样：参考类内容需要跳读，重排会破坏定位
- 两处 92 字长句保留：拆开会切断因果关系
```

「故意没改」这一节不许省。它让用户知道你是判断过的，不是漏了。

## 参考文件索引

| 文件 | 什么时候读 |
|---|---|
| `references/rules.md` | 每次都读。规则全表 + 阈值 + 轴/档标记 |
| `references/antipatterns.md` | 每次都读。八种过度优化 + 自检清单 |
| `references/rubric.md` | 需要解释分数、或要手工补 judge 项评分时 |
| `references/cjk.md` | 文档是中文 |
| `references/doc-types.md` | `level=deep` 且要重排整体骨架 |

## 常见错误

| 错误 | 后果 |
|---|---|
| 把脚本分说成最终分 | 33 条规则按满分计入，虚高。必须说明这是脚本分 |
| `scope=format` 却改了词 | verify 硬失败。回退 |
| 以「精简」为名删内容 | 违反铁律。折叠或移附录，不删 |
| 改写时写出「不是 A 而是 B」 | M1 翻案腔。直接从正面下判断 |
| 加 emoji 当锚点 | X1 扣分。用 `> **注意**`、表格、分割线 |
| 切成一堆两行小节 | X2 碎片化扣分 |
| 列表项砍成关键词 | X3 剩词不剩句扣分 |
| 说跑了校验其实没跑 | 诚信问题，比不校验严重 |
