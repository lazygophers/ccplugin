---
name: cortex-schema-knowledge
description: 知识库 schema — 项目/领域/脚本 三模块 (中文目录名) 路径规则与 frontmatter 契约, 用于 vault 入库 / 归档 / projects / domains / scripts / 内部脚本治理
when_to_use:
  - 用户要把资料"入库" / "归档"到知识库
  - 新建项目摘要 (GitHub / GitLab / Website)
  - 写或整理领域笔记 (tech / life / finance)
  - 需要决定一份内容落到 项目 / 领域 / 脚本 哪个模块
  - 编写 vault 内部脚本 (lint / canvas / frontmatter 工具)
  - 判断脚本属 vault 内部还是用户操作入口 CLI
  - lint / extract 流程要查路径规则
  - 校验 knowledge 模块 frontmatter 合法性
argument-hint: "[module]"
---

# cortex-schema-knowledge

知识库三模块的路径规则与 frontmatter schema。路径权威以 `plugins/tools/cortex/docs/layout.md` 为准。

## 路径速查

| 模块 | 用户级 | 项目级 | type |
| --- | --- | --- | --- |
| 项目 | `~/.cortex/.wiki/项目/<host>/<owner>/<repo>/` | `<repo>/.wiki/项目/<host>/<owner>/<repo>/` | `project` |
| 领域 | `~/.cortex/.wiki/领域/<area>/<sub>/...` | `<repo>/.wiki/领域/<area>/<sub>/...` | `domain` |
| 脚本 (vault 内部) | `~/.cortex/.wiki/脚本/<name>.{sh,py}` | `<repo>/.wiki/脚本/<name>.{sh,py}` | `vault-script` |

**目录命名约定**: 三模块顶层目录名采用中文 (`项目/` `领域/` `脚本/`), 与用户操作入口 `~/.cortex/scripts/` (英文) 形成视觉区分, 防止误用. 模块内部子目录命名仍用英文 kebab-case.

补充 — 用户操作入口脚本 (不属三模块):
`~/.cortex/scripts/<name>.{sh,py}` (**仅用户级**, 项目级不设, 英文路径)

## 项目模块 (项目)

记录外部 repo / 站点的摘要与心智地图。

- **路径**: `<root>/项目/<host>/<owner>/<repo>/`
  - `<root>` = `~/.cortex/.wiki` 或 `<repo>/.wiki`
  - `<host>` 枚举: `github.com` / `gitlab.com` / `bitbucket.org` / 任意自定义 domain (如 `nextjs.org`)
  - `<owner>` = 组织或用户名; 无 owner 概念的站点可用 `_` 占位
  - `<repo>` = 仓库名或站点 slug
- **目录内容**:
  - `README.md` — 必备, 摘要主文件 (含下方 frontmatter)
  - `mindmap.canvas` — 推荐, Obsidian canvas 心智地图
  - `graph.json` — 可选, 结构化关系图
  - `notes/` — 可选, 子页面
- **frontmatter (README.md)**:

```yaml
---
type: project
source: https://github.com/anthropics/claude-code
summary: Claude Code CLI — Anthropic 官方终端编码代理
mindmap: ./mindmap.canvas        # 可选, 相对当前 README.md
graph: ./graph.json              # 可选
created: 2026-06-09
updated: 2026-06-09
tags: [ai, cli, agent]
aliases: [claude-code]
---
```

- **命名约定**: 路径段全部小写, 保留原始 owner/repo 大小写时统一转小写 (与 GitHub URL 不区分大小写对齐)。

## 领域模块 (领域)

跨项目复用的领域 / 经验 / 方法笔记。

- **路径**: `<root>/领域/<area>/<sub>/[<sub2>/]<topic>.md`
  - 必须 ≥ 2 级目录 (area + sub 最少)
  - `<area>` 预设: `tech` / `life` / `finance` (用户可扩展, 如 `health` / `art`)
  - `<sub>` / `<sub2>` 自由分类
- **frontmatter**:

```yaml
---
type: domain
area: tech
created: 2026-06-09
updated: 2026-06-09
tags: [rust, async, tokio]
aliases: [tokio-runtime-notes]
weight: 0.6
---
```

- **示例路径**:
  - `领域/tech/rust/async/tokio-runtime.md`
  - `领域/life/habits/sleep-protocol.md`
  - `领域/finance/etf/global-allocation.md`
- **禁路径**: `领域/<topic>.md` (缺 sub 级); `领域/misc/...` (area=misc 不允许, 必须明确)

## 脚本模块 (脚本) — vault 内部脚本

被 cortex 流程 (lint / extract / canvas / frontmatter 整形) 调用的内部工具, **不是给用户直接调**。

- **路径**:
  - 用户级: `~/.cortex/.wiki/脚本/<name>.{sh,py}`
  - 项目级: `<repo>/.wiki/脚本/<name>.{sh,py}`
- **用途示例**:
  - `canvas-from-mindmap.py` — 由 markdown 大纲生成 Obsidian canvas
  - `frontmatter-normalize.sh` — 把缺字段的 frontmatter 补齐
  - `link-rewriter.py` — wikilink ↔ markdown link 转换
- **命名**: kebab-case, 见名知意, 禁通用名 (`tool.sh` / `script.py` 不允许)
- **shell 脚本 (sh) 要求**:
  - 第 1 行 shebang: `#!/usr/bin/env bash` 或 `#!/bin/bash`
  - 5 行内含 help text (注释或 `usage()` 函数)
  - `set -euo pipefail` 推荐
- **python 脚本 (py) 要求**:
  - 模块顶部 docstring (`"""..."""`) 描述用途与参数
  - `if __name__ == "__main__":` 入口
  - 用 `argparse` 或等价方式处理参数
- **frontmatter (推荐, 不强制, 写为脚本内顶部注释块)**:

```bash
# ---
# type: vault-script
# name: canvas-from-mindmap
# created: 2026-06-09
# ---
```

## 补充: 用户操作入口脚本 (不属三模块)

用户从 shell 直接调的 CLI / 包装器, 关注"方便人用"。

- **路径**: `~/.cortex/scripts/<name>.{sh,py}` (**仅用户级**, 项目级不设)
- **命名**: kebab-case; 鼓励 `cortex-` 前缀 (如 `cortex-save`, `cortex-recall`, `cortex-lint`)
- **用途示例**:
  - `cortex-save` — 快速把当前 stdin / 文件存入 L4-inbox
  - `cortex-recall <query>` — 全文检索 vault
  - `cortex-lint` — 用户友好的 lint 入口 (内部调 `~/.cortex/.wiki/scripts/` 或插件脚本)
- **治理**: lint 规则 R7 单独处理, **不进 knowledge 模块校验范围** (不被 cortex-schema-knowledge 视为三模块成员)。
- **混用检测**:
  - 项目级若出现 `<repo>/.cortex/scripts/` 视为错误 (lint R7 报告)
  - vault 内部脚本路径必须用中文 `脚本/`, 出现 `<root>/.wiki/scripts/` (英文) → 视为错误, lint 报告
  - 顶层 `~/.cortex/scripts/` 永远英文; 不允许出现 `~/.cortex/脚本/`

## 引用

- 目录契约: `plugins/tools/cortex/docs/layout.md`
- 记忆等级 schema: `cortex-schema-memory`
- lint 规则集 (含 R7 入口脚本治理): `cortex-lint`
- extract 路由表: `cortex-extract`
