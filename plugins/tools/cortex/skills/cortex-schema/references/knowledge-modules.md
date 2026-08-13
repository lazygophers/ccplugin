# 三模块路径规则 (项目 / 领域 / 脚本)

vault 内部三模块的路径 / 命名 / frontmatter 关键字段. 完整模板见 `../templates/`, 完整 .md 样例见 `../examples/`.

---

## 模块 1: 项目 (`项目/`) — 仅用户级

记录外部 repo / 站点的摘要与心智地图. **仅在用户级** `~/.cortex/.wiki/项目/` — 引用外部 repo 是跨项目沉淀, 项目级 `<repo>/.wiki/` 不设此模块.

### 路径

`~/.cortex/.wiki/项目/<host>/<owner>/<repo>/`

- `<host>` 起的路径段同下
- `<host>` 枚举: `github.com` / `gitlab.com` / `bitbucket.org` / 任意自定义 domain (如 `nextjs.org`)
- `<owner>` = 组织或用户名; 无 owner 概念的站点可用 `_` 占位
- `<repo>` = 仓库名或站点 slug

### 目录内容

- `README.md` — 必备, 摘要主文件 (含 frontmatter)
- `mindmap.canvas` — 推荐, Obsidian canvas 心智地图
- `graph.json` — 可选, 结构化关系图
- `notes/` — 可选, 子页面

### 命名约定

路径段全部小写, 保留原始 owner/repo 大小写时统一转小写 (与 GitHub URL 不区分大小写对齐).

### frontmatter 关键字段

`type: project` + `source` (URL, 必备) + `summary` + `mindmap` (推荐) + 通用字段. 完整模板见 `../templates/project/` (github/gitlab/website 变体), 落盘样例见 `../examples/project.md`.

---

## 模块 2: 领域 (`领域/`) — 双层

跨项目复用的领域 / 经验 / 方法笔记. **用户级 + 项目级都有** (项目级唯一的 knowledge 模块).

### 路径

`<root>/领域/<area>/<sub>/[<sub2>/]<topic>.md`

- `<root>` ∈ {`~/.cortex/.wiki`, `<repo>/.wiki`}
- 必须 ≥ 2 级目录 (area + sub 最少)
- `<area>` 预设: `tech` / `life` / `finance` (用户可扩展, 如 `health` / `art`)
- `<sub>` / `<sub2>` 自由分类

### 示例路径

- `领域/tech/rust/async/tokio-runtime.md`
- `领域/life/habits/sleep-protocol.md`
- `领域/finance/etf/global-allocation.md`

### 禁路径

- `领域/<topic>.md` (缺 sub 级)
- `领域/misc/...` (area=misc 不允许, 必须明确)

### frontmatter 关键字段

`type: domain` + `area` (必备) + 通用字段. 完整模板见 `../templates/domain.md`, 落盘样例见 `../examples/domain.md`.

---

## 模块 3: 脚本 (`脚本/`) — vault 内部脚本, 仅用户级

被 cortex 流程 (lint / extract / canvas / frontmatter 整形) 调用的内部工具, **不是给用户直接调**. **仅用户级** — 项目级 `<repo>/.wiki/` 不设 脚本/.

### 路径

`~/.cortex/.wiki/脚本/<name>.{sh,py}` (仅用户级)

### 用途示例

- `canvas-from-mindmap.py` — 由 markdown 大纲生成 Obsidian canvas
- `frontmatter-normalize.sh` — 把缺字段的 frontmatter 补齐
- `link-rewriter.py` — wikilink ↔ markdown link 转换

### 命名

kebab-case, 见名知意, 禁通用名 (`tool.sh` / `script.py` 不允许).

### shell 脚本 (sh) 要求

- 第 1 行 shebang: `#!/usr/bin/env bash` 或 `#!/bin/bash`
- 5 行内含 help text (注释或 `usage()` 函数)
- `set -euo pipefail` 推荐

### python 脚本 (py) 要求

- 模块顶部 docstring (`"""..."""`) 描述用途与参数
- `if __name__ == "__main__":` 入口
- 用 `argparse` 或等价方式处理参数

### frontmatter

`type: vault-script`, 写为脚本顶部注释块, 推荐不强制. 见 `../templates/vault-script.md`, 样例见 `../examples/vault-script.md`.

---

## 补充: 用户操作入口脚本 (不属三模块)

用户从 shell 直接调的 CLI / 包装器, 关注"方便人用".

- **路径**: `~/.cortex/scripts/<name>.{sh,py}` (**仅用户级**, 项目级不设)
- **命名**: kebab-case; 鼓励 `cortex-` 前缀 (如 `cortex-save`, `cortex-recall`, `cortex-lint`)
- **用途示例**:
  - `cortex-save` — 快速把当前 stdin / 文件存入 L4-inbox
  - `cortex-recall <query>` — 全文检索 vault
  - `cortex-lint` — 用户友好的 lint 入口
- **治理**: lint 规则 R7 单独处理, **不进 knowledge 模块校验范围**.

### 混用检测

- 项目级若出现 `<repo>/.cortex/scripts/` → lint R7 报错
- vault 内部脚本路径必须用中文 `脚本/`, 出现 `<root>/.wiki/scripts/` (英文) → lint 报错
- 顶层 `~/.cortex/scripts/` 永远英文; 不允许出现 `~/.cortex/脚本/`

## 引用

- 顶层布局: `topology.md`
- frontmatter 模板: `../templates/`
- 完整样例: `../examples/{project,domain,vault-script}.md`
- lint R1-R7: `cortex-lint`
