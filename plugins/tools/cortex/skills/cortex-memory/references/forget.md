---
name: memory-forget
description: cortex-memory 子流程 — 记忆遗忘扫描, 按 policy 标 archive_pending (原 cortex-forget skill 合并入)
---

# Memory Forget (合入 cortex-memory)

按 `_meta/memory-policy.yaml` 的 `levels.<L>.forget` 规则扫各级记忆, 给过期条目打 `archive_pending=true` frontmatter 标记。**不删除文件本身**, 物理迁出由 memory-archive cron (monthly) 执行。

> 历史: 本流程原为独立 `cortex-forget` skill (65 行单文件), PR1 合并入 `cortex-memory/references/`。`/cortex:forget` slash + `forget.sh` wrapper + daily cron 不变, 改加载 `cortex-memory` skill 走本 references。

## 触发场景

- daily cron `memory-forget.sh` (03:00)
- `/cortex:forget` slash + `forget.sh` wrapper (auto 模式)
- 用户显式 "forget expired memory" / "扫遗忘" / "忘了 X"
- cortex-warden 检测到腐化时附带触发

## 输入

- --level: 默认全扫 (L1+L2+L3+L4); 可单 level
- --dry-run: 仅打印命中, 不改 frontmatter
- 不支持 --uri (单条删走 cortex-memory delete)

## 流程

1. **读 policy**: `_meta/memory-policy.yaml`
   - L0: `forget.never=true` → 跳过 (永不遗忘)
   - L1: `forget.only_user=true` → 跳过自动扫 (仅手动 + cortex-memory delete --force-user)
   - L2: `after_days=365 unless_recalled>=5`
   - L3: `after_days=90 unless_recalled>=3`
   - L4: `compress_after_days=30` (由 memory-compact 负责)

2. **扫 L2**:
   - Glob `记忆/L2-中期/semantic/**/*.md`
   - 读 frontmatter: created, last_recalled, recall_count
   - 判定: `(now - max(created, last_recalled)).days >= 365 AND recall_count < 5` → 命中

3. **扫 L3**:
   - Glob `记忆/L3-短期/episodic/**/*.md`
   - 判定: `(now - max(created, last_recalled)).days >= 90 AND recall_count < 3` → 命中

4. **标 archive_pending**:
   - Edit frontmatter: `archive_pending: true` + `archive_reason: "expired: ..."` + `archive_marked_at: <UTC ISO>`
   - 不动 body

5. **汇总**: 输出命中条目 + 写一行到 `记忆/views/alerts.md` (审计追踪)

## 输出格式

```
[forget] scanned L2 + L3
  L2 expired: 4 (365d unused, recall<5)
    - L2://semantic/old-topic-1
  L3 expired: 12 (90d unused, recall<3)
  marked archive_pending=true on 16 entries
  alerts appended: 记忆/views/alerts.md
  next: monthly memory-archive cron will physically move to 归档/
```

## 错误处理

- frontmatter 解析失败 → 跳过, 末尾 corrupted count
- last_recalled 缺失 → 用 created 替代
- 文件无写权限 → 跳过, 记 warning
- archive_pending 已为 true → 不重复标 (幂等)

## AUTO_MODE 行为

cron 默认 AUTO_MODE; 全自动标记; --dry-run 仅汇报。L0 永不动, L1 永不自动动 (即使 AUTO_MODE)。物理删除/移动由 memory-archive 月度 cron 执行, 本流程仅打标。
