---
name: cortex-schema-knowledge
description: 知识库 schema — 项目/领域/脚本 三模块 (中文目录名) 路径规则与 frontmatter 契约, 用于 vault 入库 / 归档 / projects / domains / scripts / 内部脚本治理. 双层同构 (~/.cortex/.wiki + <repo>/.wiki), 区分 vault 内部脚本 (中文 脚本/) 与用户操作入口 (英文 scripts/).
when_to_use: 入库/归档资料 / 新建项目摘要 / 写领域笔记 / 判定三模块归属 / vault 内部脚本治理 / lint+extract 查路径规则
argument-hint: "[module]"
arguments: "[模块]"
---

# cortex-schema-knowledge

知识库 schema — 项目/领域/脚本 三模块路径规则与 frontmatter 契约. 双层同构 (`~/.cortex/.wiki/` + `<repo>/.wiki/`). 本 skill 为路径与模板权威源.

## 路径速查

| 模块 | 用户级 | 项目级 | type |
| --- | --- | --- | --- |
| 项目 | `~/.cortex/.wiki/项目/<host>/<owner>/<repo>/` | `<repo>/.wiki/项目/<host>/<owner>/<repo>/` | `project` |
| 领域 | `~/.cortex/.wiki/领域/<area>/<sub>/...` | `<repo>/.wiki/领域/<area>/<sub>/...` | `domain` |
| 脚本 (vault 内部) | `~/.cortex/.wiki/脚本/<name>.{sh,py}` | `<repo>/.wiki/脚本/<name>.{sh,py}` | `vault-script` |

三模块顶层目录名用中文 (`项目/` `领域/` `脚本/`); 用户操作入口 `~/.cortex/scripts/` 用英文, 视觉区分防误用.

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 ~/.cortex 顶层物理布局 / 双层同构 / 必备目录 / 开放扩展 | `references/topology.md` |
| 查 frontmatter 通用字段 / 各 type 模板 | `references/templates.md` |
| 入库 GitHub / GitLab / Website 摘要 | `references/projects.md` |
| 写或整理领域笔记 (tech / life / finance) | `references/domains.md` |
| vault 内部脚本 / 用户操作入口 / 混用检测 | `references/scripts.md` |

## 引用

- 记忆等级 schema: `cortex-schema-memory`
- lint 规则集 (含 R7 入口脚本治理): `cortex-lint`
- extract 路由表: `cortex-extract`
