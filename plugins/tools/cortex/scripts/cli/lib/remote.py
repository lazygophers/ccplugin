"""Remote ingest helpers — git clone + website crawl (PR1, split from ingest_remote.py).

Pure helpers; no argparse / no top-level side effects. Imported by
`cli/ingest_remote.py`.
"""

from __future__ import annotations

import hashlib
import html.parser
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GITHUB_HOSTS = {"github.com", "gitlab.com"}
SITE_PLACEHOLDER = "_site"
DEFAULT_DEPTH = 3
GIT_TIMEOUT = 60
FETCH_TIMEOUT = 15
MAX_BYTES = 10 * 1024 * 1024
USER_AGENT = "cortex-mcp/0.1 (+ingest_remote)"

_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "target",
}

_SSH_RE = re.compile(
    r"^(?:ssh://)?(?:[^@]+@)?(?P<host>[^:/]+)[:/]+(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)
_HTTP_REPO_RE = re.compile(r"^/+(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


# ─────────── host routing ───────────


def detect_source_type(url: str) -> str:
    """github.com / gitlab.com -> git; 其他 (含 github.io / gitlab.io) -> website."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "").lower()
    if "@" in host:
        host = host.split("@", 1)[1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host == "github.com":
        return "github"
    if host == "gitlab.com":
        return "gitlab"
    return "website"


def parse_git_url(url: str) -> tuple[str, str, str]:
    """Parse github/gitlab URL -> (host, org, repo).

    Supports:
      https://github.com/foo/bar[.git]
      git@github.com:foo/bar.git
      ssh://git@github.com/foo/bar.git
    """
    url = url.strip()
    if url.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(url)
        host = (parsed.netloc or "").lower()
        m = _HTTP_REPO_RE.match(parsed.path or "")
        if not m:
            raise ValueError(f"cannot parse repo path: {url}")
        return (host, m.group("org"), m.group("repo"))
    m = _SSH_RE.match(url)
    if not m:
        raise ValueError(f"cannot parse git url: {url}")
    return (m.group("host").lower(), m.group("org"), m.group("repo"))


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-_.]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "index"


def route_target(source_type: str, url: str, vault: Path) -> Path:
    """github/gitlab -> 知识库/项目/<host>/<org>/<repo>; website -> .../<host>/_site/<slug>。"""
    if source_type in ("github", "gitlab"):
        host, org, repo = parse_git_url(url)
        return vault / "知识库" / "项目" / host / org / repo
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "unknown").lower()
    if ":" in host:
        host = host.split(":", 1)[0]
    path = (parsed.path or "/").strip("/")
    slug = slugify(path.split("/", 1)[0]) if path else slugify(host)
    return vault / "知识库" / "项目" / host / SITE_PLACEHOLDER / slug


# ─────────── scoring (PR3: AI 自评启发式) ───────────


# Host credibility 查表 (PR1 schema §3.1). 默认 4.0 (未知 host).
_HOST_CREDIBILITY: dict[str, float] = {
    # 官方 doc 10.0
    "anthropic.com": 10.0,
    "openai.com": 10.0,
    "google.com": 10.0,
    # 大厂 / 标准 doc 9.5
    "react.dev": 9.5,
    "docs.python.org": 9.5,
    "pytorch.org": 9.5,
    "vuejs.org": 9.5,
    "kernel.org": 9.5,
    "rust-lang.org": 9.5,
    "developer.mozilla.org": 9.5,
    "go.dev": 9.5,
    # 学术 8.5
    "arxiv.org": 8.5,
    "acm.org": 8.5,
    "ieee.org": 8.5,
    # 代码托管 7.5
    "github.com": 7.5,
    "gitlab.com": 7.5,
    # 技术问答 7.0
    "stackoverflow.com": 7.0,
    "serverfault.com": 7.0,
    # 知名博客 5.0
    "medium.com": 5.0,
    "dev.to": 5.0,
}
_HOST_CREDIBILITY_DEFAULT = 4.0


def host_credibility(host: str) -> float:
    """Host 白名单查表, 默认 4.0 (未知 host). 支持 www. 前缀剥离 + 子域父域回退."""
    if not host:
        return _HOST_CREDIBILITY_DEFAULT
    h = host.lower()
    if h.startswith("www."):
        h = h[4:]
    if h in _HOST_CREDIBILITY:
        return _HOST_CREDIBILITY[h]
    parts = h.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in _HOST_CREDIBILITY:
            return _HOST_CREDIBILITY[parent]
    return _HOST_CREDIBILITY_DEFAULT


def compute_initial_scores(
    *,
    host: str,
    coverage_ratio: float = 0.5,
    tag_count: int = 0,
    wikilink_count: int = 0,
    when_to_read_len: int = 0,
) -> dict[str, Any]:
    """落档时计算 4 评分字段初值 (启发式见 references/extract.md §3.1).

    Returns: {score, confidence, source_credibility, maturity}.
    """
    # score: coverage_ratio × 10, clamp [0, 10]
    score = max(0.0, min(10.0, round(coverage_ratio * 10, 1)))

    # confidence: tags (≥10=5) + when_to_read (≥30 字=3) + wikilink (≥5=2)
    tag_part = min(5.0, (tag_count / 10) * 5)
    wtr_part = min(3.0, (when_to_read_len / 30) * 3)
    link_part = min(2.0, (wikilink_count / 5) * 2)
    confidence = round(max(0.0, min(10.0, tag_part + wtr_part + link_part)), 1)

    source_credibility = host_credibility(host)

    if score < 5:
        maturity = "draft"
    elif score < 8:
        maturity = "review"
    else:
        maturity = "stable"

    return {
        "score": score,
        "confidence": confidence,
        "source_credibility": source_credibility,
        "maturity": maturity,
    }


# ─────────── aliases / keywords 召回率抽取 (PR3 P4) ───────────

# 中英翻译对 (常见技术术语 — 双向扩展)
_CN_EN_PAIRS = {
    "认证": "authentication",
    "授权": "authorization",
    "测试": "test",
    "部署": "deploy",
    "日志": "log",
    "配置": "config",
    "数据库": "database",
    "缓存": "cache",
    "队列": "queue",
    "中间件": "middleware",
    "网关": "gateway",
    "代理": "proxy",
    "前端": "frontend",
    "后端": "backend",
    "架构": "architecture",
    "决策": "decision",
    "陷阱": "pitfall",
    "依赖": "dependency",
    "错误码": "error code",
    "插件": "plugin",
    "模块": "module",
    "服务": "service",
    "接口": "interface",
}
_EN_CN_PAIRS = {v: k for k, v in _CN_EN_PAIRS.items()}

# 业内常见缩写↔全称
_ABBR_FULL = {
    "RBAC": "Role-Based Access Control",
    "JWT": "JSON Web Token",
    "OAuth": "Open Authorization",
    "API": "Application Programming Interface",
    "CRUD": "Create Read Update Delete",
    "ORM": "Object Relational Mapping",
    "MVC": "Model View Controller",
    "REST": "Representational State Transfer",
    "RPC": "Remote Procedure Call",
    "DDD": "Domain-Driven Design",
    "CI": "Continuous Integration",
    "CD": "Continuous Delivery",
    "MCP": "Model Context Protocol",
    "LLM": "Large Language Model",
    "SDK": "Software Development Kit",
    "CLI": "Command Line Interface",
}
_FULL_ABBR = {v: k for k, v in _ABBR_FULL.items()}

# 代码标识符正则: snake_case / 长名识别 (≥3 chars, 含 _ 或全 lower)
_IDENT_RE = re.compile(r"\b[a-z_][a-z0-9_]{2,}\b")
_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```")


def extract_aliases(title: str, desc: str) -> list[str]:
    """从 title + desc 抽 ≥ 3 个 aliases (启发式, 无 AI 调用).

    规则:
    - 中→英 / 英→中 翻译对
    - 缩写↔全称对 (大小写不敏感匹配)
    - 不足 3 时, 补 title 中长词 (≥ 3 字符)
    """
    out: list[str] = []
    text_l = f"{title} {desc}".lower()

    # 中→英 (中文不下沉到 lower)
    text_raw = f"{title} {desc}"
    for cn, en in _CN_EN_PAIRS.items():
        if cn in text_raw and en not in out:
            out.append(en)
        if en.lower() in text_l and cn not in out:
            out.append(cn)

    # 缩写 ↔ 全称
    for abbr, full in _ABBR_FULL.items():
        if abbr.lower() in text_l and full not in out:
            out.append(full)
        if full.lower() in text_l and abbr not in out:
            out.append(abbr)

    # 不足 3 个: 补 title 词
    if len(out) < 3 and title:
        words = re.findall(r"\b\w{3,}\b", title)
        for w in words:
            if w not in out:
                out.append(w)
            if len(out) >= 3:
                break

    return out[:10]


def extract_keywords(
    title: str,
    body: str,
    path: str,
    host: str = "",
    org: str = "",
    repo: str = "",
) -> list[str]:
    """从 body / path / metadata 抽 ≥ 5 keywords (启发式, 无 AI 调用).

    规则:
    1. path 文件名 stem (`auth_middleware.py` → `auth_middleware`)
    2. project metadata: repo / org / host
    3. body 内代码标识符 (优先 fenced code 内, 频次 top 5)
    4. heading text top 3 (`## Foo Bar` → `Foo Bar`)
    """
    out: list[str] = []

    # 1. path stem
    if path:
        stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if stem:
            out.append(stem)

    # 2. repo / org / host
    for v in (repo, org, host):
        if v and v not in out:
            out.append(v)

    # 3. 代码标识符: 优先 fenced code 内; 无 fence 则用全文剥 fence 后扫
    fence_blocks = _CODE_FENCE_RE.findall(body or "")
    if fence_blocks:
        scan_text = "\n".join(fence_blocks)
    else:
        scan_text = _CODE_FENCE_RE.sub("", body or "")

    idents: dict[str, int] = {}
    for m in _IDENT_RE.finditer(scan_text):
        tok = m.group(0)
        idents[tok] = idents.get(tok, 0) + 1
    for ident, _count in sorted(idents.items(), key=lambda x: -x[1])[:5]:
        if ident not in out:
            out.append(ident)

    # 4. headings top 3
    headings = re.findall(r"^#+\s+(.+?)\s*$", body or "", re.MULTILINE)
    for h in headings[:3]:
        h_clean = h.strip()
        if h_clean and h_clean not in out and len(out) < 20:
            out.append(h_clean)

    return out[:20]


# 记忆 L0-L4 层默认 importance / confidence (PR1 scoring.md §default)
_L_LEVEL_DEFAULTS: dict[str, dict[str, float]] = {
    "L0": {"importance": 9.0, "confidence": 9.5},
    "L1": {"importance": 7.0, "confidence": 8.0},
    "L2": {"importance": 5.0, "confidence": 6.5},
    "L3": {"importance": 3.0, "confidence": 4.5},
    "L4": {"importance": 2.0, "confidence": 5.0},
}


def compute_memory_scores(
    *,
    level: str,
    user_confirmed: bool = False,
    body_len: int = 0,
) -> dict[str, float]:
    """计算记忆 2 字段初值 (importance / confidence). 按 L0-L4 层默认 + 修正."""
    base = _L_LEVEL_DEFAULTS.get(level, _L_LEVEL_DEFAULTS["L3"])
    importance = base["importance"]
    confidence = base["confidence"]

    if user_confirmed:
        confidence = min(10.0, confidence + 1.0)

    if body_len < 100:
        importance = max(0.0, importance - 0.5)

    return {
        "importance": round(importance, 1),
        "confidence": round(confidence, 1),
    }


# ─────────── filter loaders (mirror ingest_url.py) ───────────


def load_filter_module(filename: str, mod_name: str) -> Any:
    here = Path(__file__).resolve()
    # cli/lib/remote.py -> cli/lib -> cli -> scripts -> scripts/hooks/_lib/<filename>
    candidate = here.parent.parent.parent / "hooks" / "_lib" / filename
    if not candidate.is_file():
        cfg = Path.home() / ".cortex" / "config.json"
        hint = None
        if cfg.is_file():
            try:
                hint = json.loads(cfg.read_text(encoding="utf-8")).get("install_path")
            except Exception:
                hint = None
        if hint:
            candidate = Path(hint).expanduser() / "hooks" / "_lib" / filename
    if not candidate.is_file():
        raise RuntimeError(f"{filename} not found at {candidate}")
    spec = importlib.util.spec_from_file_location(mod_name, candidate)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {filename}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump_fm(fm: dict, body: str) -> str:
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


# ─────────── git clone path ───────────


def run_git(
    args: list[str], cwd: Path | None = None, timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def enumerate_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in _IGNORE_DIRS for part in p.relative_to(root).parts):
            continue
        out.append(p)
    return out


def ingest_git(url: str, target: Path, dry_run: bool) -> dict:
    """Shallow clone repo + write per-file .md notes. fail-soft (no raise)."""
    try:
        host, org, repo = parse_git_url(url)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    source_type = "github" if host == "github.com" else "gitlab"

    if dry_run:
        return {
            "ok": True,
            "source_type": source_type,
            "host": host,
            "org": org,
            "repo": repo,
            "target": str(target),
            "dry_run": True,
        }

    tmpdir = Path(tempfile.mkdtemp(prefix="cortex-clone-"))
    try:
        proc = run_git(["clone", "--depth=1", url, str(tmpdir)])
        if proc.returncode != 0:
            return {
                "ok": False,
                "error": f"git clone failed: {proc.stderr.strip()[:200]}",
            }
        sha_proc = run_git(["rev-parse", "HEAD"], cwd=tmpdir)
        sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else ""

        target.mkdir(parents=True, exist_ok=True)
        files = enumerate_files(tmpdir)
        ingested: list[str] = []
        errors: list[str] = []
        for fp in files:
            rel = fp.relative_to(tmpdir)
            dest = target / "源" / rel.with_suffix(rel.suffix + ".md")
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                errors.append(f"{rel}: {exc}")
                continue
            fm = {
                "source_url": url,
                "source_type": source_type,
                "source_path": str(rel),
                "last_commit_sha": sha,
                "last_ingested_at": utc_now(),
            }
            fm.update(
                compute_initial_scores(
                    host=host,
                    coverage_ratio=1.0,
                    tag_count=0,
                    wikilink_count=0,
                    when_to_read_len=0,
                )
            )
            body = f"# {rel}\n\n```\n{content}\n```\n"
            aliases = extract_aliases(str(rel), "")
            keywords = extract_keywords(
                title=str(rel),
                body=body,
                path=str(rel),
                host=host,
                org=org,
                repo=repo,
            )
            if aliases:
                fm["aliases"] = aliases
            if keywords:
                fm["keywords"] = keywords
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(dump_fm(fm, body), encoding="utf-8")
            ingested.append(str(rel))

        idx = target / "_index.md"
        if not idx.is_file():
            idx_fm = {
                "source_url": url,
                "source_type": source_type,
                "last_commit_sha": sha,
                "last_ingested_at": utc_now(),
            }
            idx_fm.update(
                compute_initial_scores(
                    host=host,
                    coverage_ratio=1.0,
                    tag_count=0,
                    wikilink_count=0,
                    when_to_read_len=0,
                )
            )
            idx_title = f"{org}/{repo}"
            idx_aliases = extract_aliases(idx_title, "")
            idx_keywords = extract_keywords(
                title=idx_title,
                body="",
                path="_index.md",
                host=host,
                org=org,
                repo=repo,
            )
            if idx_aliases:
                idx_fm["aliases"] = idx_aliases
            if idx_keywords:
                idx_fm["keywords"] = idx_keywords
            idx.write_text(
                dump_fm(
                    idx_fm,
                    f"# {org}/{repo}\n\nClone of `{url}` (depth=1, sha=`{sha[:8]}`)。\n",
                ),
                encoding="utf-8",
            )

        return {
            "ok": True,
            "source_type": source_type,
            "host": host,
            "org": org,
            "repo": repo,
            "target": str(target),
            "last_commit_sha": sha,
            "files_ingested": len(ingested),
            "errors": errors,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"git clone timeout after {GIT_TIMEOUT}s"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─────────── website crawl path ───────────


class _LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for k, v in attrs:
            if k.lower() == "href" and v:
                self.links.append(v)


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:  # noqa: S310
        ct = resp.headers.get("Content-Type", "")
        raw = resp.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise RuntimeError(f"payload exceeds {MAX_BYTES} bytes")
    return raw, ct


def parse_sitemap(xml_bytes: bytes) -> list[str]:
    text = xml_bytes.decode("utf-8", errors="replace")
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)


def discover_urls(base_url: str, depth: int, url_security: Any) -> list[str]:
    """Sitemap first, fallback BFS <a href>."""
    parsed = urllib.parse.urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    for sm_path in ("/sitemap.xml", "/sitemap_index.xml"):
        sm_url = origin + sm_path
        safe, _ = url_security.is_safe(sm_url)
        if not safe:
            continue
        try:
            raw, _ = fetch_bytes(sm_url)
            urls = parse_sitemap(raw)
            if urls:
                return [
                    u for u in urls if urllib.parse.urlparse(u).netloc == parsed.netloc
                ]
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError):
            continue

    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(base_url, 0)]
    out: list[str] = []
    while queue:
        cur, d = queue.pop(0)
        if cur in seen or d > depth:
            continue
        seen.add(cur)
        safe, _ = url_security.is_safe(cur)
        if not safe:
            continue
        try:
            raw, ct = fetch_bytes(cur)
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError):
            continue
        out.append(cur)
        if "html" not in ct.lower():
            continue
        parser = _LinkParser()
        try:
            parser.feed(raw.decode("utf-8", errors="replace"))
        except Exception:
            continue
        for href in parser.links:
            absolute = urllib.parse.urljoin(cur, href)
            ap = urllib.parse.urlparse(absolute)
            if ap.netloc != parsed.netloc:
                continue
            absolute = absolute.split("#", 1)[0]
            if absolute not in seen:
                queue.append((absolute, d + 1))
    return out


def ingest_website(url: str, target: Path, depth: int, dry_run: bool) -> dict:
    url_security = load_filter_module("url_security.py", "cortex_url_security")
    safe, reason = url_security.is_safe(url)
    if not safe:
        return {"ok": False, "error": f"url_security rejected: {reason}"}

    if dry_run:
        return {
            "ok": True,
            "source_type": "website",
            "target": str(target),
            "dry_run": True,
        }

    html_sanitize = load_filter_module("html_sanitize.py", "cortex_html_sanitize")
    masking = load_filter_module("masking.py", "cortex_masking")

    urls = discover_urls(url, depth, url_security)
    if not urls:
        urls = [url]

    target.mkdir(parents=True, exist_ok=True)
    ingested: list[str] = []
    errors: list[str] = []
    for page_url in urls:
        try:
            raw, ct = fetch_bytes(page_url)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{page_url}: fetch error: {exc}")
            continue
        if "html" not in (ct or "").lower() and not page_url.lower().endswith(
            (".html", ".htm", "/")
        ):
            errors.append(f"{page_url}: non-html content-type: {ct}")
            continue
        try:
            body_text = raw.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{page_url}: decode error: {exc}")
            continue
        sanitized = html_sanitize.sanitize(body_text)
        masked, _hits = masking.mask(sanitized)
        content_hash = hashlib.sha256(masked.encode("utf-8")).hexdigest()
        page_slug = slugify(urllib.parse.urlparse(page_url).path or "/")
        dest = target / f"{page_slug}.md"
        fm = {
            "source_url": page_url,
            "source_type": "website",
            "content_hash": content_hash,
            "last_ingested_at": utc_now(),
        }
        page_host = (urllib.parse.urlparse(page_url).netloc or "").lower()
        fm.update(
            compute_initial_scores(
                host=page_host,
                coverage_ratio=0.7,
                tag_count=0,
                wikilink_count=0,
                when_to_read_len=0,
            )
        )
        page_aliases = extract_aliases(page_slug, "")
        page_keywords = extract_keywords(
            title=page_slug,
            body=masked,
            path=f"{page_slug}.md",
            host=page_host,
        )
        if page_aliases:
            fm["aliases"] = page_aliases
        if page_keywords:
            fm["keywords"] = page_keywords
        dest.write_text(dump_fm(fm, masked), encoding="utf-8")
        ingested.append(page_url)

    return {
        "ok": True,
        "source_type": "website",
        "target": str(target),
        "pages_ingested": len(ingested),
        "errors": errors,
    }
