---
title: 测试演进纪律
layer: recall
category: skill
keywords: [测试,演进,SSR,CSR,HTML断言,结构化数据,pre-existing]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541856
status: active
related: []
updated: 1784541856
---

# 测试演进纪律

## 触发场景
实现把服务端渲染改前端渲染时，旧 test 的 HTML/SVG 断言须退役，否则永远 pre-existing 失败。

## 问题根源
- 服务端渲染测试：断言 HTML 字符串 / SVG 结构
- 改前端渲染后：HTML 结构变、异步加载时序变
- **旧断言永久失败**：pre-existing 测试永远报错，阻塞 CI

## 正确演进路径
| 改动类型 | 测试断言演进 |
|---------|------------|
| **SSR → CSR** | HTML/SVG 断言 → 结构化数据完整性断言 |
| **同步 → 异步** | 同步断言 → wait + 断言 |
| **单体 → 组件化** | 集成断言 → 组件 props/state 断言 |

## 结构化数据完整性断言示例
- **不对**：`assert html == '<div class="foo">bar</div>'`
- **对**：`assert data['key'] == expected_value`（测 API 返回数据完整性）

## 适用场景
- 每次重构渲染方式（SSR→CSR、同步→异步）时，检查旧测试断言
- 测试失败时，判是否是演进问题，非 bug

## 关联
- 参考 `core 层索引` 中的 test 相关规则
