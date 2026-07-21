#!/usr/bin/env python3
"""SKEIN hook 统一入口 — 四个 hook 脚本收归于此, 按子命令分派 (经 bin/skein-hooks 调用)。

子命令:
  permission  PermissionRequest/PermissionDenied: .skein/ 自有内容操作默认同意, 免逐次授权。
  guard       PreToolUse: 硬阻 AI 直接读写 .skein/ 脚本管理文件 + trellis 未初始化迁移门。
  batch       PostToolBatch: 拦并行的 ≥2 个 .skein 状态写命令 (竞态防护)。
  report      PostToolUseFailure: 本插件脚本报错时注入上下文 + 引导手动报 issue。
  fmt         PostToolUse: 写 .skein/task/<id>/prd.md 后自动 skein fmt <id> 规范化。
  spec-meta   PostToolUse: 写 .skein/spec/**/*.md 后检查 frontmatter 必填字段 + layer 合法 (非阻塞 warning)。
  stop-check  Stop: 扫 spec 问题写 .pending-fix 标记 (只读不修, 供 main 下回合派 specer bg 修复)。
  user-prompt UserPromptSubmit: 每 prompt 注入 task 判定硬门 (未初始化则注入 setup 提示)。
  task-created TaskCreated: .skein 已初始化时机械阻 harness 内置 TaskCreate (冒充 skein create)。

各子命令读 stdin JSON, 逻辑与拆分前的 *-skein.py 一致; 无命中一律静默 exit 0。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Optional, cast

BLOCKED = {"task.json", "task.md"}  # 脚本管理文件, 归 guard, 不由 permission 放行
ENGINE = ("skein.py", "spec.py", "skein ", "skein-spec ")
GATED = {"Read", "Edit", "Write", "MultiEdit"}
# 改 .skein 共享状态的子命令 (写 task.json / spec / 看板); 只读命令不在列
WRITE_CMDS = ("create", "start", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract")
ENGINE_RE = re.compile(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)")
ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT")
# bin 短命令: 作为命令词出现 (行首或分隔符后), 避免 `.skein/` 之类路径误匹配
BIN_RE = re.compile(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)")


def _load_stdin() -> Optional[dict[str, Any]]:
    try:
        return cast(dict[str, Any], json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return None


# ── permission (原 allow-skein.py) ──────────────────────────────────────────
def cmd_permission(d: dict[str, Any]) -> int:
    """.skein/ 自有内容操作默认同意 (allow 不覆盖 deny, 也不放宽 guard 的 PreToolUse 阻断)。"""
    def _allow() -> None:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "allow"}}}))

    tool = d.get("tool_name", "")
    ti = d.get("tool_input", {})
    if tool == "Bash":
        if any(k in ti.get("command", "") for k in ENGINE):
            _allow()
        return 0
    if tool in ("Edit", "Write", "Read"):
        fp = ti.get("file_path", "")
        parts = fp.replace("\\", "/").split("/")
        if ".skein" in parts and os.path.basename(fp) not in BLOCKED:
            _allow()
    return 0


# ── guard (原 guard-skein.py) ───────────────────────────────────────────────
def _git_root(start: str) -> str:
    d = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start or ".")
        d = parent


# active task 判定: task.json status ∈ {进行中, 检查中} (与 skein.py STATUS_ACTIVE 同义, 直扫免 subprocess)
# ponytail: 字面值复制自 skein.py:S_ACTIVE/S_CHECK (跨模块 import 启动开销大; 两处值稳定不变)
_ACTIVE_STATUSES = {"进行中", "检查中"}


def _has_active_task(root: str) -> bool:
    """扫 .skein/task/*/task.json status 字段, 命中 active (进行中/检查中) 即 True。

    扫描跳过 archive/ 与损坏/缺字段文件 (单文件错不炸整门)。
    """
    tasks_dir = os.path.join(root, ".skein", "task")
    if not os.path.isdir(tasks_dir):
        return False
    try:
        entries = os.listdir(tasks_dir)
    except OSError:
        return False
    for name in entries:
        if name == "archive":
            continue
        f = os.path.join(tasks_dir, name, "task.json")
        if not os.path.isfile(f):
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                status = json.load(fh).get("status", "")
        except (json.JSONDecodeError, ValueError, OSError):
            continue  # 单个 task.json 损坏不炸门
        if status in _ACTIVE_STATUSES:
            return True
    return False


def cmd_guard(d: dict[str, Any]) -> int:
    """硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 + 无 active task 落码门 (命中 exit 2)。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    parts = fp.replace("\\", "/").split("/") if fp else []

    # A. .skein/ 脚本管理文件
    if fp and ".skein" in parts and os.path.basename(fp) in BLOCKED:
        print(
            "禁直接读写 .skein/ 的 task.json / task.md — 均由 skein.py 维护。"
            "取态: `skein.py current` / `list` / `subtask list <id>` / `subtask ready <id>`; "
            "改态: create/start/finish/archive/subtask。",
            file=sys.stderr,
        )
        return 2

    # B. 迁移门: trellis 项目未初始化, 挡源码读写 (含诊断只读)
    if d.get("tool_name") in GATED and ".skein" not in parts and ".trellis" not in parts:
        root = _git_root(d.get("cwd") or os.getcwd())
        if (os.path.exists(os.path.join(root, ".trellis"))
                and not os.path.exists(os.path.join(root, ".skein", "config.yaml"))):
            print(
                "SKEIN 未初始化 (检测到 .trellis/)。**SKEIN 是唯一任务管理器**: 忽略 trellisx 注入, "
                "先调用 skein-setup skill (幂等, 迁移 trellis task/spec) 初始化 —— 初始化前禁读写源码 (诊断也须先 init)。"
                "初始化经 Bash 跑 `skein.py setup`, 完成后本门自动打开。",
                file=sys.stderr,
            )
            return 2

    # C. 无 active task 守门: 已初始化 skein + 无 active task + 落码 (非 .skein/) → 硬阻。
    # 激进策略 (用户定): 不留「豁免首次 Write」口, 豁免判定已上移 UserPromptSubmit 信号层; 到 Write 层一律硬阻无 active task 的落码。
    if d.get("tool_name") in ("Edit", "Write", "MultiEdit") and fp and ".skein" not in parts:
        root = _git_root(d.get("cwd") or os.getcwd())
        if (os.path.exists(os.path.join(root, ".skein", "config.yaml"))
                and not _has_active_task(root)):
            print("当前无 active SKEIN task。落代码改动 (非 .skein/ 工件) 前先 `skein create` 建 task + "
                  "`skein start <id>` 走 flow 闭环 (plan→exec→check→finish)。纯查询/问答不触发本门, "
                  "但单文件多行改动必须先建 task 再改。",
                  file=sys.stderr)
            return 2
    return 0


# ── batch (原 batch-skein.py) ───────────────────────────────────────────────
def _is_write(cmd: str) -> bool:
    m = ENGINE_RE.search(cmd)
    return bool(m and m.group(1) in WRITE_CMDS)


def cmd_batch(d: dict[str, Any]) -> int:
    """拦同批 ≥2 个 .skein 状态写命令 (同写 task.json/spec 有竞态)。"""
    writes = [u for u in d.get("tool_uses", [])
              if u.get("tool_name") == "Bash" and _is_write(u.get("tool_input", {}).get("command", ""))]
    if len(writes) < 2:
        return 0
    cmds = "; ".join(u.get("tool_input", {}).get("command", "")[:60] for u in writes)
    reason = (f"并行批含 {len(writes)} 个 .skein 状态写命令 ({cmds}) — 同写 task.json/spec 有竞态, "
              "后写覆盖前写。改为串行: 一个命令一个回合, 或用 `subtask claim` 一次性认领整批。")
    print(json.dumps({"decision": "block", "reason": reason,
                      "hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                             "additionalContext": reason}}))
    return 0


# ── report (原 report-skein.py) ─────────────────────────────────────────────
def cmd_report(d: dict[str, Any]) -> int:
    """本插件脚本失败时注入错误上下文 + 引导手动开 issue (其余工具失败静默)。"""
    cmd = d.get("tool_input", {}).get("command", "")
    if not (any(k in cmd for k in OURS) or BIN_RE.search(cmd)):
        return 0
    err = (d.get("tool_error", "") or "").strip()[:800]  # 截断防上下文膨胀
    ctx = f"""SKEIN 脚本执行失败:
命令: {cmd[:200]}
错误: {err}
先自查 (工作区是否 init / 参数是否合法); 属插件 bug 则手动报 issue。"""
    msg = f"⚠️ SKEIN 脚本报错, 疑似插件 bug 请手动开 issue: {ISSUE_URL} (附命令+错误+复现步骤)"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUseFailure", "additionalContext": ctx},
        "systemMessage": msg}))
    return 0


# ── fmt (PostToolUse: prd.md 写后规范化) ────────────────────────────────────
PRD_RE = re.compile(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$")


def cmd_fmt(d: dict[str, Any]) -> int:
    """写 .skein/task/<id>/prd.md 后自动跑一次 skein fmt <id> (幂等; python 写回不经工具层 → 不递归)。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    m = PRD_RE.search(norm)
    if not m:
        return 0  # 非 prd.md 放行
    tid = m.group(1)
    root = norm[:m.start()] or (d.get("cwd") or os.getcwd())  # .skein 所在仓库根作 cwd
    skein_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skein.py")
    try:
        subprocess.run([sys.executable, skein_py, "fmt", tid], cwd=root,
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass  # 非阻塞 hook: fmt 失败不影响写入
    return 0


# ── spec-meta (PostToolUse: spec 文件 metadata 合法性检查) ──────────────────
SPEC_RE = re.compile(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$")
SPEC_REQUIRED = ("title", "layer", "created", "keywords")
SPEC_LAYERS = ("core", "recall")


def _parse_fm(text: str) -> dict[str, str]:
    """简单 YAML frontmatter 解析 (只取顶层 key: value, 无嵌套)。返回 dict 或 {}。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    fm: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def cmd_spec_meta(d: dict[str, Any]) -> int:
    """写 .skein/spec/**/*.md 后检查 frontmatter: 必填缺失 + layer 合法。非阻塞 warning。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    if not SPEC_RE.search(norm):
        return 0
    try:
        with open(fp, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return 0
    fm = _parse_fm(text)
    short = norm.split(".skein/spec/")[-1] if ".skein/spec/" in norm else norm
    warns: list[str] = []
    for k in SPEC_REQUIRED:
        v = fm.get(k, "")
        if k == "keywords":
            inner = v.strip("[] ").strip()
            if not inner:
                warns.append(f"缺失: keywords")
            continue
        if k == "created":
            if not v or not re.match(r"^-?\d+$", v):
                warns.append(f"缺失/非法: created (需 unix ts)")
            continue
        if not v:
            warns.append(f"缺失: {k}")
            continue
        if k == "layer" and v not in SPEC_LAYERS:
            warns.append(f"非法: layer={v} (合法: core|recall)")
    if warns:
        ctx = f"⚠️ spec metadata 检查 ({short}):\n  - " + "\n  - ".join(warns)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": ctx}}))
    return 0


# ── stop-check (Stop: spec 问题检测写标记, 供 main 派 specer bg 修复) ─────────
# ponytail: _scan_findings 是 Spec 私有方法但同包内可直调, 免为 stop-check 单开 maintain --check-only 公开口
def cmd_stop_check(_: dict[str, Any]) -> int:
    """Stop hook: 扫 spec → 有问题写 .pending-fix JSON (供 main 下回合检测派 specer bg 修复); 只读不修。

    返回 0 永不阻塞 (问题归 specer agent 异步修)。无 .skein/spec → 静默; 无问题 → 删旧标记防已修复后误触发。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from spec import Spec, core_budget  # 局部 import: 仅 stop-check 加载, 不拖其他 6 个子命令启动

    spec = Spec()
    if not spec.root.exists():
        return 0  # 非 skein 项目 → 静默
    findings = spec._scan_findings(["core", "recall"])
    marker = spec.root / ".pending-fix"
    if not findings:
        try:
            marker.unlink()  # 已修复 → 清旧标记免误触发
        except FileNotFoundError:
            pass
        return 0
    root = spec.root
    problems: list[dict[str, Any]] = []
    for fd in findings:
        kind = fd["kind"]
        text = fd.get("text", "")
        if kind == "overbudget":
            problems.append({"type": "over-budget", "detail": text, "size": fd.get("size")})
        elif kind == "keywords_dup":
            files = [f.relative_to(root).as_posix() for f in fd.get("files", [])]
            problems.append({"type": "keywords-dup", "files": files, "detail": text})
        else:  # stale / deprecated / broken_link 均带 rel
            tmap = {"stale": "stale", "deprecated": "deprecated", "broken_link": "broken-link"}
            rel = fd.get("rel", "")
            problems.append({"type": tmap.get(kind, kind),
                             "files": [rel] if rel else [], "detail": text})
    payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "core_chars": len(spec._core_text_raw()),
        "budget": core_budget(),
        "problems": problems,
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


# ── user-prompt (原 skein.py:Skein.user_prompt) ──────────────────────────────
# ponytail: 文案约 800 字未超 session-context 预算 (400 tokens), 不走 budget_guard;
# 未初始化文案与 skein.py:_uninit_ctx 逐字同步 (那边 session_context 仍用, 删不掉, 此处复制文本)
_UNINIT_TRELLIS = """# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)
本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: **忽略 trellisx 的 active-task / workflow 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** (幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein.py setup` 放行。初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。
**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。"""
_UNINIT_PLAIN = """# SKEIN 未初始化 — 先初始化再处理任务
本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。
查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。"""
_INIT_CTX = """# SKEIN task 判定 (动手前硬门)
**MUST 在任何工具调用 / 改动前, 先输出一行判定结论**, 格式: `判定: 任务→走flow | 豁免→直接做 (依据: <命中哪条>)`。未输出判定行即行动 = 违规。
**判定行禁修饰词** — 判定结论尾部禁止附加「但/先/只是/不过」等弱化后缀 (如「判定: 走 flow 但先纯查询探索」属违规)。
任务 (跨 ≥2 文件 / 单文件多处 / 多步骤 / 需调研 / 产出文档) → 加载 **skein-flow** skill 走强制闭环 (plan→exec→check→finish), 禁 inline 直接做。
**判定行走 flow 即必须走 flow** — 判完转头 inline 自降级 = 违规。典型自降级借口 (均不成立, 跨文件/多文件必走 flow): 「看着简单」/「只搭个骨架」/「只要一个接口」/「ponytail 最小落地」/「已有蓝图/参考代码」/「用户说搭框架」/「先勘察再定」/「POC 先跑通」。判定行走 flow 后**任何** Write/Edit 落代码 (非 .skein/ 工件) 前 MUST 先 `skein create` + 加载 skein-flow, 否则即违规。
**禁用 harness 内置 TaskCreate (TodoWrite 类) 冒充 skein create** — TaskCreate 是内部工具类, 非正式 task 建立流程。跨文件任务必须 `skein create` 正式建 task, 禁用 TaskCreate 绕过 task 建立。
**走 flow 前先 `skein list --status open --json` 查重**, 命中相关 active task → 并入补 subtask, 禁重复建。
豁免 (输出判定行后可直接答/改): 纯查询 · 问答 · 单文件单处 ≤20 行且位置已知。边界模糊 → AskUserQuestion 问用户 (禁自行 inline 蒙混)。"""


def cmd_user_prompt(d: dict[str, Any]) -> int:
    """UserPromptSubmit: 每 prompt 必注入。未初始化 → 硬提示先 setup; 已初始化 → 注入 task 判定 + 查重句。"""
    root = _git_root(d.get("cwd") or os.getcwd())
    dir_ = os.path.join(root, ".skein")
    has_git = os.path.isdir(os.path.join(root, ".git"))
    # 非 git 且无 .skein: 别在任意目录 nag (用户 setup/init 建了 .skein 才接管)
    if not has_git and not os.path.isdir(dir_):
        return 0
    if not os.path.exists(os.path.join(dir_, "config.yaml")):
        ctx = _UNINIT_TRELLIS if os.path.isdir(os.path.join(root, ".trellis")) else _UNINIT_PLAIN
    else:
        ctx = _INIT_CTX
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
    return 0


# ── task-created (TaskCreated: 机械阻 harness 内置 TaskCreate 冒充 skein create) ──
def cmd_task_created(d: dict[str, Any]) -> int:
    """TaskCreated: .skein 已初始化 → 机械阻 TaskCreate (冒充 skein create)。"""
    root = _git_root(d.get("cwd") or os.getcwd())
    if os.path.exists(os.path.join(root, ".skein", "config.yaml")):
        print("检测到 TaskCreate。已初始化 SKEIN 项目禁用 harness 内置 TaskCreate 冒充 task 建立 — "
              "跨文件任务用 `skein create` 正式建 task 走 flow 闭环。", file=sys.stderr)
        return 2
    return 0


DISPATCH: dict[str, Any] = {"permission": cmd_permission, "guard": cmd_guard,
            "batch": cmd_batch, "report": cmd_report, "fmt": cmd_fmt,
            "spec-meta": cmd_spec_meta, "stop-check": cmd_stop_check,
            "user-prompt": cmd_user_prompt, "task-created": cmd_task_created}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: hooks.py {{{'|'.join(DISPATCH)}}}\n")
        return 2
    d = _load_stdin()
    if d is None:
        return 0  # stdin 非法 JSON: 静默放行
    return cast(int, DISPATCH[sys.argv[1]](d))


if __name__ == "__main__":
    sys.exit(main())
