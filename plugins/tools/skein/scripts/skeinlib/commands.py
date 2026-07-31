"""`Skein` — 门面: 把工作区底座和五个协作对象接在一起, 自己不实现任何命令。

## 从前是什么样
这里曾是一个 40 个方法的类, 状态机、调度、查询、工件读写、工作区管理全挤在一起, 共享十几个
`self.X`。谁碰了谁只能靠通读发现 —— 加一个字段, 没人说得清哪些命令会受影响。

## 现在的形状
```
Workspace          路径 / 生效配置 / TaskStore / 阶段钩子     ← 共享底座, Skein 继承它
├─ Admin           init / setup / config / clean / board      (不带 task id 的命令)
├─ Lifecycle       create → confirm → start → check → finish  (单个 task 的状态机)
├─ Scheduler       claim / subtask                            (subtask DAG 调度)
├─ Query           current / ready / status / list            (只读投影, 无写盘)
└─ Artifacts       prd / fmt / contract                       (task 工件读写)
```
依赖一律走**构造入参**: `Scheduler(ws, lifecycle)` 这一行就是它的完整依赖清单, 不必读实现。
唯二的横向依赖也在签名里写着 —— `Lifecycle` 要一个 doctor 可调用 (start 前置体检),
`Scheduler` 要 `Lifecycle` (认领就绪 task 时就地启动, 必须复用同一条启动路径)。

## 门面上为什么没有转发方法
`cli.py` 的 dispatch 直接指向 `sk.lifecycle.create` / `sk.scheduler.claim` 这样的绑定方法。
写一层 `def create(self, a): return self.lifecycle.create(a)` 只会让每加一条命令都要改两个
地方, 而且掩盖了命令归属 —— 看 dispatch 表就知道谁负责什么, 正是想要的效果。

## 两个 mixin
`DoctorMixin` (体检 + session 上下文) / `BoardSourceMixin` (http DataSource) 读的是
`Workspace` 那批属性, 见各自文件顶部的「依赖契约」。
"""
from __future__ import annotations

from skeinlib.admin import Admin
from skeinlib.artifacts import Artifacts
from skeinlib.boardsource import BoardSourceMixin
from skeinlib.doctor import DoctorMixin
from skeinlib.lifecycle import Lifecycle
from skeinlib.query import Query
from skeinlib.scheduling import Scheduler
from skeinlib.workspace import Workspace, _persist_bash_cwd_env, _workspace_lock

# cli.py / serve.py 按名取用 —— 实现已搬进 workspace.py, 这里只保留对外符号
__all__ = ["Skein", "_persist_bash_cwd_env", "_workspace_lock"]


class Skein(Workspace, DoctorMixin, BoardSourceMixin):
    """CLI 门面: 一个工作区 + 五个协作对象 + 体检/看板两个 mixin。"""

    _LOCK_ID_PATH = "/__skein__/id"  # 身份探测端点: 返回本服务的项目标识 (.skein 绝对路径)
    _REV_PATH = "/__skein__/rev"  # 版本探测端点: rev 变则 reload (WS 推送为主, 轮询兜底)
    _LIVE_PATH = "/__skein__/live"  # 热重载 WebSocket: rev 变时 server 推 "reload", 浏览器即刷

    def __init__(self) -> None:
        super().__init__()
        # 装配顺序 = 依赖顺序: lifecycle 要 doctor (本类经 DoctorMixin 提供),
        # scheduler 要 lifecycle。任何一条横向依赖都在这里显式写出来, 不靠 self 隐式共享。
        self.admin = Admin(self)
        self.lifecycle = Lifecycle(self, self.doctor)
        self.scheduler = Scheduler(self, self.lifecycle)
        self.query = Query(self)
        self.artifacts = Artifacts(self)
