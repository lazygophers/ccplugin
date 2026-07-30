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
  user-prompt UserPromptSubmit: 已初始化按 prompt 信号三档注入 (flow/inline/grey); 未初始化注入 setup 提示。
  flow-gate   PostToolUse: 写源码后若无 active task 且已跨 ≥2 文件 → 提示补 create (非阻塞, 一次)。

各子命令读 stdin JSON, 逻辑与拆分前的 *-skein.py 一致; 无命中一律静默 exit 0。
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Optional, cast

# harness 起 hook 时既不走 Bash PATH 也不保证 cwd —— 必须显式接 sys.path 才能 import skeinlib
# (bin/ wrapper 用 runpy.run_path, 它不像直调脚本那样自动加 sys.path[0], 见 test_bin_wrappers)。
# 刻意用 os.path 而非 pathlib: pathlib 要 2.5ms, 而这是每个 prompt 都跑的路径, os 本来就已导入。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skeinlib.hooks.judge import (_CTX, _PREFIX_RULE, _UNINIT_PLAIN,  # noqa: E402
                                  _UNINIT_TRELLIS, _judge_signal, _task_phase_hints)
# subprocess / datetime 改局部 import (仅 cmd_fmt / cmd_stop_check 用), 不拖 user-prompt 等热路径 (perf-research §6.2)

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


def cmd_guard(d: dict[str, Any]) -> int:
    """硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 (命中 exit 2)。"""
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
    import subprocess  # 局部: 仅 fmt 子命令用, 不拖 user-prompt 等热路径
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
                warns.append("缺失: keywords")
            continue
        if k == "created":
            if not v or not re.match(r"^-?\d+$", v):
                warns.append("缺失/非法: created (需 unix ts)")
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
    from skeinlib.spec.facade import Spec  # 局部 import: 仅 stop-check 加载, 不拖其他子命令启动
    from skeinlib.spec.model import always_budget
    from datetime import datetime  # 局部: 仅 stop-check 用 (ts 落盘)

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
        "budget": always_budget(),
        "problems": problems,
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0











def _run_config(dir_: str) -> tuple[bool, int, bool]:
    """读 config.yaml 的 worktree.enabled + max_active + auto_commit (旧扁平键 deprecated fallback 仍生效);
    默认从 skein.CONFIG_DEFAULTS (hook 不硬编码)。"""
    from skeinlib.config import CONFIG_DEFAULTS, _cfg_effective, _yaml_load  # lazy: 仅已初始化热路径需要; 默认真值唯一来源
    try:
        with open(os.path.join(dir_, "config.yaml"), encoding="utf-8") as f:
            cfg = _cfg_effective(_yaml_load(f.read()))
    except (OSError, ValueError):
        cfg = CONFIG_DEFAULTS
    uw = bool(cfg["worktree"]["enabled"])
    ac = bool(cfg["auto_commit"])
    ma = cfg["max_active"]
    env = os.environ.get("CLAUDE_PLUGIN_OPTION_MAX_ACTIVE")
    if env and env.strip().isdigit():
        ma = int(env)
    return uw, int(ma), ac


def cmd_user_prompt(d: dict[str, Any]) -> int:
    """UserPromptSubmit: 每 prompt 必注入。未初始化 → 硬提示先 setup; 已初始化 → 注入单一 _CTX (含命中信号证据, 走 flow/inline 交 AI 读判据自判)。"""
    # ponytail: 用户显式调 skein slash command = 已决定走 skein 流程, 无需路由启发判定/未初始化提示, 直接放行
    prompt = (d.get("prompt", "") or "").strip()
    if prompt.startswith("/skein-") or prompt.startswith("/skein:skein-") or prompt == "go" or prompt == "exec" or prompt == "do" or prompt == "plan" or prompt.startswith("skein-"):
        return 0
    root = _git_root(d.get("cwd") or os.getcwd())
    dir_ = os.path.join(root, ".skein")
    has_git = os.path.isdir(os.path.join(root, ".git"))
    # 非 git 且无 .skein: 别在任意目录 nag (用户 setup/init 建了 .skein 才接管)
    if not has_git and not os.path.isdir(dir_):
        return 0
    if not os.path.exists(os.path.join(dir_, "config.yaml")):
        ctx = _UNINIT_TRELLIS if os.path.isdir(os.path.join(root, ".trellis")) else _UNINIT_PLAIN
    else:
        evidence = _judge_signal(d.get("prompt", "") or "")
        ctx = _CTX
        if evidence:
            ctx += f"\n本次命中: {', '.join(evidence)}"
        ctx += "\n\n" + _PREFIX_RULE + _task_phase_hints(dir_)
        uw, ma, ac = _run_config(dir_)
        wt_txt = "启用 (task 各开 worktree 隔离)" if uw else "禁用 (原地执行, 无 worktree)"
        # worktree 模式下 finish 必 commit (不提交则 merge 丢改动), auto_commit 只对原地模式生效
        ac_txt = ("强制 (worktree 模式必自动 commit, 本配置不生效)" if uw
                  else ("启用 (finish 时自动 commit)" if ac else "禁用 (改动需手动 commit)"))
        ctx += f"\n\n# SKEIN 运行配置\n- worktree: {wt_txt}\n- 最大并行 subtask: {ma}\n- auto_commit: {ac_txt}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
    return 0


# ── flow-gate (PostToolUse: 无 active task 却在跨文件改源码 → 软提示补 create) ──────
# 背景: 旧「落码门」(改源码前强制 active task) 被移除过 (见 _CTX 上方注释), 之后
# 「判了 flow 却不建 task 直接开干」就只剩提示词自觉约束, 长会话必漂移。
# 本门是它的软替代, 刻意避开当初被移除的原因:
#   ① PostToolUse 不 PreToolUse — 只提示不阻断, 不打断工作流, 不误伤诊断只读
#   ② 累计 ≥2 个源码文件才提 — 单文件小改是 inline 的合法豁免, 不该被 nag
#   ③ 提示一次即落 flag — 不刷屏
_SRC_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".php",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sh")
_TALLY_MAX_AGE = 4 * 3600  # tally 超此秒数视为上个会话残留, 重新计数


def cmd_flow_gate(d: dict[str, Any]) -> int:
    """写源码后: 无 active task 且本轮已跨 ≥2 源码文件 → 注入补 create 提示 (非阻塞, 一次)。"""
    fp = (d.get("tool_input", {}) or {}).get("file_path", "")
    if not fp or not fp.endswith(_SRC_EXT):
        return 0
    norm = fp.replace("\\", "/")
    if ".skein/" in norm or "/tests/" in norm or "/test_" in norm:
        return 0  # spec 库与测试文件不计入 (测试常跟着单文件改动走)
    root = _git_root(d.get("cwd") or os.getcwd())
    dir_ = os.path.join(root, ".skein")
    if not os.path.exists(os.path.join(dir_, "config.yaml")):
        return 0  # 未初始化归 user-prompt 的 _UNINIT_* 提示, 本门不重复 nag
    # 有 active task → 已在 flow 内, 清 tally 直接放行
    try:
        with open(os.path.join(dir_, "task.json"), encoding="utf-8") as f:
            rows = json.loads(f.read()).get("tasks", [])
        if any(r.get("status") in ("进行中", "检查中") for r in rows):
            for p in (os.path.join(dir_, ".edit-tally"), os.path.join(dir_, ".edit-tally.warned")):
                if os.path.exists(p):
                    os.remove(p)
            return 0
    except (OSError, ValueError):
        return 0
    tally, warned = os.path.join(dir_, ".edit-tally"), os.path.join(dir_, ".edit-tally.warned")
    if os.path.exists(warned):
        return 0  # 已提过, 不刷屏
    import time  # 局部: 仅本门用, 不拖其他 8 个子命令启动
    try:
        seen: set[str] = set()
        if os.path.exists(tally) and time.time() - os.path.getmtime(tally) < _TALLY_MAX_AGE:
            with open(tally, encoding="utf-8") as f:
                seen = {ln.strip() for ln in f if ln.strip()}
        seen.add(norm)
        with open(tally, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(seen)))
        if len(seen) < 2:
            return 0
        open(warned, "w").close()
    except (OSError, ValueError):
        # ValueError 覆盖 UnicodeDecodeError (tally 被写坏成二进制) — PostToolUse 永不该失败,
        # 一个坏掉的计数文件不值得打断用户的 Edit/Write。
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": (
        f"⚠️ 已改动 {len(seen)} 个源码文件但**无 active task** — 跨 ≥2 文件正是 flow 的判据线。\n"
        "若这本该走 flow: 立刻 `skein.py create` 建 task, 把已改的纳入首个 subtask, 后续改动在 flow 内做。\n"
        "若确属 inline 豁免 (如同一处改动波及两文件): 忽略本提示, 继续。\n"
        f"已改: {', '.join(sorted(seen)[:5])}")}}))
    return 0


# ── agent-start / agent-stop (agent 生命周期钩子入口) ───────────────────────
def _agent_hook(when: str) -> int:
    """agent start/stop 钩子: 查 hooks.agent.<name>.<when> (+ "*"), 无配置即 no-op;
    命中则经 hooks.runner._run_hooks 真正执行 (具名先跑, "*" 后跑)。

    永不返回非零 —— agent 钩子失败不该影响 subtask 成败 (design.md §3 阻断语义,
    与阶段钩子 before 阻断相反; _run_hooks 对 scope=="agent" 已内建只告警不抛)。
    """
    argv = sys.argv[2:]
    opts: dict[str, str] = {}
    for i in range(0, len(argv) - 1, 2):
        if argv[i].startswith("--"):
            opts[argv[i][2:]] = argv[i + 1]
    agent = opts.get("agent", "")
    tid = opts.get("tid", "")
    sid = opts.get("sid", "")
    root = _git_root(opts.get("cwd") or os.getcwd())
    try:
        from skeinlib.config import _yaml_load  # lazy: 仅本门需要
        with open(os.path.join(root, ".skein", "config.yaml"), encoding="utf-8") as f:
            cfg = _yaml_load(f.read())
    except (OSError, ValueError, ImportError):
        return 0  # 未初始化 / 配置语法错 / 导入失败 → 静默放行 (钩子永不阻断 agent)
    spec = cfg.get("hooks")
    if not isinstance(spec, dict):
        return 0  # 无 hooks 键: 零开销直返, 不解析深层不 fork
    agents = spec.get("agent")
    if not isinstance(agents, dict):
        return 0
    # 具名先, 通配 "*" 后 (具体优先于通配)
    todo = [c for key in (agent, "*")
            if isinstance(agents.get(key), dict)
            for c in (agents[key].get(when) or [])]
    if not todo:
        return 0
    from skeinlib.hooks.runner import _run_hooks  # lazy: 仅命中时才 fork 子进程
    _run_hooks("agent", when, {"hooks": todo, "agent": agent, "tid": tid, "sid": sid, "repo_root": root})
    try:  # 审计: 供 c7 doctor 检查「配了 agent 钩子但从未触发」; 写失败不影响钩子已执行的事实
        from skeinlib.spec.facade import Spec
        Spec()._write_audit("agent-hook", f"agent.{agent}", when, f"{len(todo)} hooks", f"tid={tid} sid={sid}")
    except (OSError, ValueError):
        pass
    return 0


DISPATCH: dict[str, Any] = {"permission": cmd_permission, "guard": cmd_guard,
            "batch": cmd_batch, "report": cmd_report, "fmt": cmd_fmt,
            "spec-meta": cmd_spec_meta, "stop-check": cmd_stop_check,
            "user-prompt": cmd_user_prompt, "flow-gate": cmd_flow_gate,
            "agent-start": lambda _d: _agent_hook("start"),
            "agent-stop": lambda _d: _agent_hook("stop")}


_ARGV_DISPATCH = {"agent-start", "agent-stop"}  # dispatch 参数式子命令 (design.md §1): 用户/agent 显式调用,
# 参数走 --flag argv (非 harness PreToolUse/PostToolUse 那套 stdin JSON 协议) —— 不读 stdin, 免无输入时空等


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: hooks.py {{{'|'.join(DISPATCH)}}}\n")
        return 2
    if sys.argv[1] in _ARGV_DISPATCH:
        return cast(int, DISPATCH[sys.argv[1]]({}))
    d = _load_stdin()
    if d is None:
        return 0  # stdin 非法 JSON: 静默放行
    return cast(int, DISPATCH[sys.argv[1]](d))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        # ponytail: _judge_signal 是 non-trivial 分支逻辑, 留 ONE runnable self-check。
        # 跑: python hooks.py --self-check  (经 bin/skein-hooks 不触发, 仅本地验)
        # _judge_signal 现返回证据清单 (档位交 AI 读 _CTX 自判), 验证据命中 + shape + 拼接 + 单一 _CTX
        cases = [
            ("改 hooks.py 和 spec.py 的判定", ["文件路径×2", "改动类动词", "跨文件连接词"]),
            ("在 src/auth.py 加 login 函数", ["文件路径×1", "改动类动词"]),
            ("参考 admin-api 搭建骨架, 用 go-zero 脚手架", ["新建类信号"]),
            ("什么是 SKEIN", ["查询类词"]),
            ("先做 a 然后做 b 接着做 c", ["多步骤标记"]),
            ("继续", []),
        ]
        fails = []
        shape = _judge_signal("test")
        if not isinstance(shape, list):
            fails.append(("_judge_signal", "list", type(shape).__name__, "应返回 list"))
        for p, must_have in cases:
            ev = _judge_signal(p)
            for sig in must_have:
                if sig not in ev:
                    fails.append((p, sig, ev, "期望证据缺失"))
            print(f"  ev={ev} | {p!r}")
        # 证据行: 非空才拼 "本次命中", 空 _CTX 无 "本次命中"
        ctx_hit = _CTX + f"\n本次命中: {', '.join(_judge_signal('改 a.py 和 b.py'))}"
        ctx_empty = _CTX  # evidence 空 → 仅 _CTX, 无本次命中行
        if "本次命中" not in ctx_hit:
            fails.append(("ctx-hit", "has-line", "本次命中", "evidence 非空未拼本次命中行"))
        if "本次命中" in ctx_empty:
            fails.append(("ctx-empty", "no-line", "本次命中", "_CTX 默认含本次命中行 (应空时不展示)"))
        # 单一 _CTX: 三常量须已删
        for stale in ("_CTX_FLOW", "_CTX_INLINE", "_CTX_GREY"):
            if stale in globals():
                fails.append(("_CTX", "single-ctx", stale, "应只留 _CTX"))
        # 正向化自检
        for bad in ["MUST", "禁", "违规", "黑名单"]:
            if bad in _CTX:
                fails.append(("_CTX", "no-negation", bad, "正向化破规"))
        print(f"FAIL count: {len(fails)}")
        sys.exit(1 if fails else 0)
    sys.exit(main())
