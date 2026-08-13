"""时间格式化工具。"""
from __future__ import annotations

import time
from typing import Optional


def fmt_ts(ts: Optional[int]) -> str:
    """epoch 秒 → 本地可读时间; None/0 → '-'。"""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"
