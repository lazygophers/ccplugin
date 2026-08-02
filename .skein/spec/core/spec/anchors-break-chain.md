---
title: anchors-break-chain
category: spec
keywords: [anchors,断链,强弱,archive,maintain]
status: active
inclusion: auto
---

## anchors 强弱断链的区分与处置

# anchors 强弱断链的区分与处置

anchors 失效分两个等级，处置策略截然不同：

| 写法 | 失效判定 | 级别 | 处置 |
|---|---|---|---|
| `path/to/file.py` | 文件不存在 | **强断链** | 报告 + 可 archive |
| `path/to/file.py:symbol` | 文件存在但符号没了 | **弱断链** | 只报告，不 archive |

**为什么区分**：
- 文件消失 = 有意的代码删改，anchors 肯定要变，可安全删除
- 符号消失 = 可能是改名、重构、或正则漏判，应人工复核再决定

**实现**：破链判据由 `maintain` 单点实现，所有 namespace 复用同一份逻辑（不重复实现）。符号存在性检测复用骨架生成的正则表达式。

**跨 namespace 一致性**：`spec-map-namespace` 与 `spec-product-wiki` 两 task 都涉及 anchors，但判定表归 `spec-model-core` 统一实现，本 task 只是把自己 namespace 的处置规则填进去。
