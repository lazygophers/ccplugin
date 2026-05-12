---
name: cortex-forget
description: 记忆遗忘 — 按 _meta/memory-policy.yaml 扫过期条目, 标 archive_pending=true (不真删, 交 memory-archive cron 月度执行)。触发: "forget" / "遗忘" / daily cron 自动触发。
disable-model-invocation: true
allowed-tools: Bash Read Edit Glob
---

# cortex-forget

按 policy.levels.<L>.forget 规则扫各级记忆, 给过期条目打 `archive_pending=true` frontmatter 标记。不删除文件本身, 仅 memory-archive cron (monthly) 才物理迁出。

## 触发场景
- daily cron `memory-forget.sh` (03:00)
- 用户显式 "forget expired memory" / "扫遗忘"
- 用户说 "忘了 X" / "forget X" → 解析 X 找匹配记忆 → 立即 forget
- cortex-memory-warden agent 检测到腐化时附带触发

forget 实质: 设 `archive_pending=true`, 不删 (archive cron 物理移)。
L0 不可 forget (除非用户提供 `user_signature` 显式覆盖 forget.never=true)。

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
   - L4: `compress_after_days=30` (这条由 memory-compact 负责 gzip, 本 skill 不动)
2. **扫 L2**:
   - Glob `记忆体系/L2-中期/semantic/**/*.md`
   - 读 frontmatter: created, last_recalled, recall_count
   - 判定: `(now - max(created, last_recalled)).days >= 365 AND recall_count < 5` → 命中
3. **扫 L3**:
   - Glob `记忆体系/L3-短期/episodic/**/*.md`
   - 判定: `(now - max(created, last_recalled)).days >= 90 AND recall_count < 3` → 命中
4. **标 archive_pending**:
   - Edit frontmatter: 加/改 `archive_pending: true` + `archive_reason: "expired: ..."` + `archive_marked_at: <UTC ISO>`
   - 不动 body
5. **汇总**: 输出命中条目 + 写一行到 `记忆体系/views/alerts.md` (审计追踪)

## 输出
```
[forget] scanned L2 + L3
  L2 expired: 4 (365d unused, recall<5)
    - L2://semantic/old-topic-1
    - ...
  L3 expired: 12 (90d unused, recall<3)
  marked archive_pending=true on 16 entries
  alerts appended: 记忆体系/views/alerts.md
  next: monthly memory-archive cron will physically move to 归档/
```

## 错误处理
- frontmatter 解析失败 → 跳过, 末尾汇总 corrupted count
- last_recalled 缺失 → 用 created 替代
- 文件无写权限 → 跳过, 记 warning
- archive_pending 已为 true 的 → 不重复标 (幂等)

## AUTO_MODE 兼容
[AUTO_MODE: ...] (cron 默认) 全自动标记; --dry-run 仅汇报。L0 永不动, L1 永不自动动 (即使 AUTO_MODE)。物理删除/移动是 memory-archive 月度 cron 的事, 本 skill 仅打标。
