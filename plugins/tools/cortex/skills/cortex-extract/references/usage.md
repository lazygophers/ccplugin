# usage — extract.sh 入口 + 调用示例 + L0 mock env

## 工具入口

```bash
bash plugins/tools/cortex/scripts/extract.sh --help

# Dry-run (默认): 输出 JSON plan, 不落盘
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex

# Apply: 落盘 + 更新游标 + archive 原 inbox 条目
bash plugins/tools/cortex/scripts/extract.sh --apply --target ~/.cortex

# 全量扫 (忽略游标)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## 典型调用示例

```bash
# 1. 例行整理 (查看计划)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex \
  | python3 -m json.tool

# 2. 检查后落盘 (L0 候选自动拒绝以防误)
CORTEX_EXTRACT_L0_AUTO=reject bash plugins/tools/cortex/scripts/extract.sh \
  --apply --target ~/.cortex

# 3. 项目级 vault
bash plugins/tools/cortex/scripts/extract.sh --apply --target "$PWD/.wiki"
# 注: 项目级游标走 <repo>/.wiki/state/, 与用户级游标互不干扰

# 4. 重置游标全量重跑
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## L0 mock env

`CORTEX_EXTRACT_L0_AUTO` 控制 L0 候选在非交互场景下的决策:

| 值 | 行为 |
| --- | --- |
| `accept` | 自动接受写入 L0-core |
| `reject` | 拒绝, 保留在 inbox 不归档 |
| `ask` (默认) | 阻断, 非交互场景必须显式设值 |

应用场景: CI / 批量脚本必须显式设 `accept` 或 `reject`, 避免阻塞.
