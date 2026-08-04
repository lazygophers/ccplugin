"""core — 业务核心层 (工作区底座 + 门面 + 5 个协作对象 + 2 个 mixin)。

workspace: 路径/配置/store/锁 — 共享底座
commands: Skein 门面 — 继承 Workspace, 装配协作对象
lifecycle: create→confirm→start→check→finish 状态机
scheduling: DAG 调度 (claim/exec/subtask)
query: 只读投影 (ready/status/list)
artifacts: task 工件 (prd/fmt/contract)
admin: 工作区级命令 (init/setup/config/clean/board)
doctor: 体检 + 质量门 + session 上下文
"""
