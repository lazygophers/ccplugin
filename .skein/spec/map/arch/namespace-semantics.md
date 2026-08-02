---
title: namespace-semantics
category: arch
keywords: [骨架,语义沉淀,stale,anchors]
status: active
inclusion: auto
---

## map namespace 混合设计：骨架现算 + 语义沉淀

# map namespace 混合设计：骨架现算 + 语义沉淀

`map` namespace 采用混合设计，平衡 stale 风险与维护成本：

| 层 | 内容 | 产生方式 | stale 风险 |
|---|---|---|---|
| **骨架** | 目录树 + 每文件顶层符号名 + 行数 | 脚本现算，**不落盘** | **零** |
| **语义** | 模块职责 / 入口点 / 数据流 / 坑 | AI 沉淀成 namespace 页 + anchors | 有，但被 maintain 断链判据抓到 |

**为什么混合而非纯生成/纯沉淀**：
- 纯生成式（stdlib 正则）：只能做到目录级 + 符号列举，抓不出语义（需读懂代码）
- 纯沉淀式（全手工）：质量高但必 stale，维护负担重

拆开后各取所长：机械部分永不 stale，理解部分才沉淀，失效可检测可 archive。

**真正缺的是"规则 ↔ 代码位置绑定"**：规则里记了「exec 端点必须走 argv 白名单」，但没记在哪个文件。`anchors` 补这个缺口。
