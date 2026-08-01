---
inclusion: auto
title: authoring
layer: core
category: skill
keywords: [skill,structure,multifile,SKILL.md,frontmatter,name,description,trigger]
status: active
---

## skill 多文件结构：SKILL.md + references + templates

### 铁律

- MUST：每个 skill 至少包含 `SKILL.md` 主文件
- MUST：长文档内容拆分到 `references/*.md` 子目录
- MUST：可复用模板放入 `templates/` 子目录
- MUST：分类目录需配置 `README.md` 索引（列出子 skill 及其功能）

### 反例表

| 禁 | 改为 |
|---|---|
| 单个 SKILL.md 内嵌所有内容 | SKILL.md + references/ + templates/ |
| 无 references 文件夹 | 按主题拆分长文档 |
| 分类目录无 README.md | 添加 README 作索引 |
| templates 散列各处 | 统一归 templates/ |

## skill frontmatter：name + description(含触发词)

### 铁律

- MUST：frontmatter `name`(kebab-case) + `description` 字段
- MUST：description 包含触发词/场景说明
- MUST：手动型 skill 加 `disable-model-invocation: true`

### 反例表

| 禁 | 改为 |
|---|---|
| frontmatter 缺 name | 添加 name: skill-name |
| description 无触发词 | 添加「触发词: xxx」 |
| name 与目录不一致 | 保持 kebab-case |
