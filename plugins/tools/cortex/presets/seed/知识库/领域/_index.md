---
type: index
title: 领域
role: 知识体系 — 域名由用户自决, 不预置固化结构
namespace: 知识库
parent: 主页
children: []
last_updated: '{{UPDATED}}'
tags:
- topic/领域
- lang/zh-CN
- source/seed
- score/3
- maturity/stable
- scope/user-defined
- kind/navigation
- refresh/on-demand
icon: 🗺
template_version: 1
---

<section data-role="header" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
  <span style="font-size:24px">🗺</span>
  <h1 style="margin:0">领域</h1>
</section>

> [!info] 领域
> 按主题分类的知识体系 — 域名 (创作/学习/工作/技术/生活/金融/...) 由用户/AI 落档时自决创建

<section data-role="kpi" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0">
  <div data-type="stat" style="padding:12px;background:#f8fafc;border-radius:8px">
    <div style="font-size:12px;color:#666">📁 子目录</div>
    <div style="font-size:24px;font-weight:600">{{SUB_COUNT}}</div>
  </div>
  <div data-type="stat" style="padding:12px;background:#f8fafc;border-radius:8px">
    <div style="font-size:12px;color:#666">📄 条目</div>
    <div style="font-size:24px;font-weight:600">{{ITEM_COUNT}}</div>
  </div>
  <div data-type="stat" style="padding:12px;background:#f8fafc;border-radius:8px">
    <div style="font-size:12px;color:#666">🕐 更新</div>
    <div style="font-size:14px">{{LAST_UPDATED}}</div>
  </div>
</section>

<section data-role="breadcrumb" style="font-size:12px;color:#6b7280;margin:8px 0">
  {{BREADCRUMB}} · 路径: <code>{{CURRENT_PATH}}</code>
</section>

## 子目录

<section data-role="children-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
  <!-- cortex-dashboard 注入: 每个子目录一张 card -->
  {{CHILDREN_CARDS}}
</section>

## 最近条目

<details open>
<summary>近 7 天 (top 10)</summary>

```base
filters:
  - field: path
    op: startswith
    value: "知识库/领域/"
sort:
  - field: last_updated
    dir: desc
limit: 10
views:
  - type: list
```

</details>

## 全部条目

<details>
<summary>展开全部</summary>

```base
filters:
  - field: path
    op: startswith
    value: "知识库/领域/"
sort:
  - field: created
    dir: desc
views:
  - type: cards
```

</details>

## 相关

<section data-role="related" style="display:flex;gap:6px;flex-wrap:wrap;margin:12px 0">
  {{RELATED_LINKS}}
</section>

<section data-role="operations" style="display:flex;gap:8px;margin-top:16px">
  <a href="[[主页]]">⬅ 主页</a>
  <a href="{{NEW_LINK}}">➕ 新建</a>
  <a href="{{REFRESH_LINK}}">🔄 刷新</a>
</section>

<!-- TEMPLATE_END -->
