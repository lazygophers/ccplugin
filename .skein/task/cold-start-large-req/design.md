# cold-start-large-req — 最终设计(用户拍板,可进 exec)

## 3 条硬约束

1. 插件内闭环(禁外部 skill 依赖)
2. 不加新入口(从 flow/自动识别进)
3. 禁补丁,保简洁省 token

## 用户拍板结论(4 轮 AskUserQuestion)

| 点 | 结论 |
|---|---|
| 触发判据 | 信号判据自动触发(无动词/无路径/<15字/愿景腔) |
| prd 模板 | **不内置加段** — 改为引入 supertask 载体(见下) |
| grill 轴 | 全加 3 轴(SMARC + drift + scope) |
| strangler | 并入现有 breaking-refactor.md |
| 载体语义 | **supertask / task 父子结构**(非 vision 聚合器) |
| 页面同步 | 全同步 + supertask 下加聚合看板 |
| 创建时机 | brainstorm 后判大需求才建,末 task finish 归档 |
| 命名 | supertask(父) / task(子) |
| 递归深度 | 限 2 层 task(supertask→task)+ subtask 叶 |

## 核心设计:两层结构 + 内化增强

### 1. supertask / task 父子层(结构核心)

**语义**:一个需求过大 → 建 supertask → 拆多个 child task。每 child task = 独立小需求,各自完整 plan→exec→check→finish。supertask 是聚合层(本身不执行 subtask)。

**与现有区分**:
- supertask = 大需求聚合(本身无 subtask DAG,只聚合 child task)
- task = 独立小需求(各自 plan/exec/check/finish + subtask DAG)
- subtask = task 内执行节点(现有不变,无独立 plan)

**深度硬限**:supertask → task → subtask,3 层封顶。child task 可拆 subtask 但禁再生 child。

### 2. 数据结构改动(task.json)

task.json 现状:`{tasks:[{id,status,deps,worktree}]}`

加字段:
- task 对象加 `parent: <supertask-id> | null`(child task 指回父)
- supertask 也是 task 对象(`status` 字段复用,聚合态:待处理/进行中/已完成),`parent: null`,加 `kind: "supertask" | "task"` 区分(或 supertask 有 child_ids 数组)
- supertask 目录:`.skein/task/<supertask-id>/` 含 `prd.md`(愿景 Job Story + Open Questions + Assumptions + 非目标)+ `vision.md`(聚合看板,脚本渲染)

### 3. 目录结构改动

```
.skein/task/
├── <supertask-id>/          # 大需求聚合(无 subtask DAG)
│   ├── prd.md               # 愿景(Job Story)+ Open Questions + Assumptions + 非目标
│   ├── design.md            # supertask 级设计(child task 拆解策略)
│   ├── vision.md            # 聚合看板(脚本渲染:child task 进度汇总,禁手编)
│   └── task.json            # 脚本维护(含 child_ids)
├── <child-task-id>/         # 独立小需求(各自完整)
│   ├── prd.md / design.md / findings.md / research/
│   └── task.json / task.md  # 各自 subtask DAG
```

> **不加新顶层文件夹** — 复用 `.skein/task/`,supertask 和 child task 都在 task/ 下,靠 `parent` 字段 + `kind` 区分。用户原说「新文件夹同级」,实际需求是「父聚合层」,复用 task/ 更省概念(约束 3)。

### 4. 内化增强(方向 D 保留)

| 机制 | 触点 | 形态 |
|---|---|---|
| Job Story 愿景翻译 | brainstorm 第一步(信号判据触发) | supertask prd.md「愿景」段 |
| said/implied/missing | brainstorm + prd | Open Questions + Assumptions 段(supertask prd) |
| SMARC + drift + scope | grill 3 新轴 | child task grill 时跑 |
| walking skeleton + size 门 | 复杂度天花板表加行 | child task 拆 subtask 时判 |
| strangler | breaking-refactor.md 补模板 | heavy 档 child task 路由 |

### 5. 页面同步(用户选全同步+聚合看板)

- 顶层 task.md:supertask 作分组头,child task 缩进其下(无 parent 的 task 归「独立 task」组)
- task.html:同分组可视化
- supertask/vision.md:聚合看板(脚本渲染,列 child task 进度/状态/完成率)
- per-child-task/task.md:不动(单 task 无需显 parent)

### 6. 生命周期

```
flow 进 → plan 判模糊(信号判据)→ brainstorm 愿景翻译(Job Story)
  → 判大需求? → 否:走现有 single task
                → 是:create supertask + 拆 child task(各 create + parent=<super>)
                  → 各 child task 独立 plan→exec→check→finish
                  → 末 child task finish → supertask finish(聚合归档)
```

**默认不建 supertask**:仅信号判据命中 + brainstorm 收敛后判「需求过大需拆多独立小需求」才建。小需求走现有 single task 零增量。

## 涉及改动清单(exec 阶段拆 subtask 用)

1. **scripts/skein.py** — task.json 加 parent/kind 字段;create 加 `--parent` 选项;渲染逻辑加 supertask 分组;finish 聚合判定(末 child done → super done);vision.md 渲染
2. **skills/skein-plan/SKILL.md** — 加信号判据 + 愿景翻译步骤(Job Story)+ supertask 创建时机判据
3. **skills/skein-grill/references/review-axes-and-output.md** — 加 3 轴(SMARC/drift/scope)
4. **skills/skein-plan/references/dispatch-graph.md** — 天花板表加 cold-start 行(walking skeleton + size 门)
5. **skills/skein-plan/references/breaking-refactor.md** — 补 strangler 模板
6. **agents/skein-plan agent 或 main 流程** — supertask→child task 拆解逻辑
7. **docs/scenarios.md + best-practices.md** — 加大需求场景 + supertask 用法
8. **test** — supertask create/parent/分组渲染/聚合 finish/深度上限守卫

## 简洁性自检(对照约束 3)

- ✅ 概念净增 1(supertask),但它是「现有 task 概念的递归」非全新物,复用 task 生命周期
- ✅ 无新顶层文件夹(复用 task/)
- ✅ 无新 slash command / skill 入口(约束 2)
- ✅ 无外部 skill 依赖(约束 1)
- ✅ 小需求零增量(信号判据短路)
- ✅ supertask 默认不建(仅大需求)
- ⚠️ task.json schema 变更(parent/kind)— 向后兼容(旧 task parent=null kind=task)

## research 引用

- `.skein/task/cold-start-large-req/research/00-summary.md` — 5 核心机制 + 适配
- 01~05 维证据文件
- 一手:liza-mas/liza、JTBD、Fowler strangler
- 弃用:liza 四文档体系 / OST experiments / Story Mapping / IDD / Kano / RICE / MoSCoW 三桶

## 沉淀候选(finish 后 sediment)

- supertask/task 父子结构 + 深度上限 2 层 → `[skill]` core(结构契约,后续必遵)
- Job Story 愿景翻译 + 信号判据 → `[skill]` recall
- SMARC/drift/scope grill 3 轴 → `[skill]` recall
- walking skeleton + size 门合并天花板 → 更新现有天花板规则
- strangler 模板 → `[skill]` recall(重构类)
