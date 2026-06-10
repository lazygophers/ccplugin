"""identify — 输入识别.

优先序:
  1. https?:// URL → github / gitlab / website
  2. git@host:owner/repo(.git)? → github / gitlab
  3. local dir + .git/config remote → 递归当 URL 处理
  4. local dir 无 git → kind=local
"""
from __future__ import annotations

import configparser
import re
from pathlib import Path
from urllib.parse import urlparse

from . import (
    GITHUB_HOSTS,
    GITLAB_HOSTS,
    HTTPS_GIT_RE,
    SSH_GIT_RE,
    InputKind,
)


def _classify_host(host: str) -> str:
    if host in GITHUB_HOSTS:
        return "github"
    if host in GITLAB_HOSTS:
        return "gitlab"
    return "website"


def _slugify_path(path: str) -> str:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "_"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", parts[0])[:64] or "_"


def _from_https(source: str) -> InputKind:
    parsed = urlparse(source)
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"invalid URL (no host): {source}")
    kind = _classify_host(host)
    if kind in ("github", "gitlab"):
        m = HTTPS_GIT_RE.match(source)
        if not m:
            # host 已知但路径不像 owner/repo (e.g. https://github.com/) → website fallback
            return InputKind(kind="website", source=source, domain=host, path_slug="_")
        return InputKind(
            kind=kind,
            source=source,
            host=host if host in GITHUB_HOSTS or host in GITLAB_HOSTS else host,
            owner=m.group("owner"),
            repo=m.group("repo"),
        )
    # website
    return InputKind(
        kind="website",
        source=source,
        domain=host,
        path_slug=_slugify_path(parsed.path or ""),
    )


def _from_ssh(source: str) -> InputKind:
    m = SSH_GIT_RE.match(source)
    if not m:
        raise ValueError(f"not a valid ssh git URL: {source}")
    host = m.group("host").lower()
    kind = _classify_host(host)
    if kind == "website":
        # 未知 host 的 ssh git, fallback github 桶 (按规范不会发生)
        kind = "github"
    return InputKind(
        kind=kind,
        source=source,
        host=host,
        owner=m.group("owner"),
        repo=m.group("repo"),
    )


def _read_git_remote(p: Path) -> str | None:
    """读 <p>/.git/config 的 [remote "origin"] url. 找不到返回 None."""
    cfg = p / ".git" / "config"
    if not cfg.is_file():
        return None
    cp = configparser.ConfigParser(strict=False)
    try:
        cp.read(cfg, encoding="utf-8")
    except Exception:
        return None
    # section 名形如 'remote "origin"'
    candidates = [
        'remote "origin"',
        "remote \"origin\"",
    ]
    for sec in cp.sections():
        if sec.strip().lower().replace('"', "") in ("remote origin",):
            url = cp.get(sec, "url", fallback=None)
            if url:
                return url.strip()
    # 兜底: 任意 remote section
    for sec in cp.sections():
        if sec.lower().startswith("remote"):
            url = cp.get(sec, "url", fallback=None)
            if url:
                return url.strip()
    _ = candidates  # silence
    return None


def identify(source: str) -> InputKind:
    """识别输入. 失败抛 ValueError."""
    s = source.strip()
    if not s:
        raise ValueError("empty source")

    # 1. https/http URL
    if s.startswith(("http://", "https://")):
        return _from_https(s)

    # 2. ssh git URL
    if s.startswith("git@"):
        return _from_ssh(s)

    # 3. local dir
    p = Path(s).expanduser()
    try:
        p = p.resolve()
    except Exception as e:
        raise ValueError(f"cannot resolve path: {s} ({e})") from e
    if not p.is_dir():
        raise ValueError(f"not a directory: {p}")
    remote = _read_git_remote(p)
    if remote:
        kind = identify(remote)
        kind.git_remote = remote
        kind.local_dir = str(p)
        return kind
    return InputKind(
        kind="local",
        source=source,
        local_dir=str(p),
        local_basename=p.name,
    )
