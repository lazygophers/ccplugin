#!/usr/bin/env python3
"""cortex schema v3 一次性迁移 — 补 aliases / keywords frontmatter.

迁移内容 (启发式抽, 不调 AI; 复用 lib/remote.py):
- 目标: 知识库/项目/, 知识库/领域/, 知识库/日记/, 记忆/L0-L3
- 跳过: .obsidian/, 归档/, .trash/, _meta/, _templates/, _assets/, 知识库/收件箱/, 记忆/L4-*
- 缺 aliases → 用 `extract_aliases(title, desc)` 补 ≥ 3
- 缺 keywords → 用 `extract_keywords(title, body, path, host, org, repo)` 补 ≥ 5

CLI:
    migrate_aliases_keywords_to_v3.py --vault PATH [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

# import lib.frontmatter / lib.remote (与 v2 同 sys.path 套路)
_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parent.parent / "cli"))

from lib.frontmatter import dump as _fm_dump  # noqa: E402
from lib.frontmatter import parse as _fm_parse  # noqa: E402
from lib.remote import extract_aliases, extract_keywords  # noqa: E402
from lib.vault_path import resolve_vault as _resolve_vault  # noqa: E402

_SKIP_PATTERNS = (
    ".obsidian/",
    "归档/",
    ".trash/",
    "_meta/",
    "_templates/",
    "_assets/",
    "知识库/收件箱/",
    "记忆/L4-",
)
_TARGET_PATTERNS = (
    "知识库/项目/",
    "知识库/领域/",
    "知识库/日记/",
    "记忆/L0-",
    "记忆/L1-",
    "记忆/L2-",
    "记忆/L3-",
)


def _should_process(rel_str: str) -> bool:
    if any(p in rel_str for p in _SKIP_PATTERNS):
        return False
    return any(rel_str.startswith(p) for p in _TARGET_PATTERNS)


def _derive_project_meta(rel_str: str) -> tuple[str, str, str]:
    """从 path 推 host/org/repo (best effort, 非项目路径返空)."""
    parts = rel_str.replace("\\", "/").split("/")
    for i in range(len(parts) - 4):
        if parts[i] == "知识库" and parts[i + 1] == "项目":
            return parts[i + 2], parts[i + 3], parts[i + 4]
    return "", "", ""


def _migrate_file(
    rel: Path,
    vault: Path,
    dry_run: bool,
) -> dict[str, Any]:
    abs_path = vault / rel
    try:
        content = abs_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        return {"status": "error", "error": str(e)}

    fm, body = _fm_parse(content)
    if not fm:
        return {"status": "skip", "reason": "no_frontmatter"}

    added: list[str] = []
    rel_str = str(rel).replace("\\", "/")

    # aliases
    cur_aliases = fm.get("aliases")
    if not cur_aliases:
        title = str(fm.get("title", rel.stem))
        desc = str(fm.get("desc", "") or fm.get("description", "") or "")
        aliases = extract_aliases(title, desc)
        if aliases:
            fm["aliases"] = aliases
            added.append("aliases")

    # keywords
    cur_keywords = fm.get("keywords")
    if not cur_keywords:
        title = str(fm.get("title", rel.stem))
        host, org, repo = _derive_project_meta(rel_str)
        keywords = extract_keywords(
            title=title,
            body=body or "",
            path=rel_str,
            host=host,
            org=org,
            repo=repo,
        )
        if keywords:
            fm["keywords"] = keywords
            added.append("keywords")

    if not added:
        return {"status": "skip", "reason": "already_has"}

    if dry_run:
        return {"status": "changed", "added": added, "dry_run": True}

    try:
        abs_path.write_text(_fm_dump(fm, body), encoding="utf-8")
    except OSError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "changed", "added": added}


def _backup_vault(vault: Path) -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path("/tmp") / f"cortex-migration-backup-v3-{ts}.tar.gz"
    try:
        with tarfile.open(out, "w:gz") as tar:
            tar.add(str(vault), arcname=vault.name)
    except (OSError, tarfile.TarError) as e:
        try:
            subprocess.run(
                ["tar", "czf", str(out), "-C", str(vault.parent), vault.name],
                check=True,
                capture_output=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"backup failed: {e}; tar fallback: {exc}") from exc
    return out


def migrate(
    vault: Path,
    *,
    dry_run: bool = False,
    backup: bool = True,
) -> dict[str, Any]:
    """主入口。返回 JSON-ready dict。"""
    result: dict[str, Any] = {
        "vault": str(vault),
        "dry_run": dry_run,
        "backup_path": None,
        "files_scanned": 0,
        "files_changed": 0,
        "aliases_added": 0,
        "keywords_added": 0,
        "errors": [],
    }
    if not vault.is_dir():
        result["errors"].append(f"vault not found: {vault}")
        return result

    if backup and not dry_run:
        try:
            bpath = _backup_vault(vault)
            result["backup_path"] = str(bpath)
        except RuntimeError as e:
            result["errors"].append(str(e))
            return result

    for md in vault.rglob("*.md"):
        try:
            rel = md.relative_to(vault)
        except ValueError:
            continue
        rel_str = str(rel).replace("\\", "/")
        if not _should_process(rel_str):
            continue
        result["files_scanned"] += 1
        try:
            r = _migrate_file(rel, vault, dry_run)
        except Exception as e:  # noqa: BLE001
            result["errors"].append({"path": rel_str, "error": str(e)})
            continue
        if r["status"] == "changed":
            result["files_changed"] += 1
            added = r.get("added", [])
            if "aliases" in added:
                result["aliases_added"] += 1
            if "keywords" in added:
                result["keywords_added"] += 1
        elif r["status"] == "error":
            result["errors"].append({"path": rel_str, "error": r.get("error")})

    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="cortex migration v3 - 补 aliases/keywords frontmatter (启发式)"
    )
    ap.add_argument("--vault", help="vault path (默认 resolve_vault)")
    ap.add_argument(
        "--to",
        default="v3",
        help="target schema version (only 'v3' supported)",
    )
    ap.add_argument("--dry-run", action="store_true", help="scan only, no writes")
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="skip tar.gz backup (默认开)",
    )
    ns = ap.parse_args()
    if ns.to != "v3":
        print(
            json.dumps({"error": f"unsupported --to={ns.to}; only 'v3' is supported"}),
            file=sys.stderr,
        )
        return 2

    if ns.vault:
        vault = Path(ns.vault).expanduser().resolve()
    else:
        v = _resolve_vault()
        if v is None:
            print(
                json.dumps({"error": "vault not found; pass --vault or set config"}),
                file=sys.stderr,
            )
            return 2
        vault = v

    result = migrate(
        vault,
        dry_run=ns.dry_run,
        backup=not ns.no_backup,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    sys.exit(main())
