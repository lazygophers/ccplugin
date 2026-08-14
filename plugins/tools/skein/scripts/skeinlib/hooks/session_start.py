from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from skeinlib.hooks import budget_guard

SESSION_START_BUDGET_TOKENS = 400  # session-start 注入 token 硬预算


def _pending_fix_hint(spec_dir: Path) -> str:
    # 读 Stop hook 写的 .skein/spec/.pending-fix (有问题则停机写) → 提示 main 派 specer bg。
    # ponytail: 直读 JSON 不复用 Spec 类 — session-start 是冷启动路径, 免为读一个文件实例化 Spec + spec.py import
    marker = spec_dir / ".pending-fix"
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    problems = payload.get("problems") or []
    if not problems:
        return ""
    by_type: dict[str, int] = {}
    for p in problems:
        by_type[p.get("type", "?")] = by_type.get(p.get("type", "?"), 0) + 1
    summary = ", ".join(f"{t}({n})" for t, n in sorted(by_type.items()))
    return f"""# ⚠️ 检测到 spec 问题待修 (.pending-fix)
命中 {len(problems)} 项: {summary}。
**建议异步 bg 派 `skein-specer` agent 跑 `skein-spec maintain --apply`** (fire-and-forget, 派出即结束回合; 自动修超预算/stale/keywords重复/废弃, 断链只报告)。"""


def cmd_session_start(_: dict[str, Any]) -> int:
    # SessionStart hook: 只在用户已经建了 .skein 工作区时接管; 未初始化一律静默, 不劝进不 nag。
    from skeinlib.core.workspace import Workspace
    ws = Workspace()
    if not (ws.dir / "config.yaml").exists():
        return 0
    cfg = ws.config()
    wt_on = cfg["worktree"]["enabled"]
    # worktree 模式下 finish 必 commit (不提交则 merge 丢改动): 生效值在代码层归一, auto_commit 配置只对原地模式生效
    wt_root = ws.root / cfg["worktree"]["root"]
    wt_txt = f"启用 (task 各开 worktree 隔离, 目录: {wt_root})" if wt_on else "禁用 (原地执行, 无 worktree)"
    ac_on = bool(cfg["auto_commit"]) or wt_on
    ac_txt = "启用 (finish 时自动 commit)" if ac_on else "禁用 (改动需手动 commit)"
    hint = _pending_fix_hint(ws.dir / "spec")
    config_text = f"""# SKEIN 运行配置
- worktree: {wt_txt}
- auto_commit: {ac_txt}"""
    prefix_text = """# 回复前缀 (强制)
- 每条回复以 `[skein]` 开头
- 处理某 task 时用 `[skein|<tid，必须是已经注册的>|<阶段>]`
- 阶段取值: plan / research / exec / check / finishing"""
    body = f"""{config_text}

{prefix_text}"""
    if hint:
        body = f"""{hint}

{body}"""
    ctx = budget_guard(body, SESSION_START_BUDGET_TOKENS, "skein-hooks:session-start")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": ctx}}))
    return 0


__all__ = ["SESSION_START_BUDGET_TOKENS", "_pending_fix_hint", "cmd_session_start"]
