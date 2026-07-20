---
title: 硬护栏范式
layer: recall
category: impl
keywords: [硬护栏,对照式,范式,硬约束]
source: sediment
authored-by: skein-spec
created: 1784473563
status: active
related: []
updated: 1784473563
---

# 硬护栏范式

## 触发场景

编写 skill/agent/command 时需要硬约束（无法正向化的禁令）—— 如安全边界、防错纪律、接线规则等。

## 陷阱 / 正解

❌ "硬规" + 列表式 "禁 A、禁 B、禁 C"  
根因：负向表述难理解，AI 易忽略禁令细节或不知正确做法  
✅ "硬护栏" + 表格式 "禁 A | 正例 A；禁 B | 正例 B；禁 C | 正例 C"

## 反例

❌ "组件目录禁进 `.claude-plugin/`" — 单向禁令，AI 不知该放哪  
✅ "组件塞进 `.claude-plugin/` 目录 | 组件在插件根；`.claude-plugin/` 仅放 `plugin.json`" — 双向对照，理解禁令同时知道正确做法

## 案例

- plugin-dev SKILL.md refactor (cf200526): 从"🔴 硬规（违反即失效）"改"硬护栏（无法正向表述的禁令，配正例）"，对照表提升可执行性
- skill-dev SKILL.md: 从列表式"禁..."改表格式"禁 | 正例"

## 适用

- 无法正向化的硬约束（安全/防错/边界）
- 需要"禁 X 且配正例"的场景
- 任何 skill/agent/command 的硬规部分

## 关联

[[sediment-51]] (core, 正向表述优先原则)
