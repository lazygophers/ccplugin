# 物理布局 (topology)

cortex 双层知识库 + 记忆系统的物理目录布局. 本文件是路径权威源, 其他 skill / 脚本 / agent 仅引用此处.

**双层差异 (重要)**: 用户级 `~/.cortex/.wiki/` 含全部模块 (memory + 项目 + 领域 + 脚本); 项目级 `<repo>/.wiki/` **仅 memory + 领域** — 不含 项目/ (引用外部 repo 属跨项目沉淀, 只在用户级) 与 脚本/ (vault 内部脚本只在用户级).

## 用户级根: `~/.cortex/`

```
~/.cortex/
├── .wiki/                      ← 用户级知识库根 (全模块)
│   ├── memory/                 ← 5 级记忆树 (详见 memory-levels.md)
│   │   ├── L0-core/
│   │   ├── L1-long/
│   │   ├── L2-mid/
│   │   ├── L3-short/           ← extract 默认入口
│   │   └── L4-inbox/
│   ├── 项目/                   ← 项目模块 (GitHub/GitLab/Website 摘要)
│   │   └── <host>/<owner>/<repo>/
│   ├── 领域/                   ← 领域模块 (≥ 2 级目录)
│   │   ├── tech/...
│   │   ├── life/...
│   │   └── finance/...
│   └── 脚本/                   ← 知识库内部脚本 (vault-internal)
├── config/                     ← 插件配置 (yaml/json)
├── state/                      ← 增量游标 / 索引缓存
├── scripts/                    ← 用户操作入口 CLI (英文, cortex-save / cortex-recall ...)
├── logs/                       ← 运行日志
└── <开放扩展位>                 ← cache/credentials/templates 等
```

## 项目级根: `<repo>/.wiki/`

```
<repo>/.wiki/                   ← 项目级知识库, 仅 memory + 领域
├── memory/
│   ├── L0-core/
│   ├── L1-long/
│   ├── L2-mid/
│   ├── L3-short/
│   └── L4-inbox/
└── 领域/                       ← 本项目专属领域知识
```

**项目级不含**:
- `项目/` — 引用外部 repo/website 是跨项目沉淀, 只落用户级 `~/.cortex/.wiki/项目/`
- `脚本/` — vault 内部脚本只在用户级
- 顶层 `config/ state/ scripts/ logs/` — 仅用户级

## 详细 ASCII (含示例文件叶子)

实际填充后的样子, 帮助理解 "什么文件落在哪个目录":

```
~/.cortex/.wiki/
├── memory/
│   ├── L0-core/
│   │   └── never-commit-secrets.md      ← 示例规则 (type=rule, level=L0)
│   ├── L1-long/
│   │   └── shell-quoting-rules.md       ← 长期记忆样例
│   ├── L2-mid/
│   │   └── current-sprint-context.md    ← 中期记忆
│   ├── L3-short/
│   │   └── today-tmp-fix.md             ← 短期记忆 (extract 默认入口)
│   └── L4-inbox/
│       ├── pasted-note.md               ← 原始未分类
│       └── _archived/
│           └── ...                       ← extract 消化后归档桩
├── 项目/
│   └── github.com/
│       └── lazygophers/
│           └── ccplugin/
│               ├── README.md            ← 摘要主文件 (type=project, 含 frontmatter)
│               ├── mindmap.canvas       ← (可选) Obsidian canvas 心智地图
│               ├── graph.json           ← (可选) 结构化关系图
│               └── notes/
│                   ├── architecture.md  ← 子页面
│                   └── design.md
├── 领域/
│   ├── tech/
│   │   └── rust/
│   │       └── async/
│   │           └── tokio-runtime.md     ← ≥ 2 级 sub (area=tech/sub=rust/sub2=async)
│   ├── life/
│   │   └── habits/
│   │       └── sleep-protocol.md
│   └── finance/
│       └── etf/
│           └── global-allocation.md
└── 脚本/
    ├── canvas-from-mindmap.py           ← vault 内部脚本 (中文目录)
    └── frontmatter-normalize.sh
```

## 双层关系 (部分同构)

`~/.cortex/.wiki/` 与 `<repo>/.wiki/` **共有部分同构, 但模块集不同**:

| 模块 | 用户级 `~/.cortex/.wiki/` | 项目级 `<repo>/.wiki/` |
| --- | --- | --- |
| `memory/` 5 级 (L0-core ... L4-inbox) | ✓ | ✓ |
| `领域/` | ✓ | ✓ |
| `项目/` (外部 repo/website 摘要) | ✓ | ✗ (跨项目沉淀, 仅用户级) |
| `脚本/` (vault 内部脚本) | ✓ | ✗ (仅用户级) |

- 共有部分 (memory + 领域) frontmatter schema 共用 (详见 `../templates/`)
- lint / extract 在共有部分用相同规则; 项目级不校验 项目/脚本

## 必备目录 (validate-layout 校验)

用户级 `~/.cortex/` 顶层必备 5 项:

| 目录 | 用途 |
| --- | --- |
| `.wiki/` | 知识库根 |
| `config/` | 插件配置 |
| `state/` | 增量游标 / 索引缓存 |
| `scripts/` | 用户操作入口 CLI |
| `logs/` | 运行日志 |

vault 内部 (`.wiki/` 下) 必备, **按层级不同**:

- 用户级 `~/.cortex/.wiki/`: `memory/L0-core/` ... `memory/L4-inbox/` (5 级) + `项目/` + `领域/` + `脚本/`
- 项目级 `<repo>/.wiki/`: `memory/L0-core/` ... `memory/L4-inbox/` (5 级) + `领域/` (无 项目/脚本)

注: `validate-layout.sh` 默认 `--target ~/.cortex` 校验**用户级**全模块; 项目级仅含 memory + 领域 (无专用校验器, 见 cortex-lint R4)。

## 开放扩展位

`~/.cortex/` 顶层除上述 5 项**必备**外, 用户可任意加:

- `cache/` (各类索引缓存)
- `credentials/` (凭证, 权限 600)
- `templates/` (笔记模板)
- 其他

validate-layout **只检必备项, 不禁额外项**.

## 脚本目录用途分离 (重要)

| 目录 | 用途 | 谁调用 | 双层? |
| --- | --- | --- | --- |
| `~/.cortex/scripts/` | 用户操作入口 CLI / 包装器 (英文路径) | 用户 shell 直接调 | 仅用户级 |
| `~/.cortex/.wiki/脚本/` | vault 内部工具 (lint/canvas/frontmatter) | 被 cortex 流程调用 | **仅用户级** (项目级不设 脚本/) |

**命名差异不是 bug 是 feature**: 顶层 `scripts/` (英文) = 用户调; vault 内 `脚本/` (中文) = vault 自治. 两者绝不混用.

混用风险:

- 项目级误建 `<repo>/.cortex/scripts/` → lint R7 报错
- vault 内出现英文 `<root>/.wiki/scripts/` → lint 报错
- 顶层出现中文 `~/.cortex/脚本/` → lint 报错

## 引用

- 三模块内部规范: `knowledge-modules.md`
- frontmatter 模板: `../templates/`
- memory 5 级语义与映射: `memory-levels.md`
- 完整样例: `../examples/`
- lint 规则集: `cortex-lint`
