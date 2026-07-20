---
title: skill 多文件结构：SKILL.md + references + templates
layer: core
category: skill
keywords: [skill,structure,multifile,SKILL.md]
source: reconstruct
authored-by: skein-spec
created: 1784346620
status: active
related: []
updated: 1784346620
---

## 铁律

- MUST：每个 skill 至少包含 `SKILL.md` 主文件
- MUST：长文档内容拆分到 `references/*.md` 子目录
- MUST：可复用模板放入 `templates/` 子目录
- MUST：分类目录需配置 `README.md` 索引（列出子 skill 及其功能）

## 反例表

| 禁 | 改为 |
|---|---|
| 单个 SKILL.md 内嵌所有内容 | SKILL.md + references/ + templates/ |
| 无 references 文件夹 | 按主题拆分长文档 |
| 分类目录无 README.md | 添加 README 作索引 |
| templates 散列各处 | 统一归 templates/ |
