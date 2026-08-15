"""`Artifacts` — task 工件读写。

需求信息 (描述/边界/验收/工时) 已并入 task.json 的 TaskSpec 字段, prd.md 与其章节 CLI 不复存在。
这层只剩 design.md 测试接缝段: confirm 拿它当硬门校验, 所以给它脚本写入口,
其余 design.md 内容是自由散文 (架构/取舍), 不做章节化 CLI。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from skeinlib.core.workspace import Workspace

from skeinlib.utils.errors import SkeinError
from skeinlib.task.design import seam_read, seam_write


class Artifacts:
	"""design.md 测试接缝段的读写。"""

	def __init__(self, ws: "Workspace") -> None:
		self.ws = ws

	def design(self, a: argparse.Namespace) -> dict[str, Any]:
		"""design.md 测试接缝段 CLI 入口: seam/read <id> [--list TEXT]。"""
		tid = a.id.strip()
		self.ws.store.load(tid)  # task 存在性校验
		if a.action == "read":
			return {"id": tid, "section": "测试接缝", "body": seam_read(self.ws.tasks, tid)}
		if a.action != "seam":
			raise SkeinError(f"未知 design 动作: {a.action} — 仅 seam/read")
		if not a.list:
			raise SkeinError("seam 需要 --list (文本内容, \\n 多行)")
		items = seam_write(self.ws.tasks, tid, a.list)
		return {"id": tid, "section": "测试接缝", "action": "write", "items": len(items)}
