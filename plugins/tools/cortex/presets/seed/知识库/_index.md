---
type: index
title: 知识库
role: 持久笔记体系 — 4 子目录 (项目/领域/日记/收件箱)
namespace: 知识库
parent: 主页
children:
- 项目
- 领域
- 日记
- 收件箱
last_updated: '{{UPDATED}}'
tags:
- topic/知识库
- lang/zh-CN
- domain/knowledge-base
- source/seed
- score/3
- maturity/stable
- scope/root
- kind/navigation
- refresh/on-demand
icon: 📚
template_version: 1
---

<section data-role="header" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
  <span style="font-size:24px">📚</span>
  <h1 style="margin:0">知识库</h1>
</section>

> [!info] 知识库
> 持久笔记体系, 仅 4 个子目录:
> - **项目/**: `<host>/<org>/<repo>/` 三级嵌套, github/gitlab/local 项目笔记
> - **领域/**: 用户自决域名 (创作/学习/工作/技术/生活/金融/...), 域下结构自由
> - **日记/**: 仅 `日/<YYYY-MM>/<YYYY-MM-DD>.md` 二层, 周/月/年 已废弃 (历史归档到 `归档/日记/`)
> - **收件箱/**: 落档兜底入口, 等 digest 自动分发到 项目/笔记 或 领域/<域>

## 子目录

<section data-role="children-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">
  {{CHILDREN_CARDS}}
</section>
