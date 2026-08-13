"""parser — jsonl 一行 → Message.

Claude Code transcripts schema (已知字段, 不识别字段 skip + warn):
  type:      "user" / "assistant" / "system" / "summary" / ...
  message:   {role, content}  其中 content 可能是 str 或 list[{type,text,...}]
  timestamp: ISO-8601 字符串
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

from . import Message


def _extract_text(content) -> str:
    """content → 纯文本 (str 直返; list 拼 text 块; 其他 repr)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif "text" in block and isinstance(block["text"], str):
                    parts.append(block["text"])
        return "\n".join(parts)
    return ""


def parse_file(path: Path) -> Iterable[Message]:
    """yield Message; 解析失败 skip + stderr warn."""
    try:
        fh = path.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"warn: open failed {path}: {exc}", file=sys.stderr)
        return
    with fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"warn: {path}:{line_no} json decode: {exc}", file=sys.stderr)
                continue
            if not isinstance(obj, dict):
                continue
            top_type = obj.get("type", "unknown")
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            role = msg.get("role") or top_type or "unknown"
            content = msg.get("content", obj.get("content", ""))
            text = _extract_text(content)
            if not text:
                continue
            yield Message(
                session_file=str(path),
                line_no=line_no,
                role=str(role),
                type=str(top_type),
                text=text,
                timestamp=str(obj.get("timestamp", "")),
                raw=obj,
            )
