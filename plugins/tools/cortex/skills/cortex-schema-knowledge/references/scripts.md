# 脚本模块 (脚本) — vault 内部脚本

被 cortex 流程 (lint / extract / canvas / frontmatter 整形) 调用的内部工具, **不是给用户直接调**。

## 路径

- 用户级: `~/.cortex/.wiki/脚本/<name>.{sh,py}`
- 项目级: `<repo>/.wiki/脚本/<name>.{sh,py}`

## 用途示例

- `canvas-from-mindmap.py` — 由 markdown 大纲生成 Obsidian canvas
- `frontmatter-normalize.sh` — 把缺字段的 frontmatter 补齐
- `link-rewriter.py` — wikilink ↔ markdown link 转换

## 命名

kebab-case, 见名知意, 禁通用名 (`tool.sh` / `script.py` 不允许)。

## shell 脚本 (sh) 要求

- 第 1 行 shebang: `#!/usr/bin/env bash` 或 `#!/bin/bash`
- 5 行内含 help text (注释或 `usage()` 函数)
- `set -euo pipefail` 推荐

## python 脚本 (py) 要求

- 模块顶部 docstring (`"""..."""`) 描述用途与参数
- `if __name__ == "__main__":` 入口
- 用 `argparse` 或等价方式处理参数

## frontmatter (推荐, 不强制, 写为脚本内顶部注释块)

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

## 混用检测

- 项目级若出现 `<repo>/.cortex/scripts/` 视为错误 (lint R7 报告)
- vault 内部脚本路径必须用中文 `脚本/`, 出现 `<root>/.wiki/scripts/` (英文) → 视为错误, lint 报告
- 顶层 `~/.cortex/scripts/` 永远英文; 不允许出现 `~/.cortex/脚本/`
