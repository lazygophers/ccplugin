---
title: plugin 许可统一 AGPL-3.0-or-later
layer: recall
category: ops
keywords: [plugin,license,AGPL,marketplace]
source: reconstruct
authored-by: skein-spec
created: 1784346717
status: active
related: []
updated: 1784346717
---

## 铁律

- MUST：.claude-plugin/plugin.json license 字段为 `"AGPL-3.0-or-later"`
- MUST：.claude-plugin/marketplace.json 所有条目 license 也为 `"AGPL-3.0-or-later"`
- MUST：新 plugin 自动采用此许可

## 反例表

| 禁 | 改为 |
|---|---|
| license: "MIT" 或 "Apache-2.0" | license: "AGPL-3.0-or-later" |
| plugin.json 有 license，marketplace.json 无 | 两处都需一致许可 |
