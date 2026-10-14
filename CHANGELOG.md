# 变更记录

本文件记录正式版本与待发布改动。`v0.1.0` 因缺少版本章节未发布成功；保留原标签，首次正式发行使用 `v0.1.1`。

## Unreleased

暂无待发布条目。

## 0.1.1 - 2026-10-14

### 新增

- 增加 `extract` 与 `read` 的网页、PDF 提取和离线阅读流程；PDF 文本层使用 Poppler，扫描页可选用 Tesseract 与语言包。
- 集中维护评分规则，并生成规则、评分和证据映射表。审计与对比报告会显示规则覆盖范围。
- 增加 Python、Node CLI、npm tarball、安装器和官网构建的独立 CI 检查配置。

### 改进

- 修复加粗密度统计：排除行内代码、链接目标、转义分隔符和标题，避免跨段误配。
- 明确事实、条件、scope、用户逐字约束及 unknown 回退边界，补齐模型回归与已知失败记录。
- 增加标签版本与发布说明校验，通过复用 CI 后自动创建 GitHub Release。

- `verify` 使用 `pass`、`fail`、`unknown` 三态；对不能可靠判断或仍有警告的内容不再报告为通过。
- `fmt --write` 仅在保护检查通过后原子写回，并拒绝不安全文件类型和并发修改；`--strip-emoji` 明确作为有损操作。
- 审计与报告 JSON 升至 schema 2，加入覆盖统计和 scope 过滤后的 findings。保留既有 `findings`、`scope`、`hard_failures`、`warnings` 与 `ok` 字段。
- 安装器按用户级或项目级范围管理资产，并使用归属标记保护无法确认来源的旧目录。
- 改善移动端语言切换、键盘焦点、复制失败反馈、减少动态效果和 OG 资源生成。

### 调用方迁移说明

- `verify` 的退出码为 `0`（pass）、`3`（fail）、`4`（unknown）。自动化调用方应处理退出码 `4`；JSON 调用方应检查 `status`，并只把 `ok: true` / `status: "pass"` 视为机器检查通过。旧 JSON 字段仍保留，但 `ok` 在 unknown 时为 `false`。
- `audit --json` 与 `report --json` 的 `schema_version` 现在为 `2`。既有 `findings` 字段仍包含所有适用轴；`shown_findings` 按 scope 过滤。scope 只筛选 findings 和 coverage，脚本分仍按全文所有适用轴计算。`score.band` 在脚本分场景为 `null`，不能再假定始终是字符串。
- `fmt --write` 遇到校验失败、unknown、符号链接、硬链接、非 UTF-8 文件、并发改动或替换失败时会拒绝写回并返回非零状态。先备份目标文件，再对少量样本运行 `fmt --check`，确认报告后使用 `--write`。`--strip-emoji` 会改变内容，不属于无损格式化。
- 卸载器只移除能由软链目标或管理标记确认归属的资产。早期无标记目录会被保留；用户需先检查目录内容，再手动清理。

### 验证状态与已知限制

- 本地测试和构建记录见 [`docs/implementation-checklist.md`](docs/implementation-checklist.md)；当前宿主版本和真实执行状态见 [`docs/host-matrix.md`](docs/host-matrix.md)。
- 先前托管 CI 与失败注入已验证；本版本标签仍须通过发布工作流中的完整 CI。模型验收采用预标注约束复核：当前 9 例、30 份主回归产物通过门禁，一次服务故障已单独补跑成功。
- 按用户要求排除 H07、H09、H10，相关 UI 事实推断、逐字约束和 scope 问题仍保留为已知限制；未宣称原 12 例全量通过。Cursor、Gemini、opencode、Grok 未完成验证，真实读者试验暂缓。历史原始产物与范围变更见 `docs/eval-corpus/README.md` 和 `docs/eval-runs/2026-10-14-reacceptance/README.md`。
- `verify` 只覆盖文档中声明的 Markdown 子集与不变量，不证明语义等价，也不能自动判断所有句内关系或指代。PDF/OCR 结果依赖本机工具和语言包；缺少工具时必须说明未执行。
