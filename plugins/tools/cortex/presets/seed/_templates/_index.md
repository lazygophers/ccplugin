<!-- cortex template: _index -->
<!-- cortex-template-version: 1 -->
---
type: meta
title: {{TITLE}}
aliases: [templates]
tags: [meta]
created: {{CREATED}}
updated: {{UPDATED}}
preset: {{PRESET}}
lang: {{LANG}}
template_version: 1
---

# {{TITLE}}

<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0">
  <div style="border:1px solid #e5e7eb;border-radius:6px;padding:12px;background:#fafafa">
    <div style="font-weight:600;margin-bottom:6px">子目录</div>
    <div style="font-size:13px;color:#374151">cortex-dashboard 注入子目录列表 (Bases query)</div>
  </div>
  <div style="border:1px solid #e5e7eb;border-radius:6px;padding:12px;background:#fafafa">
    <div style="font-weight:600;margin-bottom:6px">最近条目</div>
    <div style="font-size:13px;color:#374151">cortex-dashboard 注入最近修改的笔记 (Bases query)</div>
  </div>
</div>

## 模板分类

- `html/` — HTML 片段库 (badge / card / timeline / mermaid×3 / heatmap / disclosure)
- `memory/` — L0-L4 记忆模板 (含 L4-session)
- `knowledge/` — 知识库笔记 (project / source×4 / domain×3 / journal×4 / reflection×3)
- 顶层 `concept.md / entity.md / domain.md / source.md / question.md / dashboard.md` — legacy 8-bucket 兼容模板

## frontmatter 公共字段

```yaml
type: <字面量>
title: <H1 一致>
aliases: []
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
template_version: 1
```

## 占位变量约定

所有模板用 `{{VAR}}` 双花括号占位, 由 `/cortex:new` 或 cortex-html / cortex-dashboard 渲染时替换。**不要**在模板里预填实际内容。

## 修改提示

用户可直接编辑本目录下模板, cortex-install 默认 **不覆盖** 已存在文件。
重置某模板, 删除后重跑 `cortex-install`。

<!-- TEMPLATE_END -->
