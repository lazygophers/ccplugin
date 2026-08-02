---
title: namespace-archive-policy
category: maintain
keywords: [maintain,archive,namespace,map,product]
status: active
inclusion: auto
---

## maintain 按 namespace 分治：archive 策略

# maintain 按 namespace 分治：archive 策略

`maintain` 命令对 anchors 失效的处置因 namespace 而异，遵循不同的可靠性要求：

| namespace | anchors 失效 | 处置 | 理由 |
|---|---|---|---|
| `map` | **可 archive** | 自动清理失效 anchors | 骨架现算兜底，语义页失效无损；丢了还能靠骨架定位 |
| `product` | **只报告** | 标记问题，人工复核后才删 | 需求真值是单一真实来源，自动删会隐藏问题 |

**原则**：archive 权限取决于**是否有兜底机制**。
- map：骨架永不 stale，即使 anchors 全失效也能通过目录 + 符号回找代码
- product：无兜底，失效 anchors = 丢失需求定位，必须明确可见可追踪

**注意**：与 `spec-product-wiki` p4 的逻辑边界 — 两个 task 不重复实现判定表，该表归 `spec-model-core` s6 的 `maintain` 负责，本 task 只定义 map namespace 的分值。
