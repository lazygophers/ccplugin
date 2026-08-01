"""prd.md 的章节级读写 + planning 结构校验 — 纯函数, 显式传 `tasks_dir`。

prd.md 是 planning 阶段唯一的人写入口 (其余 .md 全是脚本渲染的派生物), 所以这层要能被
`skein prd` 子命令与 confirm/start 的硬门共用。不建类: 唯一的状态就是 tasks 目录, 当参数传。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from skeinlib.errors import SkeinError
from skeinlib.model import (PRD_SECTIONS, PRD_SECTIONS_V4, PRD_SECTIONS_V6, PRD_TODO_SECTIONS)

# ---- prd 章节 CLI (读/追加/覆盖写/勾选) ----
# 公共方法 (带 self): CLI 和网页端后端复用, 禁复制逻辑。章节定位用 `## 章节名` 正则 (同 fmt/_validate_prd)。


def prd_path(tasks_dir: Path, tid: str) -> Path:
    """定位 task 的 prd.md 路径; 不存在 raise SkeinError。"""
    # task 存在性由 _load 守 (调用方先 _load); 此处只查 prd.md
    prd = tasks_dir / tid / "prd.md"
    if not prd.exists():
        raise SkeinError(f"{tid} 无 prd.md — 先 skein create 再操作章节")
    return prd


def _section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    """定位章节 [start, end) 行号区间。start = `## section` 行号+1; end = 下一 `## ` 行号 (末章节=文件尾)。
    章节不存在 raise SkeinError。"""
    start = None
    for i, ln in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if not m:
            continue
        name = m.group(1).strip()
        if start is None:
            if name == section:
                start = i + 1
        elif name:  # 已找到目标章节, 遇到下一 ## 即 end
            return start, i
    if start is None:
        raise SkeinError(f"prd 无「{section}」章节 — 检查章节名 (标准: {PRD_SECTIONS})")
    return start, len(lines)


def section_read(tasks_dir: Path, tid: str, section: str) -> str:
    """读章节正文 (不含 ## 标题行, 含其下到下一 ## 前所有行, trim 首尾空行)。"""
    lines = prd_path(tasks_dir, tid).read_text(encoding="utf-8").split("\n")
    s, e = _section_bounds(lines, section)
    body = "\n".join(lines[s:e]).strip("\n")
    return body


def _normalize(raw: str, section: str) -> list[str]:
    """规范化待写入的行:
    - \\n 字面转真换行 (shell 传 $'A\\nB' 或 "A\\nB" 收到字面 \\n)
    - 目标/验收标准: 裸 `- xxx` → `- [ ] xxx`; 已 checkbox 一律降未勾 `- [ ]` (planning 写路径禁预勾, 勾选权归 check 的 `prd check`); 有序 `N. xxx` → `- [ ] xxx`; 普通非 list 行 → `- [ ] <行>`
    - 边界: 裸文本行 → `- <行>` (补 list marker 不补 checkbox); 已 `- ` 保留; 已 checkbox 保留不动"""
    lines = raw.replace("\\n", "\n").split("\n")
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if section in PRD_TODO_SECTIONS:
            if m := re.match(r"^-\s+\[[ xX]\]\s+(.+)$", s):  # 已 checkbox → 一律降未勾 (planning 写路径禁预勾, 勾选权归 check)
                out.append(f"- [ ] {m.group(1).strip()}")
            elif m := re.match(r"^-\s+(.+)$", s):  # 裸 `- xxx` → 补 checkbox
                out.append(f"- [ ] {m.group(1).strip()}")
            elif m := re.match(r"^\d+[.)]\s+(.+)$", s):  # 有序 → 补 checkbox
                out.append(f"- [ ] {m.group(1).strip()}")
            else:  # 普通行 → 整行作 todo 条目
                out.append(f"- [ ] {s}")
        else:  # 边界
            if re.match(r"^-\s+", s):  # 已 `- `(含 checkbox) 保留
                out.append(s)
            else:
                out.append(f"- {s}")
    return out


def section_add(tasks_dir: Path, tid: str, section: str, text: str) -> list[str]:
    """追加 text 到章节末 (已有保留)。返回写后的章节正文行。"""
    prd = prd_path(tasks_dir, tid)
    lines = prd.read_text(encoding="utf-8").split("\n")
    s, e = _section_bounds(lines, section)
    new_items = _normalize(text, section)
    # 在章节正文末 (跳过尾部空行) 插入新条目
    body = lines[s:e]
    while body and body[-1].strip() == "":
        body.pop()
    body.extend(new_items)
    lines[s:e] = body
    prd.write_text("\n".join(lines), encoding="utf-8")
    return lines[s:e]


def section_write(tasks_dir: Path, tid: str, section: str, text: str) -> list[str]:
    """整章清重建 (仅保留 ## 标题行, 描述提示行 + 旧条目全清, 替换为 text 条目)。返回写后的章节正文行。"""
    prd = prd_path(tasks_dir, tid)
    lines = prd.read_text(encoding="utf-8").split("\n")
    s, e = _section_bounds(lines, section)
    new_items = _normalize(text, section)
    lines[s:e] = new_items
    prd.write_text("\n".join(lines), encoding="utf-8")
    return new_items


def section_check(tasks_dir: Path, tid: str, section: str, match: str, flag: bool) -> int:
    """章节内子串匹配 match 的行, checkbox 切换: flag=True → `- [ ]`→`- [x]`; False → 反。
    返回命中行数; 零命中 raise SkeinError (防 silent fail)。"""
    prd = prd_path(tasks_dir, tid)
    lines = prd.read_text(encoding="utf-8").split("\n")
    s, e = _section_bounds(lines, section)
    hit = 0
    for i in range(s, e):
        ln = lines[i]
        if match not in ln:
            continue
        if flag:
            new = re.sub(r"^-\s+\[ \]\s+", "- [x] ", ln)
        else:
            new = re.sub(r"^-\s+\[[xX]\]\s+", "- [ ] ", ln)
        if new != ln:
            lines[i] = new
            hit += 1
    if hit == 0:
        # 零命中: 可能 match 写错, 或目标行已是目标态 (幂等场景)
        # 区分: 章节内有含 match 的行但已是目标态 → 幂等不算错; 完全无含 match 的行 → 报错
        any_match = any(match in lines[i] for i in range(s, e))
        if not any_match:
            raise SkeinError(f"章节「{section}」无匹配「{match}」的行 — 检查 --list 文本")
        # 已是目标态, 幂等无变化
    else:
        prd.write_text("\n".join(lines), encoding="utf-8")
    return hit


def validate_prd(tasks_dir: Path, tid: str) -> None:
    """start 前只读校验 prd.md 就绪 (不写盘, 区别于 fmt 的规范化写盘):
    (1) prd.md 存在; (2) 六标准章节齐备且顺序为 目标/边界/User Stories/验收标准/Testing Decisions/索引
    (旧四段 目标/边界/验收标准/索引 兼容态只 warning 不阻断 — 存量 task 迁移期保护);
    (3) 无 `- [ ] TODO` 占位 (模板初始态, 说明该节未填实)。结构不通过 raise SkeinError 阻断。"""
    prd = tasks_dir / tid / "prd.md"
    if not prd.exists():
        raise SkeinError(f"{tid} prd 未就绪: 无 prd.md — 先 skein create + 填 prd 再 start")
    lines = prd.read_text().split("\n")
    if not any(re.match(r"^#\s+\S", ln) for ln in lines):
        raise SkeinError(f"{tid} prd 未就绪: 缺一级标题 — 先填 prd 再 start")
    sections = [m.group(1).strip() for ln in lines
                if (m := re.match(r"^##\s+(.+?)\s*$", ln))]
    if sections == PRD_SECTIONS_V4:
        print(f"{tid} prd 章节为旧四段 (兼容态, 建议迁六段模板: {PRD_SECTIONS_V6})", file=sys.stderr)
    elif sections != PRD_SECTIONS_V6:
        raise SkeinError(
            f"{tid} prd 未就绪: 二级章节须为 {PRD_SECTIONS_V6} (齐备且顺序一致), "
            f"实际 {sections} — 先填 prd 再 start")
    # 占位检查: 模板各节初始即 `- [ ] TODO: 填X`, 填实后会被替换为真实内容 → 仍含即判未填。
    # 勾选态一并拒: 把占位勾成 `- [x] TODO` 不是填写, 只是把占位藏起来
    todos = [ln for ln in lines if re.match(r"^- \[[ xX]\]\s+TODO\b", ln)]
    if todos:
        raise SkeinError(
            f"{tid} prd 未就绪: 检出 {len(todos)} 处 `TODO` 占位未填实 (勾成 `- [x]` 不算填) — "
            f"把占位整行替换为真实内容再 start")


def validate_seam(tasks_dir: Path, tid: str) -> None:
    """confirm 前校验 design.md「测试接缝 (seam)」段非占位 (对齐 `/to-spec` 全流程唯一的用户确认点)。
    旧 task (design.md 不存在 / 无此段 / 段落仍是模板占位) 一律只 warning 不阻断 — 存量 task 迁移期保护,
    同 _validate_prd 的 V4 兼容态。接缝质量靠 grill 门与 analyze 兜, 不靠 confirm 硬拦。"""
    design = tasks_dir / tid / "design.md"
    if not design.exists():
        print(f"{tid} design.md 不存在 — 无法校验测试接缝段", file=sys.stderr)
        return
    text = design.read_text()
    m = re.search(r"^##\s+测试接缝\b.*$", text, re.MULTILINE)
    if not m:
        print(
            f"{tid} design.md 缺测试接缝段 (旧 task 兼容态, 建议补齐: 优先复用现有接缝/取最高接缝/越少越好) — {design}",
            file=sys.stderr)
        return
    nxt = re.search(r"^##\s+", text[m.end():], re.MULTILINE)
    body = text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]
    if re.search(r"-\s*\[[ xX]\]\s*TODO\b", body):
        print(
            f"{tid} design.md 测试接缝段仍是占位未填 (旧 task 兼容态, 建议先填实测试接缝) — {design}",
            file=sys.stderr)


def review_summary(tasks_dir: Path, tid: str, t: dict[str, Any]) -> str:
    """给用户人眼审核用的 PRD 摘要 — 纯函数, 吃 task dict 返字符串。

    只摘**够判断该不该放行**的东西: 目标 / 验收标准 / 边界三章正文 + subtask 拆解 + 工时。
    刻意不摘全文: 全文用户可以自己开 prd.md 看, 终端里滚三屏反而没人读。
    """
    def sec(name: str) -> list[str]:
        try:
            raw = section_read(tasks_dir, tid, name)
        except SkeinError:
            return []
        return [ln.strip() for ln in raw.splitlines() if ln.strip()]

    subs = t.get("subtasks") or []
    sub_est = sum(float(s.get("estimate") or 0) for s in subs)
    out = [f"── {tid}  {t.get('name') or tid} ──", f"   {t.get('desc') or ''}", ""]
    for name in ("目标", "边界", "验收标准"):
        items = sec(name)
        out.append(f"## {name} ({len(items)} 条)")
        out += [f"   {ln}" for ln in items] or ["   (空)"]
        out.append("")
    out.append(f"## subtask ({len(subs)} 个, Σ工时 {sub_est:g}h)")
    for s in subs:
        dep = f" ← {','.join(s.get('depends_on') or [])}" if s.get("depends_on") else ""
        out.append(f"   [{s['sid']}] {s.get('name', '')} ({s.get('estimate') or '?'}h){dep}")
    out.append("")
    out.append(f"## 预计工时  task {t.get('estimate')}h  (Σsubtask {sub_est:g}h)")
    return "\n".join(out)
