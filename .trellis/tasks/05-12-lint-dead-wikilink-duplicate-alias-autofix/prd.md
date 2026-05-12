# PRD — lint dead-wikilink + duplicate-alias autofix

## 背景

`lint --fix` 默认 autofix, 但两规则 fixable=false 让用户手动:
- `dead-wikilink` 1177 条
- `duplicate-alias` 41 条

User: 应自动处理。

## 目标

`dead-wikilink` + `duplicate-alias` 改 fixable=true, 默认 `lint` 跑时自动处理。

## 设计

### dead-wikilink autofix

**频次评分** — wikilink target 在 vault 多文件被引用次数:
- **freq ≥ 2**: 建 stub `知识库/收件箱/<slug>.md` (frontmatter + 提示), wikilink 不动 → 不再 dead
- **freq = 1**: 删 wikilink (改纯文本), `[[X]]` → `X`

stub 模板:
```yaml
---
type: stub
title: <X>
created: <UTC ISO>
auto_created_by: lint-autofix
status: draft
tags: [stub, inbox]
---

# X

> [!warning] 由 lint autofix 自动创建 — 因被 ≥2 文件引用为 wikilink, 创建占位。完善后删除 stub 标签。
```

cap=100 stub/次。

### duplicate-alias autofix

41 条重复 alias 分组:
- 按 created 升序 (mtime fallback), **保留最早**
- 其它加后缀 ` (<parent-dir-name>)` → 唯一化
- 若仍冲突 (同 parent 多文件), 加 sha8 后缀

写回 frontmatter aliases 字段。

### lint/run.py 改动

1. 现有 dead-wikilink rule fixable: false → true (在 _f 调用 / 规则定义处)
2. 同 duplicate-alias
3. 加 helper:
   - `_wikilink_freq(vault, all_files)` — 扫一次 vault, 统计每 target 出现次数 (缓存)
   - `_fix_dead_wikilink(finding, vault, plugin_root, backup_dir)`
   - `_fix_duplicate_alias_group(findings_group, vault, ..., backup_dir)`
4. `apply_fixes` FIX_MAP 加映射

注意 duplicate-alias 是**多文件组**操作, 不是 per-finding fix。需在 apply_fixes 内先 group, 再批处理。

### 测试

新增 `tests/python/test_lint_wikilink_autofix.py`:
- mock vault, freq 2 → stub 创建
- freq 1 → wikilink 转纯文本
- cap=100 生效
- duplicate-alias 分组 + 加后缀
- created 升序保留最早
- backup 到 backup_dir

## 验收
- [ ] dead-wikilink + duplicate-alias fixable=true
- [ ] mock vault freq 2 wikilink → 收件箱 stub 建好
- [ ] freq 1 → 转纯文本
- [ ] duplicate-alias 重命名 (保最早 + 后缀)
- [ ] cap=100 stub/次
- [ ] backup 完整
- [ ] 258 + 新测试 PASS

## 风险
| 风险 | 缓解 |
|------|------|
| 1177 dead link 一次性炸 | cap=100, 分多次 |
| 转纯文本破坏语义 | freq=1 才删, freq≥2 建 stub 保留 |
| 后缀冲突 | (parent-dir) → sha8 二级 |
| alias 改坏 anchor | 仅改 frontmatter aliases, 不动 body wikilink |

## 子任务
单 trellis-implement 串行。
