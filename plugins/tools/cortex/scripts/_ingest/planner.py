"""planner — dry-run plan JSON 拼装.

输出形状:
  {
    "mode": "dry-run|apply",
    "source": "<input>",
    "kind": "github|gitlab|website|local",
    "target_root": "<vault-root>",
    "plan": [
      {
        "source": "<input>",
        "kind": "<kind>",
        "target_path": "项目/<host>/<owner>/<repo>",
        "target_filename": "README.md",
        "fetch_method": "gh|webfetch|local-read|...",
        "frontmatter_preview": {"type": "project", "source": "<URL>", "summary": "TODO"}
      }
    ],
    "notes": [...]   # apply 时含 "需 main 抓取" 标记
  }
"""
from __future__ import annotations

from typing import Any

from . import InputKind
from .router import fetch_method, target_path


def _frontmatter_preview(kind: InputKind) -> dict[str, Any]:
    src_ref = kind.source
    if kind.kind in ("github", "gitlab") and kind.host and kind.owner and kind.repo:
        src_ref = f"https://{kind.host}/{kind.owner}/{kind.repo}"
    return {
        "type": "project",
        "source": src_ref,
        "summary": "TODO",
    }


def build_plan(kind: InputKind, target_root: str, mode: str) -> dict[str, Any]:
    tp = target_path(kind)
    entry = {
        "source": kind.source,
        "kind": kind.kind,
        "target_path": tp,
        "target_filename": "README.md",
        "fetch_method": fetch_method(kind),
        "frontmatter_preview": _frontmatter_preview(kind),
    }
    if kind.git_remote:
        entry["git_remote"] = kind.git_remote
    if kind.local_dir:
        entry["local_dir"] = kind.local_dir

    result: dict[str, Any] = {
        "mode": mode,
        "source": kind.source,
        "kind": kind.kind,
        "target_root": target_root,
        "plan": [entry],
        "notes": [],
    }
    if mode == "apply":
        result["notes"].append(
            "需 main 抓取: 本 task 范围仅生成 plan, 实际 fetch (gh / git clone / WebFetch / local read) 由 main 会话或 sub-agent 调度落盘."
        )
    return result
