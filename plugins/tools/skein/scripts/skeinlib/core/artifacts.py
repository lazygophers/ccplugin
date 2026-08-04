"""`Artifacts` — task 工件读写: prd.md 章节、prd 规范化、契约清单。

## 为什么不让 AI 直接 Edit prd.md
prd 有固定七章结构 (`PRD_SECTIONS_V6`), 而 `confirm` 的硬门按章节校验。裸 Edit 很容易把结构
改坏, 于是 confirm 报一个和实际操作对不上的错。走 `prd read/write/add/check` 这组命令, 章节
边界由 `skeinlib.task.prd` 统一维护, 结构永远合法。

`fmt` 是幂等规范化 (补 `- [ ]`、校验章节)，PostToolUse hook 在 prd.md 写后自动跑它。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.core.workspace import Workspace

from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import PRD_SECTIONS_V6, PRD_TODO_SECTIONS, PRD_TYPE_ALIAS
from skeinlib.task.prd import section_add, section_check, section_read, section_write

import re


class Artifacts:
    """prd.md / 契约等 task 工件的读写。"""

    def __init__(self, ws: "Workspace") -> None:
        self.ws = ws

    def fmt(self, a: argparse.Namespace) -> dict[str, Any]:
        # 规范化 .skein/task/<id>/prd.md: 各章节内一级 `- ` list 项补 `- [ ]` todo (已勾选态保留),
        # 校验标准章节齐备且顺序正确, 不规范报错非零退出;
        # 仅内容变化才写 (天然幂等 + 防 hook 循环)。
        tid = a.id.strip()
        prd = self.ws.tasks / tid / "prd.md"
        if not prd.exists():
            raise SkeinError(f"prd 不存在: {prd}")
        orig = prd.read_text()
        lines = orig.split("\n")
        # 校验: 至少一个一级标题 (# ...) + 标准章节齐备且顺序正确
        if not any(re.match(r"^#\s+\S", ln) for ln in lines):
            raise SkeinError(f"prd 不规范: 缺一级标题 (# ...) — {prd}")
        sections = [m.group(1).strip() for ln in lines
                    if (m := re.match(r"^##\s+(.+?)\s*$", ln))]
        if sections != PRD_SECTIONS_V6:
            raise SkeinError(
                f"prd 不规范: 二级章节须为 {PRD_SECTIONS_V6} (齐备且顺序一致), "
                f"实际 {sections} — {prd}")
        # 规范化 (行首非缩进; 缩进子 list / 已勾选态不动):
        #   (a) 所有章节: `- ` 且非 checkbox → 补 `- [ ] `
        #   (b) 仅 PRD_TODO_SECTIONS (目标/验收标准/Testing Decisions) 章节: 有序列表 `N. ` → `- [ ] ` (逐条可勾选)
        #       User Stories 不在此列 —— 其 `1. As a ...` 编号格式是 to-spec 固定格式, 不折成 checkbox
        todo_sections = PRD_TODO_SECTIONS
        out: list[str] = []
        changed, cur = 0, None
        for ln in lines:
            if h := re.match(r"^##\s+(.+?)\s*$", ln):
                cur = h.group(1).strip()
                out.append(ln)
                continue
            if m := re.match(r"^- (?!\[[ xX]\] )(.*)$", ln):
                out.append(f"- [ ] {m.group(1)}")
                changed += 1
            elif cur in todo_sections and (mo := re.match(r"^\d+\.\s+(.*)$", ln)):
                out.append(f"- [ ] {mo.group(1)}")
                changed += 1
            else:
                out.append(ln)
        new = "\n".join(out)
        if new == orig:
            return {"id": tid, "formatted": False, "changes": 0}
        prd.write_text(new)
        return {"id": tid, "formatted": True, "changes": changed}

    def prd(self, a: argparse.Namespace) -> dict[str, Any]:
        """prd 章节 CLI 入口: read/write/add/check/uncheck <id> --type <章节> [--list TEXT]。
        task 必须存在 (经 _load 守); --type 经 PRD_TYPE_ALIAS 归一到中文章节名。"""
        tid = a.id.strip()
        self.ws.store.load(tid)  # task 存在性校验 (不存在 raise SkeinError)
        raw_type = a.type
        if raw_type not in PRD_TYPE_ALIAS:
            raise SkeinError(f"非法 --type: {raw_type!r} — 合法值: {list(PRD_TYPE_ALIAS.keys())}")
        section = PRD_TYPE_ALIAS[raw_type]
        act = a.action
        if act == "read":
            body = section_read(self.ws.tasks, tid, section)
            return {"id": tid, "section": section, "body": body}
        if not a.list:
            raise SkeinError(f"{act} 需要 --list (文本内容, \\n 多行)")
        if act == "add":
            section_add(self.ws.tasks, tid, section, a.list)
            return {"id": tid, "section": section, "action": "add",
                    "lines": len(a.list.split(chr(10)))}
        elif act == "write":
            section_write(self.ws.tasks, tid, section, a.list)
            return {"id": tid, "section": section, "action": "write"}
        elif act == "check":
            n = section_check(self.ws.tasks, tid, section, a.list, flag=True)
            return {"id": tid, "section": section, "action": "check", "matched": n}
        elif act == "uncheck":
            n = section_check(self.ws.tasks, tid, section, a.list, flag=False)
            return {"id": tid, "section": section, "action": "uncheck", "matched": n}
        else:
            raise SkeinError(f"未知 prd 动作: {act}")

    def contract(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.id)
        t.setdefault("contracts", [])
        if a.add:
            t["contracts"].append(a.add)
            self.ws.store.save(t)
            return {"id": a.id, "action": "add", "total": len(t["contracts"])}
        return {"id": a.id, "contracts": t["contracts"]}
