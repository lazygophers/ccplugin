# 移除 skein 插件对 harness 内置 task 工具的用法与拦截 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 关键取舍

**取舍 1 · 「清悬挂后台 agent」的承担者** — 该能力天然只有 main 具备：后台 agent 由 main 派出，子 agent 看不到兄弟 agent 的存在。原设计让 finisher 持 `TaskList`/`TaskStop` 本就是把 main 的视野硬塞给子 agent。职责上移是回归正确归属，不是降级。

**取舍 2 · 文档措辞去具名** — skein 文档只声明**目标状态**（「本 task 派出的后台 agent 均已结束」），不声明**达成手段**。手段归 main 的 harness，harness 换了工具名 skein 也不用改。这同时满足了「不出现内置工具名」的硬要求。

**取舍 3 · 拦截 hook 整链删除而非留桩** — `cmd_task_created` 唯一职责就是拦 `TaskCreate`，留空函数是 sediment。连同 `DISPATCH` 键、模块 docstring 行、`_CTX` 上方注释里的引用一并删，避免悬空引用。

## 改动清单 (按文件)

### A 类 · 去调用

| 文件 | 位置 | 动作 |
| --- | --- | --- |
| `agents/skein-finisher.md` | frontmatter `tools:` | 改为 `Read, Bash, Grep, Glob` |
| `agents/skein-finisher.md` | 步骤 2「清悬挂后台 task」整节 | 删除；原步骤 3/4 上提为 2/3 |
| `agents/skein-finisher.md` | `description` | 去掉「清悬挂后台 task」 |
| `agents/skein-finisher.md` | 失败模式表「悬挂残留」行 | 去掉「后台 task 已 TaskStop 的记为已清」 |
| `agents/skein-finisher.md` | 返回 JSON `dangling` 注释 | 去掉「后台task」枚举项 |
| `skills/skein-flow/SKILL.md:129` | finish 载体分工段 | 清后台 agent 从 finisher 职责移出，改挂 main |
| `.../references/for-finish.md:12` | 派发步骤 | 同上，且措辞不具名工具 |
| `.../references/for-finish.md:33` | 失败模式行 | 改为 main 侧的「后台 agent 未结束 → 停手禁 finish」 |
| `.../references/scope-boundary.md:18` | 闭环判据 | 保留判据，去掉工具名与「finisher 自跑」 |

### B 类 · 删拦截

| 文件 | 位置 | 动作 |
| --- | --- | --- |
| `scripts/hooks.py` | `cmd_task_created` 函数 + 上方分节注释 | 整块删 |
| `scripts/hooks.py` | `DISPATCH` 字典 `task-created` 键 | 删 |
| `scripts/hooks.py` | 模块 docstring 第 13 行 | 删 |
| `scripts/hooks.py` | `_CTX` 上方注释第 299 行 | 删该分句，保留同段其余论述 |
| `.claude-plugin/plugin.json` | `TaskCreated` 钩子块 | 整块删，保持 JSON 合法 |
| `docs/skein.md` | hook 表 `task-created` 行 + Guards 表 `TaskCreate 守卫` 行 | 删 |
| `docs/reference.md` | hook 表 `task-created` 行 | 删 |

## 并行安全

A 类与 B 类零文件重叠（A 动 `agents/` + `skills/`，B 动 `scripts/` + `.claude-plugin/` + `docs/`），可并发 2 路，无需串行化。

## 验证

- 全仓 grep 七个工具名零命中（排除缓存目录）
- `python3 -m json.tool plugin.json` 通过
- `hooks.py` 无参跑，用法行不含 `task-created`
- `skein doctor` exit 0
