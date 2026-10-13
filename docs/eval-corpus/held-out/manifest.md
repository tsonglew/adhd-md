# 保留语料 v1

状态：候选集已冻结于 2026-10-13；尚未运行模型。12 篇均为本仓库编写的合成材料，没有复制外部或私人文档。它们未纳入 `selftest`，也未作为本轮规则实现的调参输入。运行前从仓库根目录执行 `(cd docs/eval-corpus/held-out && shasum -a 256 -c SHA256SUMS)` 核对 [`SHA256SUMS`](SHA256SUMS)。

若某例用于修正规则或提示词，就将其转入回归集，并新建版本替代保留集；不能在同一版本上反复调参后继续称为 held-out。每次运行复制到隔离目录，只写旁路输出，保留原输入。

## 固定提示词

以下模板是任务本身的一部分。只替换 `{input}` 与 `{output}`，不按宿主临时增删要求。

### 中文 · format

> 使用 adhd-md skill 对 `{input}` 做只改格式处理，按本案例的 `scope=format` 和 `level` 执行。把结果写到 `{output}`，不要覆盖输入。保留原有字符、数字、单位、条件、例外、链接目标、代码和信息顺序；不要补充或删除内容。运行 `audit` 与 `verify --scope=format`，报告退出状态、脚本分、反模式扣分和未判定项；`unknown` 不得写成通过。

### 中文 · content

> 使用 adhd-md skill 改写 `{input}`，按本案例的 `scope=content` 和 `level` 执行，以清楚、简短、可扫读为目标。把结果写到 `{output}`，不要覆盖输入。必须保留本案例列出的所有数值、单位、条件、例外、先决条件、代码和链接目标；不要编造事实。运行 `audit` 与 `report --scope=content`，报告脚本分、反模式扣分、verify 状态和未判定项；`unknown` 不得写成通过。

### English · format

> Use the adhd-md skill to reformat `{input}` with this case's `scope=format` and `level`. Write to `{output}` and do not overwrite the input. Preserve every original character, number, unit, condition, exception, link target, code block, and ordering of information. Do not add or remove content. Run `audit` and `verify --scope=format`; report exit status, script score, anti-pattern deductions, and unjudged rules. Never report `unknown` as a pass.

### English · content

> Use the adhd-md skill to rewrite `{input}` for clear, concise scanning with this case's `scope=content` and `level`. Write to `{output}` and do not overwrite the input. Preserve every listed number, unit, condition, exception, prerequisite, code block, and link target; do not invent facts. Run `audit` and `report --scope=content`; report the script score, anti-pattern deductions, verify status, and unjudged rules. Never report `unknown` as a pass.

## 案例与独立答案键

| ID | 输入 | 语言 / 类型 | scope / level | 模板 | 复核时必须保留 |
|---|---|---|---|---|---|
| H01 | `01-zh-readme.md` | zh / README | content / standard | 中文 content | 静默时段 `21:30–08:00`、系统时区、仅当前设备、通知不收回、日历邀请和安全告警仍显示、校时后重新保存、企业策略只读 |
| H02 | `02-zh-tutorial.md` | zh / tutorial | format / standard | 中文 format | 管理员权限、旧密钥至少剩 24 小时、HTTP `201`、两个 worker、确认 `token_version=new` 后再撤销、文件超过 50 MB 走分片 |
| H03 | `03-zh-reference.md` | zh / reference | format / deep | 中文 format | `ttlSeconds=30` / `1–300`；`maxEntries=500` / `1–5000`；`retryCount=2` / `0–4`；只重试 503；429 使用 `Retry-After`；两个时间单位不同 |
| H04 | `04-zh-runbook.md` | zh / runbook | content / standard | 中文 content | CSV、少于 100,000 行、等待 2 分钟、权限错误转流程、刷新一次、取消后只重提一次、维护窗口不重启 worker、取消不删除已下载 CSV |
| H05 | `05-zh-meeting.md` | zh / meeting | format / standard | 中文 format | 中位数 1.8 秒 / 目标低于 2 秒；失败率 1.2% 到 0.7%；观察 7 天；连续 30 分钟高于 1.5% 才暂停 10% 灰度；单次告警不回滚 |
| H06 | `06-zh-boundary.md` | zh / boundary Markdown | format / deep | 中文 format | frontmatter、引用层级、列表次序、409 / 503 表格、代码 `tool sync --dry-run --timeout 12`、链接 query 和 fragment、两条环境不同的重试规则 |
| H07 | `07-en-readme.md` | en / README | content / standard | English content | 14 days、workspace owners、failed-before-upload exclusion、archive differs from recycle bin、2 GB split、30-minute link、guests excluded |
| H08 | `08-en-tutorial.md` | en / tutorial | format / standard | English format | deployment admin、48 hours remaining、keep old certificate, HTTP 200, approved fingerprint/date, one instance at a time, 495 stops rollout, hostname/trust bundle unchanged |
| H09 | `09-en-reference.md` | en / reference | format / deep | English format | `visibilitySeconds=45` / `5–600`; `maxAttempts=3` / `1–8` and includes first delivery; `1` disables retries; never retry 401/403; seconds vs milliseconds |
| H10 | `10-en-runbook.md` | en / runbook | content / standard | English content | Search index only; 5-minute stale threshold; queue depth; wait 3 minutes; requeue only affected workspace; no global rebuild during business hours; primary DB unchanged |
| H11 | `11-en-meeting.md` | en / meeting | format / standard | English format | 210 ms median / 250 ms target; 680 ms p95 / 600 ms target; three consecutive days; error rate 0.5%; rollback above 1% for 10 minutes |
| H12 | `12-en-boundary.md` | en / boundary Markdown | format / deep | English format | frontmatter v2, `A->B`, `x ** 2`, quote order, nested list order, `--check-only`, `staging`, 15 s, 0 retries, code block, full link target, both repeated copies |

## 判定規則

`format` 只在当前 verifier 返回 `pass` 且反模式扣分为 0 时通过；`unknown` 必须由独立复核逐项确认，不能计为通过。`content` 需人工核对答案键中的全部约束、条件、例外和链接 / 代码值；脚本分只作为诊断数据。

每种语言和类型各有 format 与 content 案例。首轮建议每个可运行宿主完成 12 例；代表性案例 H03、H06、H09、H12 至少重复 3 次。宿主发现、skill 加载、工具执行、最终输出和人工复核分别计数。未运行或无法启动的宿主标为 `unverified`，不能从汇总里省略。
