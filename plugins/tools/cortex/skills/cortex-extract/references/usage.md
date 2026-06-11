# usage — extract.sh 入口 + 调用示例 + L0 mock env

## 工具入口

```bash
bash plugins/tools/cortex/scripts/extract.sh --help

# Apply (默认): 落盘 + 更新游标 + archive 原 inbox 条目
bash plugins/tools/cortex/scripts/extract.sh --target ~/.cortex

# Dry-run (opt-in 预览): 输出 JSON plan, 不落盘
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex

# 全量扫 (忽略游标, opt-in 预览)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## 典型调用示例

```bash
# 1. 例行整理 (默认直接落盘 + 推进游标)
bash plugins/tools/cortex/scripts/extract.sh --target ~/.cortex

# 2. 先看计划 (opt-in 预览, 不落盘)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex \
  | python3 -m json.tool

# 2b. 落盘但拒绝 L0 候选 (防误写核心规则)
CORTEX_EXTRACT_L0_AUTO=reject bash plugins/tools/cortex/scripts/extract.sh \
  --target ~/.cortex

# 3. 项目级 vault
bash plugins/tools/cortex/scripts/extract.sh --target "$PWD/.wiki"
# 注: 项目级游标走 <repo>/.wiki/state/, 与用户级游标互不干扰

# 4. 重置游标全量重跑
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## L0 mock env

`CORTEX_EXTRACT_L0_AUTO` 控制 `--apply` 时 L0 候选的决策:

| 值 | 行为 |
| --- | --- |
| `accept` (默认) | 自动接受写入 L0-core (L0 不再 ask) |
| `reject` | 拒绝, 保留在 inbox 不归档 |

应用场景: 默认 `accept` 即 L0 自动落盘; 只想拦核心规则误写时显式设 `reject`.
