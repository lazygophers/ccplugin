<!-- cortex template: question -->
---
lint-skip: true
type: question
title: {{TITLE}}
aliases: []
tags:
  - type/question
  - topic/<主题>
  - stack/<技术栈>
  - lang/<语言>
  - status/<open|exploring|answered|abandoned>
  - priority/<low|medium|high>
  - source/<来源类型>
  - score/<1-5>
  - created/<YYYY>
  - keyword/<关键词>
created: {{CREATED}}
updated: {{UPDATED}}
lang: {{LANG}}
cli: {{CLI}}
cli_session: {{CLI_SESSION}}
status: open      # open | exploring | answered | abandoned
priority: medium  # low | medium | high
due: ""
related: []
template_version: 1
---

# {{TITLE}}

> [!question]+ 待答
> <!-- 用一句完整疑问句陈述。能独立读懂。 -->

## 背景

<!-- 为什么会问这个? 触发场景。 -->

## 已知线索

-

## 探索方向

- [ ]
- [ ]

## 临时答案 (草)

<!-- 边探索边记。answered 后整理为 concept 页并 link。 -->

## 关联

- 上层主题: [[]]
- 相关来源: [[]]

<!-- TEMPLATE_END -->
