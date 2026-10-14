I'll start by reading the skill and the input document.

Now let me run the audit on the input file.

Now let me check the evidence reference and confirm the exact byte-level details of the input.

Input is 21 lines, LF, no trailing-space issues; the workspace is **not a git repo** (so I write to a separate `output.md`, as instructed). `scope=content` → skipping step 2 (`fmt`) per the skill.

Now writing the content rewrite:

I made an error there — splitting step 3 produced 6 steps while the label still read "共 5 步". Let me fix that and restore the correct step count:

The report exposes exactly what the skill warns about: X-group deduction went 0 → −6, and 排版一致性 dropped 20 points. The bold progress labels pushed bold density over the limit. Let me see the new findings before fixing:

Confirmed: X5 (over-bolding) — my bold labels. Let me strip them and keep the progress text plain:

verify(content) = **pass**. Let me reproduce the intermediate (over-formatted) draft to get exact numbers for the report, since that's the X-group finding I must disclose:

All checks pass. Here's the report.

## 改完了：`input.md` → `output.md`

**scope** `content` · **level** `standard`（本案例指定）· 写到 `output.md`（工作区不是 git 仓库，且按要求不覆盖输入；`scope=content` 故跳过第 2 步 `fmt`）

脚本分 **100.0 → 100.0**（+0.0）

| 维度 | before | after |
|---|---|---|
| 首屏结论力 18% | 100.0 | 100.0 |
| 分块粒度 18% | 100.0 | 100.0 |
| 扫读性 13% | 100.0 | 100.0 |
| 句子负荷 13% | 100.0 | 100.0 |
| 行动性 12% | 100.0 | 100.0 |
| 排版一致性 13% | 100.0 | 100.0 |
| 活人感 13% | 100.0 | 100.0 |

**反模式扣分 0 → 0** ✓（after 为 0）

**verify(content)** `pass` —— 硬失败 0、警告 0、`unknowns` 空、`ok=true`。检查范围：代码块正文、链接目标与行内代码值、数字与单位、技术标识符、frontmatter。本文档无代码块、无链接、无行内代码，行内数值仅 `100,000` / `2`，逐字保留。这**不是**语义等价的完整证明。
完整分档：脚本 `score.band` 为 `null`（脚本分不含人工判断，不给档位）。

**改了什么**
- 补篇幅/时间预估一行（H4）：`正文约 1 分钟读完，恢复步骤共 5 步`
- 给 `## 先确认` 补判断句「以下三条同时成立，才走恢复步骤」，补上原文缺的「确认通过之后做什么」（A1）
- 5 个恢复步骤各加进度标注「第 X 步，共 5 步」（N7，纯文本，未加粗——见下方回退记录）
- 第 1 项「2 分钟」补同位语，点明它是故障判定条件而非背景

**故意没改**
- 标题三处原样：`# 导出任务没有完成` 本身是问题陈述，两个 H2 是 runbook 的祈使式小标题，改成结论式反而拉长
- 末段约束块**不前置**：它是边界条件，不是结论；首行 `范围：` 已承担结论前置功能，前 15 行满足 H1
- **不补 A7 预期输出**：原文只在第 2、3、5 步给了判断条件（「确认状态仍未变化」「等状态变为『已取消』」「若…超过 2 分钟」）。给第 1、4 步编造「跑完会看到什么」属于编造事实，明确放弃
- **不拆步骤**：第 3 步的「取消并等待」是取消动作加其完成条件，拆开会改变步骤编号，而编号被首屏声明和进度标注引用
- 不提 worker 术语解释：该词只在末段出现一次，属边界说明，加解释会拉长这一句
- `## 先确认` 第 2 项的「工作区」保留：脚本 C7 提示「工作」是虚词壳（`input.md:8` / `output.md:12`），但此处「工作区」是技术名词，不是虚词壳，改掉就是改词义

**回退记录（反模式）**
先用了加粗进度标签 `**第 1 步，共 5 步**`，`report` 立刻显示：脚本分 91.4，加粗密度 17% > 12%，`X5` 扣 6 分，排版一致性 80.0，且顺带把第 3 步拆成了 6 步却仍写「共 5 步」。这正是 skill 警告的「靠过度格式化换分数」，已整体回退为纯文本标注。上面表格的 after 列是回退后的复测值。

**未判定项（14 条 judge 规则，脚本未评分 —— 不等于通过）**
`S4` `H4` `L4` `L7` `W2` `W3` `W5` `W8` `A1` `A7` `A8` `N7` `C4` `X3` —— 我的逐条判定见上文「改了什么 / 故意没改」。脚本总覆盖 37 条：脚本检查 19、仅提示 3（`C7` `M2` `M10`，不扣分）、需判断 14、硬门禁 1。
另有 `S5` `P2` `P5` `N4` `X6` `X7` `X8` `T3` 等属 `--scope=both` 展示的全轴未判定项，本次 `scope=content` 未纳入判定。

All checks pass. Here's the report.

## 改完了：`input.md` → `output.md`

**scope** `content` · **level** `standard`（本案例指定）· 写到 `output.md`（工作区不是 git 仓库，且按要求不覆盖输入；`scope=content` 故跳过第 2 步 `fmt`）

脚本分 **100.0 → 100.0**（+0.0）

| 维度 | before | after |
|---|---|---|
| 首屏结论力 18% | 100.0 | 100.0 |
| 分块粒度 18% | 100.0 | 100.0 |
| 扫读性 13% | 100.0 | 100.0 |
| 句子负荷 13% | 100.0 | 100.0 |
| 行动性 12% | 100.0 | 100.0 |
| 排版一致性 13% | 100.0 | 100.0 |
| 活人感 13% | 100.0 | 100.0 |

**反模式扣分 0 → 0** ✓（after 为 0）

**verify(content)** `pass` —— 硬失败 0、警告 0、`unknowns` 空、`ok=true`。检查范围：代码块正文、链接目标与行内代码值、数字与单位、技术标识符、frontmatter。本文档无代码块、无链接、无行内代码，行内数值仅 `100,000` / `2`，逐字保留。这**不是**语义等价的完整证明。
完整分档：脚本 `score.band` 为 `null`（脚本分不含人工判断，不给档位）。

**改了什么**
- 补篇幅/时间预估一行（H4）：`正文约 1 分钟读完，恢复步骤共 5 步`
- 给 `## 先确认` 补判断句「以下三条同时成立，才走恢复步骤」，补上原文缺的「确认通过之后做什么」（A1）
- 5 个恢复步骤各加进度标注「第 X 步，共 5 步」（N7，纯文本，未加粗——见下方回退记录）
- 第 1 项「2 分钟」补同位语，点明它是故障判定条件而非背景

**故意没改**
- 标题三处原样：`# 导出任务没有完成` 本身是问题陈述，两个 H2 是 runbook 的祈使式小标题，改成结论式反而拉长
- 末段约束块**不前置**：它是边界条件，不是结论；首行 `范围：` 已承担结论前置功能，前 15 行满足 H1
- **不补 A7 预期输出**：原文只在第 2、3、5 步给了判断条件（「确认状态仍未变化」「等状态变为『已取消』」「若…超过 2 分钟」）。给第 1、4 步编造「跑完会看到什么」属于编造事实，明确放弃
- **不拆步骤**：第 3 步的「取消并等待」是取消动作加其完成条件，拆开会改变步骤编号，而编号被首屏声明和进度标注引用
- 不提 worker 术语解释：该词只在末段出现一次，属边界说明，加解释会拉长这一句
- `## 先确认` 第 2 项的「工作区」保留：脚本 C7 提示「工作」是虚词壳（`input.md:8` / `output.md:12`），但此处「工作区」是技术名词，不是虚词壳，改掉就是改词义

**回退记录（反模式）**
先用了加粗进度标签 `**第 1 步，共 5 步**`，`report` 立刻显示：脚本分 91.4，加粗密度 17% > 12%，`X5` 扣 6 分，排版一致性 80.0，且顺带把第 3 步拆成了 6 步却仍写「共 5 步」。这正是 skill 警告的「靠过度格式化换分数」，已整体回退为纯文本标注。上面表格的 after 列是回退后的复测值。

**未判定项（14 条 judge 规则，脚本未评分 —— 不等于通过）**
`S4` `H4` `L4` `L7` `W2` `W3` `W5` `W8` `A1` `A7` `A8` `N7` `C4` `X3` —— 我的逐条判定见上文「改了什么 / 故意没改」。脚本总覆盖 37 条：脚本检查 19、仅提示 3（`C7` `M2` `M10`，不扣分）、需判断 14、硬门禁 1。
另有 `S5` `P2` `P5` `N4` `X6` `X7` `X8` `T3` 等属 `--scope=both` 展示的全轴未判定项，本次 `scope=content` 未纳入判定。
