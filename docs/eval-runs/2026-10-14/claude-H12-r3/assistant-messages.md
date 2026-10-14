I'll start by reading the skill definition and the input file.

Now let me read the required reference files and check the script.

Let me investigate that bold-density finding — 149% looks suspicious for this small file.

Confirmed the T2d/X5 finding is a parser artifact: the lone `**` inside `` `x ** 2` `` pairs with `**Preview**`'s opening marker, capturing 428 chars as "bold". Let me verify that reading and check `fmt`.

`fmt` reports the file is already normalized. Now let me test candidate outputs against the verifier before committing to an approach.

I'll create candidates with the Write tool instead.

Both pass. Let me check how the script implements L3 (checklist steps) and inspect the verify JSON detail.

Verify passes cleanly. Let me now write the output file and run the full check chain.

Both before and after score 91.4 with X5=6. Let me rigorously verify preservation and capture exit codes.

The report command exits 1 because X≠0. Let me confirm that's inherent to the document, not caused by my edit.

Confirmed the ✗ is inherent to the document, not my edit. Let me quantify the false positive precisely and confirm final state.

The regex artifice is confirmed, but my denominator (312) doesn't match the script's implied ~291. Let me check the script's exact `prose_all`.

Reproduced exactly (436/291 = 150%). Let me confirm the input is untouched and gather the final state.

Everything checks out. Here is the report.

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（按本 case 要求，未原地覆盖；`input.md` 保持 631 字节、mtime 未变）

### 命令与退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | 脚本分 **91.4** |
| `audit output.md --level 3 --scope=format` | **0** | 脚本分 **91.4** |
| `verify input.md output.md --scope=format` | **0** | `status=pass`，`hard_failures=[]`，`warnings=[]`，`unknowns=[]`，`ok=true` |
| `report input.md output.md --scope=format` | **1** | 因 X 组 after ≠ 0 而退出 1（见下，脚本假阳性） |
| `fmt output.md`（预览） | 0 | 格式已规范，无需修改 |

脚本分 **91.4 → 91.4（+0.0）**

| 维度 | before | after |
|---|---|---|
| 首屏结论力 | 100.0 | 100.0 |
| 分块粒度 | 100.0 | 100.0 |
| 扫读性 | 100.0 | 100.0 |
| 句子负荷 | 100.0 | 100.0 |
| 行动性 | 100.0 | 100.0 |
| 排版一致性 | 80.0 | 80.0 |
| 活人感 | 100.0 | 100.0 |

**反模式扣分 −6 → −6（X5）** —— 这是**脚本假阳性**，不是过度加粗，我没有靠它换分：

- 报告行 `T2d/X5 加粗密度 150%` 的分子是 **436 字符**，来自正则 `\*\*([^*]+)\*\*` 的错配：第 8 行行内代码里的孤立 `**`（`` `x ** 2` `` 是字面量，不是强调）被当成加粗起始，依次吞掉 118 + 305 + 13 字符。
- 实际加粗只有 3 处：`Preview`、`first copy`、`second copy` = **28 字符**；对脚本同一分母 291 字符，真实密度 **9.6%** —— 仍超 T2 的 8%（排版维度扣分属实），但**低于 X5 的 12%，X5 本不该命中**。
- 复现：`python3 -I /tmp/h12-cand/probe.py`（436/291 = 150% 与脚本一致）。
- 清零 X5 只有两条路：删掉 3 处 `**`，或改写 `` `x ** 2` `` 这个字面量 —— 两者都删除/改动原始字符，违反本 case「保留每一个原始字符」的要求。**故不回退、不消音，如实报为假阳性。** 注意 `report input.md input.md`（零改动基线）同样退出 1，证明该扣分与我的改动无关。

**verify(format)** 通过 —— 覆盖的是已声明的机器检查（块结构、行内代码值、链接目标、URL、数字/单位、frontmatter 逐字、重复次数）；`unknowns` 与 `warnings` 均为空，所以这里不存在把 `unknown` 当通过的问题。`pass` 不是语义等价的证明，句内语义、词序与解析器不支持的语法仍需人工复核。

### 未判定规则（脚本未评分，**不等于通过**）

deep·format 下适用 41 条：脚本检查 23（可计分 23）、**需模型判断 32**、仅提示 5、仅自动修复 2、硬门禁 1（X4）。

- **脚本未评分 32 条**：S4、S5、S6、S8、H3、H4、P2、P5、L2、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8
- **仅提示、不计分 5 条**：S7、L6、N3、T5、C6

我的模型判断（format 轴内可判的几条，仅为我的人工结论，非脚本结论）：S5 无结论块可搬；P5 引用块 3 行（阈值 >5）；L2 唯一候选是第 8 行 `, and` 并列句，转列表需删 `and`、加句号，属 content 权限；N4/X7 无可折叠的偏离主路径内容，也未折叠任何内容；T3 粗体=关键术语、代码体=字面量，语义一致；X6 表为 2×2 字段/值同构表；X8 无套模板小节；X3 列表项均为完整句。S4/H3/H4/W 组/A 组/C4/L4/L7 等属 content 轴，`scope=format` 下不生效，我不声称它们通过。

### 改了什么

- 把 `1. **Preview** the plan.` 下的两条 `- Confirm …` 改成 `- [ ] Confirm …`（**改标记层级**，format 允许；L3 明确要求可追踪步骤用 `- [ ]`，deep 档也含 checklist）。未动任何词、数字与顺序。
- 全文 diff 只有这两行（input 631 → output 639 字节，+8 = 两个 `[ ] `）；`verify` 通过之外，我还做了逐字节校验：把 `- [ ] ` 还原成 `- ` 后与 `input.md` **完全一致**。

### 故意没改

- **frontmatter**：format 下逐字保护，未动。
- `` `A->B` `` 与 `` `x ** 2` ``：`**` 在此是字面量的一部分，加转义或改写都会改动原始字符。
- **三处既存加粗**：删掉是清 X5 的唯一手段，但会删原始字符，且末行「Repeated terms」正是重复加粗的考点。
- **警告引用块不加 `> **注意**` 标签**：加标签就是加词（content 权限），且原文自己写着「Keep the original warning text」。
- **不生成 TOC**：30 行，未达 N1 的 >80 行阈值；加目录在本文档是噪音（X2 风险）。
- **不折叠、不搬块、不新增标题/小节**：无结论块可前置（S5），无可折叠的偏离主路径内容（N4）；新增标题需新词，越界成 content。
- **不拆末行两句**：`Repeated terms:` 是这两句共同的标签，拆段会把标签与第二项分离。

Everything checks out. Here is the report.

## 改完了：`input.md` → `output.md`

**scope** `format` · **level** `deep` · 写到 `output.md`（按本 case 要求，未原地覆盖；`input.md` 保持 631 字节、mtime 未变）

### 命令与退出状态

| 命令 | 退出码 | 结果 |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | 脚本分 **91.4** |
| `audit output.md --level 3 --scope=format` | **0** | 脚本分 **91.4** |
| `verify input.md output.md --scope=format` | **0** | `status=pass`，`hard_failures=[]`，`warnings=[]`，`unknowns=[]`，`ok=true` |
| `report input.md output.md --scope=format` | **1** | 因 X 组 after ≠ 0 而退出 1（见下，脚本假阳性） |
| `fmt output.md`（预览） | 0 | 格式已规范，无需修改 |

脚本分 **91.4 → 91.4（+0.0）**

| 维度 | before | after |
|---|---|---|
| 首屏结论力 | 100.0 | 100.0 |
| 分块粒度 | 100.0 | 100.0 |
| 扫读性 | 100.0 | 100.0 |
| 句子负荷 | 100.0 | 100.0 |
| 行动性 | 100.0 | 100.0 |
| 排版一致性 | 80.0 | 80.0 |
| 活人感 | 100.0 | 100.0 |

**反模式扣分 −6 → −6（X5）** —— 这是**脚本假阳性**，不是过度加粗，我没有靠它换分：

- 报告行 `T2d/X5 加粗密度 150%` 的分子是 **436 字符**，来自正则 `\*\*([^*]+)\*\*` 的错配：第 8 行行内代码里的孤立 `**`（`` `x ** 2` `` 是字面量，不是强调）被当成加粗起始，依次吞掉 118 + 305 + 13 字符。
- 实际加粗只有 3 处：`Preview`、`first copy`、`second copy` = **28 字符**；对脚本同一分母 291 字符，真实密度 **9.6%** —— 仍超 T2 的 8%（排版维度扣分属实），但**低于 X5 的 12%，X5 本不该命中**。
- 复现：`python3 -I /tmp/h12-cand/probe.py`（436/291 = 150% 与脚本一致）。
- 清零 X5 只有两条路：删掉 3 处 `**`，或改写 `` `x ** 2` `` 这个字面量 —— 两者都删除/改动原始字符，违反本 case「保留每一个原始字符」的要求。**故不回退、不消音，如实报为假阳性。** 注意 `report input.md input.md`（零改动基线）同样退出 1，证明该扣分与我的改动无关。

**verify(format)** 通过 —— 覆盖的是已声明的机器检查（块结构、行内代码值、链接目标、URL、数字/单位、frontmatter 逐字、重复次数）；`unknowns` 与 `warnings` 均为空，所以这里不存在把 `unknown` 当通过的问题。`pass` 不是语义等价的证明，句内语义、词序与解析器不支持的语法仍需人工复核。

### 未判定规则（脚本未评分，**不等于通过**）

deep·format 下适用 41 条：脚本检查 23（可计分 23）、**需模型判断 32**、仅提示 5、仅自动修复 2、硬门禁 1（X4）。

- **脚本未评分 32 条**：S4、S5、S6、S8、H3、H4、P2、P5、L2、L4、L7、W2、W3、W5、W7、W8、W9、A1、A2、A3、A5、A6、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8
- **仅提示、不计分 5 条**：S7、L6、N3、T5、C6

我的模型判断（format 轴内可判的几条，仅为我的人工结论，非脚本结论）：S5 无结论块可搬；P5 引用块 3 行（阈值 >5）；L2 唯一候选是第 8 行 `, and` 并列句，转列表需删 `and`、加句号，属 content 权限；N4/X7 无可折叠的偏离主路径内容，也未折叠任何内容；T3 粗体=关键术语、代码体=字面量，语义一致；X6 表为 2×2 字段/值同构表；X8 无套模板小节；X3 列表项均为完整句。S4/H3/H4/W 组/A 组/C4/L4/L7 等属 content 轴，`scope=format` 下不生效，我不声称它们通过。

### 改了什么

- 把 `1. **Preview** the plan.` 下的两条 `- Confirm …` 改成 `- [ ] Confirm …`（**改标记层级**，format 允许；L3 明确要求可追踪步骤用 `- [ ]`，deep 档也含 checklist）。未动任何词、数字与顺序。
- 全文 diff 只有这两行（input 631 → output 639 字节，+8 = 两个 `[ ] `）；`verify` 通过之外，我还做了逐字节校验：把 `- [ ] ` 还原成 `- ` 后与 `input.md` **完全一致**。

### 故意没改

- **frontmatter**：format 下逐字保护，未动。
- `` `A->B` `` 与 `` `x ** 2` ``：`**` 在此是字面量的一部分，加转义或改写都会改动原始字符。
- **三处既存加粗**：删掉是清 X5 的唯一手段，但会删原始字符，且末行「Repeated terms」正是重复加粗的考点。
- **警告引用块不加 `> **注意**` 标签**：加标签就是加词（content 权限），且原文自己写着「Keep the original warning text」。
- **不生成 TOC**：30 行，未达 N1 的 >80 行阈值；加目录在本文档是噪音（X2 风险）。
- **不折叠、不搬块、不新增标题/小节**：无结论块可前置（S5），无可折叠的偏离主路径内容（N4）；新增标题需新词，越界成 content。
- **不拆末行两句**：`Repeated terms:` 是这两句共同的标签，拆段会把标签与第二项分离。
