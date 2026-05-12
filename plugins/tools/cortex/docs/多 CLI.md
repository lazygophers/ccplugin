# 多 CLI 数据兼容

cortex 的 vault 结构与 frontmatter 设计为 **CLI-agnostic**: runtime hooks/skills 仅 Claude Code, 但 vault 数据可被未来 codex/copilot/gemini 等 adapter 读写、查询、检索。

## 1. frontmatter 新增 2 字段

每个落档页 (log / fleeting / 任何由 CLI 自动写入的页) 都带:

```yaml
---
type: log
title: ...
created: 2026-05-11
updated: 2026-05-11
preset: lyt
lang: zh-CN
cli: claude-code # 新: 来源 CLI
cli_session: a1b2c3d4-... # 新: 会话 id
---
```

`cli` 枚举:

- `claude-code` — Claude Code CLI
- `codex` — OpenAI Codex (未来)
- `copilot` — GitHub Copilot CLI (未来)
- `gemini` — Google Gemini (未来)
- `qoder` / `kiro` — 实验中
- `manual` — 用户直接写的 (cortex-ingest 默认)

## 2. sessions/<cli>/<YYYY-MM>/ 备份

每次 Stop / SubagentStop / PostCompact hook 触发后:

1. 复制原始 transcript JSONL → `sessions/<cli>/<YYYY-MM>/<DD-HHMM>-<slug>.jsonl`
2. 可选 (`config.preserve_archive=true`) → 同名 `.tar.gz` 打包
3. 提炼版仍写到 `log/`, frontmatter `cli` / `cli_session` 指回 transcript

```
<vault>/sessions/
├── claude-code/
│   └── 2026-05/
│       ├── 11-1430-cortex-v2-design.jsonl
│       └── 11-1612-bug-fix.jsonl
├── codex/
│   └── 2026-05/
│       └── 11-2030-refactor-attempt.jsonl
└── copilot/
```

默认 `preserve_transcript=false` 节省磁盘, 用户开启需自负责轮转。

## 3. 跨 CLI 查询

### 3.1 基于路径

```text
cortex-search "auth" path:sessions/codex/
```

cortex-search L4 (MCP `obsidian_simple_search`) 支持 `path:` 前缀过滤。

### 3.2 基于 frontmatter (Dataview)

```dataview
TABLE cli, cli_session, created
FROM "log"
WHERE cli = "claude-code" AND created > date("2026-05-01")
SORT created DESC
```

或聚合统计:

```dataview
TABLE length(rows) AS sessions
FROM "log"
GROUP BY cli
```

### 3.3 cortex-session skill

```text
"列 codex 5 月份 sessions"
→ cortex-session 解析 sessions/codex/2026-05/, 给出列表 + 摘要
```

支持任意 CLI 来源 transcript 的 jsonl 解析与重放摘要。

## 4. 写入约束 (multi-CLI 共生)

vault 同时有多 CLI 写入时:

- 各 CLI 写自己的 `sessions/<cli>/`, 不交叉
- `log/` `fleeting/` 共享, 通过 `cli` 字段区分来源
- `cli_session` 字段必填, 否则跨 CLI 查询会丢分组键
- frontmatter `lang` 必须与 vault.lang 一致 (lint i18n-frontmatter-lang-mismatch 监控)

## 5. 未来 adapter 设计要求

新增 CLI 写入支持时, 仅需:

1. 在该 CLI 平台上实现等价 Stop/SessionEnd hook
2. 调用 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/_lib/save_session.py --cli <name>` (现成)
3. 复用 `templates/` (frontmatter 已含 `cli` 占位)

不需要改 vault 结构、不需要改既有 cortex skill, 也不需要改 lint 规则。这就是 "vault 数据兼容" 的含义。

## 6. cortex 自身 vs adapter 角色

| 维度       | cortex (本插件)                  | 未来 adapter                                        |
| ---------- | -------------------------------- | --------------------------------------------------- |
| runtime    | Claude Code 专属                 | 各自 CLI                                            |
| vault 结构 | 定义者                           | 消费者                                              |
| skills     | 14 个                            | 复用 cortex skill (若 CLI 支持 skill 概念) 或自实现 |
| hooks      | 4 个 (CC)                        | 自实现                                              |
| 数据格式   | 定义 frontmatter / 路径 / locale | 遵守                                                |

## 7. 关联

- skill: `cortex-session` (列/解析 transcript) · `cortex-save` (落档 + frontmatter cli 字段)
- 设计: `prd.md §5` · `prd.md §1.2` (不为非 CC 写 hook)
- hook 实现: `hooks/_lib/save_session.py`
