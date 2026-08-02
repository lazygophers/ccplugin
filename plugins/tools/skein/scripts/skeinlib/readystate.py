"""存量中文 status 一次性迁移。

## 为什么旧「就绪」迁到 pending
s3 把 confirm 直接吸收了 start (人审门 = 一步到位, 见 design.md 状态机)。旧「就绪」= 已
confirm、等 start 触发。若迁到 active 等价于替这些存量 task 自动重新走一次 confirm,
副作用是**批量建 worktree** —— 迁移命令不该替用户做这么大的决定。迁到 pending 退回未
confirm 态最安全: 无副作用、用户看到后自己决定要不要 `confirm`, 等于把这些 task 当成
"当初的人审门其实还没真正跑过" 处理, 代价是需要用户手动重新 confirm 一次。

## 迁移: 先备份原文件, 再原地改, 幂等
只认 task/subtask `status` 是旧中文展示值的 task.json (英文值一律跳过, 已迁移的自然也跳过)。
改之前把该文件原样拷进 `.skein/.ready-migration-backup/<时间戳>/`, 结构照抄 `priority.py` 的备份范式。
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path
from typing import Any

from skeinlib.task.model import SubtaskStatus, TaskStatus

_LEGACY_TASK_STATUS = {
    "待处理": TaskStatus.PENDING,
    "调研中": TaskStatus.RESEARCH,
    "就绪": TaskStatus.PENDING,
    "进行中": TaskStatus.ACTIVE,
    "检查中": TaskStatus.CHECK,
    "收尾中": TaskStatus.FINISHING,
    "已完成": TaskStatus.DONE,
}
_LEGACY_SUBTASK_STATUS = {
    "待处理": SubtaskStatus.PENDING,
    "运行中": SubtaskStatus.RUNNING,
    "已完成": SubtaskStatus.DONE,
    "失败": SubtaskStatus.FAILED,
}


def migrate_ready_status(root: Path, tasks_dir: Path, archive_dir: Path) -> dict[str, Any]:
    """迁移 tasks_dir/<id>/task.json (未归档) + archive_dir/*/*/<id>/task.json (已归档)。
    返回 {"migrated": [相对 root 的路径...], "backup_dir": 相对 root 路径 | None (无改动则 None)}。"""
    targets: list[Path] = []
    if tasks_dir.exists():
        targets += [p for p in tasks_dir.glob("*/task.json") if p.parent.name != "archive"]
    if archive_dir.exists():
        targets += list(archive_dir.glob("*/*/*/task.json"))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = root / ".skein" / ".ready-migration-backup" / stamp
    migrated: list[str] = []
    for f in sorted(targets):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        changed = False
        status = data.get("status")
        if status in _LEGACY_TASK_STATUS:
            data["status"] = _LEGACY_TASK_STATUS[status]
            changed = True
        for subtask in data.get("subtasks", []):
            subtask_status = subtask.get("status")
            if subtask_status in _LEGACY_SUBTASK_STATUS:
                subtask["status"] = _LEGACY_SUBTASK_STATUS[subtask_status]
                changed = True
        if not changed:
            continue  # 已迁移或本就不是旧中文 status → 幂等跳过
        dst = backup_dir / f.relative_to(root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        migrated.append(str(f.relative_to(root)))
    return {"migrated": migrated,
            "backup_dir": str(backup_dir.relative_to(root)) if migrated else None}
