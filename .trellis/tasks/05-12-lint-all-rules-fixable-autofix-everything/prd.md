# PRD — lint 全规则 fixable + autofix, 零人工

## 痛点

跑 `lint.sh` 后:
- vault 仍含 `记忆体系/` (vault-structure-violation 只报不执行)
- 91 dead-wikilink / 50 duplicate-alias / 266 orphan-page / 147 callout-unknown-type / 11 path-naming-violation / 3 i18n-path-not-in-locale 留人工处理

User 要求: **零人工**, AI 默认推荐方案直接执行。

## 当前状态 (实跑)

| rule | severity | fixable | count |
|------|----------|---------|-------|
| dead-wikilink | error | ✓ true | 91 (剩) — cap 限制 |
| duplicate-alias | error | ✓ true | 50 (剩) — 未全 fix |
| vault-structure-violation | error | ✗ false | 1 |
| frontmatter-schema-violation | warn | ✓ true | 310 |
| orphan-page | warn | ✗ false | 266 |
| callout-unknown-type | warn | ✗ false | 147 |
| vault-misaligned | warn | ✓ true | 43 |
| template-outdated | warn | ✓ true | 31 |
| fm-missing-created | warn | ✓ true | 21 |
| path-naming-violation | warn | ✗ false | 11 |
| title-h1-mismatch | warn | ✓ true | 7 |
| i18n-path-not-in-locale | warn | ✗ false | 3 |

5 规则 fixable=false 必须改 true + 实现 fix。

## 目标

每条规则推荐 autofix 方案:

### 1. `vault-structure-violation` → fixable=true
执行 mv_plan: mv 违规路径到 `~/.cache/cortex/lint-backup/<hash>/structure-<ts>/`。已有 plan, 缺 exec。

### 2. `callout-unknown-type` → fixable=true
未知 callout type → 改为 `info` (Obsidian 标准默认)。例: `> [!unknown]` → `> [!info]`。

### 3. `orphan-page` → fixable=true
孤儿页 (没任何文件链接到) → mv 到 `知识库/收件箱/`。如果已在收件箱 → 加到同目录 `_index.md` 末尾 wikilink。

### 4. `path-naming-violation` → fixable=true
路径名违规 (e.g. 含空格/特殊字符) → rename 到 slug-safe 形式 (空格→-, 特殊字符→_)。

### 5. `i18n-path-not-in-locale` → fixable=true
路径包含非 vault.lang 字符 → 同 path-naming-violation 处理 (slug)。

### 6. dead-wikilink / duplicate-alias 剩余
- 提升 stub cap 100 → 1000 (覆盖 91 dead-link)
- duplicate-alias 排查为啥没 fix 50 个 (msg parse 失败? alias 取不到?)

## 设计

### lint/run.py 改动

#### vault-structure-violation fixable=true + _fix
```python
def _fix_vault_structure_violation(finding, vault, plugin_root, backup_dir):
    """mv 违规路径到 backup_dir (structure_purge 已 plan)."""
    import shutil
    rel = finding["file"]
    src = vault / rel
    if not src.exists():
        return False
    # 计算 structure backup root
    structure_root = _get_backup_root(vault).parent / f"structure-{_now_ts()}"
    structure_root.mkdir(parents=True, exist_ok=True)
    dst = structure_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return True
```

#### callout-unknown-type fixable=true + _fix
```python
def _fix_callout_unknown_type(finding, vault, plugin_root, backup_dir):
    """未知 callout type → info."""
    import re
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    text = p.read_text()
    # 备份
    bak = backup_dir / rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    bak.write_text(text)
    # 替换 [!<unknown>] → [!info]
    # finding.msg 提示具体 type? 或全局替换非标准
    STANDARD = {"info","tip","warning","note","abstract","summary","todo",
                "success","question","failure","danger","bug","example","quote"}
    def _sub(m):
        ctype = m.group(1).lower()
        if ctype in STANDARD:
            return m.group(0)
        return m.group(0).replace(m.group(1), "info", 1)
    new = re.sub(r"\[!([a-zA-Z0-9_-]+)\]", _sub, text)
    if new != text:
        p.write_text(new)
        return True
    return False
```

#### orphan-page fixable=true + _fix
```python
def _fix_orphan_page(finding, vault, plugin_root, backup_dir):
    """孤儿页 → 加 wikilink 到同目录 _index.md."""
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    parent = p.parent
    idx = parent / "_index.md"
    if not idx.is_file():
        # 无 _index, 跳过 (或建空 _index)
        return False
    idx_text = idx.read_text()
    link = f"[[{p.stem}]]"
    if link in idx_text:
        return True  # 已链, 视为已修
    # 加到末尾
    bak = backup_dir / "_index" / rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    bak.write_text(idx_text)
    idx.write_text(idx_text.rstrip() + f"\n\n- {link}\n")
    return True
```

#### path-naming-violation + i18n-path-not-in-locale fixable=true + _fix
```python
def _fix_path_violation(finding, vault, plugin_root, backup_dir):
    """rename 文件名 slug-safe."""
    import re
    rel = finding["file"]
    src = vault / rel
    if not src.exists():
        return False
    parent = src.parent
    stem = src.stem
    ext = src.suffix
    # slug: 空格→-, 特殊字符→_, 保留中文/英文/数字
    new_stem = re.sub(r"[\s]+", "-", stem)
    new_stem = re.sub(r"[^\w一-鿿\-]", "_", new_stem)
    new_stem = re.sub(r"_+", "_", new_stem).strip("_-")
    if not new_stem or new_stem == stem:
        return False
    new_path = parent / f"{new_stem}{ext}"
    if new_path.exists():
        # 加 sha8 后缀
        import hashlib
        h = hashlib.sha256(rel.encode()).hexdigest()[:8]
        new_path = parent / f"{new_stem}-{h}{ext}"
    src.rename(new_path)
    return True
```

注: i18n-path-not-in-locale 复用 _fix_path_violation 一样的 rename 逻辑 (或 mv 到 收件箱)。

#### dead-wikilink cap 提升
```python
_STUB_CAP = 1000  # was 100
```

#### duplicate-alias 排查
检查现 _fix_duplicate_alias_group msg parse 逻辑, 确保所有 50 个 finding 都能 parse 到 alias。如果 msg 格式与 regex 不匹配 → 修。

### rules.json 同步 fixable=true

5 规则 `fixable: false` → `true`。

### autofix 顺序

RULE_PRIORITY 加:
```python
"vault-structure-violation": 0.5,  # 在 backup-in-vault=0 后, structure-missing=1 前 (先清违规再补缺)
"callout-unknown-type": 5,
"orphan-page": 6,
"path-naming-violation": 7,
"i18n-path-not-in-locale": 7,
```

## 实施

### Step 1: rules.json 5 规则 fixable=true
### Step 2: lint/run.py 5 新 _fix 函数 + cap 提升
### Step 3: FIX_MAP + RULE_PRIORITY 注册
### Step 4: 测试新增
### Step 5: marketplace 同步

## 验收

- [ ] 跑 user vault `~/persons/knowledge/obsidian` lint --fix → 残留 errors+warns 接近 0
- [ ] `记忆体系/` 自动 mv 到 ~/.cache backup
- [ ] callout-unknown-type 0
- [ ] orphan-page 显著下降 (有 _index 的目录全 link)
- [ ] path-naming-violation 0 (含 i18n)
- [ ] 278 + 新测试 PASS

## 风险

| 风险 | 缓解 |
|------|------|
| autofix 改坏用户内容 | backup 完整 |
| path rename 破 wikilink | 后续 cortex-linker 修, 或 lint --fix 再跑一次 dead-wikilink autofix |
| orphan-page 写 _index 破坏自定义内容 | append 不覆盖, 备份 |
| stub cap 1000 仍不够 | 后续可改为读 rule config |

## 子任务

单 trellis-implement。
