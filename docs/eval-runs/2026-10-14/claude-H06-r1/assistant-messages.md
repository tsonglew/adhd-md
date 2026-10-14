I'll start by reading the skill definition and the input file.

Now let me set up a scratch area and inspect what the deterministic fixer and verifier say.

Let me inspect how the script detects C6 and what the verifier treats as protected, so my decisions are grounded in the actual tooling.

Let me check the skill's own tests for this boundary scenario, which may reveal the intended behavior.

Now I understand the verifier's mechanics. Let me set up a scratch dir and build the deliverables.

Important boundary discovery. Let me confirm the mechanism precisely.

Confirmed the key boundary: **any** difference at all trips `raw_html` unknown for this file. Let me confirm byte-identity and clean up.

已完成。核心结论：**这份文档在 `scope=format` 下没有可执行的改动**——`output.md` 与 `input.md` 逐字节相同（sha256 `0e55b3fd…b7cdf`，各 618 字节），输入未被覆盖。

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（案例指定文件名；此目录不是 git 仓库，skill 默认会写 `<原名>.adhd.md`，此处按案例要求执行）

**脚本分 100.0 → 100.0（+0.0）**

| 维度 | 权重 | before | after | delta |
|---|---|---|---|---|
| 首屏结论力 | 18% | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 18% | 100.0 | 100.0 | +0.0 |
| 扫读性 | 13% | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 13% | 100.0 | 100.0 | +0.0 |
| 行动性 | 12% | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 13% | 100.0 | 100.0 | +0.0 |
| 活人感 | 13% | 100.0 | 100.0 | +0.0 |

### 退出状态与三态结论

| 命令 | 结果 | 退出状态 |
|---|---|---|
| `fmt`（第 2 步，预览） | 格式已规范，无需修改 | `0` |
| `audit --level 3 --scope=format` | 脚本分 100.0 · findings 1 条 | `0` |
| `verify --scope=format` | `status=pass` · `ok=true` · `identical=true` | `0` |
| `verify` 的两个候选改法（见下） | `status=unknown` · `raw_html old:8 / new:8` | `4` |

`verify` 的 `hard_failures`、`warnings`、`unknowns` 三项都是空数组。**这个 `pass` 只说明"已声明的机器检查通过"**：由于新旧文件逐字节相同，走的是 `identical` 快速通道；它不是语义等价证明，也不覆盖下面那 10 条未判定规则。

### 反模式扣分（X 组）

`x_deduct = −0`，`x_hits = {}` —— X 组 after 为 0，没有靠过度格式化换分数。

### 未判定项（不得写成通过）

`deep · format` 覆盖：适用 41 条；脚本检查 23（可计分 23）；**仅提示 5**；**需模型判断 10**；仅自动修复 2；硬门禁 1。

需模型判断、脚本**未**评分的 10 条：`S5`、`S6`、`P2`、`P5`、`L2`、`N4`、`T3`、`X6`、`X7`、`X8`（全轴合计 32 条）。脚本把未命中项按 0 计分，所以 100.0 是**脚本分**，不是最终分；这 10 条我没有判过，**不算通过**。

唯一的 finding 是提示项：`C6` 中文列表项句末标点不一致（`output.md:34`，仅提示、不扣分）。

### 边界发现：这份文件"一改就 unknown"

我用两个候选改法做了对照实验，都被判 `unknown`（退出 4）：

| 候选改法 | verify 结果 |
|---|---|
| 删掉 `- 只在测试环境重试。`／`- 生产环境不要自动重试。` 的句末句号（C6 的规范做法） | 无法判断 · `raw_html old:8 new:8` · 退出 `4` |
| 删掉 `链接： [恢复说明]` 冒号后的空格（format 允许的"修空格"） | 无法判断 · `raw_html old:8 new:8` · 退出 `4` |

原因在读脚本时确认了：`verify` 只在 `old == new` 时走 `identical` 快速通道；否则第 8 行的 HTML 注释会被判为 `raw_html` 待人工复核（两个 side 都报），唯一豁免是复用唯一原 H2 标题的标准 `<details>` 外壳，而注释在 H2 之前，不在豁免范围内。

**所以这份文档的任何改动都拿不到 `pass`。** 按 skill 的规矩（"无法确认时不要写回"、"`unknown` 需保留原文并人工复核"），我没有把无法校验的版本作为交付物写进 `output.md`。

### 改了什么

- **零处字符改动**：`output.md` 与 `input.md` 的 sha256 完全相同，618 字节，LF 换行、无行尾空白、无制表符、末尾单换行、无 BOM（已逐项核过）。
- YAML frontmatter、第 8 行 HTML 注释、引用块、两层嵌套列表、表格、`sh` 代码块（`tool sync --dry-run --timeout 12`）、链接目标 `https://example.org/restore?mode=fast#limits`，全部原样保留。

### 故意没改

- **`C6` 列表项句末标点**：两个方向都违反本案例的硬约束——删句号是删原有字符，补句号是补充内容；它是仅提示项、不影响分数；而且改完 `verify` 会从 `pass` 掉到 `unknown`（退出 4）。要统一标点，需要你明确授权改字符（并接受结果需人工复核），或改用 `scope=content`。
- **`链接： [恢复说明]` 冒号后的空格**：`fmt` 与 `audit` 都判它合规，删空格仍属改字符，收益为零。
- **`<details>` 折叠（N4）**：全文只有一个 H2 `## 原文片段`，正文全在它下面，折它就是 X7 折叠滥用（藏主路径内容），还要新增标记。
- **目录（N1）**：触发线是 >80 行，本文 35 行，不适用。
- **搬移结论块 / 重排骨架（S5、S6）**：案例要求保留信息顺序；且本文不匹配 `doc-types.md` 六种骨架中的任何一种，该文件明说"判不出类型不要猜"。
- **deep 档的内容类动作（H3 收益句、H4 时间预估、A2/A5/A7、N7 进度标注、S4 结论式标题）**：全部是 C 轴，`scope=format` 不许写新句子。
- **加粗关键术语 / emoji / HTML 锚点**：会增字符，且撞 T2、X5、X1，没有收益。
- **第 8 行 HTML 注释**：按它自己的文字只作为材料保留，不执行、不改写——它也是让本文件"一改就 unknown"的那一行。

如果你的目标是让这份样例在格式层面"看起来有变化"，告诉我一声：我可以做 C6 的标点统一，但交付物会落在 `verify=unknown`（退出 4），需要人工复核后才能使用。

已完成。核心结论：**这份文档在 `scope=format` 下没有可执行的改动**——`output.md` 与 `input.md` 逐字节相同（sha256 `0e55b3fd…b7cdf`，各 618 字节），输入未被覆盖。

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（案例指定文件名；此目录不是 git 仓库，skill 默认会写 `<原名>.adhd.md`，此处按案例要求执行）

**脚本分 100.0 → 100.0（+0.0）**

| 维度 | 权重 | before | after | delta |
|---|---|---|---|---|
| 首屏结论力 | 18% | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 18% | 100.0 | 100.0 | +0.0 |
| 扫读性 | 13% | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 13% | 100.0 | 100.0 | +0.0 |
| 行动性 | 12% | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 13% | 100.0 | 100.0 | +0.0 |
| 活人感 | 13% | 100.0 | 100.0 | +0.0 |

### 退出状态与三态结论

| 命令 | 结果 | 退出状态 |
|---|---|---|
| `fmt`（第 2 步，预览） | 格式已规范，无需修改 | `0` |
| `audit --level 3 --scope=format` | 脚本分 100.0 · findings 1 条 | `0` |
| `verify --scope=format` | `status=pass` · `ok=true` · `identical=true` | `0` |
| `verify` 的两个候选改法（见下） | `status=unknown` · `raw_html old:8 / new:8` | `4` |

`verify` 的 `hard_failures`、`warnings`、`unknowns` 三项都是空数组。**这个 `pass` 只说明"已声明的机器检查通过"**：由于新旧文件逐字节相同，走的是 `identical` 快速通道；它不是语义等价证明，也不覆盖下面那 10 条未判定规则。

### 反模式扣分（X 组）

`x_deduct = −0`，`x_hits = {}` —— X 组 after 为 0，没有靠过度格式化换分数。

### 未判定项（不得写成通过）

`deep · format` 覆盖：适用 41 条；脚本检查 23（可计分 23）；**仅提示 5**；**需模型判断 10**；仅自动修复 2；硬门禁 1。

需模型判断、脚本**未**评分的 10 条：`S5`、`S6`、`P2`、`P5`、`L2`、`N4`、`T3`、`X6`、`X7`、`X8`（全轴合计 32 条）。脚本把未命中项按 0 计分，所以 100.0 是**脚本分**，不是最终分；这 10 条我没有判过，**不算通过**。

唯一的 finding 是提示项：`C6` 中文列表项句末标点不一致（`output.md:34`，仅提示、不扣分）。

### 边界发现：这份文件"一改就 unknown"

我用两个候选改法做了对照实验，都被判 `unknown`（退出 4）：

| 候选改法 | verify 结果 |
|---|---|
| 删掉 `- 只在测试环境重试。`／`- 生产环境不要自动重试。` 的句末句号（C6 的规范做法） | 无法判断 · `raw_html old:8 new:8` · 退出 `4` |
| 删掉 `链接： [恢复说明]` 冒号后的空格（format 允许的"修空格"） | 无法判断 · `raw_html old:8 new:8` · 退出 `4` |

原因在读脚本时确认了：`verify` 只在 `old == new` 时走 `identical` 快速通道；否则第 8 行的 HTML 注释会被判为 `raw_html` 待人工复核（两个 side 都报），唯一豁免是复用唯一原 H2 标题的标准 `<details>` 外壳，而注释在 H2 之前，不在豁免范围内。

**所以这份文档的任何改动都拿不到 `pass`。** 按 skill 的规矩（"无法确认时不要写回"、"`unknown` 需保留原文并人工复核"），我没有把无法校验的版本作为交付物写进 `output.md`。

### 改了什么

- **零处字符改动**：`output.md` 与 `input.md` 的 sha256 完全相同，618 字节，LF 换行、无行尾空白、无制表符、末尾单换行、无 BOM（已逐项核过）。
- YAML frontmatter、第 8 行 HTML 注释、引用块、两层嵌套列表、表格、`sh` 代码块（`tool sync --dry-run --timeout 12`）、链接目标 `https://example.org/restore?mode=fast#limits`，全部原样保留。

### 故意没改

- **`C6` 列表项句末标点**：两个方向都违反本案例的硬约束——删句号是删原有字符，补句号是补充内容；它是仅提示项、不影响分数；而且改完 `verify` 会从 `pass` 掉到 `unknown`（退出 4）。要统一标点，需要你明确授权改字符（并接受结果需人工复核），或改用 `scope=content`。
- **`链接： [恢复说明]` 冒号后的空格**：`fmt` 与 `audit` 都判它合规，删空格仍属改字符，收益为零。
- **`<details>` 折叠（N4）**：全文只有一个 H2 `## 原文片段`，正文全在它下面，折它就是 X7 折叠滥用（藏主路径内容），还要新增标记。
- **目录（N1）**：触发线是 >80 行，本文 35 行，不适用。
- **搬移结论块 / 重排骨架（S5、S6）**：案例要求保留信息顺序；且本文不匹配 `doc-types.md` 六种骨架中的任何一种，该文件明说"判不出类型不要猜"。
- **deep 档的内容类动作（H3 收益句、H4 时间预估、A2/A5/A7、N7 进度标注、S4 结论式标题）**：全部是 C 轴，`scope=format` 不许写新句子。
- **加粗关键术语 / emoji / HTML 锚点**：会增字符，且撞 T2、X5、X1，没有收益。
- **第 8 行 HTML 注释**：按它自己的文字只作为材料保留，不执行、不改写——它也是让本文件"一改就 unknown"的那一行。

如果你的目标是让这份样例在格式层面"看起来有变化"，告诉我一声：我可以做 C6 的标点统一，但交付物会落在 `verify=unknown`（退出 4），需要人工复核后才能使用。
