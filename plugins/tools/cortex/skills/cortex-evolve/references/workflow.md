# workflow — 5 步执行流程

evolve **无独立脚本**, 由 main 按 5 步顺序调度 `cortex-extract` (三轴评分) / `cortex-save` (移文件) / `cortex-lint --fix` (frontmatter level 校正) 完成跨级再平衡.

## 步骤总览

```
1. --scan       列 vault 全级 (L0~L4) 条目, 输出当前分布
2. 评分          跑三轴 (频率/时间/重要度) → promote_score / demote_score
3. plan          按 rules.md 阈值生成 JSON plan (升降级候选清单)
4. 用户审        展示 plan, 对 L1/L0 升级与跳级条目 ask 确认
5. --apply      cortex-save 移文件 + cortex-lint --fix 校 frontmatter
```

## 步骤 1: --scan (默认)

列出 vault 中 `memory/L0-core/` ~ `memory/L4-inbox/` 的全部 `.md` 条目, 不评分, 仅输出当前金字塔分布:

```bash
find <vault>/memory/L{0,1,2,3,4}-* -name '*.md' -type f
```

输出 (示例):
```
L0-core:   3 条
L1-long:   12 条
L2-mid:    47 条
L3-short:  186 条
L4-inbox:  342 条 (走 cortex-extract, 不在 evolve 范围)
```

若 L0 > 20 → 提示用户跑 `cortex-lint` audit.

## 步骤 2: 评分

对 L0-L3 全部条目 (L4 跳过, 走 extract) 跑三轴评分 (详见 `signals.md`):

- 复用 `cortex-extract` 内部三轴评分函数 (传 mode=evolve)
- 数据源: git log 文件提及次数 / wikilink 反链 / frontmatter `weight` `event_date` / mtime
- 输出每条目: `{file, current_level, freq_score, recency_score, importance_score, promote_score, demote_score, user_emphasis_count}`

## 步骤 3: plan 生成

按 `rules.md` 阈值表对每条目判定升降级动作, 输出 JSON plan.

### Plan 字段 schema

```json
{
  "generated_at": "2026-06-10T12:00:00Z",
  "vault": "/path/to/vault",
  "total_scanned": 248,
  "actions": [
    {
      "file": "memory/L3-short/2025-12-foo.md",
      "current_level": "L3",
      "proposed_level": "L2",
      "action": "promote",
      "promote_score": 0.72,
      "demote_score": 0.18,
      "reason": "近 14d 提及 5 次 (freq 1.0), weight=0.8",
      "requires_ask": false,
      "skip_jump": false
    },
    {
      "file": "memory/L2-mid/auth-rule.md",
      "current_level": "L2",
      "proposed_level": "L1",
      "action": "promote",
      "promote_score": 0.85,
      "reason": "复用 6 次 + weight 0.9",
      "requires_ask": false,
      "audit_candidate": true
    },
    {
      "file": "memory/L1-long/legacy-foo.md",
      "current_level": "L1",
      "proposed_level": "L1",
      "action": "audit-candidate",
      "demote_score": 0.92,
      "reason": "120d 未访问, 但 L1/L0 不主动降",
      "requires_ask": false
    }
  ]
}
```

### 字段说明

| 字段 | 含义 |
| --- | --- |
| `action` | `promote` / `demote` / `audit-candidate` / `noop` |
| `requires_ask` | true → 步骤 4 必须用户确认 (L1/L0 升级、跳级、新写入 L1/L0) |
| `audit_candidate` | true → 步骤 5 写入 lint 报告但不移动 (L1/L0 demote 候选) |
| `skip_jump` | true → 跳级 (L3→L1 / L2→L0), 必须 ask |

## 步骤 4: 用户审

展示 plan 摘要 (按 action 分组):

```
计划升级 (12 条):
  - L3 → L2: 8 条 (自动)
  - L2 → L1: 3 条 (audit-candidate, 自动)
  - L1 → L0: 1 条 (audit-candidate, 自动) ⚠ 需确认

计划降级 (5 条):
  - L2 → L3: 5 条 (自动)

audit-candidate (不移动, 仅报告): 7 条
  - L1 demote 候选: 5 条
  - L0 demote 候选: 2 条
```

对所有 `requires_ask=true` 或 `skip_jump=true` 条目逐一询问 (yes/no/skip).

## 步骤 5: --apply

仅在 `--apply` flag 下执行写盘. 对 plan 中 `action ∈ {promote, demote}` 且通过审的条目:

1. **移文件**: 调用 `cortex-save` 的 file-move 子能力 (`mv old_path new_path`), 路径替换 `L{n}-{name}/` → `L{n±1}-{name}/`
2. **校 frontmatter**: 调用 `cortex-lint --fix` 自动更新 frontmatter `level` 字段 + `updated` 时间戳
3. **audit 报告**: `audit_candidate` 条目写入 `<vault>/.cortex/audit-YYYYMMDD.json`, 不动文件

调用样例:

```bash
# 步骤 1-2 复用 extract 评分
cortex-extract --mode=evolve --scan --target <vault>

# 步骤 3 输出 plan
cortex-extract --mode=evolve --dry-run --target <vault> > plan.json

# 步骤 5 落盘
cortex-save --move-from-plan plan.json --target <vault>
cortex-lint --fix --target <vault>
```

(实际调用形式取决于既有 script 接口; 若不支持 `--mode=evolve` 参数, main 手动展开三轴评分 + 文件移动逻辑.)

## 边界 vs cortex-extract

| 维度 | cortex-extract | cortex-evolve |
| --- | --- | --- |
| 范围 | L4-inbox → 各级 (初次落位) | L0-L3 内部跨级 (再平衡) |
| 三轴语义 | 抗遗忘度/强度/复用面 (内容特征) | 频率/时间/重要度 (使用模式) |
| 触发 | 整理 inbox / 新条目 | 记忆 audit / 定期再平衡 |
| 写盘 | 创建/移动至 L1-L4 | 跨级移动 (L0-L3 间) |

两者评分函数实现可共享 (传 mode 参数区分语义).

## 边界 vs cortex-save

| 维度 | cortex-save | cortex-evolve |
| --- | --- | --- |
| 动作 | 一次性写入新条目 (用户主动) | 移动既有条目 (跨级) |
| 内容 | 新建正文 + frontmatter | 仅改路径 + level 字段 |
| ask | L0/L1 新写入必须 ask | L0/L1 promote 不 ask (从下级来); L0/L1 直接新写入仍走 save 路径 |

evolve apply 阶段调用 save 仅复用 file-move 能力, 不重写正文.

## dry-run 默认

evolve 默认 dry-run, 输出 plan 不写盘; `--apply` 显式开关才落盘. 与 `cortex-extract` 一致.

## 回滚

apply 失败或用户撤回:

```bash
git checkout <vault>/memory/  # 撤回所有文件移动
```

evolve 不修改正文, 仅改路径 + frontmatter 两字段, 回滚成本极低.
