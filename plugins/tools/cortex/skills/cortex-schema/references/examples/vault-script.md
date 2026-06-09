> 样例 — type=vault-script, 完整可直接落盘到 脚本/canvas-from-mindmap.py (本文为描述, 真实脚本含 shebang)

---
type: vault-script
created: 2026-06-09
updated: 2026-06-09
tags: [vault, script, canvas, obsidian, mindmap]
aliases: [canvas-from-mindmap, mindmap2canvas]
---

# canvas-from-mindmap.py

vault 内部脚本: 把 markmap / freemind 思维导图转换为 Obsidian `.canvas` 文件, 自动落盘到对应项目目录.

## 用途

入库 GitHub repo 摘要时 (见 [[ccplugin]] 之类 type=project 文档), 自动生成可视化拓扑.

## 输入/输出

- 输入: `*.mm` (FreeMind) 或 `*.md` (markmap 语法)
- 输出: `项目/<host>/<owner>/<repo>/mindmap.canvas`

## 实现要点

1. 解析 mindmap 树形结构
2. 按层级布局节点坐标 (radial 或 hierarchical)
3. 输出 Obsidian canvas JSON schema (nodes + edges)

## 关联

- 引用规范: [[knowledge-modules]]
- 字段 schema: [[templates]]
