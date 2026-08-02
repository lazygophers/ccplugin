"""hooks 结构校验 — 未知键/字段一律报错而非静默忽略。"""
from __future__ import annotations

from typing import Any

from skeinlib.config.defaults import (
    HOOK_ENTRY_FIELDS, HOOK_ENTRY_REQUIRED, HOOK_ENTRY_TYPES,
    HOOK_SCOPES, HOOK_WHENS_AGENT, HOOK_WHENS_STAGE,
)


def hooks_schema_errors(hooks: Any) -> list[str]:
    """校验 hooks 结构, 返回错误清单 (空 = 合法)。"""
    errs: list[str] = []
    if not isinstance(hooks, dict):
        return [f"hooks 应为映射, 得 {type(hooks).__name__}"]
    for scope, whens in hooks.items():
        if scope not in HOOK_SCOPES:
            errs.append(f"hooks.{scope}: 未知 scope — 合法值: {', '.join(HOOK_SCOPES)}")
            continue
        if not isinstance(whens, dict):
            errs.append(f"hooks.{scope}: 应为映射, 得 {type(whens).__name__}")
            continue
        if scope == "agent":
            for agent, ws in whens.items():
                if not isinstance(ws, dict):
                    errs.append(f"hooks.agent.{agent}: 应为映射, 得 {type(ws).__name__}")
                    continue
                errs += _hook_when_errors(f"hooks.agent.{agent}", ws, HOOK_WHENS_AGENT)
        else:
            errs += _hook_when_errors(f"hooks.{scope}", whens, HOOK_WHENS_STAGE)
    return errs


def _hook_when_errors(path: str, whens: dict[str, Any], legal: tuple[str, ...]) -> list[str]:
    """校验某 scope 下的 when 键与其条目列表。"""
    errs: list[str] = []
    for when, entries in whens.items():
        if when not in legal:
            errs.append(f"{path}.{when}: 未知时机 — 合法值: {', '.join(legal)}")
            continue
        if not isinstance(entries, list):
            errs.append(f"{path}.{when}: 应为列表, 得 {type(entries).__name__}")
            continue
        for i, e in enumerate(entries, 1):
            p = f"{path}.{when}#{i}"
            if not isinstance(e, dict):
                errs.append(f"{p}: 条目应为映射, 得 {type(e).__name__}")
                continue
            for k in e:
                if k not in HOOK_ENTRY_FIELDS:
                    errs.append(f"{p}: 未知字段 {k!r} — 合法字段: {', '.join(HOOK_ENTRY_FIELDS)}")
            for k in HOOK_ENTRY_REQUIRED:
                if not e.get(k):
                    errs.append(f"{p}: 缺必填字段 {k!r}")
            t = e.get("type")
            if t and t not in HOOK_ENTRY_TYPES:
                errs.append(f"{p}: type={t!r} 不支持 — 合法值: {', '.join(HOOK_ENTRY_TYPES)}")
            to = e.get("timeout")
            if to is not None and not (isinstance(to, int) and to > 0):
                errs.append(f"{p}: timeout 须正整数, 得 {to!r}")
            ce = e.get("continue_on_error")
            if ce is not None and not isinstance(ce, bool):
                errs.append(f"{p}: continue_on_error 须 true/false, 得 {ce!r}")
    return errs
