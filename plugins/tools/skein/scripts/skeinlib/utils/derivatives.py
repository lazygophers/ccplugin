"""衍生物单一登记处 —— `.skein/.gitignore` 由此导出, 不再另维护清单。

**衍生物** = 有重建路径的可重建产物 (忽略它只是让仓库干净); 反之为真值, 绝不可入此表
(判据见 `.skein/task/skein-gitignore/design.md`)。

`rebuild` 字段记录"由哪条代码路径/命令能从真值重新产出它", 人读为主, 供未来守卫
(反查新增写盘点是否已登记) 使用 —— 本次改造只搭数据结构, 不实现守卫本身。
"""
from __future__ import annotations

from pathlib import Path
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
    Derivative(".edit-tally", "hooks/flow_gate.py cmd_flow_gate 计数标记"),
    Derivative(".edit-tally.warned", "hooks/flow_gate.py cmd_flow_gate 已提醒标记"),
    Derivative(".dispatch.warned", "hooks/post_tool_use.py _dispatch_reminder 已提醒标记"),
    Derivative("index.html", "assets/nextjs `pnpm build` (Next.js static export → assets/dist/)"),
    Derivative(".priority-migration-backup/", "priority.py migrate_priority_values 迁移前快照, 供回滚"),
    Derivative(".ready-migration-backup/", "readystate.py migrate_ready_status 迁移前快照, 供回滚"),
    Derivative("serve.log", "boardsource.py _run_server serve 崩溃日志"),
]


def gi_entries() -> list[str]:
    """导出 `.skein/.gitignore` 条目 (供 admin.py init 生成/补缺, 单一来源)。"""
    return [d.pattern for d in DERIVATIVES]


def ensure_gitignore(skein_dir: Path) -> None:
    """幂等保证 `.skein/.gitignore` 覆盖全部登记处条目。

    init 之外的代码路径 (如 hooks/flow_gate.py 写 `.edit-tally`) 也会产出衍生物, 老工作区
    的 `.gitignore` 可能是更早版本 init 写的、缺新条目 → 衍生物会漏网进版本库。本函数在任何
    写衍生物的代码路径里调一次即可自愈 (幂等: 不破坏用户手写条目, 不重复已有)。

    与 admin.py init 内联逻辑等价, 提取出来做单一来源。
    """
    gi = skein_dir / ".gitignore"
    entries = gi_entries()
    if not gi.exists():
        skein_dir.mkdir(parents=True, exist_ok=True)
        gi.write_text("# skein 自动渲染/衍生, 不入库\n" + "\n".join(entries) + "\n", encoding="utf-8")
        return
    lines = gi.read_text(encoding="utf-8").splitlines()
    have = {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}
    missing = [e for e in entries if e not in have]
    if missing:
        with gi.open("a", encoding="utf-8") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write("# skein 衍生/临时文件 (自动补缺)\n")
            fh.write("\n".join(missing) + "\n")
