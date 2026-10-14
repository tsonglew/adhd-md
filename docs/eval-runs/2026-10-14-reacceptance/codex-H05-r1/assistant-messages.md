我会使用本案例的 adhd-md skill，按 `scope=format`、`level=standard` 调整排版，写入 `output.md`，再运行审计和格式保真校验。

原文脚本分为 92，扣分来自短文标题过密（X2）。我会把四个小标题改成保留原字的加粗标签，保留主标题和信息顺序；风险段落中的条件、先后动作及例外保持完整。

校验结果为 `pass`，退出码 0；脚本分升至 100，X 组扣分降至 0。另做的逐字节比对确认只有四处排版标记变化。报告会明确保留未满足项：H4 缺阅读时间或篇幅提示、A7 缺部分完成判据、A8 仍有复合动作，不会把脚本满分写成全部规则通过。

已写入 [output.md](/private/tmp/adhd-reacceptance-20261014/codex-H05-r1/workspace/output.md)，采用 `scope=format`、`level=standard`，未覆盖输入。

仅将四个小标题改为同字加粗标签；其余字节及信息顺序保持不变。

- **audit**：前后退出码均为 `0`；脚本分 **92 → 100**，七个维度分数均未变化。
- **反模式扣分**：**−8 → 0**，X2 已消除。
- **verify --scope=format**：退出码 `0`，状态 `pass`，无机器 `unknown`。
- **人工复核**：脚本未判定的 23 项已逐项记录；S4、H4、A7、A8 未满足，W5 仍无法判断，未算作通过。

完整命令状态、逐维度分数和判断依据见 [report.md](/private/tmp/adhd-reacceptance-20261014/codex-H05-r1/workspace/report.md)。
