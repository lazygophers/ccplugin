---
title: skill frontmatter：name + description(含触发词)
layer: core
category: skill
keywords: [skill,frontmatter,name,description,trigger]
source: reconstruct
authored-by: skein-spec
created: 1784346948
status: active
related: []
updated: 1784346948
---

## 铁律

- MUST：frontmatter `name`(kebab-case) + `description` 字段
- MUST：description 包含触发词/场景说明
- MUST：手动型 skill 加 `disable-model-invocation: true`

## 反例表

| 禁 | 改为 |
|---|---|
| frontmatter 缺 name | 添加 name: skill-name |
| description 无触发词 | 添加「触发词: xxx」 |
| name 与目录不一致 | 保持 kebab-case |
