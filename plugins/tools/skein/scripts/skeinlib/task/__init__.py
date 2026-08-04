"""task 包 — task/subtask 数据结构 + task.json 落盘功能。

子模块直接 import: `from skeinlib.task.model import ...` / `from skeinlib.task.store import TaskStore`。
不在此处做 re-export — 37 个符号的 facade 表曾零消费者, 删之 (ADR 0003 S4)。
"""
