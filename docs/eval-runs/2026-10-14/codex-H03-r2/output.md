# 缓存参数参考

| 参数 | 默认值 | 范围 | 说明 |
|---|---:|---|---|
| `ttlSeconds` | 30 | 1–300 | 缓存存活秒数；设为 `0` 无效 |
| `maxEntries` | 500 | 1–5000 | 最多保存的条目数 |
| `retryCount` | 2 | 0–4 | 只对 HTTP `503` 重试 |
| `retryDelayMs` | 250 | 50–2000 | 每次重试前等待的毫秒数 |

- `retryCount=0` 时不重试。
- HTTP `429` 使用响应中的 `Retry-After`，不读取 `retryDelayMs`。
- 参数缺失时使用默认值；未知参数会被忽略并写入启动日志。

示例：

```json
{"ttlSeconds": 45, "maxEntries": 800, "retryCount": 1}
```

`ttlSeconds` 与 `retryDelayMs` 的单位不同，不能互换。更改参数后重启服务才会生效。
