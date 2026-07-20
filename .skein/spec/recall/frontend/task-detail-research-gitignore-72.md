---
title: doc tab 非单篇 md 渲染分支顺序
layer: recall
category: frontend
keywords: [doc,tab,渲染,分支,dict,v-if]
source: task-detail-research-gitignore
authored-by: skein-spec
created: 1784560014
status: active
related: []
updated: 1784560014
---

# 触发场景

在 task 详情页 DOC_TABS 新加 research tab 时，数据源从 `docs[tab]` 单篇 md 改为 `research` dict（filename→content 多篇），遇到渲染分支被「暂无内容」兜底分支吞掉的问题。

## 陷阱-正解

当 tab 数据形态是 **dict/列表**（非单篇 md），模板渲染独立分支必须放在 `v-if="!docs[tab]"` 兜底分支**之前**，否则被吞掉。

**反例**（放错顺序会被吞）：
```js
// v-if="!docs[tab]" 在前 → dict 数据源的独立分支永远不可见
<div v-if="!docs[tab]">暂无内容</div>
<div v-if="tab === 'research' && researchHtml">
  <div v-html="researchHtml"></div>
</div>
```

**正解**（独立分支在前）：
```js
// research 渲染分支放最前，dict 数据源优先处理
<div v-if="tab === 'research' && researchHtml">
  <div v-html="researchHtml"></div>
</div>
<div v-if="!docs[tab]">暂无内容</div>
```

## 反例

| 禁 | 改为 |
|---|---|
| 兜底分支在 dict 渲染分支之前 | dict 渲染分支放最前 |
| `v-if="!docs[tab]"` 在前 | 专属渲染分支 `v-if="tab === 'research'"` 在前 |
| 期望 dict 数据源能穿过兜底分支 | 兜底分支只在单篇 md 场景生效 |

## 案例

task.js DOC_TABS 加 research tab：`research` 是 `{filename: content}` dict，research 渲染分支（`v-if="tab === 'research'"`）必须放 `v-if="!docs[tab]"` 之前，否则多篇笔记被「暂无内容」吞掉。

## 适用

- 任何 tab/板块渲染涉及 **dict/列表数据源**（非单篇 md）
- 模板有兜底「暂无内容」分支
- Vue v-if 渲染顺序依赖的场景

## 关联

- `[frontend] Markdown 渲染必须 sanitize`（内容安全，不涉及分支顺序）
- `[arch] SPA page 模块统一契约`（模块依赖，不涉及模板渲染）
