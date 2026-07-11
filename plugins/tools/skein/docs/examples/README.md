# 样例 `.skein/`

一份**执行中途**的真实 `.skein/` 快照, 对着 [glossary.md](../glossary.md) / [workflow.md](../workflow.md) 看每个文件长啥样、谁维护, 以及跑起来后 `.skein/` 目录里的**实际内容**。全部 json/md 由 `skein.py` / `memory.py` 真跑生成 (非手搓, 仅手写 `prd.md`/`implement.md` 两份 planning 工件)。worktree 路径相对 project root 存盘, 时间字段一律 Unix 时间戳, 状态一律中文。

## 场景: 一条订单流

围绕「电商订单」建了三条 task, 定格在其中一条 exec 中途, **覆盖 task 全部状态 + subtask 全部状态**:

| task | 状态 | 说明 | 落盘位置 |
| --- | --- | --- | --- |
| t01 订单查询接口 | **已完成** (已归档) | 走完 plan→exec→check→finish, worktree 已合并销毁 | `task/archive/2026/07-11/t01/` |
| **t02 订单创建 API** | **进行中** | planning 完, exec 中途 — subtask 覆盖四态 | `task/t02/` |
| t03 订单支付 | **待处理** | 仅 `create` 排队, 未 start, 无 worktree / 无 subtask | `task/t03/` |

无 task 级 focus — t02/t03 无未完成前置, 就绪即可并行, 见顶层 `task.json`。t02 的四个 subtask 恰好各占一态:

| sid | 名称 | 状态 | 含义 |
| --- | --- | --- | --- |
| s1 | 请求参数校验 | **已完成** | 跑完, 释放并发槽 |
| s2 | 库存扣减 | **运行中** | 正在跑 (占一个并发槽) |
| s3 | 订单落库 | **失败** | 首跑失败 (幂等键冲突), 待重试 |
| s4 | 订单创建事件 | **待处理** | 依赖 s3, s3 已完成前不就绪 |

> 这正是 `subtask claim` 跑到一半的样子: 首轮认领 s1+s2 (并发 2), s1 先完成、s3 补位后失败; 真实调度环下一步会 `subtask start t02 s3` 重试, 成功后 s4 才就绪。

## 文件导览

| 文件 | 是什么 | 谁维护 · AI 可否读写 |
| --- | --- | --- |
| `.gitignore` | `init` 生成: 忽略 `task.md`/`task.html` (自动渲染, 从 task.json 无损重建); `init` 另把 worktree_root 补到**仓库根** `.gitignore` | 脚本生成 · 一次性 |
| `config.yaml` | 插件配置 (`max_active`/`max_parallel`/`auto_commit`/`worktree_root`) | 用户手改 · AI 可读 |
| `task.json` | 顶层状态汇总 `{tasks:[{id,状态,deps,worktree}]}` — 全部未归档 task 一览 | **脚本** · AI 禁读写 (guard 硬阻) |
| `task.md` | 顶层看板 (t02 进行中 / t03 待处理, 由 task.json 渲染) | **脚本** · AI 禁读写 |
| `task.html` | 可视化看板: 任务进展总览 + 每 task 耗时/预期 + 子任务完成% (莫兰迪配色, 由 task.json 渲染) | **脚本** · `skein.py view` 打开 |
| `task/t02/task.json` | 单 task 记录 + subtask DAG (`subtasks[]`) + `contracts[]` | **脚本** · AI 禁读写 |
| `task/t02/task.md` | 子任务看板 (四态一览) | **脚本** · AI 禁读写 |
| `task/t02/prd.md` | planning 工件: 需求 + 契约 + 验收 | skein-planning · **AI 可读写** |
| `task/t02/implement.md` | planning 工件: subtask 拆分 + mermaid 调度图 + 落盘命令 | skein-planning · **AI 可读写** |
| `task/t02/journal.md` | append-only 过程记录 | AI 追加 · 随 task 归档 |
| `task/t03/*` | 排队 task, 仅 create 未 start (无 prd/worktree) | 同上 |
| `task/archive/2026/07-11/t01/*` | 已完成归档 task (按完成日期分层) | **脚本** · 只读留痕 |
| `spec/index.md` + `core/`/`recall/` | 两层规则记忆库 (差异化核心) | **`memory.py`** · AI 经命令沉淀/召回 |

## 两层规则记忆 (差异化核心)

`spec/` 是 SKEIN 区别于普通 TODO 工具的地方 — 踩过的坑落盘成规则, 下个 task 自动带上。样例里四条规则跨四个类目:

- `spec/core/git/t01-00.md` — **core** (常驻注入): "finish 前 `go test ./...` 全绿"。
- `spec/core/domain/t02-01.md` — **core**: "金额一律整数分, 禁 float"。
- `spec/recall/arch/t02-00.md` — **recall** (按需召回): "订单幂等键 + 库存 Redis 原子扣减约定"。
- `spec/recall/test/t03-01.md` — **recall**: "订单状态机测试覆盖要求"。

core 层每 session 由 SessionStart hook 注入**极简索引** (仅标题, 全文按需 `inject-core`, token 硬预算守卫); recall 层 planning 时 `memory.py recall <query>` 粗筛命中, model 再读全文定用否。文件命名 `<source>-<seq>.md` (source=沉淀它的 task id), frontmatter 带 title/layer/category/keywords/source。类目 (git/domain/arch/test) = 层内物理子目录, 自由建。

## 怎么用这份样例

```bash
# 复制到你的 repo 试跑 (脚本会拿它当已存在的工作区)
cp -r plugins/tools/skein/docs/examples/sample-skein /path/to/your-repo/.skein
cd /path/to/your-repo
python3 <skein>/scripts/skein.py current             # 列 active task (t02, 无 focus)
python3 <skein>/scripts/skein.py list                # 含归档的 t01
python3 <skein>/scripts/skein.py subtask list t02    # 看 subtask 四态 DAG
python3 <skein>/scripts/memory.py recall 幂等         # 召回 recall 规则
```

> 直接 `cat .skein/task.json` 能看内容, 但**真实流程里 AI 禁读写这些脚本管理的文件** — guard PreToolUse hook 会拦。取态一律走 `skein.py` / `memory.py` 命令 stdout。
