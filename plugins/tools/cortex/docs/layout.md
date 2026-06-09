# cortex 目录契约

cortex 双层同构知识库 + 记忆系统的目录与路径规范。所有 skill / 脚本 / agent 都以本文档为单一真相。

## 用户级根: `~/.cortex/`

```
~/.cortex/
├── .wiki/                      ← 用户级知识库根 (与项目 .wiki 同构)
│   ├── memory/                 ← 记忆树 (按遗忘曲线分级)
│   │   ├── L0-core/            ← 核心记忆, 不可违反 (永久)
│   │   ├── L1-long/            ← 长期记忆 (曲线尾端, 已稳固)
│   │   ├── L2-mid/             ← 中期记忆 (周月级)
│   │   ├── L3-short/           ← 短期记忆 (曲线头端, 最易遗忘) — extract 默认入口
│   │   └── L4-inbox/           ← 收件箱, 原始资料未分类
│   ├── 项目/                    ← 项目模块 (GitHub/GitLab/Website 摘要)
│   │   └── <host>/<owner>/<repo>/
│   ├── 领域/                    ← 领域模块 (≥ 2 级目录)
│   │   ├── tech/...
│   │   ├── life/...
│   │   └── finance/...
│   └── 脚本/                    ← 知识库内部脚本 (vault-internal: lint/canvas/frontmatter 工具)
├── config/                     ← 插件配置 (yaml/json)
├── state/                      ← 增量游标 / 索引缓存 (lint cursor, extract cursor)
├── scripts/                    ← 用户操作入口脚本 (user-facing CLI: cortex-save / cortex-recall 等)
├── logs/                       ← 运行日志
└── <开放扩展位>                  ← cache/credentials/templates 等 (用户可自由扩展, 校验只检必备项)
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

## 同构原则

`~/.cortex/.wiki/` 与 `<repo>/.wiki/` 内部结构**完全一致**, 仅根路径不同:
- 都含 5 级 memory 子目录
- 都含 项目/领域/脚本 三模块 (vault 内部目录名采用中文)
- frontmatter schema 共用
- lint / extract 用相同规则两边跑

## 脚本目录用途分离 (重要)

| 目录 | 用途 | 谁调用 | 双层? |
| --- | --- | --- | --- |
| `~/.cortex/scripts/` | 用户操作入口 CLI / 包装器 (英文路径) | 用户 shell 直接调 | 仅用户级 |
| `~/.cortex/.wiki/脚本/` | vault 内部工具 (lint/canvas/frontmatter) | 被 cortex 流程调用 | 用户级 + 项目级 |

**命名差异不是 bug 是 feature**: 顶层 `scripts/` (英文) = 用户调; vault 内 `脚本/` (中文) = vault 自治. 两者绝不混用.

混用风险: 项目级误建 `<repo>/.cortex/scripts/` → lint R7 报错.

## 记忆等级语义 (按遗忘曲线设计)

**反直觉警告**: 数字越小 ≠ 越短期。本系统按 Ebbinghaus 遗忘曲线设计:

```
L3 短期 (易忘) ─ promote → L2 中期 ─ promote → L1 长期 (稳固) ─ promote → L0 核心
       7d 阈值                90d 阈值              365d 阈值              永久, 仅手动
```

- **L0-core**: 不进入曲线, 永久, 用户显式 "永远 / 硬性" 才进, 不自动降级
- **L1-long**: 曲线尾端, 已稳固, 365d 未访问才 demote (不自动 forget)
- **L2-mid**: 曲线中段, 90d 未访问 demote 到 L3
- **L3-short**: 曲线头端, 最易遗忘, extract 默认入口, 7d 未访问标 forget 候选
- **L4-inbox**: 未进入曲线, 收件箱原始资料

升级方向 = 抵抗遗忘: L3 → L2 → L1 → L0。降级方向 = 遗忘: L1 → L2 → L3 → forget 候选。

## frontmatter 通用字段

| 字段 | 必备 | 类型 | 说明 |
| --- | --- | --- | --- |
| `type` | 是 | str | `rule` (memory/L0) / `memory` (L1-L4) / `project` / `domain` / `vault-script` |
| `level` | type=rule/memory 时必备 | str | `L0` `L1` `L2` `L3` `L4` |
| `created` | 是 | ISO date | 创建日期 |
| `updated` | 否 | ISO date | 最近编辑 |
| `tags` | 否 | list | wikilink-friendly 标签 |
| `aliases` | 否 | list | 别名 |
| `weight` | 否 (L1-L3 建议) | float 0-1 | 用户标注强度 |
| `source` | type=project 必备 | URL | 项目来源链接 |
| `area` | type=domain 必备 | str | domains 一级 area |
| `mindmap` | type=project 推荐 | path | canvas 文件相对路径 |

## 开放扩展位

`~/.cortex/` 顶层除 `.wiki/ config/ state/ scripts/ logs/` 五项**必备**外, 用户可任意加:
- `cache/` (各类索引缓存)
- `credentials/` (凭证, 权限 600)
- `templates/` (笔记模板)
- 其他

`validate-layout.sh` **只检必备项, 不禁额外项**。

## 引用

- 记忆等级详细规则: `skills/cortex-schema-memory/SKILL.md`
- 三模块路径规则: `skills/cortex-schema-knowledge/SKILL.md`
- lint 规则: `skills/cortex-lint/SKILL.md`
- extract 路由: `skills/cortex-extract/SKILL.md`
