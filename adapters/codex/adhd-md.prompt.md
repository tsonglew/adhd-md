---
description: 把 Markdown 改造成 ADHD 友好（可只改格式 / 只改内容 / 兼改）
argument-hint: <文件.md> [--scope=format|content|both] [--level=light|standard|deep]
---

读取并严格执行 `__CANON__/SKILL.md` 里定义的工作流。

参数在 `$ARGUMENTS` 里。解析规则：

- 第一个非 flag 参数是目标文件
- `--scope` 缺省为 `both`，`--level` 缺省为 `standard`
- 用户用自然语言表达时按 SKILL.md 的映射表转换（「只改格式」→ `--scope=format`）

确定性工具层在 `__CANON__/scripts/adhd_md.py`，用 `python3` 调。

铁律：只重排信息，绝不删信息。`scope=format` 时 `verify` 是硬门禁，不通过必须回退。
