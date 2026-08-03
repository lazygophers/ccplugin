---
title: typer-migration-pattern
category: cli
keywords: [cli, typer, argparse, framework, migration, 命令行]
status: active
inclusion: auto
anchors: plugins/tools/skein/scripts/skeinlib/cli.py,plugins/tools/skein/scripts/tests/test_skein.py
---

## Typer CLI 框架迁移模式

从 argparse 迁移到 Typer 框架时，按以下原则保护现有命令合同和业务逻辑：

### 核心原则

1. **命令合同优先** - 迁移只改框架层（CLI 参数解析），不重写业务逻辑（business domain）
2. **锁边界保护** - 写盘命令继续经过统一锁，纯读命令免锁
3. **全局参数兼容** - `-d/--debug` 与 `-j/--json` 可放在子命令前后，保留既有调用习惯

### 迁移策略

- 每个 CLI 命令只负责把 Typer 参数组装成轻量 namespace
- 业务逻辑继续留在 lifecycle/scheduling/admin/artifacts/query 等专属模块
- 避免框架迁移变成业务重写

### 子命令结构保留

- `del/delete/rm/remove` 用 Typer alias 或多个 command 包同一 handler
- `config set/reset` 与 `prd read/write/add/check/uncheck` 保持子命令结构
- `subtask` 保持 `action tid [sid]` 形态，避免一次性拆成多层命令造成调用面变化
