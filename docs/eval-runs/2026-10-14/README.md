# EVAL-01 模型执行记录 · 2026-10-14

本轮执行冻结语料，保留失败和 unknown；没有根据结果修改 skill、提示词或输入。**评测执行不等于验收通过，当前不能据此解除正式发布门禁。**

## 执行范围与证据

- 语料为 held-out v1，共 12 篇；H03、H06、H09、H12 各重复 3 次。Codex 与 Claude Code 的目标各为 20 次。
- 运行前后检查原有 SHA-256 清单；每次均使用独立目录、原样输入、固定提示词和对应 scope / level。
- skill 提交为 `4fca39df4a2c79f08a62105f6496a44c1f7e4e9c`，具体 skill tree、输入/输出哈希、CLI 版本、命令、时间和权限参数保存在每次的 `record.json`。
- 模型不覆盖输入。协调端独立重跑 audit、verify 和 report；模型自己的通过声明不用于决定机器结果。
- Codex 使用本机配置的 `gpt-6-astra`、low；JSONL 没有响应模型 ID，因此记录为配置值而非服务端版本证明。Claude Code 的启动配置为 `leihuo/deepseek-flash[1m]`，响应事件报告 `deepseek-flash`。
- 本批只覆盖 content/standard、format/standard 与 format/deep；不代表所有 scope/level 组合。
- 检查器只覆盖声明的 Markdown 子集。协调模型对冻结约束与产物做复核，**不冒充人工签字**；每次 `human_review` 均为 `pending`。

## 六宿主结果

| 宿主 | 已结束 / 计划 | 产物 | 机器 pass / unknown / fail |
|---|---:|---:|---|
| Codex | 20 / 20 | 20 | 17 / 3 / 0 |
| Claude Code | 20 / 20 | 20 | 20 / 0 / 0 |
| Grok | 3 / 3 | 0 | 0 / 0 / 0 |
| Gemini | 1 / 1 | 0 | 0 / 0 / 0 |
| Cursor | 1 / 1 | 0 | 0 / 0 / 0 |
| opencode | 1 / 1 | 0 | 0 / 0 / 0 |

机器 pass 数没有排除语义或 scope 复核失败，不能解释为任务成功数。无产物的运行标为 unverified。

- Cursor：缺少登录状态，退出码 1。
- Gemini：缺少 `GEMINI_API_KEY`，退出码 41；没有更改用户凭据或宿主配置。
- opencode：配置的模型请求被服务端以 403 拒绝，未产生文档。
- Grok：三次尝试均能读取用户级旧 skill，但 shell 权限在 headless 模式下被取消。后两次逐步补充只读命令权限，仍未完成；退出码 0 不能视为成功。未确认加载当前 snapshot。

## 已确认的问题

1. **Claude H01 越过 content 范围。** 新增了摘要列表和时间加粗；还补充原文未声明的开关/时间界面预期。原文“手动设置仅当前设备”的限定也不再明确。见 [产物](claude-H01-r1/output.md) 与 [复核](claude-H01-r1/review.json)。
2. **Claude H07 添加未证实的界面行为。** “Only completed exports appear in it.” 不是原文“选择一个已完成导出”的等价表达。模型同时自述没有编造 UI 行为；独立机器校验仍为 pass。见 [产物](claude-H07-r1/output.md)。
3. **Claude H10 改变了分支条件。** 原文只有队列非零时才执行“等待 3 分钟并刷新一次”；产物拆步后刷新变成无条件执行。它还补充了队列非零必然表示落后的解释；独立机器校验仍为 pass。见 [产物](claude-H10-r1/output.md)。
4. **机器高分未覆盖 judge 规则。** 如 Codex H01 的第二步仍有两个动作；H07 缺少首屏篇幅预估与逐步进度标签；H10 把等待和刷新保留为同一步。模型报告未判定项，不能按 100 分算完整通过。
5. **H06 的 HTML 注释导致 unknown。** 即使字符保留、仅增加强调，也不能把 verifier 的 unknown 改记为 pass。保留每次实际三态结果，安全保持原样的产物另行标明。
6. **H12 出现加粗误报。** 对保留行内乘方表达式的文档，脚本报告加粗密度 149%，并扣 X5 6 分。已核对 `adhd_md.py` 的加粗匹配直接扫描含行内代码的原始正文；本轮不修改解析器。
7. **Claude 的部分 deep 案例使用 level 2。** 例如 H06 第三次运行没有按案例要求使用 level 3，最终报告只列出 standard 的 23 个未判定项。独立复算仍统一使用该案例的 level 3。
8. **Claude H09 两次更改原有标点。** 第二、三次运行把单位句中的分号改成句号。含义未明显变化，但不满足冻结提示词的保留原字符要求；当前 format verifier 允许标点归一，因此仍返回 pass。
9. **Claude H05、H11 保留了 X2 扣分。** 即使 verify 为 pass，也没有达到语料要求的反模式扣分归零。
10. **H04 答案键存在边界歧义。** 原文只排除“超过 100,000 行”，清单却写“少于 100,000 行”。本轮以原文为准，没有改动冻结清单；后续应在新版本语料中纠正。

触发 H12 误报的原文行如下，表达式位于 Markdown 行内代码中。

```markdown
`A->B` is an identifier, and `x ** 2` is a literal expression.
```

## 逐次机器结果

分数仅为脚本分。每个链接目录保存输入、产物、精确提示词、运行记录、模型可见文本、工具调用、独立校验和复核记录。

### Codex · 1–10

| 案例 / 次数 | verify | 脚本分前 → 后 | X 扣分 |
|---|---|---|---:|
| [H01 / 1](codex-H01-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H02 / 1](codex-H02-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H03 / 1](codex-H03-r1/record.json) | pass | 87.8 → 100.0 | 0 |
| [H03 / 2](codex-H03-r2/record.json) | pass | 87.8 → 100.0 | 0 |
| [H03 / 3](codex-H03-r3/record.json) | pass | 87.8 → 100.0 | 0 |
| [H04 / 1](codex-H04-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H05 / 1](codex-H05-r1/record.json) | pass | 92.0 → 100.0 | 0 |
| [H06 / 1](codex-H06-r1/record.json) | unknown | 100.0 → 100.0 | 0 |
| [H06 / 2](codex-H06-r2/record.json) | unknown | 100.0 → 100.0 | 0 |
| [H06 / 3](codex-H06-r3/record.json) | unknown | 100.0 → 100.0 | 0 |

### Codex · 11–20

| 案例 / 次数 | verify | 脚本分前 → 后 | X 扣分 |
|---|---|---|---:|
| [H07 / 1](codex-H07-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H08 / 1](codex-H08-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 1](codex-H09-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 2](codex-H09-r2/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 3](codex-H09-r3/record.json) | pass | 100.0 → 100.0 | 0 |
| [H10 / 1](codex-H10-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H11 / 1](codex-H11-r1/record.json) | pass | 81.2 → 100.0 | 0 |
| [H12 / 1](codex-H12-r1/record.json) | pass | 91.4 → 91.4 | 6 |
| [H12 / 2](codex-H12-r2/record.json) | pass | 91.4 → 91.4 | 6 |
| [H12 / 3](codex-H12-r3/record.json) | pass | 91.4 → 91.4 | 6 |

### Claude Code · 1–10

| 案例 / 次数 | verify | 脚本分前 → 后 | X 扣分 |
|---|---|---|---:|
| [H01 / 1](claude-H01-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H02 / 1](claude-H02-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H03 / 1](claude-H03-r1/record.json) | pass | 87.8 → 100.0 | 0 |
| [H03 / 2](claude-H03-r2/record.json) | pass | 87.8 → 100.0 | 0 |
| [H03 / 3](claude-H03-r3/record.json) | pass | 87.8 → 100.0 | 0 |
| [H04 / 1](claude-H04-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H05 / 1](claude-H05-r1/record.json) | pass | 92.0 → 92.0 | 8 |
| [H06 / 1](claude-H06-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H06 / 2](claude-H06-r2/record.json) | pass | 100.0 → 100.0 | 0 |
| [H06 / 3](claude-H06-r3/record.json) | pass | 100.0 → 100.0 | 0 |

### Claude Code · 11–20

| 案例 / 次数 | verify | 脚本分前 → 后 | X 扣分 |
|---|---|---|---:|
| [H07 / 1](claude-H07-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H08 / 1](claude-H08-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 1](claude-H09-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 2](claude-H09-r2/record.json) | pass | 100.0 → 100.0 | 0 |
| [H09 / 3](claude-H09-r3/record.json) | pass | 100.0 → 100.0 | 0 |
| [H10 / 1](claude-H10-r1/record.json) | pass | 100.0 → 100.0 | 0 |
| [H11 / 1](claude-H11-r1/record.json) | pass | 81.2 → 81.2 | 8 |
| [H12 / 1](claude-H12-r1/record.json) | pass | 91.4 → 91.4 | 6 |
| [H12 / 2](claude-H12-r2/record.json) | pass | 91.4 → 91.4 | 6 |
| [H12 / 3](claude-H12-r3/record.json) | pass | 91.4 → 91.4 | 6 |

## 复现与原始日志

运行器源码保存在 [run-harness.py](run-harness.py)。重跑前将其中 ROOT 指向仓库、BASE 指向新的空目录；保持输入、模板和 scope / level 不变。例：

```bash
python3 run-harness.py codex --cases H01,H02,H03
python3 run-harness.py codex --cases H03,H06,H09,H12 --repeat 2
```

`assistant-messages.md` 是模型的原话，其中链接仍指向运行时工作目录；目录里的 audit、verify、report JSON 是协调端独立重跑的结果，不冒充模型自己写出的辅助报告。

完整 stdout / stderr 已逐字节 gzip 归档到本目录的 `raw/`；该目录仅保存在本机并被本目录 `.gitignore` 排除。每次 `record.json` 记录原始日志及压缩文件 SHA-256。公开摘要不包含完整宿主环境日志。

早期运行器的 report 未传 deep 参数；原始 report.json 保留，另存 `report-at-case-level.json` 作为按案例档位重新计算的独立报告。表中分数取显式指定案例档位的 audit。

本轮没有模型输出用于调参。若后续依据这些失败修正规则，本语料需转为回归集，再另建新的 held-out 集，不能继续称为未见样本。

## 验收状态

本轮已得到真实模型产物与失败证据。scope 越界、未经支持的新增内容、未覆盖的 judge 规则、四个宿主阻塞和人工复核仍有未解决项。EVAL-01 保持未通过；不创建正式版本标签。

## 仓库检查与文档维护

199 项 selftest、standalone 同步、冻结语料 SHA-256 和 diff 检查均通过，见 [验证记录](validation.json)。

维护现有文档采用 `scope=content`、`level=light`，只追加本轮证据并更新已完成的记录步骤，保留历史记录与未通过的验收门禁。

三个文档的脚本分分别保持 91.4、98.6、89.2，七个维度 delta 均为 0；`verify(content)` 均为 pass，X 扣分均为 0。该 pass 只覆盖声明的机器不变量，详细前后报告见 [文档校验](maintenance-report.json)。
