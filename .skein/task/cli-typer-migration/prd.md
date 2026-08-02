# CLI 迁移 Typer — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] `skein.py` CLI 从 `argparse` 迁移到 Typer 框架，保留现有命令、参数、stdout/stderr 行为和 exit code 语义。
- [ ] `skein claim --dry-run`、`skein claim exec --dry-run`、`skein claim check --dry-run` 等现有调用继续可用。
- [ ] 迁移后命令分发仍复用现有 `Skein` command 对象，不顺手重写业务逻辑。
- [ ] plugins/tools/skein/bin/ 下除 serve 外全部 wrapper stdout 必须是 JSON-only。
- [ ] `plugins/tools/skein/scripts/skein.py` direct-run 除 serve 外 stdout 也必须是 JSON-only；`claim --dry-run` 必须返回结构化 `data`，不能把原中文输出塞进 `stdout` 字符串。
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `plugins/tools/skein/scripts/skeinlib/cli.py` parser 从 argparse 改为 Typer。
- [ ] 范围内: 必要时调整 tests/helper 以适配 Typer 行为，但不改变业务命令合同。
- [ ] 范围内: 更新与 CLI 框架相关的文档/模块说明。
- [ ] 范围外: 不重构 lifecycle/scheduling/admin/artifacts/query 的业务逻辑。
- [ ] 范围外: 不新增 CLI 命令、不改 task/subtask 数据 schema。
- [ ] 约束: `pyproject.toml` 已有 `typer>=0.24.1`，不新增依赖。
- [ ] 约束: 全局 `-d/--debug`、`-j/--json` 仍可放在子命令前后。

## User Stories
1. As a main dispatcher, I want existing `skein.py <command>` invocations to keep working, so that skein-flow 不因 CLI 迁移中断。
2. As a user, I want Typer-based help output for all commands, so that CLI 更易发现和维护。
3. As a checker/executor/finisher agent, I want stdout 机器输出保持稳定, so that agent parsing 不被框架迁移破坏。
4. As a maintainer, I want CLI declaration separated from business command methods, so that adding commands no longer需要手写 argparse 分支。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] `plugins/tools/skein/scripts/skeinlib/cli.py` 不再 import/use `argparse` 构建 parser，改用 Typer app/commands。
- [x] `python3 plugins/tools/skein/scripts/skein.py --help` 成功显示 Typer help。
- [x] `python3 plugins/tools/skein/scripts/skein.py claim --dry-run` 可运行且同时返回 exec 与 check/finishing 两路信息。
- [x] 现有 smoke / DAG CLI 测试覆盖的核心命令仍通过，或失败项明确是既有非本任务问题。
- [x] 写盘命令仍经过 `_workspace_lock`，纯读命令仍免锁。
- [x] bin/skein、bin/skein-spec、bin/skein-hooks 输出均为单个 JSON 对象；bin/skein serve 例外直通。
- [x] `python3 plugins/tools/skein/scripts/skein.py claim --dry-run` 输出单个 JSON 对象，结果在结构化 `data.exec` / `data.check` 内；`serve` 例外直通。
## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- [ ] 复用 `plugins/tools/skein/scripts/tests/test_skein.py` 的端到端 CLI smoke。
- [ ] 复用 `plugins/tools/skein/scripts/tests/test_dag.py` 的调度命令行为测试。
- [ ] 不测试 Typer 内部实现，只测试 CLI 命令输入输出、状态落盘和锁边界。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list cli-typer-migration`)
