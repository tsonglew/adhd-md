I'll start by reading the skill and the input file.

Now I have what I need. The input is short already, so the work is content-level: conclusion-first lead, conclusion-style headings, step-level verification (A7), splitting compound steps (A8), progress/length marking (N7/H4). Under `scope=content` I must not touch layout style, so no new headings, no bold, no blockquote conversions.

The verifier protects the scope sentence as a literal — it must stay verbatim. Fixing:

Done. `input.md` is untouched; the rewrite is in `output.md`.

## 改完了：`input.md` → `output.md`

**mode** `edit` · **scope** `content` · **level** `standard` · 写到 `output.md`
Path rule: the workspace is not a git repo, and you asked for a separate output file, so no in-place edit. Step 2 (`fmt`) was skipped — `scope=content` never runs it.

**脚本分 100.0 → 100.0 (+0.0)**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 100.0 | 100.0 | +0.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

**反模式扣分（X 组） −0 → −0** — requirement met (after must be 0).
**findings(content)** 0 → 0；whole-document 1 → 1 (N3 only, F-axis, advisory).
**verify(content)** 通过 — no hard failures, no warnings, no `unknown`. One hard failure did occur mid-run and was fixed, not ignored: the verifier treats the whole sentence after `Scope:` as a protected literal, so my "…search index **only**." wording was rejected as `protected_literals_missing`; I reverted that line to the original bytes. `pass` covers only the declared checks — it is not proof of semantic equivalence.
**这不是最终分**：脚本按未命中计入的 23 条规则（content 范围内 14 条）仍需模型判断，见下。

**改了什么**
- Lead: added a two-sentence summary line under the scope statement — "Check the three signs, then work the six recovery steps in order. Requeueing does not modify the primary database." (the safety sentence was moved up from the last line; nothing deleted)
- Moved "Do not rebuild the global index during business hours." from the end to the top of Recovery, before the reader acts
- Headings now carry the answer: `Confirm the issue` → `Confirm the three signs`; `Recovery` → `Recovery — 6 steps` (S4, H4, N7's "共 N 步")
- Split the compound step "wait 3 minutes **and** refresh the dashboard once" into step 3 and step 4 (A8)
- Added a verification line to the two steps that had none, using the runbook's own conditions (A7): step 1 "You will use these three values for the requeue and the final confirmation."; step 2 "A nonzero depth means the indexer is still behind." No outputs were invented.

**故意没改**
- The `Scope:` sentence — byte-identical, because the verifier protects it as a literal (see above)
- No layout changes at all: no bold, no `---`, no `> **Warning**` conversion, no TOC or `<details>`. N3 ("add a divider between the two H2 sections") stays unfixed — F axis, advisory, unscored, and out of content scope
- The three diagnosis bullets keep their original order and wording (they are conditions, not prose to rewrite)
- "six steps" instead of "about N minutes": the document states no duration and I won't invent one

**需模型判断、脚本未评分（content · standard，14 条）** — my judgment, not script output:

| 规则 | 我的判断 |
|---|---|
| S4 标题写结论 | 命中 —— 两个 H2 都写答案与规模 |
| H4 篇幅预估 | 命中 —— 首屏与标题给出步数（6） |
| A7 每步给验证 | 命中 —— 步骤 1、2、3、5、6 均带条件或确认 |
| A8 一步一动作 | 命中 —— 唯一的复合步骤已拆开 |
| N7 进度标注 | 命中 —— 有序列表 1–6 + 标题/首屏声明共 6 步；未在每项重复 "Step X of 6"（避免噪音） |
| A1 结尾给下一步 | 命中 —— 诊断节以分支结尾，恢复节以第 6 步结尾 |
| L7 / X3 列表项完整语义 | 命中 —— 无碎词项 |
| W2 主动语态 | 命中 —— 无被动句 |
| W3 括号插入语 | 命中 —— 无括号插入语 |
| W5 术语首现即解释 | 部分 —— "indexer queue depth" 的含义由步骤 2 的判断句给出 |
| W8 一句一从句 | 命中 |
| L4 列表项平行结构 | 部分 —— 编号步骤均为动词开头，步骤 3、5 以条件从句开头（条件必须在前，否则丢分支） |
| C4（中文长定语） | 不适用 —— 文档语言为 `en`，脚本仍把它计入适用集；我不把它报成通过 |

Judged rules outside content scope (9 more, from the full-axis audit: S5, P2, P5, L2, N4, T3, X6, X7, X8) are also unscored; hint-only advisories C7, M2, M10 carry no score. Everything in that table is my own reading — the script proves none of it.

Done. `input.md` is untouched; the rewrite is in `output.md`.

## 改完了：`input.md` → `output.md`

**mode** `edit` · **scope** `content` · **level** `standard` · 写到 `output.md`
Path rule: the workspace is not a git repo, and you asked for a separate output file, so no in-place edit. Step 2 (`fmt`) was skipped — `scope=content` never runs it.

**脚本分 100.0 → 100.0 (+0.0)**

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 100.0 | 100.0 | +0.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

**反模式扣分（X 组） −0 → −0** — requirement met (after must be 0).
**findings(content)** 0 → 0；whole-document 1 → 1 (N3 only, F-axis, advisory).
**verify(content)** 通过 — no hard failures, no warnings, no `unknown`. One hard failure did occur mid-run and was fixed, not ignored: the verifier treats the whole sentence after `Scope:` as a protected literal, so my "…search index **only**." wording was rejected as `protected_literals_missing`; I reverted that line to the original bytes. `pass` covers only the declared checks — it is not proof of semantic equivalence.
**这不是最终分**：脚本按未命中计入的 23 条规则（content 范围内 14 条）仍需模型判断，见下。

**改了什么**
- Lead: added a two-sentence summary line under the scope statement — "Check the three signs, then work the six recovery steps in order. Requeueing does not modify the primary database." (the safety sentence was moved up from the last line; nothing deleted)
- Moved "Do not rebuild the global index during business hours." from the end to the top of Recovery, before the reader acts
- Headings now carry the answer: `Confirm the issue` → `Confirm the three signs`; `Recovery` → `Recovery — 6 steps` (S4, H4, N7's "共 N 步")
- Split the compound step "wait 3 minutes **and** refresh the dashboard once" into step 3 and step 4 (A8)
- Added a verification line to the two steps that had none, using the runbook's own conditions (A7): step 1 "You will use these three values for the requeue and the final confirmation."; step 2 "A nonzero depth means the indexer is still behind." No outputs were invented.

**故意没改**
- The `Scope:` sentence — byte-identical, because the verifier protects it as a literal (see above)
- No layout changes at all: no bold, no `---`, no `> **Warning**` conversion, no TOC or `<details>`. N3 ("add a divider between the two H2 sections") stays unfixed — F axis, advisory, unscored, and out of content scope
- The three diagnosis bullets keep their original order and wording (they are conditions, not prose to rewrite)
- "six steps" instead of "about N minutes": the document states no duration and I won't invent one

**需模型判断、脚本未评分（content · standard，14 条）** — my judgment, not script output:

| 规则 | 我的判断 |
|---|---|
| S4 标题写结论 | 命中 —— 两个 H2 都写答案与规模 |
| H4 篇幅预估 | 命中 —— 首屏与标题给出步数（6） |
| A7 每步给验证 | 命中 —— 步骤 1、2、3、5、6 均带条件或确认 |
| A8 一步一动作 | 命中 —— 唯一的复合步骤已拆开 |
| N7 进度标注 | 命中 —— 有序列表 1–6 + 标题/首屏声明共 6 步；未在每项重复 "Step X of 6"（避免噪音） |
| A1 结尾给下一步 | 命中 —— 诊断节以分支结尾，恢复节以第 6 步结尾 |
| L7 / X3 列表项完整语义 | 命中 —— 无碎词项 |
| W2 主动语态 | 命中 —— 无被动句 |
| W3 括号插入语 | 命中 —— 无括号插入语 |
| W5 术语首现即解释 | 部分 —— "indexer queue depth" 的含义由步骤 2 的判断句给出 |
| W8 一句一从句 | 命中 |
| L4 列表项平行结构 | 部分 —— 编号步骤均为动词开头，步骤 3、5 以条件从句开头（条件必须在前，否则丢分支） |
| C4（中文长定语） | 不适用 —— 文档语言为 `en`，脚本仍把它计入适用集；我不把它报成通过 |

Judged rules outside content scope (9 more, from the full-axis audit: S5, P2, P5, L2, N4, T3, X6, X7, X8) are also unscored; hint-only advisories C7, M2, M10 carry no score. Everything in that table is my own reading — the script proves none of it.
