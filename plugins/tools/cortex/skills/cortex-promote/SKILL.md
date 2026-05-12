---
name: cortex-promote
description: 记忆晋级 — 读 views/candidates.md 按 policy 执行 L4→L3 / L3→L2 / L2→L1 / L1→L0; L1→L0 强制 AskUserQuestion 二次确认 (AUTO_MODE 下绝不执行)。触发: "promote memory" / "晋级" / "审批候选"。
disable-model-invocation: true
allowed-tools: Read Edit Glob AskUserQuestion
---

# cortex-promote

读 `记忆/views/candidates.md` 中由 cortex-consolidate 写入的候选, 按 `_meta/memory-policy.yaml` 各级 `promote_criteria` 校验, 执行晋级 (改 frontmatter level/uri + 移文件)。L2→L1 与 L1→L0 必须人工审批。

## 触发场景
- 用户显式 "promote memory" / "审批候选" / "晋级 X"
- 月度复盘 (用户驱动, 非 cron)
- cortex-memory-warden agent 检测稳定候选时提示用户触发

## 输入
- --uri: 单条候选 URI (可选, 默认扫 candidates.md 全部)
- --target-level: 单条时指定目标 (e.g. `L1`), 全扫时按候选行内目标
- --auto-low: 默认 false; true 时 L4→L3 / L3→L2 自动批 (无交互)
- --dry-run: 仅打印计划

## 流程

1. **读候选**: `记忆/views/candidates.md` 每行格式:
   ```
   - [ ] L3://episodic/<date>/<slot> → L2://semantic/<topic>  (recurrence: 5x in 7d, weight 0.6)
   ```
2. **policy 校验** (`_meta/memory-policy.yaml`):
   - L4→L3: `promote_criteria.ai_detected_pattern=true` → 满足 ✓
   - L3→L2: `recall_count >= 5 AND recurrence >= weekly`
   - L2→L1: `recall_count >= 20 AND stable_days >= 90`
   - L1→L0: 无定量阈值 (用户审批决定)
3. **分级处理**:
   - **L4→L3 / L3→L2** (AUTO 可执行):
     - --auto-low=true 或 AUTO_MODE → 直接走步骤 4
     - 否则汇总待办列表, 不执行
   - **L2→L1** (needs_user_approval):
     - AUTO_MODE → **仅汇报**, 不执行
     - 交互 → AskUserQuestion 单条确认 (per uri)
   - **L1→L0** (强制审批):
     - AUTO_MODE → **绝不执行**, 输出候选清单, 提示 `~/.cortex/scripts/memory.sh promote --interactive`
     - 交互 → **必须** AskUserQuestion 二次确认 (第 1 次列出 brief + 影响, 第 2 次最终批准), 任一选 cancel 即终止
4. **执行晋级** (per uri):
   - 解析 source uri → 源文件路径
   - 解析 target uri → 目标路径 (按 URI 解析规则)
   - Edit 源文件 frontmatter: `level: <new>`, `uri: <new>`, `promoted_from: <old uri>`, `promoted_at: <now>`
   - 文件 mv (源 → 目标) (用 Bash mv; 路径校验 in-vault)
   - L0 额外: git tag `cortex-L0-<sha8>` (`Bash git -C <vault> tag ...`)
5. **更新索引**:
   - 改 `_meta/uri-index.json`: 删旧 URI, 加新 URI
   - 改 `候选.md` 行: `- [ ]` → `- [x]` + 加完成时间注释
6. **回滚**: 任一步骤失败 → 用 Edit 恢复 frontmatter, mv 回原位 (best-effort), 输出 failed_at_step

## 输出
```
[promote] scanned candidates.md: 12 候选
  L4→L3: 3 (auto-batch executed)
    ✅ L4://ledger/2026-05-10#evt-3 → L3://episodic/2026-05-10/T0930
    ...
  L3→L2: 4 (need --auto-low, current dry)
    🟡 L3://episodic/2026-05-08/T1100 → L2://semantic/go/channel  (recall 6x)
  L2→L1: 2 (need user approval, prompting...)
    [AskUserQuestion] 批准 L2://semantic/pkm → L1://semantic-stable/pkm ?
  L1→L0: 1 (CRITICAL, AUTO_MODE 拒绝)
    🛑 候选: L1://procedural/git-commit-flow → L0://habits/git
        请跑 ~/.cortex/scripts/memory.sh promote --interactive 人工审批

总结: 3 executed, 4 pending --auto-low, 2 pending user, 1 blocked
索引更新: _meta/uri-index.json
```

## 错误处理
- 候选行格式非法 → 跳过 + warning
- 目标 URI 已存在 → 拒, 不覆盖 (冲突解决交用户)
- mv 失败 (权限/磁盘) → 回滚 frontmatter, 退 1
- git tag 失败 (vault 非 git repo) → L0 晋级仍执行, 但输出 warning "L0 晋级无 git tag, 完整性追溯减弱"
- AskUserQuestion 取消 → 该条标记 cancelled, 继续后续

## 晋级算法 (三层重复检测)

扫 L4 ledger 上 7 天, 统计 (entity, topic, context) 三元组:
- freq ≥ 3 → 创建 L3 episodic 候选, auto promote (L4→L3)
- freq ≥ 5 + 跨 ≥3 天 → L3 → L2 候选 (写 candidates.md, 不自动)
- freq ≥ 10 + 跨 ≥30 天 → L2 → L1 候选

扫 L3 episodic 上 30 天: 同 topic ≥ 5 次 + last_recalled 增长 → L2 候选。
扫 L2 semantic 上 365 天: recall_count ≥ 20 + 90 天无 weight 大改 → L1 候选。
L0 永不自动, 必经用户审批。

## 级别边界速查 (详见 `_meta/memory-policy.yaml`)

| level | 边界 | 审批 | review |
|-------|------|------|--------|
| L0 | 性格/价值观/硬约束, ≤1500c, 不可逆 | user 必审 + git tag | monthly hash 检测 |
| L1 | 技能/稳定语义, ≤5000c, recall≥20+90 天稳定 | AI 自动 w≥0.8 | monthly 矛盾告警 |
| L2 | 语义, ≤3000c, 365 天时效 | AI dedupe | monthly 365 天衰减 |
| L3 | 情节, ≤2000c, 90 天时效 | AI 自动 | weekly 同事件 ≥5 抽象 L2 |
| L4 | ledger/sessions, append-only | 系统自动 | weekly 30 天 gzip 60 天归档 |

## AUTO_MODE 兼容
**这是唯一与 AUTO_MODE 强对抗的 skill**:
- [AUTO_MODE: ...] 下: L4→L3 / L3→L2 仅在显式 --auto-low=true 才执行; L2→L1 仅汇报不执行; **L1→L0 绝不执行**, 仅输出候选清单 + 提示人工审批命令。
- 任何 AskUserQuestion 调用在 AUTO_MODE 下被 skill 自身拦截 (本 skill 在每次调用 AskUserQuestion 前先检测 AUTO_MODE flag, 命中即视为 cancel)。

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/promote.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走 policy 默认值跳过
3. fail-fast: 任何 error 立即返回错误码 + 简短消息
4. 特殊规则:
   - L4→L3 / L3→L2: 仅在显式 `--auto-low=true` 才执行写盘, 否则仅汇报
   - L2→L1: 仅汇报, **不执行**
   - L1→L0: **绝不执行**, 仅写候选清单到 `views/candidates.md` + 提示人工审批命令 `~/.cortex/scripts/promote.sh --interactive`
