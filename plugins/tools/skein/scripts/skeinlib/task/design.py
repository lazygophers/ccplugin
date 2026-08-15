"""design.md 测试接缝段读写 — 纯函数, 显式传 `tasks_dir`。

需求信息 (描述/边界/验收/工时) 已并入 task.json 的 TaskSpec 字段, prd.md 不复存在;
design.md 只剩架构散文 + 测试接缝段 (confirm 硬门), 本模块只管接缝段。
"""
from __future__ import annotations

import re
from pathlib import Path

from skeinlib.utils.errors import SkeinError

_SEAM_HEADING = re.compile(r"^##\s+测试接缝\b.*$")


def _seam_bounds(tasks_dir: Path, tid: str) -> tuple[Path, list[str], int, int]:
	"""定位 design.md「## 测试接缝」段 → (路径, 全文行, 正文 start, 正文 end)。"""
	design = tasks_dir / tid / "design.md"
	if not design.exists():
		raise SkeinError(f"{tid} design.md 不存在 — 无法定位测试接缝段")
	lines = design.read_text(encoding="utf-8").split("\n")
	head = next((i for i, ln in enumerate(lines) if _SEAM_HEADING.match(ln)), None)
	if head is None:
		raise SkeinError(f"{tid} design.md 缺测试接缝段 — {design}")
	end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
	return design, lines, head + 1, end


def seam_read(tasks_dir: Path, tid: str) -> str:
	"""读 design.md 测试接缝段正文。"""
	_, lines, s, e = _seam_bounds(tasks_dir, tid)
	return "\n".join(lines[s:e]).strip("\n")


def seam_write(tasks_dir: Path, tid: str, text: str) -> list[str]:
	"""整段清重建 design.md 测试接缝正文。

	confirm 拿测试接缝当硬门, 但此前只有手改文件一条路 —— 有校验没写入口, 每个 task 都得
	Read+Edit 一趟。这里补上, 让 planning 全程走 CLI。
	"""
	design, lines, s, e = _seam_bounds(tasks_dir, tid)
	items = [f"- {ln.strip().lstrip('-').strip()}"
	         for ln in text.replace("\\n", "\n").split("\n") if ln.strip()]
	if not items:
		raise SkeinError("--list 为空 — 至少写一条测试接缝")
	lines[s:e] = ["", *items, ""]
	design.write_text("\n".join(lines), encoding="utf-8")
	return items


def validate_seam(tasks_dir: Path, tid: str) -> None:
	"""confirm 前校验 design.md「测试接缝 (seam)」段非占位。"""
	design, lines, s, e = _seam_bounds(tasks_dir, tid)
	body = "\n".join(lines[s:e])
	if re.search(r"-\s*\[[ xX]\]\s*TODO\b", body):
		raise SkeinError(
			f"{tid} design.md 测试接缝段仍是占位未填 — "
			f"`skein design seam {tid} --list '<接缝1>\\n<接缝2>'` 或直接编辑 {design}")
