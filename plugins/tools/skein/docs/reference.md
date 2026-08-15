# 参考手册

## CLI

### skein

| 命令                                                                              | 用途                                                                                                                                                                                                                                       |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `skein init`                                                                      | 初始化 .skein/ 工作区                                                                                                                                                                                                                      |
| `skein doctor`                                                                    | 健康检查                                                                                                                                                                                                                                   |
| `skein task create <id> [--name] [--desc] [--deps] [--repos]` | 创建 task                                                                                                                                                                                                                                  |
| `skein task research <id>`                                                        | 待处理→调研中: 需已登记 ≥1 `--phase research` subtask                                                                                                                                                                                      |
| `skein task plan <id>`                                                            | 调研中→待处理: 需调研 subtask 全 done, 收敛回规划                                                                                                                                                                                          |
| `skein task confirm <id> [--summary\|--approved]`                                 | 用户确认门, **吸收原 `start`**: 待处理→进行中, 一步做完 doctor 体检 + 建 worktree (不校验前置 task 进度 — 依赖门在 claim 取活时判)。裸跑非 TTY 会拒。`--summary` 只打印 PRD 审核摘要不改状态; `--approved` = 已在 `AskUserQuestion` 拿到用户批准                                |
| `skein task check <id>`                                                           | 进行中→检查中                                                                                                                                                                                                                              |
| `skein task finishing <id>`                                                       | 检查中→收尾中: 占 gate 池槽位 (`pools.gate`)                                                                                                                                                                                               |
| `skein task finish <id>`                                                          | 收尾中→已完成: commit→merge→销 worktree (归档=保留期后自动, 非 finish 步)                                                                                                                                                                  |
| `skein task rename <id> [--id <new-id>] [--name <新标题>]`                        | 重命名 task id / 标题                                                                                                                                                                                                                      |
| `skein del <id> [<sid>]` `[--dry-run]`                                            | 软删: 整 task 移入 `.skein/trash/`; 给 sid 则只删该 subtask。`--dry-run` 只打印将删什么                                                                                                                                                    |
| `skein list [--status <态>]`                                             | 列 task。`--status` 取 plan/research/exec/check/finishing/finish/done (或 待处理/调研中/进行中/检查中/收尾中/已完成, 等价 pending/active 别名同收), 逗号多选; `open`/`plan`=待处理阶段 (未开工), `unfinished`=全部未完成, `all`=不筛。缺省输出固定为 JSON 对象信封 `{"tasks": [{id,status,name,desc,deps,repos,worktree,worktrees,priority,pct,subs,ready}, ...]}`；`status` 固定是英文枚举 `pending\|research\|active\|check\|finishing\|done` (中文名与阶段别名只用于 `--status` 入参, 不出现在 JSON 输出里)；消费方从 `.tasks[]` 读取、取单个 tid 用 `jq -r '.tasks[0].id'`，禁止按裸数组 `.[]` 解析或与中文展示名比较。 |
| 全局 flag `-h/--help`                                                        | 所有命令与子命令组通用, 两者完全等价 (`skein subtask add -h` 与 `--help` 同效); 每条子命令的必填/可选参数都在自己的 `-h` 里, 不必翻文档 |
| 全局 flag `--show`                                                           | 所有命令 (除 serve) 通用: dict 结果改 rich 面板渲染 (人读); 缺省是 JSON, **没有 `--json`** (JSON 本就是缺省)。与 `-d/--debug` 同为全局 flag, 可置任意位置, 位置参数不受影响。`skein status` 有专用渲染, 其余命令走通用面板 |
| `skein status [--show]`                                                        | 全局运行态概览 (只读, 无建议字段): work/gate 两池占用 + 执行中 subtask + 就绪待派计数 + 状态统计。默认 JSON 精简形态: `running_subtasks[]` 只含 `{tid,sid,name,status}`, `active_tasks/plan_tasks/gate_tasks[]` 只含 `{id,name,status}` (调度细节走 `--show` 或 `flow run --dry-run`); `--show` 的 rich 渲染含阶段/进度/已跑/工时/依赖阻塞等完整细节。单 task 详情仍走 `skein task status <tid>` |
| `skein board`                                                                     | 文本看板                                                                                                                                                                                                                                   |
| `skein serve --open`                                                              | 可视化看板                                                                                                                                                                                                                                 |
| `skein task deps <id> [--set <id1,id2>]`                                          | 无 `--set` 只查; 带则设前置 (仅 pending 且无既有 deps 可写, 脚本查自引用/不存在/成环)                                                                                                                                                      |
| `skein subtask add/claim/ready/start/check/show/done/fail/list <task-id\|all> [sid]` | subtask 管理 (add 登记, `--name <str> --desc <str> --estimate <小时>` 必填 / claim 整批认领就绪 / ready 只读预览 / start 单个占槽 / check 勾验收 / show 查全字段 / done 完成 / fail 失败 / list 列态; list 收 `--status pending\|running\|done\|failed` 过滤, tid=`all` 跨全部 task 合并 (查全局 running: `skein subtask list all --status running`)) |
| `skein claim exec\|check`                                                         | 全局跨 task 认领批; phase 必填: `exec`=认领 ready subtask → running / `check`=认领 全done 的 进行中 task → 检查中 + 检查通过的 → 收尾中 (占 gate 槽, 待 finisher 跑 finish)                                                                |
| `skein task spec <task-id> [--desc] [--should] [--not] [--acceptance]`             | TaskSpec 四要素读写 (落盘 prd.md frontmatter, task.json 不存); 列表 `;` 分号分隔; 不带参数 = 只读回显; confirm 后锁定                                                                                                                       |
| `skein research add/list/show/start/done/fail <task-id> [sid]`                     | research 任务清单 (research_tasks, 与 exec subtask 分列): add 必填 sid/name/desc/estimate; 全 done 后 `task plan` 收敛回规划                                                                                                                 |

### skein-spec

| 命令                                                     | 用途                                                                                                                                          |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`                                                   | 初始化 spec 目录                                                                                                                              |
| `reindex`                                                | 重建各层 index.md + 顶层总索引 (改盘后同步)                                                                                                   |
| `recall <query>`                                         | 按关键词 FTS5 BM25 排序 recall                                                                                                                |
| `sediment [--namespace <ns>] [--inclusion] [--category]` | 沉淀一条规则 + 自动 reindex                                                                                                                   |
| `analyze`                                                | [只读] 五类一致性核查: 验收覆盖率/硬规冲突/范围蔓延/proposed 置信度/接缝存在性                                                                |
| `list`                                                   | 列已存规则                                                                                                                                    |
| `maintain [--apply]`                                     | 全量体检 (按 namespace 判据分表: 超预算/stale/断链含anchors/keywords重复/废弃/孤立/配置问题); --apply 自动修复 (断链/配置问题/report类只报告) |
| `degrade`                                                | always→auto 单文件降级 (仅改 inclusion frontmatter + reindex + 审计, 不移动文件)                                                              |
| `archive`                                                | [完全重构前] 可逆归档旧规则到 .archive/<ts>/ + reindex                                                                                        |
| `restore`                                                | 从归档恢复规则 (撞名不覆盖新规则, 加 restored- 前缀并存)                                                                                      |
| `restructure`                                            | 按映射把碎片文件合并进主题文件 (源进 .archive/, 可 restore 回滚)                                                                              |
| `map`                                                    | [只读] 现算目录树+符号+行数 (不写盘)                                                                                                          |
| `amend`                                                  | 改写既有章节正文, 其余章节与 frontmatter 逐字不动; 改前 archive 旧版; --rename-section 同步更新反链; 后自动 reindex                           |
| `finish-candidates`                                      | [finish 用] 为 task 生成候选 product wiki 页 (三路降级: anchors反查→prd关键词recall→皆无建议新建)                                             |
| `-d, --debug`                                            | rich 美化叙事到 stderr — 展示命令与参数 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)                                                             |

> Hook 内部入口不作为用户命令暴露; 技术细节见 [hooks.md](hooks.md)。

### Config

| 键                       | 默认               | 说明                                                                          |
| ------------------------ | ------------------ | ----------------------------------------------------------------------------- |
| pools.work               | 2                  | exec+research 共享的全局 running subtask 槽                                   |
| pools.gate               | 3                  | 检查中+收尾中共享的全局 task 槽                                               |
| retain_days              | 7                  | 归档保留天数                                                                  |
| auto_commit              | true               | 原地模式 finish 时自动 git commit; worktree 模式恒强制 commit, 本键不参与判定 |
| worktree_root            | `.worktrees`       | worktree 路径                                                                 |
| spec.always_budget       | 1000               | always 页常驻注入软预算 (char); 旧键 spec_core_budget 已废弃仍作 fallback     |
| board_theme/palette/mode | default/blue/light | 看板样式                                                                      |

`hooks` (阶段钩子 + agent 钩子) 是可选特性, 不在 `CONFIG_DEFAULTS` 里 (无默认值, `init`/展示均不含),
需手写进 `config.yaml`, 详见 [hooks.md](hooks.md)。

---

## 场景用法

### 请求路由

| 特征               | 路由   | 入口                             |
| ------------------ | ------ | -------------------------------- |
| 纯查询/单文件小改  | inline | Claude 直接改                    |
| 跨文件/多步/破坏式 | flow   | 明确说“走 skein-flow 闭环”或自动 |
| 模糊/边界不清      | grey   | AskUserQuestion                  |

### 场景表

| #   | 场景         | 例              | 要点                              |
| --- | ------------ | --------------- | --------------------------------- | ------------------ |
| 1   | 单功能开发   | 加手机号登录    | brainstorm 选型, grill  |
| 2   | 破坏式重构   | User→UserDTO    | 全站 grep 一次改, worktree 可丢弃 |
| 3   | 调研选型     | 选队列方案      | researcher 只读, 结论→sediment    |
| 4   | 多 task 并行 | 导出+样式       | `--deps` 声明, pools.work=2       |
| 5   | 根因 bug     | 金额差 1 分     | 共享函数修, 补回归测试            |
| 6   | 模糊请求     | —               | 自动按信号路由                    |
| 7   | 中途出问题   | exec/check 卡住 | 自愈→根因复盘                     | 软删走 `skein del` |
| 8   | 冷启动空仓   | 空 spec/        | bootstrap 扫 5 维, 默认 recall    |
| 9   | 清理残留     | 孤儿 worktree   | `/skein-clean`                    |
| 10  | 大需求冷启动 | 「重构支付」    | 愿景翻译→多 task + deps, grill 3 轴 |

### 错误处理

| 阶段   | 失败           | 重试            | 兜底             |
| ------ | -------------- | --------------- | ---------------- |
| exec   | subtask 报错   | 重派 ≤2 轮      | 停手回传         |
| check  | lint/type/test | 修复重跑        | 第 3 轮根因复盘  |
| finish | 合并冲突       | auto abort→手动 | 禁强解           |
| 任意   | 方案跑歪       | —               | `skein del` 软删 |

---

## 术语

### 核心概念

| 术语       | 定义                                                                 |
| ---------- | -------------------------------------------------------------------- |
| task       | SKEIN 管理的闭环工作记录                                             |
| subtask    | task 内最小执行单元, DAG 调度                                        |
| 闭环       | plan→exec→check→finish, 不可跳步                                     |
| worktree   | git worktree, 1 task 1 物理隔离                                      |
| board      | task.md + task.html, 从 task.json 渲染                               |
| spec       | 规则记忆库 (namespace × inclusion)                                   |
| core       | 违反即错, 每 session 自动注入                                        |
| recall     | 值得参考, 按关键词召回                                               |
| sediment   | finish 判 learning → namespace×inclusion / drop                      |
| compaction | SessionStart 对活跃 task 状态压缩重注入                              |

### 状态

| 状态             | 含义                                                                                                                 | 占 active 槽 |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- | ------------ |
| 待处理           | 规划中 (未过 confirm 用户门)                                                                                         | 否           |
| 就绪             | 规划完成待启动 (已过 confirm, 可 start)                                                                              | 否           |
| 进行中           | 正在 worktree 中执行                                                                                                 | 是           |
| 检查中           | subtask 全完成, 质量门验证                                                                                           | 否           |
| 已完成           | 检查通过, 等待归档                                                                                                   | 否           |
| (已归档)         | 完成后 \_autoclean 目录迁移到 archive/, 非状态值·不在看板; 关联链 (deps + parent/child) 上有未完成 task 时整链不归档 | —            |
| 运行中 (subtask) | 正在执行                                                                                                             | —            |
| 失败 (subtask)   | 执行失败, 可重试                                                                                                     | —            |

### Signal Routing

| 术语                       | 定义                  |
| -------------------------- | --------------------- |
| flow                       | 复杂请求→建 task 闭环 |
| inline                     | 简单请求→直接改       |
| grey                       | 模糊→AskUserQuestion  |
| 明确说“走 skein-flow 闭环” | 强制 flow 信号        |
