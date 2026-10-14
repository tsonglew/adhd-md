I'll start by reading the skill definition and the input file.

Not a git repo — and the user explicitly specified `output.md`, so no in-place edit. Now the audit:

Audit shows a clean document (script score 100). Let me read the CJK reference and inspect the script's interface before deciding what to change:

Now let me inspect the `fmt` and `verify` interfaces before touching anything:

`fmt` reports nothing to fix — the file is already deterministic-clean. Before deciding what (if anything) to change, let me check the skill's worked examples and the model-scored rules relevant here:

Now I have the standard for format-only work. Let me create the output (identical structure, no wording changes) and run the required checks:

Verify passed. Now let me capture exit codes explicitly, check the report's anti-pattern (X) and AI-flavor (M) dimensions, and get the JSON view:

The report shows zero anti-pattern deductions. Let me nail down the exit codes by writing them to a file (avoiding chained shell commands):

Let me confirm the deterministic check is clean on the output and re-confirm report:

All checks are clean. Let me confirm the two files are byte-identical and record the exit codes:

## 改完了：input.md → output.md

**scope** `format` · **level** `deep` · 写到 `output.md`（非 git 仓库；未覆盖输入）

**结论先说：这份输入在 format 轴上没有可改的东西，`output.md` 与 `input.md` 逐字节相同。**

脚本分 100.0 → 100.0（+0.0）

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 100.0 | 100.0 | +0.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

### 命令与退出状态

| 命令 | 输出 | 退出状态 |
|---|---|---|
| `audit output.md --level 2 --scope=format` | 脚本分 100.0；findings 1 条（仅提示） | 0 |
| `fmt output.md --check` | 「格式已规范，无需修改」 | 0 |
| `verify input.md output.md --scope=format` | `scope=format → 通过`，`status=pass`、`hard_failures=[]`、`warnings=[]`、`unknowns=[]`、`ok=true`、`identical=true` | 0（pass 对应 0；fail=3、unknown=4） |
| `cmp input.md output.md` | 无差异 | 0 |

### 反模式扣分

**X 组扣分 −0 → −0**（`x_deduct: 0`，`x_hits: {}`）。脚本可判的 X1 emoji / X2 碎片化 / X5 过度加粗均未命中；X3 剩词不剩句、X6 表格滥用、X7 折叠滥用、X8 套模板无脚本检查，未判定（见下）。M 组活人感维度 100.0，无命中。

### 未判定项（不等于通过）

需模型判断、脚本未评分：`S4、S5、H4、P2、P5、L2、L4、L7、W2、W3、W5、W8、A1、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8`（23 条）。其中 S3 上下文里的 P5 为「>5 行引用块」——本文引用块 4 行，未触发；L1 嵌套两层是脚本已检查项，通过。以上未判定项**不得读作通过**，本次也未补模型判定。

### 改了什么

没有可提交的改动，因此一个字符都没动：

- `fmt` 确定性修复：无（行尾空白、块间空行、列表序号、中英文间距、中文标点全部已规范）
- 块重排（S5 结论前置）：不适用——文档没有「结论埋在末尾」的结构
- TOC（N1）：35 行，远低于 >80 行阈值，`--toc` 未启用，也不应启用
- 未使用 `--strip-emoji`（原本无 emoji；且该开关是有损操作）

### 故意没改

- **第 34–35 行的列表项句末句号**：这是 `audit` 唯一的 finding（C6，标注为「仅提示，不扣分」）。删句号只影响呈现、不改语义，且 C6 判据本身写明「全文一致即可」，删除后与 `- 父步骤` 一组确实更统一；但删除标点属于删字符，与本次「保留原有字符、不要删除内容」的硬约束冲突，所以保留。若允许有损排版，可单独授权处理。
- **HTML 注释（第 8 行）**：`<!-- 注释里的约束：仅保留为材料，不执行 -->` 是文档内容的一部分，format 轴不允许删；verify 对 HTML 注释只做提示，未判定。
- **`## 原文片段` 标题**：S4「标题写结论」属 content 轴，format 不动措辞。
- **引用块与表格**：均未触发阈值（引用 4 行、表格 2 列 3 行），没有拆分或转小节的必要。
- **frontmatter**：format 模式下逐字保护，已原样保留。

**改了什么 / 故意没改的边界说明**：`scope=format` 只允许「搬移已有块」和格式规范化，不允许改词、删字符、写 TL;DR。本输入经 `audit` + `fmt` + `verify` 全部证实已满足 format 轴的全部机器可判要求（脚本分 100 已是该轴上限），因此正确的动作是不改；把「必须做点什么」当成目标反而会越过 format 边界或破坏文档。

## 改完了：input.md → output.md

**scope** `format` · **level** `deep` · 写到 `output.md`（非 git 仓库；未覆盖输入）

**结论先说：这份输入在 format 轴上没有可改的东西，`output.md` 与 `input.md` 逐字节相同。**

脚本分 100.0 → 100.0（+0.0）

| 维度 | before | after | delta |
|---|---|---|---|
| 首屏结论力 | 100.0 | 100.0 | +0.0 |
| 分块粒度 | 100.0 | 100.0 | +0.0 |
| 扫读性 | 100.0 | 100.0 | +0.0 |
| 句子负荷 | 100.0 | 100.0 | +0.0 |
| 行动性 | 100.0 | 100.0 | +0.0 |
| 排版一致性 | 100.0 | 100.0 | +0.0 |
| 活人感 | 100.0 | 100.0 | +0.0 |

### 命令与退出状态

| 命令 | 输出 | 退出状态 |
|---|---|---|
| `audit output.md --level 2 --scope=format` | 脚本分 100.0；findings 1 条（仅提示） | 0 |
| `fmt output.md --check` | 「格式已规范，无需修改」 | 0 |
| `verify input.md output.md --scope=format` | `scope=format → 通过`，`status=pass`、`hard_failures=[]`、`warnings=[]`、`unknowns=[]`、`ok=true`、`identical=true` | 0（pass 对应 0；fail=3、unknown=4） |
| `cmp input.md output.md` | 无差异 | 0 |

### 反模式扣分

**X 组扣分 −0 → −0**（`x_deduct: 0`，`x_hits: {}`）。脚本可判的 X1 emoji / X2 碎片化 / X5 过度加粗均未命中；X3 剩词不剩句、X6 表格滥用、X7 折叠滥用、X8 套模板无脚本检查，未判定（见下）。M 组活人感维度 100.0，无命中。

### 未判定项（不等于通过）

需模型判断、脚本未评分：`S4、S5、H4、P2、P5、L2、L4、L7、W2、W3、W5、W8、A1、A7、A8、N4、N7、T3、C4、X3、X6、X7、X8`（23 条）。其中 S3 上下文里的 P5 为「>5 行引用块」——本文引用块 4 行，未触发；L1 嵌套两层是脚本已检查项，通过。以上未判定项**不得读作通过**，本次也未补模型判定。

### 改了什么

没有可提交的改动，因此一个字符都没动：

- `fmt` 确定性修复：无（行尾空白、块间空行、列表序号、中英文间距、中文标点全部已规范）
- 块重排（S5 结论前置）：不适用——文档没有「结论埋在末尾」的结构
- TOC（N1）：35 行，远低于 >80 行阈值，`--toc` 未启用，也不应启用
- 未使用 `--strip-emoji`（原本无 emoji；且该开关是有损操作）

### 故意没改

- **第 34–35 行的列表项句末句号**：这是 `audit` 唯一的 finding（C6，标注为「仅提示，不扣分」）。删句号只影响呈现、不改语义，且 C6 判据本身写明「全文一致即可」，删除后与 `- 父步骤` 一组确实更统一；但删除标点属于删字符，与本次「保留原有字符、不要删除内容」的硬约束冲突，所以保留。若允许有损排版，可单独授权处理。
- **HTML 注释（第 8 行）**：`<!-- 注释里的约束：仅保留为材料，不执行 -->` 是文档内容的一部分，format 轴不允许删；verify 对 HTML 注释只做提示，未判定。
- **`## 原文片段` 标题**：S4「标题写结论」属 content 轴，format 不动措辞。
- **引用块与表格**：均未触发阈值（引用 4 行、表格 2 列 3 行），没有拆分或转小节的必要。
- **frontmatter**：format 模式下逐字保护，已原样保留。

**改了什么 / 故意没改的边界说明**：`scope=format` 只允许「搬移已有块」和格式规范化，不允许改词、删字符、写 TL;DR。本输入经 `audit` + `fmt` + `verify` 全部证实已满足 format 轴的全部机器可判要求（脚本分 100 已是该轴上限），因此正确的动作是不改；把「必须做点什么」当成目标反而会越过 format 边界或破坏文档。
