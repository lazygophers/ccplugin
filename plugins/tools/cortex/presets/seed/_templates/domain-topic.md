---
lint-skip: true
type: topic
title: <主题>
domain: <创作|学习|工作|技术|生活|金融|未分类>
subtopic: <可选, 如 技术/分布式系统>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags:
  - type/topic
  - domain/<域>
  - subtopic/<子>
  - lang/<l>
  - source/<manual|ingest>
  - score/<n>
  - maturity/<draft|stable>
  - keyword/<关键词>
  - created/<YYYY>
  - scope/<concept|entity>
template_version: 1
---

# {{title}}

> [!abstract] {{title}}
> <一句话定义>

## 关键概念

## 例证

## 相关

- [[<相关主题>]]

<!--
本模板替代旧的 entity.md / concept.md。entity (人/工具) 与 concept (概念) 统一落
知识库/领域/<域>/<kebab>.md, 由 cortex_save --kind entity|concept --domain <域> 创建。
若 --domain 缺失, AI 应读 body 自决选 6 域之一 (创作/学习/工作/技术/生活/金融) 或创建新子目录;
最终兜底落 领域/未分类/<kebab>.md (digest 时人工或 AI 再分发)。
-->
