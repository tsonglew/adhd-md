I'll start by reading the skill and the input document.

Now I have a clear picture. Let me write the candidate output and test it against the verifier.

Verifier passes. Now let me refine the wording pass — checking the judge rules I can still improve, and confirming the numeric/literal invariants survive:

All checks pass. Here is the report.

## 改完了：`input.md` → `output.md`

**scope** `content` · **level** `deep` · 写到 `output.md`（按 prompt 指定，原地 `input.md` 未改动）

脚本分 **87.8 → 100.0**（+12.2）· 反模式扣分 **−0 → −0**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

findings(content) `1 → 0`（全文 findings 也是 `2 → 0`）· 全轴复审 findings 为空 · X 组命中数 `0`

**verify(content)** 通过 —— `{"status":"pass","hard_failures":[],"warnings":[],"unknowns":[]}`。范围：代码块正文、链接目标、行内字面值、选项/路径/权限值/大小写敏感标识符、数值与单位（`7 minutes` 原样保留）。原文没有代码块、链接与行内代码，所以这些检查项本次为空集；`pass` 只覆盖这些不变量，语义等价仍需人工复核。`fmt --check` 另报「格式已规范，无需修改」。

### 改了什么（都用原文已有的信息，未新增事实）

| 改动 | 轴 |
|---|---|
| 把原文末尾的判定「`accepted` ≠ 渲染完成」与硬约束「Do not retry jobs marked archived」提到首屏，首屏现在直接给出「做什么 + 几步 + 不能做什么」 | content（H1/H3/H4） |
| 步骤行加 `Step X of 4` 进度标签，走神回来能定位（T7 序号 1–4 未动，仍是普通有序列表） | content（N7） |
| 原第 3 行拆成两段：首屏段落只讲任务与归档禁区，「手动设置只对本会话有效」单独成段 | content（P1 段落 ≤3 句） |
| Step 1 补「Check that it is not marked archived」——把归档约束复制到它真正约束的动作处（原文只在开头说一次） | content（A7，用的是原文已有条件） |
| 删填充式主语壳：`This procedure retries a thumbnail job.` → `Retry a failed thumbnail job in four steps.`；被动/伴随句保持原意 | content（W1/W7/M4） |

### 故意没改

- **不新增 H2 小节、不加复选框、不折叠**：`scope=content` 禁止改排版风格，且你要求保留原布局。deep 档的 runbook 骨架（复选框 + `x/N`）属于 format 权限，本轮不做。
- **不加时间预估（如"约 3 分钟"）**：原文没有任何耗时依据，编一个就违反「不得补未提供的成功输出」。H4 用篇幅预估「in four steps」满足。
- **Step 3、Step 4 不补预期输出**：原文没有给出抄写后与提交后的界面反馈，A7 对这两步标「不满足（缺来源）」，不猜。
- **标题 `Thumbnail recovery` 保持原样**：content 不改标题措辞/形态（S4 判不适用）。
- **Step 2 拆句但不拆项**：「If its lock is active, wait 7 minutes and reload the panel once.」条件与动作已分句、顺序与条件覆盖都在，但没有变成一个编号一个动作 —— A8 记为「不满足（scope 限制）」。

### 判断规则逐条（适用 32 条 judge 规则）

| 规则 | 判断 | 依据（位置） |
|---|---|---|
| S4 标题写结论 | 不适用 | 唯一标题 `# Thumbnail recovery`，content scope 不改标题措辞/形态 |
| S5 结论块前置 | 满足 | 「Do not retry jobs marked archived」整句移到首屏；「accepted ≠ 完成」在末尾保留原位，未搬 |
| S6 骨架顺序 | 不适用 | 无 H2，deep 骨架需新增小节=format 权限；4 步流程本身已按操作顺序 |
| S8 每节首句交代 | 不适用 | 文档无小节 |
| H3 读完能做到什么 | 满足 | 首屏 `Retry a failed thumbnail job in four steps.` |
| H4 时间/篇幅预估 | 满足 | `in four steps`；耗时无来源，按规则以篇幅替代 |
| P2 一段一件事 | 满足 | 第 3 行开头/约束拆段，首段=任务+禁区，次段=设置作用域，末段=验收 |
| P5 长引用块 | 不适用 | 无引用块 |
| L2 并列句转列表 | 不适用 | 三段正文无「冒号 + 并列成分」，无可转项（转列表也属 format） |
| L4 列表项平行 | 满足 | 四项均 `Step X of 4 — 动词开头`，时态一致 |
| L7 列表项完整语义 | 满足 | 每项都是完整句，含主谓（见 X3） |
| W2 主动语态 | 满足 | 全文祈使句，`Signing in elsewhere does not copy…` 为主动；无新增被动 |
| W3 括号插入语 | 满足 | 无括号插入语 |
| W5 术语首现解释 | 满足 | 无缩写；`job key`、`incident note` 沿用系统既有名词 |
| W7 第二人称现在时 | 满足 | `Retry…` / `Open…` / `Check…` / `Copy…` / `Submit…` |
| W8 一句一从句 | 满足 | 无三层嵌套从句 |
| W9 否定改正面 | 满足 | `Do not retry jobs marked archived.` 属警告/例外，规则明示保留否定式 |
| A1 章节结尾下一步 | 满足 | 末段 `A successful request shows status accepted.`（原文即为收尾判定，未编） |
| A2 步骤时间预估 | 不适用（无来源） | 原文无任何耗时；补数字=编事实，按规则只留篇幅 |
| A3 多选项给默认 | 不适用 | 文档无分叉选项 |
| A5 只做一件事就做这个 | 不适用 | 短文档（12 行），首屏即全文；规则限定长文档首屏 |
| A6 决策点判断依据 | 满足 | 分支条件明确：`If its lock is active`、`jobs marked archived`（原文已有条件） |
| A7 预期输出/验证法 | 部分满足 · 明确未满足项 | Step 1 用原文约束当前置校验（`Check that it is not marked archived.`）、Step 4 的验收在末段（`shows status accepted`）。**Step 1 选择后、Step 3 抄写后的可观察输出，原文未提供 → A7 对这两步标未满足（来源缺口），不编造界面行为** |
| A8 一步一动作 | 不满足（scope 限制） | Step 1（打开+选择+检查，缺条件粘连）、Step 2（等待+刷新）仍是一个编号多个动作；未新增列表项以规避，理由即内容轴限制 |
| N4 折叠可选内容 | 不适用 | 全文都是主路径内容；无 `## H2`，无偏离分支，无可折叠项（折叠也属 format） |
| N7 多步进度 | 满足 | 4 步流程，四项均标 `Step X of 4` |
| T3 标记语义一致 | 不适用（空集） | 未新增任何强调标记，原文也无 |
| C4 长定语后置 | 不适用 | 英文文档，中文专项 |
| X3 剩词不剩句 | 满足 | 复读检查：每项独立可读，无关键词碎片 |
| X6 表格滥用 | 不适用 | 未新增表格 |
| X7 折叠滥用 | 不适用 | 无折叠，主路径全部可见 |
| X8 套模板 | 不适用 | 未给任何小节套统一小标题壳 |

**M 组（AI 味）**：before 命中 0，after 命中 0 —— 未上升（改后全轴复审 findings 为空）。正文未出现「不是 A 而是 B」类翻案腔、预告式冒号、黑话或名词化。

**scope 相关限制（已记入理由）**：内容轴下未做 format 操作——不加 H2/复选框/`<details>`/TOC，不改列表形态与标题，未跑 `fmt --write`；deep 档 runbook 骨架的复选框与「先做这个」小节因此保留为原布局，改由首屏段落与 `Step X of 4` 标签达成同等的可扫读性。

All checks pass. Here is the report.

## 改完了：`input.md` → `output.md`

**scope** `content` · **level** `deep` · 写到 `output.md`（按 prompt 指定，原地 `input.md` 未改动）

脚本分 **87.8 → 100.0**（+12.2）· 反模式扣分 **−0 → −0**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

findings(content) `1 → 0`（全文 findings 也是 `2 → 0`）· 全轴复审 findings 为空 · X 组命中数 `0`

**verify(content)** 通过 —— `{"status":"pass","hard_failures":[],"warnings":[],"unknowns":[]}`。范围：代码块正文、链接目标、行内字面值、选项/路径/权限值/大小写敏感标识符、数值与单位（`7 minutes` 原样保留）。原文没有代码块、链接与行内代码，所以这些检查项本次为空集；`pass` 只覆盖这些不变量，语义等价仍需人工复核。`fmt --check` 另报「格式已规范，无需修改」。

### 改了什么（都用原文已有的信息，未新增事实）

| 改动 | 轴 |
|---|---|
| 把原文末尾的判定「`accepted` ≠ 渲染完成」与硬约束「Do not retry jobs marked archived」提到首屏，首屏现在直接给出「做什么 + 几步 + 不能做什么」 | content（H1/H3/H4） |
| 步骤行加 `Step X of 4` 进度标签，走神回来能定位（T7 序号 1–4 未动，仍是普通有序列表） | content（N7） |
| 原第 3 行拆成两段：首屏段落只讲任务与归档禁区，「手动设置只对本会话有效」单独成段 | content（P1 段落 ≤3 句） |
| Step 1 补「Check that it is not marked archived」——把归档约束复制到它真正约束的动作处（原文只在开头说一次） | content（A7，用的是原文已有条件） |
| 删填充式主语壳：`This procedure retries a thumbnail job.` → `Retry a failed thumbnail job in four steps.`；被动/伴随句保持原意 | content（W1/W7/M4） |

### 故意没改

- **不新增 H2 小节、不加复选框、不折叠**：`scope=content` 禁止改排版风格，且你要求保留原布局。deep 档的 runbook 骨架（复选框 + `x/N`）属于 format 权限，本轮不做。
- **不加时间预估（如"约 3 分钟"）**：原文没有任何耗时依据，编一个就违反「不得补未提供的成功输出」。H4 用篇幅预估「in four steps」满足。
- **Step 3、Step 4 不补预期输出**：原文没有给出抄写后与提交后的界面反馈，A7 对这两步标「不满足（缺来源）」，不猜。
- **标题 `Thumbnail recovery` 保持原样**：content 不改标题措辞/形态（S4 判不适用）。
- **Step 2 拆句但不拆项**：「If its lock is active, wait 7 minutes and reload the panel once.」条件与动作已分句、顺序与条件覆盖都在，但没有变成一个编号一个动作 —— A8 记为「不满足（scope 限制）」。

### 判断规则逐条（适用 32 条 judge 规则）

| 规则 | 判断 | 依据（位置） |
|---|---|---|
| S4 标题写结论 | 不适用 | 唯一标题 `# Thumbnail recovery`，content scope 不改标题措辞/形态 |
| S5 结论块前置 | 满足 | 「Do not retry jobs marked archived」整句移到首屏；「accepted ≠ 完成」在末尾保留原位，未搬 |
| S6 骨架顺序 | 不适用 | 无 H2，deep 骨架需新增小节=format 权限；4 步流程本身已按操作顺序 |
| S8 每节首句交代 | 不适用 | 文档无小节 |
| H3 读完能做到什么 | 满足 | 首屏 `Retry a failed thumbnail job in four steps.` |
| H4 时间/篇幅预估 | 满足 | `in four steps`；耗时无来源，按规则以篇幅替代 |
| P2 一段一件事 | 满足 | 第 3 行开头/约束拆段，首段=任务+禁区，次段=设置作用域，末段=验收 |
| P5 长引用块 | 不适用 | 无引用块 |
| L2 并列句转列表 | 不适用 | 三段正文无「冒号 + 并列成分」，无可转项（转列表也属 format） |
| L4 列表项平行 | 满足 | 四项均 `Step X of 4 — 动词开头`，时态一致 |
| L7 列表项完整语义 | 满足 | 每项都是完整句，含主谓（见 X3） |
| W2 主动语态 | 满足 | 全文祈使句，`Signing in elsewhere does not copy…` 为主动；无新增被动 |
| W3 括号插入语 | 满足 | 无括号插入语 |
| W5 术语首现解释 | 满足 | 无缩写；`job key`、`incident note` 沿用系统既有名词 |
| W7 第二人称现在时 | 满足 | `Retry…` / `Open…` / `Check…` / `Copy…` / `Submit…` |
| W8 一句一从句 | 满足 | 无三层嵌套从句 |
| W9 否定改正面 | 满足 | `Do not retry jobs marked archived.` 属警告/例外，规则明示保留否定式 |
| A1 章节结尾下一步 | 满足 | 末段 `A successful request shows status accepted.`（原文即为收尾判定，未编） |
| A2 步骤时间预估 | 不适用（无来源） | 原文无任何耗时；补数字=编事实，按规则只留篇幅 |
| A3 多选项给默认 | 不适用 | 文档无分叉选项 |
| A5 只做一件事就做这个 | 不适用 | 短文档（12 行），首屏即全文；规则限定长文档首屏 |
| A6 决策点判断依据 | 满足 | 分支条件明确：`If its lock is active`、`jobs marked archived`（原文已有条件） |
| A7 预期输出/验证法 | 部分满足 · 明确未满足项 | Step 1 用原文约束当前置校验（`Check that it is not marked archived.`）、Step 4 的验收在末段（`shows status accepted`）。**Step 1 选择后、Step 3 抄写后的可观察输出，原文未提供 → A7 对这两步标未满足（来源缺口），不编造界面行为** |
| A8 一步一动作 | 不满足（scope 限制） | Step 1（打开+选择+检查，缺条件粘连）、Step 2（等待+刷新）仍是一个编号多个动作；未新增列表项以规避，理由即内容轴限制 |
| N4 折叠可选内容 | 不适用 | 全文都是主路径内容；无 `## H2`，无偏离分支，无可折叠项（折叠也属 format） |
| N7 多步进度 | 满足 | 4 步流程，四项均标 `Step X of 4` |
| T3 标记语义一致 | 不适用（空集） | 未新增任何强调标记，原文也无 |
| C4 长定语后置 | 不适用 | 英文文档，中文专项 |
| X3 剩词不剩句 | 满足 | 复读检查：每项独立可读，无关键词碎片 |
| X6 表格滥用 | 不适用 | 未新增表格 |
| X7 折叠滥用 | 不适用 | 无折叠，主路径全部可见 |
| X8 套模板 | 不适用 | 未给任何小节套统一小标题壳 |

**M 组（AI 味）**：before 命中 0，after 命中 0 —— 未上升（改后全轴复审 findings 为空）。正文未出现「不是 A 而是 B」类翻案腔、预告式冒号、黑话或名词化。

**scope 相关限制（已记入理由）**：内容轴下未做 format 操作——不加 H2/复选框/`<details>`/TOC，不改列表形态与标题，未跑 `fmt --write`；deep 档 runbook 骨架的复选框与「先做这个」小节因此保留为原布局，改由首屏段落与 `Step X of 4` 标签达成同等的可扫读性。
