---
title: skein-plan 文档分层约定
layer: recall
category: skill
keywords: [skein-plan,SKILL.md,references,分层,单一真值源,承接式标题]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541843
status: active
related: []
updated: 1784541843
---

# skein-plan 文档分层约定

## 触发场景
写 SKILL.md / references/ 文档时，主判据表落 SKILL.md，细化/变体落 references/，防止重复。

## 分层判据
| 内容类型 | 位置 | 理由 |
|---------|------|------|
| **主判据表（复杂度天花板）** | SKILL.md | 核心判据，常驻召回 |
| **同维度细化/变体** | references/ | 承接式标题，保单一真值源 |

## 承接式标题（避免复制）
- 若 reference 说"参考 SKILL.md 中的某表"，在 reference 中加承接段非复制表内容
- 示例：
  ```
  参考 SKILL.md [审查轴表](#审查轴表)，本表补充复杂场景判据：
  | 场景 | 判据 |
  ```
- 禁在 reference 复制 SKILL.md 的表，造成多处维护

## 单一真值源原则
- 主表落 SKILL.md，reference 仅承接细化/变体
- 若主表更新，reference 不需同步修改（仅承接段落）

## 适用场景
- 写新 skill 文档时，判主表细化维度
- 更新 SKILL.md 时，检查 reference 是否复制，改为承接

## 关联
- 参考 `cold-start 模糊信号判据 + Job Story 愿景翻译` 中的主判据表落地
