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
