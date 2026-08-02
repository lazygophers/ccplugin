# CLI 迁移 Typer — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 方案

把 `skeinlib.cli.main()` 改为 Typer app 入口。每个 CLI 命令只负责把 Typer 参数组装成轻量 namespace，再调用现有 `Skein` 协作对象方法。业务逻辑继续留在 `admin/lifecycle/scheduling/artifacts/query`，避免框架迁移变成业务重写。

## 锁边界

保留现有单一锁入口：CLI 层根据命令名判断是否写盘。Typer command wrapper 内复用同一个 dispatch helper；写盘命令包 `_workspace_lock(sk.dir / ".lock")`，纯读命令直接调用。

## 全局参数

Typer 原生支持全局 option 放在命令前。为兼容旧调用习惯，入口继续预剥离 `-d/--debug` 与 `-j/--json`，让它们可放在子命令前后；再把结果写入 namespace。

## 命令映射

- 一层命令保持当前名称。
- `del/delete/rm/remove` 用 Typer alias 或多个 command 包同一 handler。
- `config set/reset` 与 `prd read/write/add/check/uncheck` 保持子命令结构。
- `subtask` 保持 `action tid [sid]` 形态，避免一次性拆成多层命令造成调用面变化。

## Bin JSON-only wrapper

`plugins/tools/skein/bin/` 是插件市场对外入口。除 `bin/skein serve` 持久服务直通外，`bin/skein`、`bin/skein-spec`、`bin/skein-hooks` 统一经 `_jsonwrap.run_json()` 包装脚本执行结果，stdout 只输出一个 JSON object。wrapper 同时捕获 `sys.stdout` 与 fd 1，覆盖 Rich/Console 等已缓存 stdout handle 的输出路径；原脚本 stdout 能解析 JSON 时放入 `data`，否则放入 `stdout`。

## 测试接缝 (seam)
check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

- [x] 复用 `plugins/tools/skein/scripts/tests/test_skein.py` 端到端 CLI smoke。
- [x] 复用 `plugins/tools/skein/scripts/tests/test_dag.py` 调度命令行为测试。
