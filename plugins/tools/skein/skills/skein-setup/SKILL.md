---
name: skein-setup
description: SKEIN 工作区初始化 + 结构维护。未初始化仓库 (无 .skein/ 或 SessionStart 提示) 一键 scaffold; 已初始化时按需手动优化 .skein 结构 (spec 类目重组 / core↔recall 层调 / config 调参), 改盘后 reindex。既有 trellis 仓迁移见 references/trellis-migration.md。幂等可重跑。
argument-hint: "[trellis 迁移模式: 缺省=兼容保留 .trellis 数据, 完全删除 .trellis]"
arguments: "[trellis 迁移模式: 缺省=兼容保留 .trellis 数据, 完全删除 .trellis]"
model: sonnet
effort: medium
user-invocable: true
---

# skein-setup — 初始化 / 结构维护

两用途：**① 未初始化仓库 → 建 `.skein/` 工作区**；**② 已初始化 → 手动优化 `.skein/` 结构**。**幂等** — 重跑安全。

> 触发: 用户显式 `/skein-setup`, 或 SessionStart hook 注入「无 `.skein/`」提示后 main 主动调用。

## 分流

```bash
skein setup   # 幂等 scaffold + 输出 manifest JSON
```

| manifest / 现状                             | 用途                               | 见                                |
| ------------------------------------------- | ---------------------------------- | --------------------------------- |
| 无 `.skein/` (`trellis_present:false`)      | **① 初始化** — main 直接跑, 纯机械 | 下 §初始化                        |
| 已有 `.skein/`                              | **② 结构维护** — 用户手动优化      | 下 §结构维护                      |
| 检测到 `.trellis/` (`trellis_present:true`) | ① 的一种场景 — 派 agent 语义迁移   | `references/trellis-migration.md` |

## ① 初始化 (未初始化仓库)

1. **新仓** → main 直接跑 `skein setup` (纯机械, 不派 agent): 建 `.skein/` + config + gitignore + 本地 `.skein/spec` 库。完成即可用。
2. **既有 trellis 仓 (`.trellis/`)** → 🛑 检测到 `.trellis/` 时 main 用 `AskUserQuestion` 让用户选迁移模式 (缺省兼容 · STOP, `--full` 整删不可逆): 兼容 (留 `.trellis/` 数据) / `--full` (整删 `.trellis/`); 接线 (hooks/scripts/settings) 两模式都删。据选定跑 `setup` 或 `setup --full`, 语义迁移 (派 skein-setup agent) 详见 `references/trellis-migration.md`。

## ② 结构维护 (已初始化, 用户手动优化)

用户想调整 `.skein/` 布局时用。可调项 + 落地方式：

| 想改                                                                                | 怎么改                                                 | 收尾                                  |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------- | ------------ |
| 并发上限 (max_active / max_parallel)                                                | 直接 Edit `.skein/config.yaml`                         | 无                                    |
| spec 类目重组 (类目 = 层内子目录, 自由取名 git/test/arch/build/style/domain/ops...) | 移动 / 改名 `.skein/spec/<layer>/<category>/*.md`      | `skein-spec reindex`                   |
| core↔recall 层调 (core 常驻过重, >8000 字符会告警)                                  | 把规则文件从 `spec/core/` 移到 `spec/recall/` (或反向) | `skein-spec reindex`                   |
| 新增一条规则                                                                        | `skein-spec sediment --layer <core                      | recall> --category <cat> --title <T>` | 自动 reindex |

- **改 spec 盘后必 `reindex`** — 索引 (三份 index.md) 落后于实际盘面 = 召回失效。
- **task.json / task.md 禁手改** — 经 `skein create/start/...` 命令维护, PreToolUse hook 硬阻直接写。

## 铁律 (通用)

- **幂等** — 已初始化重跑不覆盖 (config/spec 存在则跳过); `.skein/spec` 已存在则不重复拷贝。
- **spec 盘面变更后 reindex** — 手动重组 / 迁移后同步索引。
- **task 状态经脚本** — 不直接编辑 `.skein/task*`。

## ❌ 反例 (命中=操作错误)

> 🔒 Iron Law: 幂等可重跑; task.json/task.md 经脚本不经手改 (PreToolUse hook 硬阻)。

| 禁                                     | 为什么                                    | 改为                                      |
| -------------------------------------- | ----------------------------------------- | ----------------------------------------- |
| 手改 `.skein/task*` 绕过脚本           | PreToolUse hook 硬阻 + 破坏索引一致性     | 经 `skein create/start/...` 命令       |
| 改 spec 盘面后不 reindex               | 三份 index.md 落后盘面 = 召回失效         | 必跑 `skein-spec reindex`                  |
| 检测到 `.trellis/` 直接 `setup --full` | 未问用户就整删可能丢数据                  | 先 `AskUserQuestion` 选兼容 / `--full`    |
| 已初始化仓重跑当报错                    | setup 幂等, 重跑安全不覆盖                 | 正常重跑, config/spec 存在则跳过          |
| 什么都堆进 core 常驻                    | >8000 字符告警, 稀释硬约束                 | 默认 recall, core 只留命令式硬契约        |

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                        | 一线修复                              | 仍失败兜底                                  |
| --------------------------- | ------------------------------------- | ------------------------------------------- |
| `skein setup` 报错       | 读 manifest JSON `error` 字段定位 (权限 / 路径占用 / 已存在) | 仍失败 → 报用户, 禁手工拼凑 `.skein/`       |
| `skein-spec reindex` 报错    | 读 stderr 定位 (类目名非法 / 路径)    | 仍失败 → 停手报用户, 禁半写坏索引            |
| trellis 迁移中断            | 数据仍在 `.trellis/` (兼容模式未删), 重跑迁移 | 仍中断 → 报用户, 禁手工拼凑 `.skein/`       |
