I'll start by reading the skill and the input file.

Now let me explore the skill's scripts and references.

Not a git repo; the task specifies writing to `output.md` anyway. Let me read the required references and run the audit.

Now let me run the audit and read the matching English reference example plus doc-types.

`fmt` already reports no changes needed. Let me inspect the rule definitions and audit JSON to pin down exactly which judge rules apply at deep·format.

Let me check an English example for list-conversion style conventions.

Now I'll write the reformatted output: split at existing sentence boundaries to isolate the exception and the restart requirement, and reuse the two parallel unit clauses as a list (format-axis moves only, no wording changes).

Compound commands are blocked; I'll run each individually.

Verify exits 0 (the probe confirms non-zero exits surface as errors). Now the report:

Verify passes cleanly. Now let me confirm at character level exactly what changed:

The two `False` results are artifacts of my regex capturing the new `-` list markers as tokens. Let me redo the comparison correctly:

Let me capture the exact exit codes for all four commands in one shot:

All checks are green. Here is the report.

## 改完了：input.md → output.md

**scope** `format` · **level** `deep`（`deep` → 脚本档位 3）· 写到 `output.md`

写出位置说明：工作区不是 git 仓库（`git status` → `fatal: not a git repository`），按 skill 第 0 步本应写 `<原名>.adhd.md`；本次按任务要求写 `output.md`，`input.md` 未改动（sha256 前缀 `6374a44faee4d2ec`，与写入前一致）。

### 脚本分与退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | `0` | 100.0 / 100 |
| `audit output.md --level 3 --scope=format` | `0` | 100.0 / 100 |
| `verify input.md output.md --scope=format` | `0` | `status=pass`（`ok:true`，`hard_failures:[]`，`warnings:[]`，`unknowns:[]`） |
| `report input.md output.md --scope=format --level 3` | `0` | 见下表 |

脚本分 **100.0 → 100.0（+0.0）**

| 维度 | 权重 | before | after | delta |
|---|---:|---:|---:|---:|
| 首屏结论力 | 18% | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 18% | 100.0 | 100.0 | +0.0 |
| 扫读性 | 13% | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 13% | 100.0 | 100.0 | +0.0 |
| 行动性 | 12% | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 13% | 100.0 | 100.0 | +0.0 |
| 活人感 | 13% | 100.0 | 100.0 | +0.0 |

**反模式扣分（X 组脚本项）−0 → −0**，`x_hits` 为空。**findings(format) 0 → 0**（全文 0 → 0）。

分数没动，是因为原文在所有**脚本可判**轴（23 条）上本来就满分；我改的是脚本判不了的 judge 轴（P2、L2）。**100 分只是脚本分**：deep·format 下有 10 条规则纯靠模型判断，脚本按未命中计分，未判定不等于通过（`report` 原文：「分数不是越高越好」）。

### verify 结论

`verify --scope=format` **通过**，退出码 0，无硬失败、无警告、无 `unknown`。检查覆盖：代码块正文逐字与重复次数、行内代码值、数字与单位、大小写敏感标识符、链接目标、frontmatter、块级结构映射。**`pass` 只表示已声明的不变量成立，不是语义等价证明**；句内语序、指代仍需人工复核（本次改动不涉及句内换序，见下）。

我自己另做的字符级核对（比 verify 更严）：
- 词/代码 token 序列（剥标点后）：**102 → 102，逐位完全相同**，无增删、无换序。
- 剥空白后比对：**完全相同**，唯一差异是 1 个 `;`→`.`。
- 字符增量账本：`\n +5`、`- +2`（列表标记）、`; −1`、`. +1`、空格 `−1`。除此之外零改动。
- 数字序列（`45/5/600/3/1/8/400/100/5000/8/1/20/4/800/1/401/403`）排序后完全一致；``` 围栏 2→2；YAML 代码块逐字未动；表格 4 行 × 4 列逐字未动。

### 改了什么（全部为 format 轴操作，零改词）

1. **在已有句界拆段** —— `maxAttempts` 段拆成两段，把「Authentication errors (`401` and `403`) are never retried…」这条**例外**单独成段。原文 3 句挤一段，例外埋在句尾，最容易漏读。
2. **在已有句界拆段** —— 末段拆成两段：「Configuration changes take effect after the worker restarts.」这条运维前提单独成段。
3. **并列句转列表（复用原句）** —— `visibilitySeconds` is measured in seconds; `backoffMs` is measured in milliseconds. → 两项列表，词序与用词逐字保留。分号是全文唯一的标点改动（`;`→`.`），使两项各自收尾；这是 format 允许的标点规范，如不接受可把两项合回一行。

`fmt input.md` 预览为「格式已规范，无需修改」，故无确定性修复可写回。

### judge 规则逐条判定

**范围内（deep·format 的 10 条 judge_only）**

| ID | 判定 | 位置 | 理由 |
|---|---|---|---|
| S5 答案块前置 | 满足 | 表格位于 H1 后首个块 | 参考文档的速查表就是答案面，已在最前；其后无「结论段」可搬。任务要求保留信息顺序，故不做块重排 |
| S6 符合类型骨架 | 满足 | 全文 | 参考骨架要求「速查表放最前」，已满足；无 H2 小节，不存在章节顺序违规。骨架里的「一句话职责」需新写句子 = content，受 scope 限制未加 |
| P2 一段只讲一件事 | **不满足 → 满足** | 原第 2、3 段 | 原两段各含话题转折（设置语义→例外；重启前提→单位），已各拆为独立段落 |
| P5 超长引用块 | 不适用 | — | 全文 0 处 `>` 引用块 |
| L2 并列句转列表 | **不满足 → 满足** | 末段 | 分号并列的单位说明已转列表，复用原词 |
| N4 可选内容折叠 | 不适用 | — | 无偏离主路径的块：表格是主查表面，YAML 示例与单位说明都在主路径上；折叠即命中 X7 |
| T3 标记语义一致 | 满足 | 全文 | 行内代码全部用于字面量（设置名/数值/状态码）；全文无加粗、无斜体，无混用 |
| X3 剩词不剩句 | 满足 | 新增 2 个列表项 | 两项均主谓完整、可独立读懂；表格单元格同为完整短语 |
| X6 表格滥用 | 满足 | 表格 | 同构可对比数据（设置/默认/范围/行为），单元格 7–8 词，无因果叙述塞入 |
| X7 折叠滥用 | 满足 | 全文 | 未使用 `<details>`，未折叠任何内容 |

**范围外（content 轴，scope=format 下不适用）**：S4、S8、H3、H4、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N7、C4 —— 共 21 条一律记 **不适用（scope 限制）**，不记为通过。其中需点名的：**H4**（无时间/篇幅预估，加一句即新写措辞）、**A7**（YAML 块后无预期输出，补预期即编造事实）、**A8**（原文无复合步骤可拆）、**N7**（全文无 ≥4 步流程，无进度可标）。这几条要达标必须开 `content`，且 A7 在无来源时只能记「未满足」而非补事实。

**硬门禁**：X4 删信息 —— **满足**，`verify` 无 `hard_failures`。

### 故意没改

- **没做块重排**：任务要求保留信息顺序，且 S5 无合格搬移对象（速查表已在最前），format 的块重排能力在此无收益、只有悬空指代风险。
- **没加任何加粗**：T2/X5 是上限不是指标；全文术语已统一用行内代码标记，加粗会引入第二套标记语义（违反 T3）。0% 加粗是刻意选择。
- **没加 TL;DR / 时间预估 / 下一步 / 预期输出 / 小标题**：这五项全是 content 轴（H1、H4、A1、A7、S8），format 下加一个字就是越界 —— 这正是本例 100 分却不代表「全规则通过」的原因。
- **没折叠任何内容**：18 行文档里没有偏离主路径的块，折叠主路径内容即 X7。
- **没加分割线 / TOC**：N3 要有 H2 才谈得上分节，N1 门槛是 >80 行（本文 18 行），均不适用。
- **没动表格、YAML 代码块、H1、链接与标识符**：逐字保留。

All checks are green. Here is the report.

## 改完了：input.md → output.md

**scope** `format` · **level** `deep`（`deep` → 脚本档位 3）· 写到 `output.md`

写出位置说明：工作区不是 git 仓库（`git status` → `fatal: not a git repository`），按 skill 第 0 步本应写 `<原名>.adhd.md`；本次按任务要求写 `output.md`，`input.md` 未改动（sha256 前缀 `6374a44faee4d2ec`，与写入前一致）。

### 脚本分与退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | `0` | 100.0 / 100 |
| `audit output.md --level 3 --scope=format` | `0` | 100.0 / 100 |
| `verify input.md output.md --scope=format` | `0` | `status=pass`（`ok:true`，`hard_failures:[]`，`warnings:[]`，`unknowns:[]`） |
| `report input.md output.md --scope=format --level 3` | `0` | 见下表 |

脚本分 **100.0 → 100.0（+0.0）**

| 维度 | 权重 | before | after | delta |
|---|---:|---:|---:|---:|
| 首屏结论力 | 18% | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 18% | 100.0 | 100.0 | +0.0 |
| 扫读性 | 13% | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 13% | 100.0 | 100.0 | +0.0 |
| 行动性 | 12% | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 13% | 100.0 | 100.0 | +0.0 |
| 活人感 | 13% | 100.0 | 100.0 | +0.0 |

**反模式扣分（X 组脚本项）−0 → −0**，`x_hits` 为空。**findings(format) 0 → 0**（全文 0 → 0）。

分数没动，是因为原文在所有**脚本可判**轴（23 条）上本来就满分；我改的是脚本判不了的 judge 轴（P2、L2）。**100 分只是脚本分**：deep·format 下有 10 条规则纯靠模型判断，脚本按未命中计分，未判定不等于通过（`report` 原文：「分数不是越高越好」）。

### verify 结论

`verify --scope=format` **通过**，退出码 0，无硬失败、无警告、无 `unknown`。检查覆盖：代码块正文逐字与重复次数、行内代码值、数字与单位、大小写敏感标识符、链接目标、frontmatter、块级结构映射。**`pass` 只表示已声明的不变量成立，不是语义等价证明**；句内语序、指代仍需人工复核（本次改动不涉及句内换序，见下）。

我自己另做的字符级核对（比 verify 更严）：
- 词/代码 token 序列（剥标点后）：**102 → 102，逐位完全相同**，无增删、无换序。
- 剥空白后比对：**完全相同**，唯一差异是 1 个 `;`→`.`。
- 字符增量账本：`\n +5`、`- +2`（列表标记）、`; −1`、`. +1`、空格 `−1`。除此之外零改动。
- 数字序列（`45/5/600/3/1/8/400/100/5000/8/1/20/4/800/1/401/403`）排序后完全一致；``` 围栏 2→2；YAML 代码块逐字未动；表格 4 行 × 4 列逐字未动。

### 改了什么（全部为 format 轴操作，零改词）

1. **在已有句界拆段** —— `maxAttempts` 段拆成两段，把「Authentication errors (`401` and `403`) are never retried…」这条**例外**单独成段。原文 3 句挤一段，例外埋在句尾，最容易漏读。
2. **在已有句界拆段** —— 末段拆成两段：「Configuration changes take effect after the worker restarts.」这条运维前提单独成段。
3. **并列句转列表（复用原句）** —— `visibilitySeconds` is measured in seconds; `backoffMs` is measured in milliseconds. → 两项列表，词序与用词逐字保留。分号是全文唯一的标点改动（`;`→`.`），使两项各自收尾；这是 format 允许的标点规范，如不接受可把两项合回一行。

`fmt input.md` 预览为「格式已规范，无需修改」，故无确定性修复可写回。

### judge 规则逐条判定

**范围内（deep·format 的 10 条 judge_only）**

| ID | 判定 | 位置 | 理由 |
|---|---|---|---|
| S5 答案块前置 | 满足 | 表格位于 H1 后首个块 | 参考文档的速查表就是答案面，已在最前；其后无「结论段」可搬。任务要求保留信息顺序，故不做块重排 |
| S6 符合类型骨架 | 满足 | 全文 | 参考骨架要求「速查表放最前」，已满足；无 H2 小节，不存在章节顺序违规。骨架里的「一句话职责」需新写句子 = content，受 scope 限制未加 |
| P2 一段只讲一件事 | **不满足 → 满足** | 原第 2、3 段 | 原两段各含话题转折（设置语义→例外；重启前提→单位），已各拆为独立段落 |
| P5 超长引用块 | 不适用 | — | 全文 0 处 `>` 引用块 |
| L2 并列句转列表 | **不满足 → 满足** | 末段 | 分号并列的单位说明已转列表，复用原词 |
| N4 可选内容折叠 | 不适用 | — | 无偏离主路径的块：表格是主查表面，YAML 示例与单位说明都在主路径上；折叠即命中 X7 |
| T3 标记语义一致 | 满足 | 全文 | 行内代码全部用于字面量（设置名/数值/状态码）；全文无加粗、无斜体，无混用 |
| X3 剩词不剩句 | 满足 | 新增 2 个列表项 | 两项均主谓完整、可独立读懂；表格单元格同为完整短语 |
| X6 表格滥用 | 满足 | 表格 | 同构可对比数据（设置/默认/范围/行为），单元格 7–8 词，无因果叙述塞入 |
| X7 折叠滥用 | 满足 | 全文 | 未使用 `<details>`，未折叠任何内容 |

**范围外（content 轴，scope=format 下不适用）**：S4、S8、H3、H4、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N7、C4 —— 共 21 条一律记 **不适用（scope 限制）**，不记为通过。其中需点名的：**H4**（无时间/篇幅预估，加一句即新写措辞）、**A7**（YAML 块后无预期输出，补预期即编造事实）、**A8**（原文无复合步骤可拆）、**N7**（全文无 ≥4 步流程，无进度可标）。这几条要达标必须开 `content`，且 A7 在无来源时只能记「未满足」而非补事实。

**硬门禁**：X4 删信息 —— **满足**，`verify` 无 `hard_failures`。

### 故意没改

- **没做块重排**：任务要求保留信息顺序，且 S5 无合格搬移对象（速查表已在最前），format 的块重排能力在此无收益、只有悬空指代风险。
- **没加任何加粗**：T2/X5 是上限不是指标；全文术语已统一用行内代码标记，加粗会引入第二套标记语义（违反 T3）。0% 加粗是刻意选择。
- **没加 TL;DR / 时间预估 / 下一步 / 预期输出 / 小标题**：这五项全是 content 轴（H1、H4、A1、A7、S8），format 下加一个字就是越界 —— 这正是本例 100 分却不代表「全规则通过」的原因。
- **没折叠任何内容**：18 行文档里没有偏离主路径的块，折叠主路径内容即 X7。
- **没加分割线 / TOC**：N3 要有 H2 才谈得上分节，N1 门槛是 >80 行（本文 18 行），均不适用。
- **没动表格、YAML 代码块、H1、链接与标识符**：逐字保留。
