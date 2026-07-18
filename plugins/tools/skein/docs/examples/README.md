# 样例 `.skein/`

一份**执行中途**的真实 `.skein/` 快照, 对着 [glossary.md](../glossary.md) / [workflow.md](../workflow.md) 看每个文件长啥样、谁维护, 以及跑起来后 `.skein/` 目录里的**实际内容**。全部 json/md 由 `skein` / `skein-spec` 真跑生成 (非手搓, 仅手写 `prd.md`/`design.md`/`findings.md` 三份 planning 工件)。worktree 路径相对 project root 存盘, 时间字段一律 Unix 时间戳, 状态一律中文。

## 场景: 一条订单流

围绕「电商订单域」建了 **10 条 task** (7 在看板 + 3 已归档), 定格在多条并行推进的中途, **覆盖 task 全部状态 + subtask 全部状态 + 显式依赖 DAG**:

| task | 状态 | 说明 | 落盘位置 |
| --- | --- | --- | --- |
| **order-create-api 订单创建 API** | **进行中** | exec 中途 — 4 subtask 覆盖四态 | `task/order-create-api/` |
| payment-gateway 支付网关对接 | **检查中** | exec 完, 质量门验证中 — subtask 全已完成 | `task/payment-gateway/` |
| inventory-service 库存服务 | **进行中** | exec 中途 — subtask 混合态 + 依赖链 | `task/inventory-service/` |
| order-pay 订单支付 | **待处理** | 依赖 order-create-api, 已 plan 出 3 subtask (全待处理) | `task/order-pay/` |
| refund-flow 退款流程 | **待处理** | 依赖 order-pay+payment-gateway, 已 plan 出 subtask (全待处理) | `task/refund-flow/` |
| order-report 订单报表导出 | **待处理** | 依赖 order-create-api, 已 plan 出 3 subtask | `task/order-report/` |
| notification-service 消息通知服务 | **待处理** | 依赖 payment-gateway, 已 plan 出 3 subtask | `task/notification-service/` |
| order-query 订单查询接口 | **已完成** (归档) | 走完全闭环, worktree 已合并销毁 | `task/archive/2026/07-11/order-query/` |
| user-auth 用户认证中间件 | **已完成** (归档) | 前一日完成 | `task/archive/2026/07-10/user-auth/` |
| api-gateway API 网关脚手架 | **已完成** (归档) | 更早完成 | `task/archive/2026/07-09/api-gateway/` |

无 task 级 focus — 就绪 task (前置全 done + 文件不冲突) 皆可并行, 见顶层 `task.json`; 归档 task 不进看板。order-create-api 的四个 subtask 恰好各占一态:

| sid | 名称 | 状态 | 含义 |
| --- | --- | --- | --- |
| s1 | 请求参数校验 | **已完成** | 跑完, 释放并发槽 |
| s2 | 库存扣减 | **运行中** | 正在跑 (占一个并发槽) |
| s3 | 订单落库 | **失败** | 首跑失败 (幂等键冲突), 待重试 |
| s4 | 订单创建事件 | **待处理** | 依赖 s3, s3 已完成前不就绪 |

> 这正是 `subtask claim` 跑到一半的样子: 首轮认领 s1+s2 (并发 2), s1 先完成、s3 补位后失败; 真实调度环下一步会 `subtask start order-create-api s3` 重试, 成功后 s4 才就绪。

每个 subtask 还带 `agent` (执行 agent, 省略默认 `skein-executor`) + `skills` (关联 skills, 0-n) 两字段 — main 按此 dispatch。样例里 s1 关联 `input-validation` skill, s2 无 skill (纯 0), 演示 0-n 范围。

## 文件导览

| 文件 | 是什么 | 谁维护 · AI 可否读写 |
| --- | --- | --- |
| `.gitignore` | `init` 生成: 忽略 `task.md`/`task.html`/`board/` (自动渲染, 从 task.json 无损重建); `init` 另把 worktree_root 补到**仓库根** `.gitignore` | 脚本生成 · 一次性 |
| `config.yaml` | 插件配置 (`max_active`/`max_parallel`/`retain_days`/`auto_commit`/`worktree_root`/`board_theme`/`board_palette`/`board_mode`) | 用户手改 · AI 可读 |
| `task.json` | 顶层状态汇总 `{tasks:[{id,状态,deps,worktree}]}` — 全部未归档 task 一览 | **脚本** · AI 禁读写 (guard 硬阻) |
| `task.md` | 顶层看板 (order-create-api 进行中 / order-pay 待处理, 由 task.json 渲染) | **脚本** · AI 禁读写 |
| `task.html` | 可视化看板 (title/标题带项目名, 2 列 dashboard + 满宽概览 banner): 任务进展总览 (预期/已耗/剩余合计 + 综合 & 预估加权完成率 + 预计执行顺序图) + 每 task 耗时/预期时间条 + 子任务完成% + 「明细」折叠区 (subtask DAG + 子任务表, 默认展开, 可手动收起保紧凑) (4 主题 6 配色 深浅色, 页内切换器, 由 task.json 渲染) | **脚本** · `skein view` 打开 |
| `board/` | 主题/配色 CSS (base + themes/ + palettes/, 从插件 `assets/board/` 拷贝, 看板 html 相对路径 `<link>` 引入) | **脚本** · git 忽略 |
| `task/order-create-api/task.json` | 单 task 记录 + subtask DAG (`subtasks[]`) + `contracts[]` | **脚本** · AI 禁读写 |
| `task/order-create-api/task.md` | 子任务看板 (四态一览) | **脚本** · AI 禁读写 |
| `task/order-create-api/prd.md` | planning 主入口: 分章节 (目标/边界/验收标准/索引, 每章节自带 TODO) + 索引区 (链 design/findings/task.json) | skein-plan · **AI 可读写** |
| `task/order-create-api/design.md` | planning 详细设计: 架构/数据流/取舍/选型 (不含调度图) | skein-plan · **AI 可读写** |
| `task/order-create-api/findings.md` | planning 调研收敛结论 (过程笔记存 research/) | skein-plan · **AI 可读写** |
| `task/order-pay/*` | 待处理但已 plan 出 subtask (未 start, 无 prd/worktree); order-report/notification-service 同类 | **脚本** · AI 禁读写 |
| `task/refund-flow/*` | 待处理但已 plan 出 subtask (subtask 全待处理) — 展示"排队 + 已拆分" | **脚本** · AI 禁读写 |
| `task/archive/<年>/<月-日>/<id>/*` | 3 个已完成归档 task (order-query/user-auth/api-gateway, 按完成日期分层) | **脚本** · 只读留痕 |
| `spec/index.md` + `core/`/`recall/` | 两层规则记忆库 (差异化核心) | **`skein-spec`** · AI 经命令沉淀/召回 |

## 两层规则记忆 (差异化核心)

`spec/` 是 SKEIN 区别于普通 TODO 工具的地方 — 踩过的坑落盘成规则, 下个 task 自动带上。样例里四条规则跨四个类目:

- `spec/core/git/order-query-00.md` — **core** (常驻注入): "finish 前 `go test ./...` 全绿"。
- `spec/core/domain/order-create-api-01.md` — **core**: "金额一律整数分, 禁 float"。
- `spec/recall/arch/order-create-api-00.md` — **recall** (按需召回): "订单幂等键 + 库存 Redis 原子扣减约定"。
- `spec/recall/test/order-pay-01.md` — **recall**: "订单状态机测试覆盖要求"。

core 层每 session 由 SessionStart hook 注入**极简索引** (仅标题, 全文按需 `inject-core`, token 硬预算守卫); recall 层 planning 时 `skein-spec recall <query>` 粗筛命中, model 再读全文定用否。文件命名 `<source>-<seq>.md` (source=沉淀它的 task id), frontmatter 带 title/layer/category/keywords/source。类目 (git/domain/arch/test) = 层内物理子目录, 自由建。

## 怎么用这份样例

```bash
# 复制到你的 repo 试跑 (脚本会拿它当已存在的工作区)
cp -r plugins/tools/skein/docs/examples/sample-skein /path/to/your-repo/.skein
cd /path/to/your-repo
skein current             # 列 active task (order-create-api, 无 focus)
skein list                # 含归档的 order-query
skein subtask list order-create-api    # 看 subtask 四态 DAG
skein-spec recall 幂等         # 召回 recall 规则
```

> 直接 `cat .skein/task.json` 能看内容, 但**真实流程里 AI 禁读写这些脚本管理的文件** — guard PreToolUse hook 会拦。取态一律走 `skein` / `skein-spec` 命令 stdout。
