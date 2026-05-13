"""`cortex_save` MCP tool — write a typed note into the vault.

Pipeline (P1):

1. `masking.mask(body)` (reuse P0 module from `hooks/_lib/masking.py`).
2. Compute path by kind (4 知识库 子目录: 项目/领域/日记/收件箱):
   - `entity`/`concept`        → `知识库/领域/<domain>/<slug>.md` (--domain 可选, 缺则 `未分类`)
   - `project`/`domain` (alias) → `知识库/项目/<host>/<org>/<repo>/<slug>.md`
     (host/org/repo 接受任意字符串: github.com/gitlab.com 或相对 $HOME 路径段, 不足 3 段补 `_local`)
   - `source`                   → `知识库/收件箱/<host>-<slug>.md` (repo host 严禁; arxiv/网页/书籍统一落收件箱)
   - `reflection`               → `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<slug>.md`
   - `question`/`fleeting`/`inbox` → `知识库/收件箱/<slug>.md`
   - `log`/`journal`            → `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`
3. Prepend frontmatter (`type/title/created/tags/aliases`).
4. `wikilinks.add_block_ids` — append `^cortex-<sha8>` to each paragraph.
5. `lib.lock.file_lock` advisory write.
6. Patch `hot.md` (prepend new wikilink) and `index.md` (append).

Returns `{path, block_ids, hits}` JSON-serialized into `TextContent`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

# Allow `python3 save.py` invocation: add this dir to sys.path so `from lib...` works.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import re as _re  # noqa: E402

from lib.frontmatter import dump as fm_dump  # noqa: E402
from lib.lock import file_lock  # noqa: E402
from lib.vault_path import resolve_vault  # noqa: E402
from lib.wikilinks import add_block_ids, slugify  # noqa: E402

_TAGS_MIN = 10
_TAGS_MAX = 20
_PLACEHOLDER_RE = _re.compile(
    r"<.*?>|placeholder|TODO|待填|待用户填|TBD|FIXME|XXX", _re.I,
)


def _derive_tags(fm: dict, body: str) -> list[str]:
    """Extend `fm['tags']` to ≥ _TAGS_MIN by deriving from fm + body.

    严禁占位符。返回去重保序后 tag list (>=10 时上限 _TAGS_MAX);
    若派生不足 _TAGS_MIN, 返回尽力派生的结果 (调用方自决是否报错).
    """
    existing = list(fm.get("tags") or [])
    derived: list[str] = []

    def _push(t: str) -> None:
        if t and isinstance(t, str):
            derived.append(t)

    if fm.get("type"):
        _push(f"type/{fm['type']}")
    if fm.get("lang"):
        _push(f"lang/{fm['lang']}")
    src = fm.get("source") or {}
    if isinstance(src, dict):
        url = src.get("url")
        if url:
            m = _re.search(r"://([^/]+)", str(url))
            if m:
                _push(f"host/{m.group(1)}")
            _push("source/web")
    for k in ("host", "org", "repo"):
        v = fm.get(k)
        if v:
            _push(f"{k}/{v}")
    if fm.get("maturity"):
        _push(f"maturity/{fm['maturity']}")
    if fm.get("score") is not None:
        _push(f"score/{fm['score']}")
    if fm.get("created"):
        y = str(fm["created"])[:4]
        if y.isdigit():
            _push(f"created/{y}")

    # h1/h2 → topic
    for m in _re.finditer(r"^#{1,2}\s+(.+?)$", body[:2000], _re.M):
        title = m.group(1).strip()
        slug = _re.sub(r"[\s/\\:*?\"<>|]+", "-", title)[:30].strip("-_")
        if slug and len(slug) >= 2:
            _push(f"topic/{slug}")

    # first 500 chars: 中文 2-4 字 + 英文 PascalCase
    head = body[:500]
    for ph in _re.findall(r"[一-龥]{2,4}", head):
        if len(ph) >= 2:
            _push(f"keyword/{ph}")
    for ph in _re.findall(r"\b[A-Z][a-zA-Z]{2,15}\b", head):
        _push(f"keyword/{ph.lower()}")

    seen: set[str] = set()
    merged: list[str] = []
    for t in list(existing) + derived:
        if not isinstance(t, str) or not t.strip():
            continue
        if _PLACEHOLDER_RE.search(t):
            continue
        if t in seen:
            continue
        seen.add(t)
        merged.append(t)
    return merged[:_TAGS_MAX]


def _load_masking() -> Any:
    """Import the P0 masking module from `hooks/_lib/masking.py`.

    The MCP server may be run via 绝对路径 (no package install); in
    both cases we resolve the path relative to this file: `mcp/tools/save.py`
    → `mcp/` → `plugins/tools/cortex/scripts/hooks/_lib/masking.py`.
    """
    here = Path(__file__).resolve()
    # cli/save.py → cli/ → scripts/ → scripts/hooks/_lib/masking.py
    candidate = here.parent.parent / "hooks" / "_lib" / "masking.py"
    if not candidate.is_file():
        # via abs path: hooks 与 source 同 checkout, 直接
        # ~/.cortex/config.json (install_path) so cortex-doctor can wire it
        # explicitly without env vars.
        import json

        cfg = Path.home() / ".cortex" / "config.json"
        if cfg.is_file():
            try:
                hint = json.loads(cfg.read_text(encoding="utf-8")).get("install_path")
            except Exception:
                hint = None
            if hint:
                candidate = Path(hint).expanduser() / "hooks" / "_lib" / "masking.py"
    if not candidate.is_file():
        raise RuntimeError(
            "cortex_save: masking.py not found. "
            "Set 'install_path' in ~/.cortex/config.json to the cortex plugin directory."
        )
    spec = importlib.util.spec_from_file_location("cortex_masking", candidate)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load masking from {candidate}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cortex_masking"] = mod
    spec.loader.exec_module(mod)
    return mod


def _safe_segment(value: str, field: str) -> str:
    """Reject path-traversal in user-supplied path segments.

    `host`/`org`/`repo` land directly in the file path (we want to preserve
    casing for `github.com/Org/Repo`), so we must hard-reject any segment
    containing `/`, `\\`, NUL, or `..`. Empty segments are caller's problem.
    """
    if "/" in value or "\\" in value or "\x00" in value or value in ("..", "."):
        raise ValueError(
            f"cortex_save: invalid {field}={value!r} (path traversal)"
        )
    return value


def _resolve_path(vault: Path, args: dict, now: _dt.datetime) -> Path:
    kind = args["kind"]
    title = args["title"]
    slug = slugify(title)
    if kind in ("entity", "concept"):
        # 落 知识库/领域/<域>/<kebab>.md. --domain 可选, 缺则 领域/未分类/ (AI 自决)
        domain = args.get("domain") or "未分类"
        domain = _safe_segment(domain, "domain")
        target = vault / "知识库" / "领域" / domain / f"{slug}.md"
    elif kind in ("project", "domain"):
        # kind=domain is retained as backward-compatible alias; both route to 知识库/项目/.
        host = args.get("host")
        if not host:
            raise ValueError(f"cortex_save: 'host' required when kind={kind!r}")
        host = _safe_segment(host, "host")
        # 不再使用 local/<basename> 字面: host/org/repo 全接受任意字符串
        # (host=_local/workspace/persons/github.com/... 均合法; 调用方负责相对 $HOME 路径切分)
        org = _safe_segment(args.get("org") or "_local", "org")
        repo = _safe_segment(args.get("repo") or "_local", "repo")
        target = (
            vault / "知识库" / "项目" / host / org / repo / f"{slug}.md"
        )
    elif kind == "source":
        host = args.get("host")
        if not host:
            raise ValueError("cortex_save: 'host' required when kind='source'")
        # repo host 严禁走 source 路由, 引导改 kind=project
        if host in ("github.com", "gitlab.com") or "gitlab" in host:
            raise ValueError(
                f"cortex_save: repo host {host!r} should use kind='project', not 'source'"
            )
        host = _safe_segment(host, "host")
        # 非 repo 来源落 收件箱/<host>-<slug>.md (待 digest 分发)
        target = vault / "知识库" / "收件箱" / f"{host}-{slug}.md"
    elif kind == "reflection":
        ymd = now.strftime("%Y-%m-%d")
        ym = now.strftime("%Y-%m")
        target = vault / "知识库" / "日记" / "日" / ym / f"{ymd}-反思-{slug}.md"
    elif kind in ("question", "fleeting", "inbox"):
        # inbox: 若提供 host 则用 `<host>-<slug>.md` 帮助 digest 分发, 否则纯 slug
        host = args.get("host")
        if host:
            host = _safe_segment(host, "host")
            target = vault / "知识库" / "收件箱" / f"{host}-{slug}.md"
        else:
            target = vault / "知识库" / "收件箱" / f"{slug}.md"
    elif kind in ("log", "journal"):
        ymd = now.strftime("%Y-%m-%d")
        ym = now.strftime("%Y-%m")
        target = vault / "知识库" / "日记" / "日" / ym / f"{ymd}.md"
    else:
        raise ValueError(f"cortex_save: invalid kind {kind!r}")
    # Final guard: resolved path must stay inside vault root.
    vault_resolved = vault.resolve()
    try:
        target.resolve().relative_to(vault_resolved)
    except ValueError as exc:
        raise ValueError(
            f"cortex_save: resolved path escapes vault: {target}"
        ) from exc
    return target


def _patch_hot(vault: Path, wikilink: str) -> None:
    hot = vault / "hot.md"
    header = "## 最近落档"
    body_line = f"- {wikilink}\n"
    if not hot.is_file():
        hot.write_text(f"{header}\n\n{body_line}", encoding="utf-8")
        return
    text = hot.read_text(encoding="utf-8")
    if header in text:
        # Insert right after the header line.
        idx = text.index(header) + len(header)
        # Skip an immediate newline if present, then prepend our line.
        nl = text.find("\n", idx)
        if nl == -1:
            new = text + "\n" + body_line
        else:
            new = text[: nl + 1] + body_line + text[nl + 1 :]
        hot.write_text(new, encoding="utf-8")
    else:
        sep = "" if text.endswith("\n") else "\n"
        hot.write_text(text + f"{sep}\n{header}\n\n{body_line}", encoding="utf-8")


def _patch_index(vault: Path, wikilink: str) -> None:
    idx = vault / "index.md"
    line = f"- {wikilink}\n"
    if not idx.is_file():
        idx.write_text(f"# index\n\n{line}", encoding="utf-8")
        return
    text = idx.read_text(encoding="utf-8")
    if wikilink in text:
        return
    sep = "" if text.endswith("\n") else "\n"
    idx.write_text(text + sep + line, encoding="utf-8")


def _wikilink_for(path: Path, vault: Path) -> str:
    try:
        rel = path.relative_to(vault).with_suffix("")
    except ValueError:
        rel = Path(path.stem)
    return f"[[{rel.as_posix()}]]"


def _save_internal(
    kind: str,
    title: str,
    body: str,
    *,
    tags: list[str] | None = None,
    host: str | None = None,
    org: str | None = None,
    repo: str | None = None,
    source_sub: str | None = None,
    domain: str | None = None,
    source_meta: dict | None = None,
    extra_fm: dict | None = None,
) -> dict:
    """Shared write pipeline reused by handle_save and ingest tools.

    Pipeline: masking -> path resolve -> block-id -> frontmatter -> locked write
    -> patch hot/index. Returns dict with `path`, `block_ids`, `hits`.

    `source_meta` and `extra_fm` are stitched into frontmatter (source/meta keys)
    when provided.
    """
    for key, val in (("kind", kind), ("title", title), ("body", body)):
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"cortex_save: '{key}' required (non-empty string)")
    tags = list(tags or [])
    if not all(isinstance(t, str) for t in tags):
        raise ValueError("cortex_save: 'tags' must be list[str]")

    masking = _load_masking()
    masked_body, mask_hits = masking.mask(body)

    vault = resolve_vault()
    now = _dt.datetime.now()
    args = {"kind": kind, "title": title}
    if host is not None:
        args["host"] = host
    if org is not None:
        args["org"] = org
    if repo is not None:
        args["repo"] = repo
    if source_sub is not None:
        args["source_sub"] = source_sub
    if domain is not None:
        args["domain"] = domain
    target = _resolve_path(vault, args, now)
    target.parent.mkdir(parents=True, exist_ok=True)

    body_with_ids, block_ids = add_block_ids(masked_body)

    fm: dict[str, Any] = {
        "type": kind,
        "title": title,
        "created": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "tags": list(tags),
        "aliases": [],
    }
    if host is not None:
        fm["host"] = host
    if org is not None:
        fm["org"] = org
    if repo is not None:
        fm["repo"] = repo
    if domain is not None:
        fm["domain"] = domain
    if source_meta:
        fm["source"] = source_meta
    if extra_fm:
        for k, v in extra_fm.items():
            fm[k] = v
    # 强制 tags ≥ 10 (严禁占位符): 派生 fm + 正文派生
    fm["tags"] = _derive_tags(fm, masked_body)
    content = fm_dump(
        fm, body_with_ids if body_with_ids.endswith("\n") else body_with_ids + "\n"
    )

    lock_path = str(target) + ".lock"
    with file_lock(lock_path, timeout=5.0):
        target.write_text(content, encoding="utf-8")

    wikilink = _wikilink_for(target, vault)
    _patch_hot(vault, wikilink)
    _patch_index(vault, wikilink)

    return {
        "path": str(target),
        "block_ids": block_ids,
        "hits": len(mask_hits),
    }


def cli_save(args: dict) -> dict:
    """CLI entry: same shape as the old MCP handler, returns dict directly."""
    args = args or {}
    return _save_internal(
        kind=args.get("kind", ""),
        title=args.get("title", ""),
        body=args.get("body", ""),
        tags=args.get("tags") or [],
        host=args.get("host"),
        org=args.get("org"),
        repo=args.get("repo"),
        source_sub=args.get("source_sub"),
        domain=args.get("domain"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="cortex_save CLI: write a typed note into the vault.")
    parser.add_argument(
        "--kind",
        required=True,
        choices=[
            "entity", "concept", "project", "domain", "source",
            "reflection", "question", "fleeting", "inbox",
            "log", "journal",
        ],
        help="entity/concept → 知识库/领域/<域>/; project/domain → 知识库/项目/<host>/<org>/<repo>/; source → 知识库/收件箱/<host>-<slug>; reflection → 日记 一项; question/fleeting/inbox → 收件箱; log/journal → 日记/日/<YYYY-MM>/<YYYY-MM-DD>.md",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--body",
        help="Markdown body. If omitted, read from stdin.",
    )
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--host")
    parser.add_argument("--org")
    parser.add_argument("--repo")
    parser.add_argument(
        "--source-sub",
        dest="source_sub",
        default=None,
        help="(已废弃) source subdir, 旧字段保留兼容, 新版统一落 知识库/收件箱/",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="entity/concept 落档域 (创作/学习/工作/技术/生活/金融/...); 缺省 '未分类' (调用方/AI 应自决)",
    )
    ns = parser.parse_args()
    body = ns.body if ns.body is not None else sys.stdin.read()
    tags = [t.strip() for t in ns.tags.split(",") if t.strip()] if ns.tags else []
    result = cli_save(
        {
            "kind": ns.kind,
            "title": ns.title,
            "body": body,
            "tags": tags,
            "host": ns.host,
            "org": ns.org,
            "repo": ns.repo,
            "source_sub": ns.source_sub,
            "domain": ns.domain,
        }
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
