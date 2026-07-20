---
title: 配置写端点防注入（仅认 CONFIG_DEFAULTS 键）
layer: core
category: security
keywords: [security,config,injection,whitelist]
source: reconstruct
authored-by: skein-spec
created: 1784346878
status: active
related: []
updated: 1784346878
---

## 铁律

- MUST：POST /config 接收的 JSON 仅保留 CONFIG_DEFAULTS 中已列举的键
- MUST：按类型 coerce，coerce 失败时保持原值或默认
- MUST：未知键一律忽略

## 反例表

| 禁 | 改为 |
|---|---|
| 接收任意 JSON key | 仅过滤已知 key |
| 直接将用户 JSON 写入配置 | 按已知字段逐个赋值 + 类型转换 |
| 新增 key 被接受 | 未知 key 忽略 |
