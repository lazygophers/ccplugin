# 物理布局 (topology)

cortex 双层同构知识库 + 记忆系统的物理目录布局。本文件是路径权威, 其他 skill / 脚本 / agent 仅引用此处。

## 用户级根: `~/.cortex/`

```
~/.cortex/
├── .wiki/                      ← 用户级知识库根 (与项目 .wiki 同构)
│   ├── memory/                 ← 记忆树 (按遗忘曲线分级, 详见 cortex-schema-memory)
│   │   ├── L0-core/
│   │   ├── L1-long/
│   │   ├── L2-mid/
│   │   ├── L3-short/           ← extract 默认入口
│   │   └── L4-inbox/
│   ├── 项目/                    ← 项目模块 (GitHub/GitLab/Website 摘要, 详见 projects.md)
│   │   └── <host>/<owner>/<repo>/
│   ├── 领域/                    ← 领域模块 (≥ 2 级目录, 详见 domains.md)
│   │   ├── tech/...
│   │   ├── life/...
│   │   └── finance/...
│   └── 脚本/                    ← 知识库内部脚本 (vault-internal, 详见 scripts.md)
├── config/                     ← 插件配置 (yaml/json)
├── state/                      ← 增量游标 / 索引缓存 (lint cursor, extract cursor)
├── scripts/                    ← 用户操作入口脚本 (user-facing CLI: cortex-save / cortex-recall 等)
├── logs/                       ← 运行日志
└── <开放扩展位>                  ← cache/credentials/templates 等 (用户可自由扩展)
```

## 项目级根: `<repo>/.wiki/`

```
<repo>/.wiki/                   ← 项目级知识库, 与 ~/.cortex/.wiki 内部完全同构
├── memory/
│   ├── L0-core/
│   ├── L1-long/
│   ├── L2-mid/
│   ├── L3-short/
│   └── L4-inbox/
├── 项目/                       ← 本项目引用的外部 repo/website
├── 领域/                       ← 本项目专属领域知识
└── 脚本/                       ← 项目知识库内部脚本 (用途同 ~/.cortex/.wiki/脚本/)
```

**项目级不设 `.cortex/scripts/`**: 用户操作入口仅在用户级。

## 双层同构原则

`~/.cortex/.wiki/` 与 `<repo>/.wiki/` 内部结构**完全一致**, 仅根路径不同:

- 都含 5 级 memory 子目录 (L0-core ... L4-inbox)
- 都含 项目/领域/脚本 三模块 (vault 内部目录名采用中文)
- frontmatter schema 共用 (详见 templates.md)
- lint / extract 用相同规则两边跑

## 必备目录 (validate-layout.sh 校验)

用户级 `~/.cortex/` 顶层必备 5 项:

| 目录 | 用途 |
| --- | --- |
| `.wiki/` | 知识库根 |
| `config/` | 插件配置 |
| `state/` | 增量游标 / 索引缓存 |
| `scripts/` | 用户操作入口 CLI |
| `logs/` | 运行日志 |

vault 内部 (`.wiki/` 下) 必备:

- `memory/L0-core/` ... `memory/L4-inbox/` (5 级齐全)
- `项目/` / `领域/` / `脚本/` (三模块齐全)

## 开放扩展位

`~/.cortex/` 顶层除上述 5 项**必备**外, 用户可任意加:

- `cache/` (各类索引缓存)
- `credentials/` (凭证, 权限 600)
- `templates/` (笔记模板)
- 其他

`validate-layout.sh` **只检必备项, 不禁额外项**。

## 脚本目录用途分离 (重要)

| 目录 | 用途 | 谁调用 | 双层? |
| --- | --- | --- | --- |
| `~/.cortex/scripts/` | 用户操作入口 CLI / 包装器 (英文路径) | 用户 shell 直接调 | 仅用户级 |
| `~/.cortex/.wiki/脚本/` | vault 内部工具 (lint/canvas/frontmatter) | 被 cortex 流程调用 | 用户级 + 项目级 |

**命名差异不是 bug 是 feature**: 顶层 `scripts/` (英文) = 用户调; vault 内 `脚本/` (中文) = vault 自治. 两者绝不混用.

混用风险:

- 项目级误建 `<repo>/.cortex/scripts/` → lint R7 报错
- vault 内出现英文 `<root>/.wiki/scripts/` → lint 报错
- 顶层出现中文 `~/.cortex/脚本/` → lint 报错

## 引用

- 三模块内部规范: `projects.md` / `domains.md` / `scripts.md`
- frontmatter 模板: `templates.md`
- memory 5 级语义与映射: `cortex-schema-memory`
- lint 规则集: `cortex-lint`
