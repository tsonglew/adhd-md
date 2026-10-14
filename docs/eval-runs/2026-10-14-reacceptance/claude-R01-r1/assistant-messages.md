I'll start by reading the skill and the input document.

Now let me check the lint patterns for the rules that could trip on my rewrite, then write the output.

Not a git repo, so per the skill's step 0 I'll write to a separate `output.md`. Now writing the edited document:

Done. `input.md` is untouched; the rewrite is in `output.md`. Here is the report.

## 改完了：`output.md`（源文件 `input.md`）

**scope** `content` · **level** `deep` · 写到**新文件** `output.md` —— 第 0 步 `git status` 返回 `fatal: not a git repository`，不在 git 里，按规则不原地覆盖。`fmt` 步骤按 `scope=content` 跳过。

脚本分 **87.8 → 100.0（+12.2）**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | 0 |
| 句子负荷 | 100.0 | 100.0 | 0 |
| 行动性 | 100.0 | 100.0 | 0 |
| 排版一致性 | 100.0 | 100.0 | 0 |
| 活人感 | 100.0 | 100.0 | 0 |
| X 组扣分 | −0 | −0 | 0 |

before 的 findings：`H1`（input.md:1，content 轴）+ `P1`（input.md:3，4 句 / 30 单位，超 3 句上限，F 轴）；after：0 条。

**校验结论**

| 命令 | 结果 |
|---|---|
| `verify --scope=content` | **通过**（无硬失败、无警告、无 unknown） |
| `verify --scope=both` | **通过** |
| `verify --scope=format` | **失败（预期内，非缺陷）**：`prose_tokens_missing` / `prose_tokens_added`。format 门禁是**词元多重集相等**——任何 content 改写都必然触发。本次声明 scope 是 content，以 content/both 结论为准；这里如实列出，不当作通过。 |

`pass` 只覆盖已声明的机器检查（代码块、链接、行内字面值、选项、路径、数字、X4），**不是语义等价证明**；句内语义与人工判断项见下表。

---

### 改了什么（全部为 content 轴）

1. **H1 标题改结论式**：`# Thumbnail recovery` → `# Retry a failed thumbnail job`（output.md:1）。标题文字属于措辞，scope=content 允许改写（SKILL 第 3 步判据第 4 条）。
2. **新写首屏 TL;DR 段落**（output.md:3）：`Retry one failed thumbnail job in 4 steps.` —— 一句话，1 句 / 9 词，落在 H1 首段判据内（≤3 句且 ≤40 词）。信息全部是重述原文 + 可从原文数出的步数。
3. **原首段拆成两块**：结论句独立成段，三条约束独立成段（output.md:5）。原文首段 4 句同时触发 H1 与 P1；拆开后两项都消除，且**没有新增标题层级、没有改列表形态**——新块用的是文档里已有的段落类型（"摘要用现有段落风格"）。
4. **复合步骤项内分句**（不新增列表项）：
   - `Open the job panel and select a failed job.` → `Open the job panel. Select a failed job.`（output.md:7）
   - `If its lock is active, wait 7 minutes and reload the panel once.` → `If the job's lock is active, wait 7 minutes. After the wait, reload the panel once.`（output.md:8）——条件仍控制两个子动作，先后顺序保留，刷新**没有**变成无条件步骤；`its` → `the job's` 只为消除悬空指代。
5. **N7 进度标注**：4 步 ≥ 阈值，每项前加 `Step X of 4:`（output.md:7–10），用普通文字表达（不能改列表形态/加复选框）。
6. **A7 部分补预期输出**：`A successful request shows status accepted.` 从结尾段移到第 4 步项内（output.md:10），这是原文**已有**的成功信号，不是新造的界面行为。
7. **结尾段收窄为一件事**（output.md:12）：`Status accepted does not mean the thumbnail has finished rendering.` —— 主语补全为 `Status accepted`，让末段能独立读懂；否定式按 W9 警告例外保留。

### 故意没改

- **三条约束几乎逐字保留**（output.md:5）：`manual retry settings`、`this browser session`、`Signing in elsewhere`、`those manual settings`、`Do not retry jobs marked archived` 一个都没动 —— 没有泛化成 "settings"（丢掉「手动」限定）或 "device"（丢掉「浏览器会话」限定），也没有把禁令改成正面说法。
- **数字与边界值原样**：`7 minutes`、`once`（恰好一次）、`4 steps` 均未改。`一次` 是边界，改写成 "reload the panel" 会丢约束。
- **列表形态不变**：仍是 4 项有序列表，没有转成 `- [ ]` 复选框（runbook 骨架建议复选框，但那是排版变更，scope 不允许），没有加小标题、表格、`<details>`、加粗或行内代码。
- **没编造缺来源的内容**：A2（每步时间预估）、A7（第 1–3 步的预期输出）、A1（结尾下一步）原文都没有依据，按规则在下面标「不满足」，不用填充句凑分。

---

### Judge 规则逐条判定（audit 返回的全部 32 条）

| 规则 | 判定 | 位置 / 理由 |
|---|---|---|
| S4 标题写结论 | **满足** | output.md:1 —— 只看标题就知道答案（retry a failed thumbnail job），不再是话题式 "recovery" |
| S5 结论块前置 | **不适用** | 原文没有可整块搬移的结论段（末段是注意事项，不是结论）；首屏结论按 C 轴新写，见 H1 |
| S6 章节顺序符合骨架 | **不适用（scope 限制）** | runbook 骨架需新增「先做这个 / 升级 / 事后」等标题，scope=content 不允许新增标题层级 |
| S8 每节开头交代本节解决什么 | **满足** | output.md:3 —— 唯一章节的开头一句即交代 |
| H3 读完你能做到什么 | **满足** | output.md:3 "Retry one failed thumbnail job"，写收益不写文档结构 |
| H4 首屏时间/篇幅预估 | **满足** | output.md:3 "in 4 steps"（篇幅型；原文无任何可支撑时长的依据，不编造分钟数） |
| P2 一段只讲一件事 | **满足** | 结论 / 约束 / 结果提示分属三段，原文首段混装 4 句已拆开 |
| P5 超长引用块 | **不适用** | 无 `>` 块 |
| L2 并列句转列表 | **不适用** | 原文已是列表；三条约束不是并列枚举，转列表还会改排版形态 |
| L4 列表项平行结构 | **满足** | output.md:7–10 —— 四项均为 `Step X of 4:` + 动词开头（第 2 项按原文以条件分支开头） |
| L7 列表项完整语义 | **满足** | 每项单独取出可读懂，无关键词碎片（X3 未命中） |
| W2 主动语态 | **满足** | 被动占比 0%（apply / copy / open / select / wait / reload / submit / shows） |
| W3 括号插入语 | **不适用** | 全文无括号 |
| W5 术语首现解释 | **不适用** | 无缩写；job panel / job key / incident note / lock 沿用原文用词，原文未给定义，不补 |
| W7 第二人称 + 现在时 | **满足** | 全篇祈使句 + "Your … apply"，现在时 |
| W8 一句一从句 | **满足** | 最长句 10 词，无三层嵌套 |
| W9 否定改正面 | **满足（按警告例外）** | output.md:5 禁令、output.md:12 警告均保留否定式；output.md:5 的 "does not copy" 是事实边界，正面化会丢限定 |
| A1 章节结尾给下一步 | **不满足（缺来源）** | 原文没有任何升级路径或后续动作；结尾为原文自带的结果提示。按边界规则不补事实，保留缺口 |
| A2 步骤给时间预估 | **不满足（缺来源）** | 全文唯一时间值是第 2 步条件下的 `7 minutes`（output.md:8），已保留；其余步骤原文无时长依据 |
| A3 多选项给默认推荐 | **不适用** | 原文无并列选项 |
| A5 只做一件事就做这个 | **不适用** | 12 行短文，非长文档；首屏结论行已承担该角色 |
| A6 决策点给判断依据 | **满足** | output.md:8 "If the job's lock is active" 明写分支条件 |
| A7 预期输出 / 验证方法 | **不满足（部分满足 + 缺来源）** | 第 4 步有原文依据的 "A successful request shows status accepted."（output.md:10）✓；第 1–3 步原文未给输出或判断条件，A7 明令不得编造，保留缺口 |
| A8 一步只做一个动作 | **不满足（scope 限制）** | 第 1、2 步已项内分句（output.md:7、8），但一个编号下仍是两个动作；拆成独立列表项会改列表形态，scope=content 不允许 —— 按规则不得报满足 |
| N4 折叠深入内容 | **不适用** | 无偏离主路径的内容；折叠本身也是排版变更 |
| N7 多步流程标注进度 | **满足** | 4 步 ≥ 阈值，output.md:7–10 均标 `Step X of 4`，走神回来可定位 |
| T3 标记语义一致 | **不适用** | 全文未使用强调 / 代码标记，无混用 |
| C4 长定语前置改后置 | **不适用** | 中文专项，本文档语言 `en` |
| X3 剩词不剩句 | **满足（未命中）** | 列表项均为完整指令 |
| X6 表格滥用 | **满足（未命中）** | 无表格 |
| X7 折叠滥用 | **满足（未命中）** | 无 `<details>` |
| X8 套模板 | **满足（未命中）** | 无重复空话小标题 |

**X 组全量**（脚本侧）：X1 emoji 0 · X2 碎片化未命中（1 个标题 / 12 行）· X4 `verify(content)` 通过 · X5 加粗 0% · after 扣分 −0。
**M 组（活人感）**：100 → 100，命中数未上升；新增文字无翻案腔、预告式冒号（`Step X of 4:` 属字段标签冒号）、空泛量词。

**需注意的一处取舍**：`verify --scope=format` 报 `recovery`、`procedure` 等词元消失——它们分别被 `Retry a failed thumbnail job` 和 `Retry one failed thumbnail job in 4 steps.` 重述，信息未丢，但**词面确实变了**。若这份 runbook 需要逐字冻结，请告知，我按 scope=format 重做一版（那版无法补 TL;DR、进度标注与预期输出）。

Done. `input.md` is untouched; the rewrite is in `output.md`. Here is the report.

## 改完了：`output.md`（源文件 `input.md`）

**scope** `content` · **level** `deep` · 写到**新文件** `output.md` —— 第 0 步 `git status` 返回 `fatal: not a git repository`，不在 git 里，按规则不原地覆盖。`fmt` 步骤按 `scope=content` 跳过。

脚本分 **87.8 → 100.0（+12.2）**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | 0 |
| 句子负荷 | 100.0 | 100.0 | 0 |
| 行动性 | 100.0 | 100.0 | 0 |
| 排版一致性 | 100.0 | 100.0 | 0 |
| 活人感 | 100.0 | 100.0 | 0 |
| X 组扣分 | −0 | −0 | 0 |

before 的 findings：`H1`（input.md:1，content 轴）+ `P1`（input.md:3，4 句 / 30 单位，超 3 句上限，F 轴）；after：0 条。

**校验结论**

| 命令 | 结果 |
|---|---|
| `verify --scope=content` | **通过**（无硬失败、无警告、无 unknown） |
| `verify --scope=both` | **通过** |
| `verify --scope=format` | **失败（预期内，非缺陷）**：`prose_tokens_missing` / `prose_tokens_added`。format 门禁是**词元多重集相等**——任何 content 改写都必然触发。本次声明 scope 是 content，以 content/both 结论为准；这里如实列出，不当作通过。 |

`pass` 只覆盖已声明的机器检查（代码块、链接、行内字面值、选项、路径、数字、X4），**不是语义等价证明**；句内语义与人工判断项见下表。

---

### 改了什么（全部为 content 轴）

1. **H1 标题改结论式**：`# Thumbnail recovery` → `# Retry a failed thumbnail job`（output.md:1）。标题文字属于措辞，scope=content 允许改写（SKILL 第 3 步判据第 4 条）。
2. **新写首屏 TL;DR 段落**（output.md:3）：`Retry one failed thumbnail job in 4 steps.` —— 一句话，1 句 / 9 词，落在 H1 首段判据内（≤3 句且 ≤40 词）。信息全部是重述原文 + 可从原文数出的步数。
3. **原首段拆成两块**：结论句独立成段，三条约束独立成段（output.md:5）。原文首段 4 句同时触发 H1 与 P1；拆开后两项都消除，且**没有新增标题层级、没有改列表形态**——新块用的是文档里已有的段落类型（"摘要用现有段落风格"）。
4. **复合步骤项内分句**（不新增列表项）：
   - `Open the job panel and select a failed job.` → `Open the job panel. Select a failed job.`（output.md:7）
   - `If its lock is active, wait 7 minutes and reload the panel once.` → `If the job's lock is active, wait 7 minutes. After the wait, reload the panel once.`（output.md:8）——条件仍控制两个子动作，先后顺序保留，刷新**没有**变成无条件步骤；`its` → `the job's` 只为消除悬空指代。
5. **N7 进度标注**：4 步 ≥ 阈值，每项前加 `Step X of 4:`（output.md:7–10），用普通文字表达（不能改列表形态/加复选框）。
6. **A7 部分补预期输出**：`A successful request shows status accepted.` 从结尾段移到第 4 步项内（output.md:10），这是原文**已有**的成功信号，不是新造的界面行为。
7. **结尾段收窄为一件事**（output.md:12）：`Status accepted does not mean the thumbnail has finished rendering.` —— 主语补全为 `Status accepted`，让末段能独立读懂；否定式按 W9 警告例外保留。

### 故意没改

- **三条约束几乎逐字保留**（output.md:5）：`manual retry settings`、`this browser session`、`Signing in elsewhere`、`those manual settings`、`Do not retry jobs marked archived` 一个都没动 —— 没有泛化成 "settings"（丢掉「手动」限定）或 "device"（丢掉「浏览器会话」限定），也没有把禁令改成正面说法。
- **数字与边界值原样**：`7 minutes`、`once`（恰好一次）、`4 steps` 均未改。`一次` 是边界，改写成 "reload the panel" 会丢约束。
- **列表形态不变**：仍是 4 项有序列表，没有转成 `- [ ]` 复选框（runbook 骨架建议复选框，但那是排版变更，scope 不允许），没有加小标题、表格、`<details>`、加粗或行内代码。
- **没编造缺来源的内容**：A2（每步时间预估）、A7（第 1–3 步的预期输出）、A1（结尾下一步）原文都没有依据，按规则在下面标「不满足」，不用填充句凑分。

---

### Judge 规则逐条判定（audit 返回的全部 32 条）

| 规则 | 判定 | 位置 / 理由 |
|---|---|---|
| S4 标题写结论 | **满足** | output.md:1 —— 只看标题就知道答案（retry a failed thumbnail job），不再是话题式 "recovery" |
| S5 结论块前置 | **不适用** | 原文没有可整块搬移的结论段（末段是注意事项，不是结论）；首屏结论按 C 轴新写，见 H1 |
| S6 章节顺序符合骨架 | **不适用（scope 限制）** | runbook 骨架需新增「先做这个 / 升级 / 事后」等标题，scope=content 不允许新增标题层级 |
| S8 每节开头交代本节解决什么 | **满足** | output.md:3 —— 唯一章节的开头一句即交代 |
| H3 读完你能做到什么 | **满足** | output.md:3 "Retry one failed thumbnail job"，写收益不写文档结构 |
| H4 首屏时间/篇幅预估 | **满足** | output.md:3 "in 4 steps"（篇幅型；原文无任何可支撑时长的依据，不编造分钟数） |
| P2 一段只讲一件事 | **满足** | 结论 / 约束 / 结果提示分属三段，原文首段混装 4 句已拆开 |
| P5 超长引用块 | **不适用** | 无 `>` 块 |
| L2 并列句转列表 | **不适用** | 原文已是列表；三条约束不是并列枚举，转列表还会改排版形态 |
| L4 列表项平行结构 | **满足** | output.md:7–10 —— 四项均为 `Step X of 4:` + 动词开头（第 2 项按原文以条件分支开头） |
| L7 列表项完整语义 | **满足** | 每项单独取出可读懂，无关键词碎片（X3 未命中） |
| W2 主动语态 | **满足** | 被动占比 0%（apply / copy / open / select / wait / reload / submit / shows） |
| W3 括号插入语 | **不适用** | 全文无括号 |
| W5 术语首现解释 | **不适用** | 无缩写；job panel / job key / incident note / lock 沿用原文用词，原文未给定义，不补 |
| W7 第二人称 + 现在时 | **满足** | 全篇祈使句 + "Your … apply"，现在时 |
| W8 一句一从句 | **满足** | 最长句 10 词，无三层嵌套 |
| W9 否定改正面 | **满足（按警告例外）** | output.md:5 禁令、output.md:12 警告均保留否定式；output.md:5 的 "does not copy" 是事实边界，正面化会丢限定 |
| A1 章节结尾给下一步 | **不满足（缺来源）** | 原文没有任何升级路径或后续动作；结尾为原文自带的结果提示。按边界规则不补事实，保留缺口 |
| A2 步骤给时间预估 | **不满足（缺来源）** | 全文唯一时间值是第 2 步条件下的 `7 minutes`（output.md:8），已保留；其余步骤原文无时长依据 |
| A3 多选项给默认推荐 | **不适用** | 原文无并列选项 |
| A5 只做一件事就做这个 | **不适用** | 12 行短文，非长文档；首屏结论行已承担该角色 |
| A6 决策点给判断依据 | **满足** | output.md:8 "If the job's lock is active" 明写分支条件 |
| A7 预期输出 / 验证方法 | **不满足（部分满足 + 缺来源）** | 第 4 步有原文依据的 "A successful request shows status accepted."（output.md:10）✓；第 1–3 步原文未给输出或判断条件，A7 明令不得编造，保留缺口 |
| A8 一步只做一个动作 | **不满足（scope 限制）** | 第 1、2 步已项内分句（output.md:7、8），但一个编号下仍是两个动作；拆成独立列表项会改列表形态，scope=content 不允许 —— 按规则不得报满足 |
| N4 折叠深入内容 | **不适用** | 无偏离主路径的内容；折叠本身也是排版变更 |
| N7 多步流程标注进度 | **满足** | 4 步 ≥ 阈值，output.md:7–10 均标 `Step X of 4`，走神回来可定位 |
| T3 标记语义一致 | **不适用** | 全文未使用强调 / 代码标记，无混用 |
| C4 长定语前置改后置 | **不适用** | 中文专项，本文档语言 `en` |
| X3 剩词不剩句 | **满足（未命中）** | 列表项均为完整指令 |
| X6 表格滥用 | **满足（未命中）** | 无表格 |
| X7 折叠滥用 | **满足（未命中）** | 无 `<details>` |
| X8 套模板 | **满足（未命中）** | 无重复空话小标题 |

**X 组全量**（脚本侧）：X1 emoji 0 · X2 碎片化未命中（1 个标题 / 12 行）· X4 `verify(content)` 通过 · X5 加粗 0% · after 扣分 −0。
**M 组（活人感）**：100 → 100，命中数未上升；新增文字无翻案腔、预告式冒号（`Step X of 4:` 属字段标签冒号）、空泛量词。

**需注意的一处取舍**：`verify --scope=format` 报 `recovery`、`procedure` 等词元消失——它们分别被 `Retry a failed thumbnail job` 和 `Retry one failed thumbnail job in 4 steps.` 重述，信息未丢，但**词面确实变了**。若这份 runbook 需要逐字冻结，请告知，我按 scope=format 重做一版（那版无法补 TL;DR、进度标注与预期输出）。
