---
type: index
title: 项目
role: 本地项目实践 (有期限的产出)
namespace: 知识库
parent: 主页
children:
- 项目笔记
- 决策记录
last_updated: '{{UPDATED}}'
tags:
- topic/项目
- lang/zh-CN
- domain/knowledge-base
- source/seed
- score/3
- maturity/stable
- scope/host-org-repo
- kind/navigation
- refresh/on-demand
icon: 📂
template_version: 1
---

<section data-role="header" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
  <span style="font-size:24px">📂</span>
  <h1 style="margin:0">项目</h1>
</section>

> [!tip] 项目
> git repo 与本地项目统一归档 — 三级嵌套 `<host>/<org>/<repo>/` 承载所有 GitHub/GitLab/local 项目。

> [!info]+ 📂 目录结构
>
> ```
> 知识库/项目/
> ├── _index.md
> ├── <host>/                  # github.com / gitlab.com / gitlab.<your>.com 或 相对 $HOME 路径首段 (persons/workspace/_local 等)
> │   └── <org>/               # 组织 / 用户 / 团队 (本地 fallback: 相对 $HOME 路径第二段, 不足时为 _local)
> │       └── <repo>/          # 仓库名 (本地 fallback: 相对 $HOME 路径第三段, 不足时为 _local 或目录 basename)
> │           ├── _index.md    # 项目概览
> │           ├── 架构.md
> │           ├── 决策.md
> │           ├── 陷阱.md
> │           ├── 依赖.md
> │           ├── 笔记/
> │           └── 决策/
> ```

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
    value: "知识库/项目/"
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
    value: "知识库/项目/"
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
