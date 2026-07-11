---
name: skein-setup
description: SKEIN 工作区初始化 + 结构维护。未初始化仓库 (无 .skein/ 或 SessionStart 提示) 一键 scaffold; 已初始化时按需手动优化 .skein 结构 (spec 类目重组 / core↔recall 层调 / config 调参), 改盘后 reindex。既有 trellis 仓迁移见 references/trellis-migration.md。幂等可重跑。
disable-model-invocation: true
user-invocable: true
---

# skein-setup — 初始化 / 结构维护

两用途：**① 未初始化仓库 → 建 `.skein/` 工作区**；**② 已初始化 → 手动优化 `.skein/` 结构**。**幂等** — 重跑安全。

> 触发: 用户显式 `/skein-setup`, 或 SessionStart hook 注入「无 `.skein/`」提示后 main 主动调用。

## 分流

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py setup   # 幂等 scaffold + 输出 manifest JSON
```

| manifest / 现状                             | 用途                               | 见                                |
| ------------------------------------------- | ---------------------------------- | --------------------------------- |
| 无 `.skein/` (`trellis_present:false`)      | **① 初始化** — main 直接跑, 纯机械 | 下 §初始化                        |
| 已有 `.skein/`                              | **② 结构维护** — 用户手动优化      | 下 §结构维护                      |
| 检测到 `.trellis/` (`trellis_present:true`) | ① 的一种场景 — 派 agent 语义迁移   | `references/trellis-migration.md` |

## ① 初始化 (未初始化仓库)

新仓 **main 直接跑** `skein.py setup` (纯机械, 不派 agent): 已建 `.skein/` + config + gitignore + 本地 `.skein/spec` 库。完成即可用。

既有 trellis 仓 (`.trellis/`) → 见 `references/trellis-migration.md` (派 skein-setup agent 语义迁移)。

## ② 结构维护 (已初始化, 用户手动优化)

用户想调整 `.skein/` 布局时用。可调项 + 落地方式：

| 想改                                                                                | 怎么改                                                 | 收尾                                  |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------- | ------------ |
| 并发上限 (max_active / max_parallel)                                                | 直接 Edit `.skein/config.yaml`                         | 无                                    |
| spec 类目重组 (类目 = 层内子目录, 自由取名 git/test/arch/build/style/domain/ops...) | 移动 / 改名 `.skein/spec/<layer>/<category>/*.md`      | `memory.py reindex`                   |
| core↔recall 层调 (core 常驻过重, >8000 字符会告警)                                  | 把规则文件从 `spec/core/` 移到 `spec/recall/` (或反向) | `memory.py reindex`                   |
| 新增一条规则                                                                        | `memory.py sediment --layer <core                      | recall> --category <cat> --title <T>` | 自动 reindex |

- 🔴 **改 spec 盘后必 `reindex`** — 索引 (三份 index.md) 落后于实际盘面 = 召回失效。
- ⛔ **task.json / task.md 禁手改** — 经 `skein.py create/start/...` 命令维护, PreToolUse hook 硬阻直接写。

## 铁律 (通用)

- **幂等** — 已初始化重跑不覆盖 (config/spec 存在则跳过); 软链已存在不重建。
- **spec 盘面变更后 reindex** — 手动重组 / 迁移后同步索引。
- **task 状态经脚本** — 不直接编辑 `.skein/task*`。
