# EVAL-01 重新验收 · 2026-10-14

**结论：未通过。** 本轮发现模型执行仍会违反显式约束，机器 pass 不能替代内容与规则复核。验收期间没有修改被测 skill，也没有替换失败样本。

47 次执行已全部结束：40 次主回归、2 次最终澄清复测、4 个其他宿主探测、1 次服务故障补跑。原失败记录全部保留。

补跑 Codex H06-r4 正常退出，输出与原文逐字一致，verify pass / X=0。冻结 skill、全部输入及导出产物哈希复核通过，见 [完整性记录](final-integrity.json)。

## 未通过的原因

1. [Claude H07](claude-H07-r1/output.md) 把归档保留/排除规则改写成列表可见性的保证；源文没有描述该界面行为。报告又把缺少逐步进度标签的四步流程判为 N7 满足，理由误将 content 的格式限制扩展为不能加普通文字进度标签。见 [约束复核](claude-H07-r1/review.json)。
2. [Claude H09 第 3 次](claude-H09-r3/candidate.diff) 把原有分号改为句号。模型知道这个改动，却仍用默认 format 允许标点归一来接受它，忽略提示词的逐字保留要求；X8 判断也未填写。见 [复核](claude-H09-r3/review.json)。
3. [Claude H10](claude-H10-r1/review.json) 将记录可见强化为数据库已有新值，并在 content 范围内原样搬移警告段。旧的等待—刷新条件问题本次没有重现，但新增问题仍不符合事实与 scope 边界。

## 运行与机器门禁

| 宿主 | 原矩阵已记录 | 正常退出 | 输出 | verify pass | X=0 |
|---|---:|---:|---:|---:|---:|
| codex | 20/20 | 19 | 20 | 20 | 20 |
| claude | 20/20 | 20 | 20 | 20 | 20 |

Codex H06-r2 在生成产物后遇到 TLS/503 和模型容量错误，退出码 1。产物校验与运行完成分开记录；保留这次失败，补跑使用独立 r4，不覆盖原记录。


## 可确认的修复与限制

- H01 手动设置/当前设备限定保留，未再次新增列表、加粗或无来源的 UI 成功状态。
- 已完成的会议记录可通过标题降为原字标签消除 X2，没有填空行或补内容。
- H06 的完成输出逐字保留源文；相同文件的 pass 不表示解析器已能验证任意 HTML 改写。
- 完整 selftest 203 项、unittest 221 项、构建脚本测试 7 项通过；standalone 和规则生成检查通过。日志保存在本目录。
- S4 等主观判断仍有偏宽案例，例如 Claude H04 将“恢复步骤”判为结论式标题；协调端单独保留此判断差异。

## 方法与证据

- [验收标准](acceptance-policy.md) 与 [运行计划](plan.json) 在复核前固定。使用旧 H01–H12 回归集，H03/H06/H09/H12 各重复三次；它们已用于修复，不能再称盲测。R01 另外核对最终 A8/S4 澄清。
- 原始提示词、输入、输出、独立 audit/verify/report、模型可见报告、工具调用及逐次 review.json 均保留。完整日志与实际 skill 副本压缩保存在本地 raw/（不入 Git）。
- [skill-snapshot.json](skill-snapshot.json) 与逐次 actual-skill-snapshot.json 指向实际未提交工作区版本；HEAD 字段单独不足以描述本轮版本，差异另存 source.patch。
- [模型配置](model-config.json)：Codex 配置 gpt-6-astra/ultra，首次评测为 low，不能把差异全部归因于 skill。Claude 配置 leihuo/deepseek-flash[1m]，响应模型 ID 单独记录。配置不等于服务器版本证明。
- 信息保留由协调端对照预标注约束和源文复核，不依赖被测模型自述，不冒充独立人工签字。EVAL-01 清单允许“独立人工或已标注约束”这一替代路径；整体门禁仍因上述失败未关闭。
- H04 以源文的“超过 100,000 行不适用”为准，不采用历史答案键中“少于”的边界错误。冻结语料不追改。

## 其他宿主重试

| 宿主 | 结果 |
|---|---|
| Cursor | 缺少登录或 CURSOR_API_KEY；exit 1，无输出 |
| Gemini | 缺少 GEMINI_API_KEY，目录未受信；exit 41，无输出 |
| opencode | 网关拒绝 claude-sonnet-4-6 的 /v1/chat/completions 请求，HTTP 403；exit 1，无输出 |
| Grok | 读取用户级旧 skill，未确认加载本轮 snapshot；终端调用被取消，MCP 还出现 502；exit 0 但无输出 |

这四个宿主均为 unverified；没有改用户认证、权限或网关配置。逐次 host-observation.json 分开记录路径提供、加载证据、工具调用和最终输出。

## 逐次结果

| 运行 | CLI | verify | X 扣分 | 约束/报告复核 |
|---|---:|---|---:|---|
| [claude-H01-r1](claude-H01-r1/metadata.json) | 0 | pass | 0 | pass under declared constraint and reporting criteria |
| [claude-H02-r1](claude-H02-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H03-r1](claude-H03-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H03-r2](claude-H03-r2/metadata.json) | 0 | pass | 0 | pass |
| [claude-H03-r3](claude-H03-r3/metadata.json) | 0 | pass | 0 | pass |
| [claude-H04-r1](claude-H04-r1/metadata.json) | 0 | pass | 0 | information/scope gates pass; judge caveat recorded |
| [claude-H05-r1](claude-H05-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H06-r1](claude-H06-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H06-r2](claude-H06-r2/metadata.json) | 0 | pass | 0 | pass |
| [claude-H06-r3](claude-H06-r3/metadata.json) | 0 | pass | 0 | pass |
| [claude-H07-r1](claude-H07-r1/metadata.json) | 0 | pass | 0 | fail despite verify pass and X=0 |
| [claude-H08-r1](claude-H08-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H09-r1](claude-H09-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H09-r2](claude-H09-r2/metadata.json) | 0 | pass | 0 | pass |
| [claude-H09-r3](claude-H09-r3/metadata.json) | 0 | pass | 0 | fail despite verify pass and X=0 |
| [claude-H10-r1](claude-H10-r1/metadata.json) | 0 | pass | 0 | fail despite verify pass and X=0 |
| [claude-H11-r1](claude-H11-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H12-r1](claude-H12-r1/metadata.json) | 0 | pass | 0 | pass |
| [claude-H12-r2](claude-H12-r2/metadata.json) | 0 | pass | 0 | pass |
| [claude-H12-r3](claude-H12-r3/metadata.json) | 0 | pass | 0 | pass |
| [claude-R01-r1](claude-R01-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H01-r1](codex-H01-r1/metadata.json) | 0 | pass | 0 | pass under declared constraint and reporting criteria |
| [codex-H02-r1](codex-H02-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H03-r1](codex-H03-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H03-r2](codex-H03-r2/metadata.json) | 0 | pass | 0 | pass |
| [codex-H03-r3](codex-H03-r3/metadata.json) | 0 | pass | 0 | pass |
| [codex-H04-r1](codex-H04-r1/metadata.json) | 0 | pass | 0 | pass under declared constraint and reporting criteria |
| [codex-H05-r1](codex-H05-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H06-r1](codex-H06-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H06-r2](codex-H06-r2/metadata.json) | 1 | pass | 0 | artifact gates pass; runtime failed due to service capacity, separate recovery run required |
| [codex-H06-r3](codex-H06-r3/metadata.json) | 0 | pass | 0 | pass |
| [codex-H06-r4](codex-H06-r4/metadata.json) | 0 | pass | 0 | pass |
| [codex-H07-r1](codex-H07-r1/metadata.json) | 0 | pass | 0 | pass under declared constraint and reporting criteria |
| [codex-H08-r1](codex-H08-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H09-r1](codex-H09-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H09-r2](codex-H09-r2/metadata.json) | 0 | pass | 0 | pass |
| [codex-H09-r3](codex-H09-r3/metadata.json) | 0 | pass | 0 | pass |
| [codex-H10-r1](codex-H10-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H11-r1](codex-H11-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H12-r1](codex-H12-r1/metadata.json) | 0 | pass | 0 | pass |
| [codex-H12-r2](codex-H12-r2/metadata.json) | 0 | pass | 0 | pass |
| [codex-H12-r3](codex-H12-r3/metadata.json) | 0 | pass | 0 | pass |
| [codex-R01-r1](codex-R01-r1/metadata.json) | 0 | pass | 0 | pass |
| [cursor-H01-r1](cursor-H01-r1/metadata.json) | 1 | 无产物 | — | unverified: no output |
| [gemini-H01-r1](gemini-H01-r1/metadata.json) | 41 | 无产物 | — | unverified: no output |
| [grok-H01-r1](grok-H01-r1/metadata.json) | 0 | 无产物 | — | unverified: no output |
| [opencode-H01-r1](opencode-H01-r1/metadata.json) | 1 | 无产物 | — | unverified: no output |
