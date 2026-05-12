# PRD — lint --fix 自动移除非 schema 项 (mv to backup)

## 背景

用户:
> lint.sh 的时候, 需要移除不应该存在的目录结构, 只保留预期的目录结构

现行 cortex-lint vault-structure-violation (P6 加入) 处理流:
1. lint/run.py 输出违规 JSON
2. SKILL.md LLM 拿违规 → 每项 AskUserQuestion 询问 (move/delete/whitelist/skip)
3. 用户逐个回答

问题:vault 可能含上百违规项,逐个询问烦。用户期待**默认就移除**只留预期。

## 目标

`~/.cortex/scripts/lint.sh --fix` 默认行为:
1. lint/run.py 扫违规 → 输出 mv plan (违规 → `_meta/.cortex-backup/lint-<ts>/`)
2. SKILL.md LLM 一次性 AskUserQuestion **总体确认**:
   - "将移除 N 个不在 LYT preset 内的项到 backup, 确认?" [yes / cancel / whitelist all / per-item]
3. 选 yes:批量 mv (走 obsidian CLI / 直 mv,**非真删**, backup 可恢复)
4. 选 cancel:不动
5. 选 whitelist all:全加 `_meta/version.json:.lint_whitelist[]`
6. 选 per-item:走原 P6 逐个询问流 (向后兼容)

数据安全:**永远 mv 到 backup,从不真删** (除非用户后续手动清 backup)。

## 范围

### 修改

- `plugins/tools/cortex/lint/run.py` — 新增 `--fix-structure` flag,输出含 `mv_plan` 数组的 JSON
- `plugins/tools/cortex/skills/cortex-lint/SKILL.md` — §交互修复 改为先一次性总体确认,再分支
- `plugins/tools/cortex/tests/python/test_lint_structure.py` — 加 mv plan 输出验证

### 不在范围

- 不动 schemas.py / rules.json
- 不动 lint.sh wrapper (已 dual-mode, --fix 透传到 SKILL)
- 不动 hooks / P0-P6 / Phase A 实施
- 不引入真 rm 操作 (永远 mv to backup)

## 详细规范

### 1. lint/run.py mv_plan 输出

vault-structure-violation 违规项扩展输出字段:

```python
def check_vault_structure(vault: Path, preset: str, whitelist: set,
                          extra_allowed_dirs: set = None) -> list[dict]:
    ...
    # 现行 violations[i] 含 {rule, path, kind, reason}
    # 加 backup_target 字段:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = f"_meta/.cortex-backup/lint-{ts}"
    for v in violations:
        v["backup_target"] = f"{backup_root}/{v['path']}"
    return violations
```

main 报告输出加汇总:

```json
{
  "errors": [...],
  "warns": [...],
  "structure_purge": {
    "preset": "LYT",
    "violation_count": 42,
    "backup_root": "_meta/.cortex-backup/lint-20260512T034500Z",
    "mv_plan": [
      {"from": "foobar/", "to": "_meta/.cortex-backup/lint-.../foobar/"},
      {"from": "random.txt", "to": "_meta/.cortex-backup/lint-.../random.txt"},
      ...
    ]
  }
}
```

`mv_plan` 仅当 `--fix-structure` 或 `--fix` flag 时生成。

### 2. cortex-lint SKILL.md §交互修复 重写

原段保留 backwards compat (per-item),改默认行为为总体确认。

新流程伪码:

```markdown
## 交互修复 (--fix 模式)

1. 跑 run.py --fix → 拿 JSON 报告
2. 若 `structure_purge.violation_count == 0`:跳过结构修复段
3. 否则用 AskUserQuestion **一次性总体确认**:
   ```
   问: "lint 发现 N 个不在 <preset> preset 内的项. 将批量 mv 到
       _meta/.cortex-backup/lint-<ts>/ (非真删, 可恢复). 如何处理?"
   选项:
     - "全部移除到 backup (推荐)"  → BATCH_MV
     - "全部加入白名单"             → BATCH_WHITELIST
     - "逐个询问 (P6 原流程)"       → PER_ITEM
     - "取消, 本次不动"             → CANCEL
   ```
4. BATCH_MV:
   - mkdir backup_root
   - 对 mv_plan 每项: obsidian CLI move (L1) → mcp__obsidian (L2)
     → mv (L3, 须 AskUserQuestion 兜底确认, **但因已总体确认本步跳**)
   - 报告 "moved N items to <backup_root>"
5. BATCH_WHITELIST:
   - 读 _meta/version.json
   - .lint_whitelist[] 追加所有 violations[].path
   - 写回 (obsidian CLI property:set 或直写)
   - 报告 "whitelisted N items"
6. PER_ITEM:
   - 走原 4 选项 (move/delete/whitelist/skip) 逐项询问
7. CANCEL: 不动

后续 errors[] / warns[] 中非 vault-structure-violation 项, 走原 autofix 流程
(rules.json autofix=true 自动落; 其它 AskUserQuestion 单独询问).
```

明示 BATCH_MV 是**默认推荐**,用户大概率选这个。

### 3. mv 实际执行 (SKILL 工作流内)

```bash
# 用 obsidian CLI 优先 (保 wikilink 更新)
obsidian move "<source>" "<backup_target>"

# CLI 不可用 fallback
mkdir -p "$(dirname "$BACKUP_TARGET")"
mv "$VAULT/$SOURCE" "$VAULT/$BACKUP_TARGET"
```

## 验收

1. lint/run.py `--fix-structure` flag 在违规存在时输出 `structure_purge.mv_plan` 数组
2. mv_plan 每项 `{from, to}`,`to` 含 `_meta/.cortex-backup/lint-<ISO>/`
3. 无违规时 `structure_purge.violation_count == 0`,无 mv_plan 字段或空数组
4. SKILL.md §交互修复 段含 4 选项 (BATCH_MV / BATCH_WHITELIST / PER_ITEM / CANCEL),BATCH_MV 标默认推荐
5. pytest test_lint_structure.py 加 ≥2 用例:mv_plan 字段存在 + backup_root 时间戳格式
6. P0-P6 + Phase A + previous lint tests 不回归

## 不变量

- 永远 mv 到 backup, **从不**真 rm
- 默认 BATCH_MV (用户最常选)
- 白名单仍生效 (跳过白名单内 path)
- backup_root 时间戳 UTC ISO8601 紧凑 (`%Y%m%dT%H%M%SZ`)
- mv plan 由 python 输出, mv 执行在 SKILL/LLM 流程 (python 不动盘)
- per-item 流程保留 (向后兼容 P6)

## 风险

- **backup 累积大**:多次 lint --fix 会留多个 lint-<ts>/ 目录. **缓解**:文档建议定期清 `_meta/.cortex-backup/`
- **AskUserQuestion 总确认在 CLI 模式有效?**:cortex-lint skill 在 claude 会话内跑, AskUserQuestion 工具可用; `lint.sh --fix` 走 wrapper 也是经 cortex_stream_runner → claude session 上下文, OK
- **vault 根含 100+ 违规一次性 mv**:风险大, 但 backup 可逆. AskUserQuestion 文案明示数量给用户决策
- **i18n locale dirs / .obsidian / .trash 误删**:已在 schemas.py 加 allowed + locale_dirs 探测, mv plan 不含
