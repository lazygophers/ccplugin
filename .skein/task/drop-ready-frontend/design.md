# 前端清除遗留就绪态 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 测试接缝 (seam)
check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

- [x] 接缝: `plugins/tools/skein/assets/nextjs/src/{components/status.tsx, lib/model.ts, app/board/page.tsx, app/globals.css}` — 状态枚举/元数据/映射表/过滤器全集与色变量, 单一真值链路

## f1 执行记录 (状态枚举与展示层收口)

改动 (worktree 落地, master 侧 `053fe262a` prd/task 已 fast-forward 合入本分支):
- `src/components/status.tsx`: `TaskStatus` 类型删 `ready`; `ST_META` 删 `ready` 条目; `ST_ORDER` 删 `ready`
- `src/lib/model.ts`: `STATUS_MAP` 删 `'就绪'|'待执行'|'ready'` → `'ready'` 的三个映射条目
- `src/app/board/page.tsx`: `ALL_STATUSES`、`DEFAULT_ACTIVE` 两个全集/默认集均删 `ready`
- `src/app/globals.css`: light (`:root`) 与 dark (`.dark`) 两套主题各删一行 `--st-ready`

同名不同义三处确认原样保留 (逐个核对未动):
1. `src/lib/depdag.ts:13,41` — edge kind `"ready"`(依赖已完成的连线配色分类), 与 task 状态枚举无关
2. `src/lib/api.ts:59` — `Task.ready?: boolean`(可被调度器认领的布尔标记), 非状态枚举值
3. `src/app/page.tsx:11` — 首页脚手架文案「脚手架已就绪」, 纯自然语言

未触碰 (越界自查见 `git diff --stat 91ede1caa..HEAD`): `scripts/`、`assets/dist/`、`app/help/page.tsx`(帮助页归 f2)、任何测试文件(归 f3)。

类型检查: `pnpm install && npx tsc --noEmit` — 零报错, 删枚举后所有引用点均已跟进。

## f2 执行记录 (帮助页过时流程文案)

背景: 引擎侧 `concurrency-pools` 合入后状态机改为 `待处理 ⇄ 调研中(research) → confirm(吸收原 start) → 进行中 → check → 检查中 → finishing → 收尾中 → finish → 已完成`, 双池 `pools.work`(执行) / `pools.gate`(验收+收尾)。帮助页 `src/app/help/page.tsx` 仍描述旧 4 态流程(`planning→active→check→done`)且把 `claim exec` 说成「自动 start task」, 二者均已删除/不存在。

改动 (仅 `src/app/help/page.tsx`, 三处 commit):
1. `TASK_FLOW`: 4 态 → 6 态, 补 `research`(调研中)/`finishing`(收尾中) 两卡片; `active` 卡片 `enter` 字段由 `skein claim exec`(误) 改为 `skein confirm`(实际入口, 吸收原 start); `planning` 卡片 `exit` 补 `skein research` 分支
2. 「关键命令速查」表: 删 `["skein claim exec", "全局认领就绪 subtask (自动 start task)"]` 这条错误表述, 改为「认领 ready subtask → running, 竞争 pools.work 槽 (不改 task 状态)」; 补 `skein research`/`skein plan`/`skein finishing` 三条已存在但原表缺失的命令; `claim check` 描述改为「进行中→检查中 或 检查中→收尾中」双职能
3. `FlowDiagram` SVG: 主链由 4 节点扩为 5 节点 (`planning→active→check→finishing→done`), 新增 `research` 作为 `planning` 上方双向支线节点 (⇄ research/plan, 不阻断直接 confirm); 主链 edge label `claim exec` 改为 `confirm`, `claim check` 改为 `check / claim check` 与 `finishing / claim check`

核对证据: 实测 `skein.py --help`(顶层生命周期行 `research⇄plan→confirm→check→finishing→finish→archive`)、`skein.py claim --help`(exec/check 双职能)、`skein.py confirm --help`(吸收 start 的门)、`skein.py research/finishing --help`(均只需 `id`)、`skein.py subtask --help`(确认 subtask 级 `start` 命令仍存在, 未误删)。

验收自证:
- 帮助页无 `start` 命令与「自动 start task」表述 — 全文 grep `start` 仅剩「吸收原 start」历史说明与 subtask 级 `skein subtask start`(实际仍存在的命令), 无误导表述
- 描述与当前 CLI `--help` 实际输出一致 — 卡片/表格/SVG 三处均对照实测 `--help` 输出改写

`npx tsc --noEmit` 零报错。越界自查: `git diff --stat 26916c89d..HEAD` 与 `c10a001b9^..HEAD` 均只涉 `src/app/help/page.tsx`, 未碰 f1 的 status.tsx/model.ts/board.tsx/globals.css。
