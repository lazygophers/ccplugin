"""cortex history-digest — Claude Code 会话历史 → 全局记忆库 路由模块包.

子模块:
  scanner   — rglob ~/.claude/projects/**/*.jsonl → 文件清单
  parser    — 每行 json.loads → 消息对象 (role/type/content/timestamp)
  extractor — 消息 → 学习增量条目 (kind/summary)
  router    — 增量 → memory L0-L4 路径 (全部全局, 复用 cortex-schema)
  runner    — argparse + 拼装 JSON plan
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# kind 枚举: user-correction / L0-rule / decision / tip
KIND_CORRECTION = "user-correction"
KIND_L0 = "L0-rule"
KIND_DECISION = "decision"
KIND_TIP = "tip"

# 关键词正则 (中英混合)
RE_CORRECTION = re.compile(
    r"(?i)\b(no,? that|wrong|not that|don'?t do that|stop doing)\b|不对|不是这样|别这样|搞错了|错了"
)
RE_L0 = re.compile(
    r"(?i)\b(always|never|must always|must never)\b|永远|硬性|严禁|绝不|从不"
)
RE_DECISION = re.compile(
    r"(?i)\b(let'?s use|we'?ll use|going with|decided to|we choose)\b|我们选|决定用|采用|选用"
)
RE_TIP = re.compile(
    r"(?i)\b(failed because|error because|gotcha|pitfall|broke because)\b|踩坑|坑|翻车|教训"
)


@dataclass
class Message:
    """jsonl 一行 → 消息对象 (parser 输出)."""
    session_file: str
    line_no: int
    role: str  # user / assistant / system / tool / unknown
    type: str  # message / tool_use / tool_result / unknown
    text: str  # 提取后的纯文本
    timestamp: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Increment:
    """学习增量条目 (extractor 输出)."""
    session_file: str
    line_no: int
    kind: str  # KIND_*
    summary: str  # 前 80 字
    text: str  # 原文用于 router 路由
    role: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_file": self.session_file,
            "line_no": self.line_no,
            "kind": self.kind,
            "summary": self.summary,
        }


def truncate(text: str, n: int = 80) -> str:
    """前 n 字摘要 (单行)."""
    t = " ".join(text.split())
    return t if len(t) <= n else t[: n - 1] + "…"
