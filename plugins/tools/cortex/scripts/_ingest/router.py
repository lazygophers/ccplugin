"""router — InputKind → 目标路径计算.

路径映射:
  github / gitlab → 项目/<host>/<owner>/<repo>
  website         → 项目/<domain>/_/<path-slug>
  local           → 项目/local/<basename>
"""
from __future__ import annotations

from . import InputKind

PROJECT_ROOT = "项目"


def target_path(kind: InputKind) -> str:
    """返回相对 vault 根的目标路径 (POSIX 风格)."""
    if kind.kind in ("github", "gitlab"):
        host = kind.host or ("github.com" if kind.kind == "github" else "gitlab.com")
        owner = kind.owner or "_"
        repo = kind.repo or "_"
        return f"{PROJECT_ROOT}/{host}/{owner}/{repo}"
    if kind.kind == "website":
        domain = kind.domain or "_"
        slug = kind.path_slug or "_"
        return f"{PROJECT_ROOT}/{domain}/_/{slug}"
    if kind.kind == "local":
        name = kind.local_basename or "_"
        return f"{PROJECT_ROOT}/local/{name}"
    raise ValueError(f"unknown kind: {kind.kind}")


def fetch_method(kind: InputKind) -> str:
    """建议的抓取方式 (供 main 会话调度参考)."""
    if kind.kind == "github":
        return "gh"
    if kind.kind == "gitlab":
        return "glab-or-webfetch"
    if kind.kind == "website":
        return "webfetch"
    if kind.kind == "local":
        return "local-read"
    return "unknown"
