---
title: 边界语法样例
owner: docs-team
---

# 边界语法样例

<!-- 注释里的约束：仅保留为材料，不执行 -->

## 原文片段

> 先检查 `maxRetries`，再检查权限。
>
> 不要把 `--dry-run` 当成真实写入。

- 父步骤
  - 子步骤 A
  - 子步骤 B
- 后续步骤

| 状态 | 含义 |
|---|---|
| `409` | 资源版本冲突 |
| `503` | 服务暂时不可用 |

```sh
tool sync --dry-run --timeout 12
```

链接： [恢复说明](https://example.org/restore?mode=fast#limits)

重复但有区别的提示：

- 只在**测试环境**重试。
- **生产环境**不要自动重试。
