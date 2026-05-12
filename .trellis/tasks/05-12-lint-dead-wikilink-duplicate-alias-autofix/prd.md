# PRD — lint vault 结构 + 元数据自动同步 (autofix 建设性扩展)

## 背景

User 跑 `lint` (默认 autofix) 但 vault 目录未按预期 (双 namespace 结构) 变更。

根因诊断:
- lint 现状只"**破坏性** mv 违规路径" (`structure_purge` rule `vault-structure-violation`)
- **缺"建设性 创建/复制"** 步骤: 没有把 plugin 最新 _structure.json + seed_files 同步到 vault
- vault 缺 `知识库/` `记忆体系/` `仪表盘/` 等新顶层目录, lint 既不报也不修

类似问题扫:
| Gap | 状态 |
|-----|------|
| `template-outdated` (_templates/* 漂移) | ✓ 已修 |
| `seed-outdated` (seed 来文件版本旧) | ✓ 已修 |
| `structure-missing` (vault 缺目录) | ❌ 缺 — 本任务 |
| `meta-missing` (`_meta/memory-policy.yaml` 等缺) | ❌ 缺 — 本任务 |
| `templates-dir-missing` (vault 缺 `_templates/{html,memory,knowledge}`) | ❌ 缺 — 本任务 |
| `dead-wikilink` autofix | ❌ 缺 — **推 follow-up** |
| `duplicate-alias` autofix | ❌ 缺 — **推 follow-up** |

## 目标

lint --fix (现默认) 跑时, 自动把 vault 同步到 plugin 最新结构。3 新规则:

1. **`structure-missing`** (warn, fixable=true):
   - 扫 `_structure.json` `directories_keys` 嵌套结构, 检每个目录是否存在 vault
   - 缺 → mkdir + 报 fix
2. **`seed-missing`** (warn, fixable=true):
   - 扫 `_structure.json` `seed_files`, 检 vault 内目标路径是否存在
   - 缺 → 复制 plugin seed 源 (含占位符替换 TITLE/CURRENT_PATH/LAST_UPDATED)
3. **`meta-missing`** (warn, fixable=true):
   - 检 `<vault>/_meta/{memory-policy.yaml, triggers.yaml, template-manifest.json}` 存在
   - 缺 → 复制 plugin 模板 (memory-policy 从 `presets/seed/_meta/memory-policy.yaml`, triggers 从 `templates/triggers.yaml`, template-manifest 从 `templates/_manifest.json`)

## 设计

### 1. lint/run.py 加 3 helper

```python
def _check_structure_missing(vault: Path, plugin_root: Path) -> list[dict]:
    """扫 _structure.json directories, 检 vault 内缺目录."""
    findings = []
    sf = plugin_root / "presets" / "_structure.json"
    if not sf.exists():
        return findings
    d = json.loads(sf.read_text())
    # 递归扫 directories 嵌套
    def walk(node, prefix=""):
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{prefix}/{k}" if prefix else k
                if not (vault / p).is_dir():
                    findings.append(_f(
                        "structure-missing", "warn", p, 1,
                        f"vault 缺目录 {p} (plugin _structure.json 要求)",
                        True,
                    ))
                walk(v, p)
        elif isinstance(node, list):
            for item in node:
                walk(item, prefix)
    walk(d.get("directories", {}))
    return findings

def _check_seed_missing(vault: Path, plugin_root: Path) -> list[dict]:
    """扫 _structure.json seed_files, 检 vault 内目标缺失."""
    findings = []
    sf = plugin_root / "presets" / "_structure.json"
    if not sf.exists():
        return findings
    d = json.loads(sf.read_text())
    for s in d.get("seed_files", []):
        dst_key = s.get("dst_key", ".")
        name = s.get("name")
        rel = name if dst_key == "." else f"{dst_key}/{name}"
        if not (vault / rel).exists():
            findings.append(_f(
                "seed-missing", "warn", rel, 1,
                f"vault 缺 seed 文件 {rel}",
                True,
            ))
    return findings

def _check_meta_missing(vault: Path, plugin_root: Path) -> list[dict]:
    findings = []
    targets = [
        ("_meta/memory-policy.yaml", plugin_root / "presets/seed/_meta/memory-policy.yaml"),
        ("_meta/triggers.yaml", plugin_root / "templates/triggers.yaml"),
        ("_meta/template-manifest.json", plugin_root / "templates/_manifest.json"),
    ]
    for rel, src in targets:
        if src.exists() and not (vault / rel).exists():
            findings.append(_f(
                "meta-missing", "warn", rel, 1,
                f"vault 缺 _meta 文件 {rel}",
                True,
            ))
    return findings
```

### 2. fix 函数

```python
def _fix_structure_missing(finding, vault, plugin_root, backup_dir) -> bool:
    p = vault / finding["file"]
    p.mkdir(parents=True, exist_ok=True)
    return True

def _fix_seed_missing(finding, vault, plugin_root, backup_dir) -> bool:
    rel = finding["file"]
    # 反查 plugin seed 源 (按 _structure.json seed_files)
    sf = plugin_root / "presets" / "_structure.json"
    d = json.loads(sf.read_text())
    src_path = None
    for s in d.get("seed_files", []):
        dst_key = s.get("dst_key", ".")
        name = s.get("name")
        cand_rel = name if dst_key == "." else f"{dst_key}/{name}"
        if cand_rel == rel:
            src_path = plugin_root / "presets" / s["src"]
            break
    if not src_path or not src_path.exists():
        return False
    # 占位符渲染
    now = datetime.now(timezone.utc).isoformat()
    content = src_path.read_text()
    content = content.replace("{{LAST_UPDATED}}", now)
    content = content.replace("{{UPDATED}}", now)
    content = content.replace("{{CREATED}}", now)
    content = content.replace("{{TITLE}}", Path(rel).stem)
    content = content.replace("{{CURRENT_PATH}}", str(Path(rel).parent))
    dst = vault / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content)
    return True

def _fix_meta_missing(finding, vault, plugin_root, backup_dir) -> bool:
    rel = finding["file"]
    src_map = {
        "_meta/memory-policy.yaml": plugin_root / "presets/seed/_meta/memory-policy.yaml",
        "_meta/triggers.yaml": plugin_root / "templates/triggers.yaml",
        "_meta/template-manifest.json": plugin_root / "templates/_manifest.json",
    }
    src = src_map.get(rel)
    if not src or not src.exists():
        return False
    dst = vault / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    return True
```

### 3. 主流程接入

`lint/run.py` 末尾 vault-level 检查段 (现已含 _check_template_outdated / _check_seed_outdated), 加调:
```python
findings.extend(_check_structure_missing(vault, plugin_root))
findings.extend(_check_seed_missing(vault, plugin_root))
findings.extend(_check_meta_missing(vault, plugin_root))
```

`apply_fixes` 分发加映射:
```python
FIX_MAP = {
    ...,
    "structure-missing": _fix_structure_missing,
    "seed-missing": _fix_seed_missing,
    "meta-missing": _fix_meta_missing,
}
```

### 4. 顺序敏感

执行顺序:
1. structure-missing (建目录) — 必先
2. meta-missing (建 _meta 文件)
3. seed-missing (复制 seed 到目录, 依赖 structure 已建)
4. 其他 fix (现有)

加 fix priority 字段或显式排序。

## 验收

- [ ] 3 新规则在 lint/run.py 注册
- [ ] 跑 mock 空 vault (仅 `.obsidian/` + `_meta/version.json`):
  - 默认 lint (autofix) 跑完后 vault 含完整 双 namespace 目录树 + 43 seed _index.md + _meta/{memory-policy, triggers, template-manifest} 文件
- [ ] 不破坏用户已存在的内容 (frontmatter created 检测; 复制前先 backup)
- [ ] 占位符正确替换 ({{TITLE}} / {{CURRENT_PATH}} / {{LAST_UPDATED}})
- [ ] 242 + 新测试 PASS
- [ ] backup 到 lint backup_dir (现有机制)

## 不在范围 (follow-up)

- `dead-wikilink` autofix (1177 条, freq 评分 + stub 创建/转纯文本)
- `duplicate-alias` autofix (41 条, 加后缀)
- 老 vault 迁移 (v2 8 桶 → v3 双 namespace) — 单独 task

## 风险

| 风险 | 缓解 |
|------|------|
| structure_purge mv 老目录后 structure-missing 又建 (循环) | 一次 lint --fix 不再重跑; structure_purge 已把 vault-structure-violation mv backup, lint 重跑应 0 violation; 用户老内容已不在原位, 但新目录建好 OK |
| seed-missing 覆盖用户笔记 | 只补缺失文件 (existing → skip) |
| seed_files 列 44 项一次性创建大批 | cap=100/次 (与 template autofix 一致) |
| 占位符渲染编码问题 | 中文 utf-8 直接处理 |

## 子任务

单 agent 串行 (lint/run.py + 测试)。
