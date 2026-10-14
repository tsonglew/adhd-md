I'll start by reading the skill definition and the input file.

Now let me examine the skill's scripts and references.

Let me check the reference-document example to calibrate scope=format expectations.

I have what I need. Let me draft candidate format-only outputs and test them empirically.

Let me verify character-level preservation programmatically.

Character-identical modulo whitespace confirms candidate A is the faithful choice. Let me write `output.md`.

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（本目录不是 git 仓库，按 skill 第 0 步不能原地改；案例指令也指定了新文件，`input.md` 未改动）

脚本分 **87.8 → 100.0**（+12.2）

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | 0 |
| 句子负荷 | 100.0 | 100.0 | 0 |
| 行动性 | 100.0 | 100.0 | 0 |
| 排版一致性 | 100.0 | 100.0 | 0 |
| 活人感 | 100.0 | 100.0 | 0 |

### 脚本退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | 87.8 分；findings(format) 1 条：`P1` @ `input.md:10`；**反模式扣分 −0** |
| `audit output.md --level 3 --scope=format` | **0** | 100.0 分；findings 0 条；**反模式扣分 −0** |
| `verify input.md output.md --scope=format` | **0** | `status=pass`，`hard_failures=[]`、`warnings=[]`、`unknowns=[]` |
| `fmt --check output.md` | **0** | 格式已规范，无需修改 |

覆盖（deep · format）：适用 41 条；脚本检查 23（可计分 23）；仅提示 5；需判断 10；仅自动修复 2；硬门禁 1。

**未判定项：`audit` 在全文所有轴上列出 32 条需模型判断的规则未评分**（S4、S5、S6、S8、H3、H4、P2、P5、L2、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8），其中落在 deep·format 适用范围内的是 S5、S6、P2、P5、L2、N4、T3、X6、X7、X8 共 10 条。**这 32 条未判定，不等于通过**；脚本分 100 只是 23 条机器检查项满分，不是最终分。本次 `verify` 没有返回 `unknown`（三态明确落在 `pass`），但 `pass` 也只覆盖它声明支持的机器检查，不是语义等价证明。

### 改了什么

- **在既有句界拆段（format）**：`input.md:10` 的 4 句段落（`P1` 命中）拆成两段，2 句 + 2 句，中间补一个空行。前段是重试行为（`retryCount=0` 不重试 / HTTP `429` 走 `Retry-After`），后段是默认值与未知参数处理，一段一件事。
- 字符级复核：去掉所有空白后，`output.md` 与 `input.md` **完全一致**——没有增删任何一个字符、数字、单位、条件、例外、链接目标或代码值；代码块正文逐字未动，行内代码值全部保留，信息顺序未变。

### 故意没改

- **块顺序重排 / 结论前置（S5、S6）**：案例要求保留信息顺序；且文档类型是参考类，读者九成是来查单个参数的，重排会破坏跳读（`doc-types.md` 明确警告别把参考文档重排成别的类型）。现有顺序已经符合参考骨架：H1 → 速查表 → 例外说明 → 示例。
- **TL;DR、时间预估、下一步动作（H1/H2/H3/H4/A1/A2）**：都属 content 轴，`scope=format` 不允许新写措辞。首屏那 +60 分要如实说明：这是脚本把「前 15 行内第一个 ≤3 句、≤80 字的段落」判定为结论块的启发式结果，不是我做了结论前置——文档段序一点没动，S5 仍是未判定项。
- **把第 10 行三条规则转成列表（L2）**：会删掉句末的「。」并新增「- 」标记，与「保留原有字符」冲突；拆成两段后 P1、P2 已满足，收益不足。
- **给「示例」加 `##` 标题**：原文没有这个标题，「标题层级修正」只适用于已有标题；凭空补标题属于补充内容。
- **TOC（N1）**：19 行，未到 >80 行阈值。
- **`<details>` 折叠（N4）**：没有可复用的既有标题文字当 `<summary>`，且表格与规则说明是主路径内容（会触 X7）。
- **加粗关键术语（T2/T3/X5）**：原文已统一用行内代码标记字面量，再叠一层粗体属于混用标记语义，也逼近 8% 上限。
- **表格拆分（N5）**：4 列 6 行，在上限内；示例代码块已有 `json` 语言标签，无需补。

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（本目录不是 git 仓库，按 skill 第 0 步不能原地改；案例指令也指定了新文件，`input.md` 未改动）

脚本分 **87.8 → 100.0**（+12.2）

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 40.0 | 100.0 | +60.0 |
| 分块粒度 | 92.0 | 100.0 | +8.0 |
| 扫读性 | 100.0 | 100.0 | 0 |
| 句子负荷 | 100.0 | 100.0 | 0 |
| 行动性 | 100.0 | 100.0 | 0 |
| 排版一致性 | 100.0 | 100.0 | 0 |
| 活人感 | 100.0 | 100.0 | 0 |

### 脚本退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | 87.8 分；findings(format) 1 条：`P1` @ `input.md:10`；**反模式扣分 −0** |
| `audit output.md --level 3 --scope=format` | **0** | 100.0 分；findings 0 条；**反模式扣分 −0** |
| `verify input.md output.md --scope=format` | **0** | `status=pass`，`hard_failures=[]`、`warnings=[]`、`unknowns=[]` |
| `fmt --check output.md` | **0** | 格式已规范，无需修改 |

覆盖（deep · format）：适用 41 条；脚本检查 23（可计分 23）；仅提示 5；需判断 10；仅自动修复 2；硬门禁 1。

**未判定项：`audit` 在全文所有轴上列出 32 条需模型判断的规则未评分**（S4、S5、S6、S8、H3、H4、P2、P5、L2、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8），其中落在 deep·format 适用范围内的是 S5、S6、P2、P5、L2、N4、T3、X6、X7、X8 共 10 条。**这 32 条未判定，不等于通过**；脚本分 100 只是 23 条机器检查项满分，不是最终分。本次 `verify` 没有返回 `unknown`（三态明确落在 `pass`），但 `pass` 也只覆盖它声明支持的机器检查，不是语义等价证明。

### 改了什么

- **在既有句界拆段（format）**：`input.md:10` 的 4 句段落（`P1` 命中）拆成两段，2 句 + 2 句，中间补一个空行。前段是重试行为（`retryCount=0` 不重试 / HTTP `429` 走 `Retry-After`），后段是默认值与未知参数处理，一段一件事。
- 字符级复核：去掉所有空白后，`output.md` 与 `input.md` **完全一致**——没有增删任何一个字符、数字、单位、条件、例外、链接目标或代码值；代码块正文逐字未动，行内代码值全部保留，信息顺序未变。

### 故意没改

- **块顺序重排 / 结论前置（S5、S6）**：案例要求保留信息顺序；且文档类型是参考类，读者九成是来查单个参数的，重排会破坏跳读（`doc-types.md` 明确警告别把参考文档重排成别的类型）。现有顺序已经符合参考骨架：H1 → 速查表 → 例外说明 → 示例。
- **TL;DR、时间预估、下一步动作（H1/H2/H3/H4/A1/A2）**：都属 content 轴，`scope=format` 不允许新写措辞。首屏那 +60 分要如实说明：这是脚本把「前 15 行内第一个 ≤3 句、≤80 字的段落」判定为结论块的启发式结果，不是我做了结论前置——文档段序一点没动，S5 仍是未判定项。
- **把第 10 行三条规则转成列表（L2）**：会删掉句末的「。」并新增「- 」标记，与「保留原有字符」冲突；拆成两段后 P1、P2 已满足，收益不足。
- **给「示例」加 `##` 标题**：原文没有这个标题，「标题层级修正」只适用于已有标题；凭空补标题属于补充内容。
- **TOC（N1）**：19 行，未到 >80 行阈值。
- **`<details>` 折叠（N4）**：没有可复用的既有标题文字当 `<summary>`，且表格与规则说明是主路径内容（会触 X7）。
- **加粗关键术语（T2/T3/X5）**：原文已统一用行内代码标记字面量，再叠一层粗体属于混用标记语义，也逼近 8% 上限。
- **表格拆分（N5）**：4 列 6 行，在上限内；示例代码块已有 `json` 语言标签，无需补。
