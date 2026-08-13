"""task 优先级: 四档校验 + 存量 0-10 数字一次性迁移。

## 校验归这里, 不归 lifecycle
`validate_priority` 被 create 与未来的改优先级命令共用, 放独立文件免两处各抄一份合法值列表
(错误信息里那四个值必须跟 `PRIORITIES` 是同一个 tuple, 不是分别硬编码的两份字符串)。

## 迁移: 先备份原文件, 再原地改, 幂等
`migrate_priority_values` 只认 `priority` 是数字的 task.json (字符串值一律当已迁移跳过,
缺字段的也跳过)。改之前把该文件原样拷进 `.skein/.priority-migration-backup/<时间戳>/`,
备份目录结构照抄源相对路径 —— 回滚 = 把备份目录里的文件拷回原位, 不需要额外工具。
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path
from typing import Any, Optional

from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import PRIORITIES, PRIORITY_DEFAULT


def validate_priority(raw: Optional[str]) -> str:
    """None → 默认档 (中/normal); 非四档合法值 → 拒, 错误信息列出全部四个合法值。"""
    if raw is None:
        return PRIORITY_DEFAULT
    if raw not in PRIORITIES:
        raise SkeinError(f"非法优先级: {raw!r} — 仅允许: {', '.join(PRIORITIES)}")
    return raw


def priority_from_legacy(n: int) -> str:
    """存量 0-10 数字 → 四档, 映射表见 design.md: 8-10 紧急/6-7 高/4-5 中(默认 5 落这)/0-3 低。"""
    if n >= 8:
        return "urgent"
    if n >= 6:
        return "high"
    if n >= 4:
        return "normal"
    return "low"


def migrate_priority_values(root: Path, tasks_dir: Path, archive_dir: Path) -> dict[str, Any]:
    """迁移 tasks_dir/<id>/task.json (未归档) + archive_dir/*/*/<id>/task.json (已归档)。
    返回 {"migrated": [相对 root 的路径...], "backup_dir": 相对 root 路径 | None (无改动则 None)}。"""
    targets: list[Path] = []
    if tasks_dir.exists():
        targets += [p for p in tasks_dir.glob("*/task.json") if p.parent.name != "archive"]
    if archive_dir.exists():
        targets += list(archive_dir.glob("*/*/*/task.json"))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = root / ".skein" / ".priority-migration-backup" / stamp
    migrated: list[str] = []
    for f in sorted(targets):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        p = data.get("priority")
        if isinstance(p, bool) or not isinstance(p, (int, float)):
            continue  # 已是字符串 (已迁移) 或字段缺失 → 幂等跳过
        dst = backup_dir / f.relative_to(root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        data["priority"] = priority_from_legacy(int(p))
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        migrated.append(str(f.relative_to(root)))
    return {"migrated": migrated,
            "backup_dir": str(backup_dir.relative_to(root)) if migrated else None}
