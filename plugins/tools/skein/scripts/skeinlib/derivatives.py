"""衍生物单一登记处 —— `.skein/.gitignore` 由此导出, 不再另维护清单。

**衍生物** = 有重建路径的可重建产物 (忽略它只是让仓库干净); 反之为真值, 绝不可入此表
(判据见 `.skein/task/skein-gitignore/design.md`)。

`rebuild` 字段记录"由哪条代码路径/命令能从真值重新产出它", 人读为主, 供未来守卫
(反查新增写盘点是否已登记) 使用 —— 本次改造只搭数据结构, 不实现守卫本身。
"""
from __future__ import annotations

from typing import NamedTuple


class Derivative(NamedTuple):
    pattern: str  # .gitignore 匹配模式 (支持 glob, 如 "spec/*/index.md")
    rebuild: str  # 重建路径: 产出它的代码位置或命令


DERIVATIVES: list[Derivative] = [
    Derivative("task.md", "store.py _write_board (由 task.json 重渲染)"),
    Derivative("vision.md", "store.py _write_vision"),
    Derivative("*.lock", "workspace.py 加锁产物"),
    Derivative("spec/.archive/", "spec/maintain.py 完全重构可逆归档转储"),
    Derivative("spec/.pending-fix", "hooks/stopcheck.py 标记"),
    Derivative("spec/.audit-log", "spec/maintain.py 审计日志"),
    Derivative("spec/.recall.db", "spec/index.py FTS 索引"),
    Derivative("trash/", "lifecycle.py 软删转储"),
    Derivative("spec/index.md", "spec/index.py _reindex_top (总索引)"),
    Derivative("spec/*/index.md", "spec/index.py _reindex_layer (各 namespace 索引)"),
    Derivative("spec/*/backlinks.md", "spec/index.py _rebuild_backlinks_md (正反链表)"),
    Derivative(".edit-tally", "hooks/postwrite.py cmd_flow_gate 计数标记"),
    Derivative(".edit-tally.warned", "hooks/postwrite.py cmd_flow_gate 已提醒标记"),
    Derivative("index.html", "assets/nextjs `pnpm build` (Next.js static export → assets/dist/)"),
    Derivative(".priority-migration-backup/", "priority.py migrate_priority_values 迁移前快照, 供回滚"),
    Derivative(".ready-migration-backup/", "readystate.py migrate_ready_status 迁移前快照, 供回滚"),
    Derivative("serve.log", "boardsource.py _run_server serve 崩溃日志"),
]


def gi_entries() -> list[str]:
    """导出 `.skein/.gitignore` 条目 (供 admin.py init 生成/补缺, 单一来源)。"""
    return [d.pattern for d in DERIVATIVES]
