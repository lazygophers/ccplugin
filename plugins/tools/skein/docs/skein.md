# SKEIN 概念详解

## 系统架构

```
用户请求 → Hook 系统(user-prompt→session-context)
        → Skill 编排层(skein-flow→plan→exec→check→finish)
        → Agent 执行层(executor/checker/researcher/finisher/specer/recaller/dedup)
        → 脚本引擎(skein.py/spec.py/hooks.py)
        → .skein/ 工作区
```

### Skills (5)

| Skill | 职责 | 入口 |
| --- | --- | --- |
| skein-flow | 主线编排: plan→exec→check→finish 四阶段单一真值源, 参数路由 (`/skein-flow [flow\|plan\|exec\|check\|finish]`, 缺省 = flow 全闭环)。plan=brainstorm+research+grill+DAG / exec=claim exec+dispatch / check=lint+type+test+contract / finish=merge+sediment+archive | 自动 (flow 信号) |
| skein-spec | 规则记忆: recall/sediment/bootstrap/prune | 按需 |
| skein-grill | 对抗审查: red team (plan 后硬门) | flow 调用 |
| skein-research | 调研: 代码 survey + 外部搜索 | plan/exec 调用 |
| skein-clean | 清理: 孤儿 worktree / 悬挂分支 | 手动 |
| skein-setup | 初始化 / trellis 迁移 | 首次 |

### Agents (9)

| Agent | 读写限制 | 用途 |
| --- | --- | --- |
| skein-executor | 全读写 | 默认执行, 写代码/配置 |
| skein-checker | 只读 | lint/type/test/contract 验证 |
| skein-researcher | 只读 | 代码 survey + 外部搜索 |
| skein-finisher | 只读 | 完成度检查 |
| skein-specer | 只写 spec/ | sediment/reconstruct/prune |
| skein-recaller | 只读 spec/ | 按关键词召回规则 |
| skein-setup | 全读写 | 初始化/迁移 |
| skein-dedup | 只读 | 去重 + DAG 排序 |
| skein-clean | 只读 + 清理命令 | 归档完成 task + 清孤儿 worktree/悬挂分支 (仅 `/skein-clean` 显式调用) |

### Hooks (12)

> 触发事件以 `.claude-plugin/plugin.json` 的 `hooks` 段为真值源。

| Hook | 触发 | 用途 |
| --- | --- | --- |
| session-start | SessionStart | spec 索引注入 (`skein-spec`) |
| session-context | SessionStart | 注入活跃 task + core 规则 |
| user-prompt | UserPromptSubmit | 信号路由 (flow/inline/grey) |
| subagent-start | SubagentStart | 注入 core 规则到 subagent |
| guard | PreToolUse (Edit/Write/MultiEdit/Read) | 阻止 AI 直接读写脚本管理文件 |
| permission | PermissionRequest + PermissionDenied | 自动批准 `.skein/` 操作 |
| fmt | PostToolUse (Edit/Write/MultiEdit) | 自动格式化 prd.md |
| spec-meta | PostToolUse (Edit/Write/MultiEdit) | 检查 spec frontmatter |
| batch | PostToolBatch | 阻止并发状态写 |
| report | PostToolUseFailure (Bash) | 错误上下文注入 |
| stop-check | Stop | 扫描 spec 问题 → `.pending-fix` |

### Guards

| Guard | 拦截 | 例外 |
| --- | --- | --- |
| 文件守卫 | AI 直接读写 task.json/task.md | 通过 skein 命令 |
| batch 守卫 | 并发 start/finish/archive | 串行 |
| trellis 迁移守卫 | 同时 .trellis/ + .skein/ | 迁移完成 |

---

## 任务生命周期

```
状态机: 待处理 ⇄ 调研中   待处理 → 进行中 → 检查中 → 收尾中 → 已完成
         ↑research ↑plan      ↑confirm  ↑check   ↑finishing  ↑finish
两个独立并发池 (task 级并发上限已取消):
  work 池: subtask phase∈{exec,research} 且 status=运行中
  gate 池: task status∈{检查中,收尾中}
归档: 已完成后 _autoclean 目录迁移 (task/archive/…), 非状态值
```

### 状态转换

| from → to | 触发 | 动作 |
| --- | --- | --- |
| (无) → 待处理 | plan 完成 | 产出 prd/design/findings + subtask DAG + contracts |
| 待处理 → 调研中 | `skein research` | 需已登记 ≥1 `--phase research` subtask |
| 调研中 → 待处理 | `skein plan` | 需调研 subtask 全 done, 收敛回规划 |
| 待处理 → 进行中 | `skein confirm` | 用户确认门 (**吸收 start**): 验 prd + ≥1 subtask + doctor 体检 + deps 校验, 一步建 worktree 直接开工, 无就绪中间态 |
| 进行中 → 检查中 | `skein check` | 全部 subtask 完成后手工/编排触发 |
| 检查中 → 收尾中 | `skein finishing` | 占 gate 池槽位 (上限 `pools.gate`) |
| 收尾中 → 已完成 | `skein finish` | merge → 销wt → 标记完成 + 异步 spec sediment |
| 已完成 → (归档) | retain_days 到期 / =0 立即, **且关联链全完成** | 目录迁移 task/archive/…, 非状态值 |
| 任意 → (丢弃) | `skein archive` | 删 worktree, 不合并 |

### Phase 1: Plan

| 步骤 | 执行者 | 产出 |
| --- | --- | --- |
| 愿景翻译 | skein-flow plan 阶段 | Job Story + said/implied/missing |
| Brainstorm | skein-flow plan 阶段 + 你 | 需求/方案/验收标准 |
| Research | skein-researcher | `research/<topic>.md` |
| Grill | skein-grill (hard gate) | 对抗审查通过 |
| Subtask DAG | skein-flow plan 阶段 | subtask + depends_on + skills |
| Contract | skein-flow plan 阶段 | contracts[] 不变量 |

### Phase 2: Exec

| 步骤 | 说明 |
| --- | --- |
| claim | `skein claim exec`: DAG → 就绪 subtask → 拓扑排序 → dispatch |
| dispatch | 一律派 `skein-executor`, 并发 ≤ max_active |
| 完成判定 | 每 subtask 回 done/fail; fail 重派 ≤2 轮 (质量验收全归 check) |
| 完成即派 | 1 subtask 完 → 释放槽 → `skein claim exec` 下一个 |

**自愈**:
| 情况 | 处理 |
| --- | --- |
| 定点小缺陷 | 原地重派 ≤2 轮 |
| 根因可修 | 加修复 subtask → 重派 |
| 兜底 | 停手回传你 |

### Phase 3: Check

| 检查项 | 执行者 | 失败处理 |
| --- | --- | --- |
| lint | checker | 修复重跑 |
| typecheck | checker | 修复重跑 |
| test | checker | 修复重跑 |
| contract | checker | 评估是否回退 |
| 一致性 | checker | 评估是否回退 |

**Root Cause Protocol** (≥2 轮仍不过 → 第 3 轮 5 维复盘):

| 维度 | 问题 |
| --- | --- |
| 需求 | 验收标准完整可测? |
| 设计 | 方案根本缺陷? |
| 实现 | 代码跑偏? |
| 环境 | 依赖/工具链异常? |
| 测试 | 测试本身有误? |

### Phase 4: Finish

| 步骤 | 执行者 | 说明 |
| --- | --- | --- |
| 完成度检查 | finisher (只读) | git diff + subtask 全完成 + 无 dangling |
| 合并+销wt | skein finish | 各子 worktree → 主分支, 合并后即销 wt/branch |
| 标记完成 | skein finish | status=已完成, 记 finished 时刻 |

**Supertask 收束门**: `kind=supertask` 的 task finish 前, 所有 `parent` 指向它的 child task 必须**全部已完成** (status=已完成), 否则 `skein finish` 硬拒并列出未完成 child。子 task 各自独立走完整 plan→exec→check→finish 闭环, supertask 自身不占 worktree、只在末尾做聚合收束。详见「[Supertask](#supertask)」。
| Sediment | skein-specer | 异步 fire-and-forget: learning → core / recall / drop |
| 归档 | _autoclean | retain_days 到期目录迁移 `task/archive/<年>/<月-日>/<id>/` (wt 已销) |

**Sediment 判定**:

| 维度 | core | recall | drop |
| --- | --- | --- | --- |
| 违反后果 | 炸 (数据丢失/安全) | 可修复 | 无影响 |
| 复用概率 | 高 (项目通用) | 中 (同类场景) | 低 (一次性) |
| 确定性 | 明确对错 | 场景依赖 | 口味/风格 |

---

## DAG 调度

双层同构: task 级 + subtask 级 共用 depends_on 语义。

```
Task 层                          Subtask 层
order-create-api                  s1 参数校验
 ├─ payment-gateway                ├─ s2 库存扣减 (等 s1)
 └─ order-pay ── refund-flow       └─ s3 订单落库 (等 s1)
                                        └─ s4 事件发送 (等 s3)
```

### 依赖声明

```bash
# task 级
skein create order-pay --deps "order-create-api,user-auth"
skein deps order-pay                      # 只查前置
skein deps order-pay --set "a,b"          # 设前置 (仅 pending 且无既有 deps 可写)
```

```yaml
# subtask 级 (prd.md)
subtasks:
  - id: s1; depends_on: []
  - id: s2; depends_on: [s1]
  - id: s3; depends_on: [s1]    # 与 s2 并行
  - id: s4; depends_on: [s3]
```

### Claim 模型

| 范围 | 命令 | 行为 |
| --- | --- | --- |
| 单 task | `skein subtask claim <id>` | DAG → ready set → 拓扑排序 → max_active 个 |
| 全局 exec | `skein claim exec` | 所有进行中 task 同上 |
| 全局 check | `skein claim check` | 全done 进行中 task → 检查中; 检查通过 → 已完成 |

### 调度约束

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| max_active | 2 | 同时进行中 task 数 (subtask 并发全局复用同一键) |
| 深度 | 2 层 | supertask→task→subtask, child 不再生 child |

### Supertask

`kind` 字段区分两种 task: 默认 `task` (独立, 自成一个 plan→exec→check→finish 闭环) vs `supertask` (顶层父聚合层, 自身不写代码, 只聚合一组 child task)。二者怎么选:

| 场景 | 用 |
| --- | --- |
| 单 task 可覆盖的中小需求 | `task` (默认, 不建 supertask) |
| 需求过大, 拆成多个**各自完整闭环**的独立小需求 | `supertask` 作聚合层, 各小需求各建一个 `task` 挂它 |
| 单 task 内部需要拆步骤但仍是一次闭环 | 不建新 task, 用 `subtask` (task 内最小执行单元, DAG 调度) |

`parent`/`kind` 是唯一受控父子字段 (`doctor` 只放行这两个, 未登记字段名如 `parent_id`/`children`/`subtask_of` 一律拒), 与 `deps` (前置依赖 DAG) 正交 — parent 管**归属** (谁聚合谁), deps 管**执行顺序**, 挂 parent 不影响也不替代 deps。

```bash
# 建 supertask + child (建时声明)
skein create <super-id> --kind supertask --name "<名>"
skein create <child-id> --parent <super-id>

# 存量 task 改挂 (无需删档重建)
skein parent <id>                    # 查当前 parent (无父打印 "(无父)")
skein parent <id> --set <parent-id>  # 挂到 supertask/task 下
skein parent <id> --set ""           # 摘除 (parent 置空)
```

`--parent`/`skein parent --set` 落盘前硬拒: 自引用、`parent` 指向不存在 task、深度超 2 层 (父自身已是 child, 即父的 parent 非空)、以及 `skein parent --set` 特有的一条 —— 若目标 task 自己已是别的 task 的 parent (已有 child 挂它), 再给它挂父会让那些 child 变 3 层, 直接拒绝 (先摘除那些 child 或改挂别处)。

**收束约束**: supertask finish 前, 全部 child (parent 指向它的 task) 须已完成, 否则 `skein finish` 硬拒并列出未完成 child — 见「Phase 4: Finish」。

### Worktree 模型

```
repo/.worktrees/
├── skein-order-create-api/    # 1 task = 1 worktree
└── skein-payment-gateway/     # 物理隔离
```

| 事件 | 操作 |
| --- | --- |
| start | `git worktree add` |
| exec 期间 | 主工作区 zero diffs |
| finish | 合并 + `git worktree remove` |
| archive | 丢弃 + `git worktree remove` |

| 模式 | 条件 | 位置 |
| --- | --- | --- |
| Single-root | 默认 | `.worktrees/skein-<id>/` |
| Multi-git | `--repos` | 各仓库各自 .worktrees/ |
| In-place | git < 2.5 | `.skein/worktree/<id>/` |

**Supertask**: 自身无 worktree, 只有 child 有。

---

## 规则记忆库 (namespace × inclusion)

差异化核心: 每 task 踩过的坑自动落盘, 后续 task 自动带上。

### 三层存储

| 层 | 路径 | 用途 | 注入 |
| --- | --- | --- | --- |
| core | `spec/core/<cat>/` | 违反即错硬约束 | 每 session 自动 |
| recall | `spec/recall/<cat>/` | 值得参考经验 | 按关键词召回 |
| external | `spec/external/<cat>/` | 外部引用 | 仅手动 CLI |

### 类目

`git` / `domain` / `arch` / `test` / `language` / `project` / `security` / `general`

### 文件格式

`<source>-<seq>.md`:
```yaml
---
title: 金额用整数分, 禁 float
layer: core
category: domain
keywords: [金额, float, 精度, 分]
source: order-create-api-01
created: 2026-07-11
---
正文...
```

### 流转路径

| 路径 | 触发 | 执行者 | 流程 |
| --- | --- | --- | --- |
| Recall | plan | skein-recaller | `skein-spec recall <query>` → FTS5 → 注入 |
| Sediment | finish | skein-specer | learning → namespace×inclusion / drop |
| Bootstrap | 首次空仓 | skein-researcher | 扫 5 维约定 → 定 namespace×inclusion → 落盘 |
| Maintain | 定期 | skein-specer | `skein-spec maintain` 全量健康检查 |
| Prune | 定期 | skein-specer | `/skein-spec prune` (skill 模式) 归档 stale/重复 |
| Reconstruct | 按需 | skein-specer | `/skein-spec reconstruct` (skill 模式) 按项目类型重建 |
| Auto-fix | stop-check hook | skein-specer | `.pending-fix` → 启动修复 |

### 注入路径

| 时机 | 内容 | 预算 |
| --- | --- | --- |
| SessionStart | core 全部规则 (标题摘要) | ~4000 char |
| plan/exec | recall 匹配结果 | 无硬限 |
| subagent-start | core (按 agent 类型选) | ~4000 char |
