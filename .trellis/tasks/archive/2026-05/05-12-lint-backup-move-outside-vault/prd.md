# PRD — lint backup 移出 vault, vault 完全干净

## 痛点

User vault `/tmp/test-cortex-v3` 显示:
```
_meta/.cortex-backup/lint-20260512T114122Z/记忆体系/
_meta/.cortex-backup/lint/
```

老 `记忆体系/` 被 mv backup 到 vault 内, 用户看 vault 仍含 `记忆体系` 痕迹 → 觉得"不干净/不一致"。

## 根因

lint backup_dir = `<vault>/_meta/.cortex-backup/<ts>/` (默认 vault 内)。
应 = `~/.cache/cortex/lint-backup/<vault-hash>/<ts>/` (vault 外)。

## 目标

vault 完全干净:
1. lint backup 默认落 vault 外 (`~/.cache/cortex/lint-backup/`)
2. 已存 vault 内 `_meta/.cortex-backup/` 自动迁移到 vault 外 + 删 vault 副本
3. structure_purge 也落 vault 外

## 设计

### 1. backup root 路径

```python
def _get_backup_root(vault: Path) -> Path:
    """Backup 落 vault 外 (~/.cache/cortex/lint-backup/<vault-hash>/<ts>/)."""
    import hashlib
    vault_hash = hashlib.sha256(str(vault.resolve()).encode()).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = Path.home() / ".cache" / "cortex" / "lint-backup" / vault_hash / ts
    base.mkdir(parents=True, exist_ok=True)
    return base
```

替换 lint/run.py 内所有 `<vault>/_meta/.cortex-backup/` 引用为 `_get_backup_root(vault)`。

### 2. structure_purge backup 也外

`structure_backup_root` 同样改为 vault 外。

### 3. 新规则: `backup-in-vault` (warn, fixable=true)

迁移已存 vault 内 backup:
- 扫 `<vault>/_meta/.cortex-backup/` 若存在 → mv 到 `~/.cache/cortex/lint-backup/<vault-hash>/migrated-<ts>/`
- 删 vault 内 `.cortex-backup/`

### 4. _structure.json / schemas 不动

`_meta/.cortex-backup` 不在白名单, 仍是 violation, 但 backup 不再创建到 vault, 旧的迁走即可。

### 5. cron 清理

`memory-compact` / 新加 `lint-backup-prune`: 删 `~/.cache/cortex/lint-backup/` 30 天前的 ts 目录。

或简单: lint 跑时自动清理 30 天前。

## 实施

1. `lint/run.py` 改:
   - 加 `_get_backup_root(vault)`
   - 替换 backup_dir 来源 (在 `apply_fixes` / `structure_purge` 入口)
   - 加 `_check_backup_in_vault` + `_fix_backup_in_vault` (迁移已存)
2. 测试: 跑 lint, 改文件触发 fix → 验证 backup 在 `~/.cache/cortex/lint-backup/`, vault 内无 `.cortex-backup`
3. marketplace sync

## 验收
- [ ] lint --fix 跑后, vault 内**无** `_meta/.cortex-backup/`
- [ ] backup 在 `~/.cache/cortex/lint-backup/<hash>/<ts>/`
- [ ] 已存 vault backup 自动迁走 (新规则)
- [ ] 278 tests PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| ~/.cache 满 | 加自动清理 30 天 |
| 用户期望 backup 在 vault (易找) | 用户偏好可后续加 config 项; 默认外 |
| Cross-platform ~/.cache | python `Path.home() / ".cache"` 跨平台 OK |

## 子任务
单 trellis-implement。
