"""extractor — Message → Increment 学习增量条目.

启发式 (优先序):
  1. L0 关键词 (永远/硬性/never/严禁/绝不) → KIND_L0
  2. user 消息含校正语 (no/wrong/不对/别这样) → KIND_CORRECTION
  3. assistant 消息含决策语 (let's use/我们选/决定) → KIND_DECISION
  4. 任意消息含踩坑词 (failed because/error because/踩坑) → KIND_TIP

一条消息最多产 1 个 Increment (优先序高者胜); 短消息 (< 8 字符) skip.
"""
from __future__ import annotations

from typing import Iterable

from . import (
    KIND_CORRECTION,
    KIND_DECISION,
    KIND_L0,
    KIND_TIP,
    RE_CORRECTION,
    RE_DECISION,
    RE_L0,
    RE_TIP,
    Increment,
    Message,
    truncate,
)


def classify(msg: Message) -> str | None:
    """返回 kind 或 None."""
    text = msg.text
    if len(text.strip()) < 8:
        return None
    if RE_L0.search(text):
        return KIND_L0
    if msg.role == "user" and RE_CORRECTION.search(text):
        return KIND_CORRECTION
    if msg.role == "assistant" and RE_DECISION.search(text):
        return KIND_DECISION
    if RE_TIP.search(text):
        return KIND_TIP
    return None


def extract(messages: Iterable[Message]) -> list[Increment]:
    """批量分类 → Increment 列表."""
    incs: list[Increment] = []
    for m in messages:
        kind = classify(m)
        if not kind:
            continue
        incs.append(
            Increment(
                session_file=m.session_file,
                line_no=m.line_no,
                kind=kind,
                summary=truncate(m.text, 80),
                text=m.text,
                role=m.role,
            )
        )
    return incs
