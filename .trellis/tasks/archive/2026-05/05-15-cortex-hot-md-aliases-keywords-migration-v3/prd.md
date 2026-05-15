# cortex 收尾 — hot.md 项目高分子页 + aliases/keywords migration v3

## Goal

补完上批 PR 留 2 TODO:

1. **hot.md 项目高分子页维护** (上批 PR3 R6.3 标 TODO) — save/ingest 落档时若 score ≥ 7.0 + maturity in (stable/review) → 入 hot.md `## 项目高分页面` 节, ≤ 3 / 项目 (按 score 排序保留最新)
2. **aliases/keywords migration v3** — migrate_scores_to_v2 升级到 v3, 老文件自动补 aliases/keywords (启发式抽取, 不依赖 AI 重写)

## What I already know

### hot.md 现状

- vault 内 `hot.md` 是顶层文件 (不在 `记忆/working/` 下, 直接 `/hot.md`)
- 现 `save.py:_patch_hot` 仅 prepend wikilink, 无 section / 排序 / 限项目
- 用户真实 hot.md frontmatter: `type: meta, title: hot, tags: [activity, context, daily, digest, recent]`

### Migration v2 现状

`scripts/migrate/migrate_scores_to_v2.py` (335 行) 处理:
- score 1-5 → 0-10 × 2.0
- patterns confidence 0-1 → 0-10 × 10
- 缺评分字段加 stub

不动 aliases/keywords。

### lib/remote.py 已有

PR3 上批已加 `extract_aliases` (中英对 23 + 缩写 16) + `extract_keywords` (path/repo/idents/headings)。本 PR 复用。

## Decision (ADR-lite)

**Decision**:
- D1: hot.md `## 项目高分页面` 节维护放 save.py + 集成到 ingest_remote (而非新 helper script), 复用 `_patch_hot` 同位置
- D2: migration v3 单独命令 `migrate_aliases_keywords_to_v3.py`, 不与 v2 合并 (v2 一次性已跑过, v3 再加, 各做各的)
- D3: migration v3 用 lib/remote.py 既有 `extract_aliases` / `extract_keywords` (启发式), 不调 AI 重写
- D4: 阈值: hot.md 子页 `score >= 7.0 AND maturity in {stable, review}` (用户 PR3 R6.3 定)

**Consequences**:
- save.py 行数加 ~50 (新 `_patch_hot_project_subpages`)
- 新 migrate v3 script ~250 行
- 不动 v2 已跑过的字段, 不重复 score migration

## Requirements

### R1: hot.md 项目高分子页维护

#### F1.1 `scripts/cli/save.py` 加 `_patch_hot_project_subpages`

```python
_HOT_PROJECT_SECTION = "## 项目高分页面"
_HOT_PROJECT_MAX = 3  # 每项目最多 3 篇

def _patch_hot_project_subpages(
    vault: Path,
    project_key: str,  # "host/org/repo" 三段
    wikilink: str,
    score: float,
    maturity: str,
) -> None:
    """高分页 (score ≥ 7 + maturity in stable/review) 入 hot.md `## 项目高分页面` 节.
    
    每项目 ≤ 3 篇, 按 score desc + updated desc 保留 top.
    """
    if score < 7.0 or maturity not in {"stable", "review"}:
        return
    
    hot = vault / "hot.md"
    if not hot.is_file():
        return  # 无 hot.md (新 vault), 跳过 — _patch_hot 已会创建主结构
    
    text = hot.read_text(encoding="utf-8")
    
    # 找/建 ## 项目高分页面 节
    if _HOT_PROJECT_SECTION not in text:
        text += f"\n\n{_HOT_PROJECT_SECTION}\n\n"
    
    # 找 project_key 子段 (`### <host/org/repo>`)
    project_heading = f"### {project_key}"
    
    # 解析现有 project_heading 下 ≤ 3 行 wikilink
    lines = text.split("\n")
    proj_start = None
    proj_end = None
    for i, ln in enumerate(lines):
        if ln.strip() == project_heading:
            proj_start = i + 1
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("#"):
                    proj_end = j
                    break
            else:
                proj_end = len(lines)
            break
    
    if proj_start is None:
        # 项目不存在, 在 ## 项目高分页面 节末尾加新子段
        sect_idx = next(i for i, ln in enumerate(lines) if ln.strip() == _HOT_PROJECT_SECTION)
        # 找节末 (下个 ## 或 EOF)
        sect_end = len(lines)
        for j in range(sect_idx + 1, len(lines)):
            if lines[j].startswith("## ") and lines[j].strip() != _HOT_PROJECT_SECTION:
                sect_end = j
                break
        insert_at = sect_end
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, project_heading)
        lines.insert(insert_at + 2, f"- {wikilink} (score: {score}, {maturity})")
    else:
        # 项目存在, 收集现有 wikilink 行 + 加新
        proj_lines = lines[proj_start:proj_end]
        existing = [ln for ln in proj_lines if ln.strip().startswith("- ")]
        new_entry = f"- {wikilink} (score: {score}, {maturity})"
        # 去重: 同 wikilink 替换, 否则 append
        existing = [ln for ln in existing if wikilink not in ln]
        existing.append(new_entry)
        # 取 top _HOT_PROJECT_MAX (按 score desc, 简单提 score 数字排序)
        existing.sort(key=lambda ln: _extract_score_from_line(ln), reverse=True)
        existing = existing[:_HOT_PROJECT_MAX]
        # 替换原项目子段
        new_proj_lines = [project_heading, "", *existing]
        lines = lines[:proj_start - 1] + new_proj_lines + (["",] if proj_end < len(lines) else []) + lines[proj_end:]
    
    hot.write_text("\n".join(lines), encoding="utf-8")


def _extract_score_from_line(line: str) -> float:
    """提 wikilink 行内 score 值, fallback 0."""
    m = re.search(r"score:\s*([\d.]+)", line)
    return float(m.group(1)) if m else 0.0
```

#### F1.2 save.py 集成调用

`_save_internal` 内 `_patch_hot(vault, wikilink)` 后追加:

```python
if score >= 7.0 and maturity in {"stable", "review"} and kind in {"project", "domain"}:
    # 取 project_key (host/org/repo)
    project_key = _derive_project_key(path)  # 从 vault 路径推
    if project_key:
        _patch_hot_project_subpages(vault, project_key, wikilink, score, maturity)
```

`_derive_project_key` helper: 从 `知识库/项目/<host>/<org>/<repo>/...` 路径取前 3 段, 不是项目路径返 None。

#### F1.3 ingest_remote 集成 (lib/remote.py)

ingest_git / ingest_website 落每页时, 同样调 `_patch_hot_project_subpages` (导入)。或更简: ingest 落每页走 save.py CLI 链路, 自动触发。如不走 save.py, 加同 hook。

### R2: aliases/keywords migration v3

#### F2.1 新 `scripts/migrate/migrate_aliases_keywords_to_v3.py`

```python
"""一次性 migration v3: 老 .md 加 aliases (≥3) + keywords (≥5) frontmatter.

复用 lib/remote.py extract_aliases / extract_keywords 启发式 (不调 AI).
"""

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "cli"))

from lib.remote import extract_aliases, extract_keywords  # type: ignore


SKIP_PATTERNS = (
    ".obsidian/", "归档/", ".trash/", "_meta/", "_templates/", "_assets/",
    "知识库/收件箱/",
)
TARGET_PATTERNS = ("知识库/项目/", "知识库/领域/", "知识库/日记/")


def _should_process(rel_str: str) -> bool:
    if any(p in rel_str for p in SKIP_PATTERNS):
        return False
    if not any(rel_str.startswith(p) for p in TARGET_PATTERNS):
        return False
    return True


def migrate_file(rel: Path, vault: Path, dry_run: bool) -> dict:
    """单文件 migrate: 缺 aliases → 加, 缺 keywords → 加.
    
    返 {status: changed|skip|error, added: [aliases|keywords|both]}
    """
    abs_path = vault / rel
    content = abs_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = _split_frontmatter(content)  # 复用 lib helper
    if fm is None:
        return {"status": "skip", "reason": "no_frontmatter"}
    
    added = []
    
    if "aliases" not in fm or not fm["aliases"]:
        title = fm.get("title", rel.stem)
        desc = fm.get("desc", "")
        aliases = extract_aliases(str(title), str(desc))
        if aliases:
            fm["aliases"] = aliases
            added.append("aliases")
    
    if "keywords" not in fm or not fm["keywords"]:
        title = fm.get("title", rel.stem)
        # path 推 host/org/repo (best effort, 老文件不一定有)
        parts = str(rel).split("/")
        host, org, repo = "", "", ""
        if len(parts) >= 5 and parts[0] == "知识库" and parts[1] == "项目":
            host, org, repo = parts[2], parts[3], parts[4]
        keywords = extract_keywords(
            title=str(title),
            body=body or "",
            path=str(rel),
            host=host, org=org, repo=repo,
        )
        if keywords:
            fm["keywords"] = keywords
            added.append("keywords")
    
    if not added:
        return {"status": "skip", "reason": "already_has"}
    
    if dry_run:
        return {"status": "changed", "added": added, "dry_run": True}
    
    new_content = _rebuild_frontmatter(fm, body)
    abs_path.write_text(new_content, encoding="utf-8")
    return {"status": "changed", "added": added}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true", default=True)
    parser.add_argument("--no-backup", dest="backup", action="store_false")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()
    
    vault = Path(args.vault) if args.vault else resolve_vault()
    
    backup_path = None
    if args.backup and not args.dry_run:
        backup_path = _create_backup(vault)
    
    results = {"files_scanned": 0, "files_changed": 0, "aliases_added": 0, "keywords_added": 0, "errors": []}
    
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        rel_str = str(rel).replace("\\", "/")
        if not _should_process(rel_str):
            continue
        results["files_scanned"] += 1
        try:
            r = migrate_file(rel, vault, args.dry_run)
            if r["status"] == "changed":
                results["files_changed"] += 1
                if "aliases" in r.get("added", []):
                    results["aliases_added"] += 1
                if "keywords" in r.get("added", []):
                    results["keywords_added"] += 1
        except Exception as e:
            results["errors"].append({"path": str(rel), "error": str(e)})
    
    results["vault"] = str(vault)
    results["dry_run"] = args.dry_run
    results["backup_path"] = str(backup_path) if backup_path else None
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0
```

≤ 300 行。

#### F2.2 wrapper `scripts/migrate_v3.sh` (新, 或扩既有 migrate.sh)

复用既有 `migrate.sh` 加 sub-command 分发:

```bash
# migrate.sh --to=v2 (现有)
# migrate.sh --to=v3 (新, 走 migrate_aliases_keywords_to_v3.py)
```

读 migrate.sh, case "$1" 加 v3 分支。

### R3: 测试 + docs/memory 同步

#### F3.1 测试

- `tests/python/test_hot_md_project_subpages.py` (≥ 8 case): score 阈值过滤 / maturity 过滤 / 项目子段创建 / 排序保 top 3 / 同 wikilink 替换 / 非项目路径返 / hot.md 不存在跳过 / 无 ## 项目高分页面 节自动创建
- `tests/python/test_migrate_aliases_keywords.py` (≥ 8 case): 缺 aliases 加 / 缺 keywords 加 / 都缺加都 / 都有跳 / non-target 路径跳 / dry-run 不写盘 / backup 创建 / 老 frontmatter 无 title 用 stem

#### F3.2 docs/memory

- `docs/快速上手.md` 加 `bash ~/.cortex/scripts/migrate.sh --to=v3` 示例
- `docs/故障排查.md` 加 v3 migration 失败排查 (复用 v2 模式)
- `.claude/memory/cortex-plugin-2026-05-13.md` 加 §P10 (hot.md 高分子页 + migration v3)

## Acceptance Criteria

- [ ] save.py `_patch_hot_project_subpages` 实现 + 集成
- [ ] migrate_aliases_keywords_to_v3.py 实现
- [ ] migrate.sh 加 --to=v3 分支
- [ ] 2 测试文件 (≥ 16 case 合计)
- [ ] pytest 524 → ≥ 540 (≥ +16)
- [ ] ruff clean
- [ ] docs/memory P10 同步
- [ ] dry-run smoke: hot.md project subpages 干跑 + migrate v3 dry-run 真 vault

## Definition of Done

- pytest 全绿
- ruff clean
- migrate v3 真 vault dry-run 报合理 changed 数
- hot.md smoke: 写多个 score 7/8/9 不同项目 → hot.md 节正确 grouping
- git commit (拆 3 commits: hot.md / migration v3 / docs)

## Out of Scope

- 不动评分字段实现 (上批 PR P8)
- 不动 MCP 契约 (P9)
- 不破坏 524 测试基线
- 不实现 AI 重写 aliases/keywords (启发式即可, 复用 lib/remote.py)
- 不删 v2 migration script (留, 用户可独立跑)

## Technical Notes

- hot.md 路径: vault 根 `hot.md` (不是 `记忆/working/hot.md`)
- save.py 现有 `_patch_hot` 简单 prepend, **不动**, 仅在其后追加调 `_patch_hot_project_subpages`
- migrate v3 复用 lib/remote.py extract helper, 不重写
