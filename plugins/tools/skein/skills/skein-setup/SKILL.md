---
name: setup
description: SKEIN 工作区初始化 + trellis 兼容迁移。首次在仓库启用 SKEIN、或 SessionStart 提示「无 .skein/」时使用 — 新仓一键 scaffold; 检测到 .trellis/ 则派 skein-setup agent 语义迁移 (spec 重组为 core/recall×类目 + 软链 / task 重建 / 清 trellis 残留)。幂等可重跑。
---

# setup — 初始化 / trellis 迁移

在仓库首次启用 SKEIN 时建 `.skein/` 工作区。若仓库原用 trellis (`.trellis/`), 一并迁移并清残留。**幂等** — 重跑安全。

> 触发: 用户显式调用 `/setup`, 或 SessionStart hook 注入「无 `.skein/`」提示后 main 主动调用。

## 分流 (先判有无 trellis)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py setup   # 幂等 scaffold + 输出 manifest JSON
```

manifest 的 `trellis_present` 决定路径:

| 场景 | 载体 | 动作 |
|---|---|---|
| **新仓** (`trellis_present:false`) | **main 直接跑** (纯机械, 不派 agent) | `skein.py setup` 已建 `.skein/` + config + gitignore + 本地 `.skein/spec` 库。完成即可用。 |
| **有 trellis** (`trellis_present:true`) | **派 `skein-setup` agent** (语义迁移) | scaffold 已建 + `.skein/spec` 软链 `.trellis/spec`; 但 spec 重组 / task 重建 / 残留清理需语义判断 → 派 agent。 |

## 派 skein-setup agent (仅 trellis 迁移)

dispatch prompt 6 字段自包含:

- **目标**: 把 `.trellis/` (spec/task/.claude 接线) 语义迁移为 skein 结构并清残留。
- **已知**: `skein.py setup` 已跑, manifest = `<粘贴 JSON>`; 决策已定 — **软链保留 `.trellis/spec`** (不删), `.skein/spec` 已软链过去。
- **工作目录与范围**: 仓库根; 改 `.trellis/spec` (经软链原地重组) + `.skein/task/` + `.claude/` trellis 接线。
- **输出格式**: 见 skein-setup agent 定义 (spec 层/类目分布 + task 迁移数 + 清理清单)。
- **验收标准**: `memory.py list` 有分层规则; `skein.py list` 有迁移 task; `.claude/*trellis*` 与 `.trellis/task*` 已清; `.trellis/spec` 软链仍有效。
- **失败处理**: agent 标 `需要:` → main 用 `AskUserQuestion` 转达用户裁定分层/字段歧义。

## 铁律

- **spec 决策 (已拍板)**: `.skein/spec` **软链** → `../.trellis/spec`, 原地重组, **保留 `.trellis/spec`**。清理只删 `.trellis/task*` + `.claude/*trellis*`, 不碰 spec。
- **清理是破坏性操作** — `--purge` 由 agent 在内容迁走后调用; main 派发即视为授权 (用户调 setup = 同意迁移清理)。
- **幂等** — 已初始化重跑不覆盖 (config/spec 存在则跳过); 软链已存在不重建。
- **task.md / task.json 禁手改** — 迁移经 `skein.py create` 等命令, 不直接写 (PreToolUse hook 硬阻)。
