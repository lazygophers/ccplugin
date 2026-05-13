"""`cortex_ingest_file` MCP tool — read local file, extract, save (P4)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Allow direct CLI invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.extractors import docx as docx_extractor  # noqa: E402
from lib.extractors import epub as epub_extractor  # noqa: E402
from lib.extractors import pdf as pdf_extractor  # noqa: E402
from save import _save_internal  # noqa: E402

_SUPPORTED_EXTS = {".pdf", ".epub", ".docx", ".md", ".txt", ".markdown"}

_GIT_REMOTE_RE = re.compile(
    r"(?:https?://|git@|ssh://(?:git@)?)(?P<host>[^/:]+)[/:](?P<org>[^/]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"
)


def _rel_home_to_host_org_repo(abs_path: Path) -> tuple[str, str, str, str]:
    """Map an absolute directory path → (host, org, repo, source_url).

    Strategy: take path relative to $HOME, split into segments.
    - 3+ segments: host/org/repo = first three
    - 2 segments: host=parts[0], org=`_local`, repo=parts[1]
    - 1 segment:  host=`_local`, org=`_local`, repo=parts[0]
    - 0 segments (== $HOME): host=`_local`, org=`_local`, repo=`home`
    - not under $HOME: host=`_local`, org=`_local`, repo=basename

    `source_url` is a pseudo `file://$HOME/<rel>` form when under $HOME,
    otherwise `file://<abs_path>`.
    """
    home = Path.home()
    try:
        rel = abs_path.relative_to(home)
    except ValueError:
        return ("_local", "_local", abs_path.name or "home", f"file://{abs_path}")
    parts = rel.parts
    if len(parts) >= 3:
        host, org, repo = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        host, org, repo = parts[0], "_local", parts[1]
    elif len(parts) == 1:
        host, org, repo = "_local", "_local", parts[0]
    else:
        host, org, repo = "_local", "_local", "home"
    source_url = f"file://$HOME/{rel.as_posix()}" if parts else "file://$HOME"
    return (host, org, repo, source_url)


def _detect_project_root(start: Path) -> dict | None:
    """Walk up from `start` looking for .git or project markers.

    Strategy:
    1. `.git/config` with origin in github/gitlab → use origin host/org/repo
    2. `.git/config` with non-github/gitlab origin (private / local) → 相对 $HOME 路径策略
    3. No `.git/` but project marker found → 相对 $HOME 路径策略 (anchored at ancestor)
    4. None found → None (caller treats as inbox/source)

    Returns dict with kind=project + host/org/repo (+ source_url) or None.
    """
    cur = start if start.is_dir() else start.parent
    project_markers = {"pyproject.toml", "package.json", "Cargo.toml", "go.mod"}
    for ancestor in [cur, *cur.parents]:
        git_cfg = ancestor / ".git" / "config"
        if git_cfg.is_file():
            try:
                cfg_text = git_cfg.read_text(encoding="utf-8", errors="replace")
            except OSError:
                cfg_text = ""
            m_origin = re.search(
                r'\[remote "origin"\][^\[]*?url\s*=\s*(\S+)',
                cfg_text,
                re.S,
            )
            if m_origin:
                origin = m_origin.group(1).strip()
                m = _GIT_REMOTE_RE.search(origin)
                if m:
                    host = m.group("host").lower()
                    if host in ("github.com", "gitlab.com") or "gitlab" in host:
                        return {
                            "kind": "project",
                            "host": host,
                            "org": m.group("org"),
                            "repo": m.group("repo"),
                        }
            # Has .git but no github/gitlab origin → 相对 $HOME 路径策略
            host, org, repo, source_url = _rel_home_to_host_org_repo(ancestor)
            return {
                "kind": "project",
                "host": host,
                "org": org,
                "repo": repo,
                "source_url": source_url,
            }
        if any((ancestor / mk).is_file() for mk in project_markers):
            host, org, repo, source_url = _rel_home_to_host_org_repo(ancestor)
            return {
                "kind": "project",
                "host": host,
                "org": org,
                "repo": repo,
                "source_url": source_url,
            }
    return None


def _find_nested_repos(root: Path) -> list[Path]:
    """递归发现 `root` 子树中所有 `.git/` 父目录 (skip node_modules / `.git` 自身)。

    用于多 repo 工作树 ingest: 每个嵌套 repo 独立 ingest, 父项目内容范围 = root - 子 repos.
    """
    result: list[Path] = []
    if not root.is_dir():
        return result
    for p in root.rglob(".git"):
        if not p.is_dir():
            continue
        parts = set(p.parts)
        if "node_modules" in parts:
            continue
        parent = p.parent.resolve()
        # skip the root itself (caller's parent repo)
        if parent == root.resolve():
            continue
        result.append(parent)
    return result


def cli_ingest_file(args: dict) -> dict:
    args = args or {}
    raw_path = args.get("path")
    kind = args.get("kind")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("cortex_ingest_file: 'path' required (non-empty string)")
    if kind is not None and kind not in (
        "entity", "concept", "project", "domain", "source",
        "reflection", "question", "fleeting", "inbox", "log", "journal",
    ):
        raise ValueError(
            "cortex_ingest_file: 'kind' must be one of entity/concept/project/domain/source/reflection/question/fleeting/inbox/log/journal"
        )

    path = Path(os.path.expanduser(raw_path)).resolve()
    if not path.exists():
        raise OSError(f"cortex_ingest_file: file not found: {path}")
    if not path.is_file():
        raise OSError(f"cortex_ingest_file: not a regular file: {path}")
    if not os.access(path, os.R_OK):
        raise OSError(f"cortex_ingest_file: not readable: {path}")

    ext = path.suffix.lower()
    if ext not in _SUPPORTED_EXTS:
        raise ValueError(f"cortex_ingest_file: unsupported extension: {ext}")

    # If kind omitted: walk up to detect git/project root.
    if kind is None:
        detected = _detect_project_root(path)
        if detected is not None:
            kind = detected["kind"]
            for k in ("host", "org", "repo"):
                if detected.get(k) and not args.get(k):
                    args[k] = detected[k]
            if detected.get("source_url") and not args.get("source_url"):
                args["source_url"] = detected["source_url"]
        else:
            # No project root → fall back to inbox (待 digest 分发到 项目/笔记 或 领域/<域>)
            kind = "inbox"

    warnings: list[str] = []
    extracted_title: str | None = None

    if ext == ".pdf":
        result = pdf_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    elif ext == ".epub":
        result = epub_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    elif ext == ".docx":
        result = docx_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    else:  # .md, .markdown, .txt -- read directly
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            body = path.read_text(encoding="utf-8", errors="replace")
            warnings.append("encoding-fallback")
        extracted_title = None

    if not body or not body.strip():
        raise RuntimeError("cortex_ingest_file: extracted body is empty")

    title = args.get("title") or extracted_title or path.stem

    save_res = _save_internal(
        kind=kind,
        title=title,
        body=body,
        tags=args.get("tags") or [],
        host=args.get("host"),
        org=args.get("org"),
        repo=args.get("repo"),
        source_sub=args.get("source_sub"),
        source_meta={"file": str(path), "ext": ext},
    )

    result_obj = {
        "path": save_res["path"],
        "source_file": str(path),
        "block_ids": save_res["block_ids"],
        "hits": save_res["hits"],
        "warnings": warnings,
    }
    return result_obj


def main() -> None:
    parser = argparse.ArgumentParser(description="cortex_ingest_file CLI.")
    parser.add_argument("--path", required=True)
    parser.add_argument(
        "--kind",
        choices=[
            "entity", "concept", "project", "domain", "source",
            "reflection", "question", "fleeting", "inbox", "log", "journal",
        ],
        default=None,
        help="If omitted, auto-detect by walking up for .git/project markers (fallback: inbox)",
    )
    parser.add_argument("--title")
    parser.add_argument("--host")
    parser.add_argument("--org")
    parser.add_argument("--repo")
    parser.add_argument(
        "--source-sub",
        dest="source_sub",
        default=None,
        help="source subdir (网页/论文/书籍)",
    )
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    ns = parser.parse_args()
    tags = [t.strip() for t in ns.tags.split(",") if t.strip()] if ns.tags else []
    result = cli_ingest_file(
        {
            "path": ns.path,
            "kind": ns.kind,
            "title": ns.title,
            "host": ns.host,
            "org": ns.org,
            "repo": ns.repo,
            "source_sub": ns.source_sub,
            "tags": tags,
        }
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
