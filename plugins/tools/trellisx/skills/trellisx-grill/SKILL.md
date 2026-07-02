---
name: trellisx-grill
description: '对抗式审查 trellis 任务工件 (prd / design / implement / spec / subtask 文件), 贯穿 plan 前/中/后全程逐分支 stress-test 设计树, 帮用户确认/审查/拆解需求。逐问审 (可一次多问批量确认提效 + 推荐答案 + codebase 能答先查), 产物 = 工件内联批注 + 弱点表 (不改写工件, 由 orchestrate/spec 决定怎么改)。独立全周期可调, plan 前 / planning 中 / start 前 / spec 重构前 / 任意决策点都能用。源于 grill-me (relentless interview) + 项目盲点实证'
when_to_use: '由调用方强制驱动 (非 model 自启): trellisx-flow / trellisx-orchestrate 在 PRD 编写中 + start 前两处硬门 MUST 调本 skill; 用户显式 "grill 这个" "审下设计" "红队" "确认需求"。原生 phase 1.1 (写 prd) / 1.4 (start 前) 未走 trellisx 时, model 应主动调 (user-invocable, 非自动加载)'
argument-hint: '<工件路径 或 "active task">'
arguments: '[被审工件路径 (prd/design/implement/spec/subtask 或任一 planning/架构产物, 如 task-tree/调度图/scheduling/config hook/架构决策), 缺省 = active task 全部 planning + 架构产物]'
---

# trellisx-grill — 对抗式工件审查 (贯穿 plan 前/中/后)

**贯穿 plan 全程** (前/中/后) 的对抗式访谈工具, 帮用户**确认 / 审查 / 拆解**需求。plan 前 (brainstorm 草稿出方向后审对不对); planning 中 (审 design/subtask 拆解有无盲点); 写盘 / `task.py start` / spec 重构**之前** (最后一遍校对)。逐分支 stress-test 设计树, 挖「结构合规但实质失效」的盲点。**只批注不改写** —— 改工件是 orchestrate / spec 的职责, grill 只标注弱点 + 给推荐改法。

> 源于 grill-me (relentless interview to sharpen a plan) + 项目实战盲点。grill-me 法: 逐问审, 可一次多问 (批量确认多个设计点提效), 每问给推荐答案, codebase 能答的先查 codebase 不问用户。

## 立场

| 立场 | 说明 |
| --- | --- |
| 对抗非审批 | grill 是红队挑刺, 不是盖章。找不到盲点 ≠ 通过, 是 grill 失败 (没问够) |
| 只批注不改写 | 产物 = 工件内联批注 (行号 + 弱点 + 推荐改法) + 弱点汇总表。改盘交 orchestrate/spec |
| 结构合规 ≠ 实质有效 | 上轮 darwin 结构优化已 90+ 分, grill 专挖结构合规下的实质失效 (token 生命周期 / 触发准确性 / 自举矛盾 / 诚实边界摘樱桃) |
| 可一次多问 | 允许批量问多个问题 (一次确认多个设计点提效), 非强制一次一问。强相关/同源决策点宜批量; 互不相关或需先答才能定下一问的仍分批
| codebase 优先 | 问题能由 Read/Grep 文件答 → 自己查, 不问用户。只问 codebase 答不了的决策点 |

## 可扩展骨架轴 (12 轴默认 + 动态裁剪)

每轮 grill 按骨架逐轴过, 每轴下自由深挖分支。**任一轴答不出 / 答得虚 = 弱点**。

**骨架可扩展 + 动态裁剪** (非固定 12 轴): 上表是默认骨架 (源自项目盲点实证), 按**问题性质 / 项目域 / 工件类型**增减轴 ——
- **增**: 项目特有风险 (如安全/合规/性能/国际化) 可临时加轴; 调度类工件 (task-tree/scheduling) 加"调度正确性"轴; config hook 加"hook 副作用"轴。
- **减**: 与本工件无关的轴可跳过 (如纯 spec 审查未必需 token 生命周期轴), 但**跳过须在报告标注"未审"**, 禁默默跳。
- **动态判据**: 按项目域 (Web/CLI/数据/Agent 工作流) + 问题类型 (设计缺陷/边界冲突/执行风险) 选相关轴, 非机械全过。

| 轴 | 审什么 | 典型盲点 |
| --- | --- | --- |
| **A 目标** | 工件解决的核心问题是什么? 一句话能说清? | 开放式 PRD ("实现 X 功能") 无 deliverable |
| **B 产出** | 交付物是什么? 可验收? | 模糊交付, 无验收标准 |
| **C 验证** | 怎么验产出对不对? 有可执行断言 (grep/test/task.py)? | 铁律要求验证但正文无可执行命令, 验证落 reference 易跳过 |
| **D 资源** | 改哪些文件? 谁独占? 并行还是串行? | 多 agent 文件集重叠 → 互相覆盖 |
| **E 依赖** | 前后序? 共享文件? 阻塞? | 并行组不标依赖箭头 → 乱序 |
| **F 失败模式 (dim3)** | 每步失败怎么办? 有 if-then 三段式 (触发/一线修复/兜底)? | 只写正向流程, 失败分支缺失 |
| **G 检查点 (dim4)** | 关键决策有 🔴 视觉标记 + 用户确认? | 靠"必须"措辞代替标记, LLM 扫标记优先于语义 |
| **H 触发准确性** | should-trigger + should-not-trigger 对? 与邻居 skill 边界清? | 触发词与邻居重叠 → 误抢; 缺 not-trigger 对 |
| **I token 生命周期** | 工件 + references 总行数? auto-trigger 还是手动? 多 skill session 会被踢吗? | auto-trigger skill 堆 references → 旧 skill 静默踢出, 无错误信息 |
| **J 自举/矛盾** | 工件规则适用于自身吗? 有无路径互斥 (skill 说 A, agent 说非 A)? | 同名 skill+agent 走两条互斥路径 → routing 死结 |
| **K 诚实边界** | 局限/降级/dry_run 显式标注? 有无摘樱桃? | 用"诚实"框架选择性呈现事实 (弃用论据但保结论) |
| **L 反例黑名单 (dim9)** | 有"不要做什么"清单? 只写应做? | 只写"应该做 X"没"不要做 Y" |

## 触发: 两硬门 (由 flow/orchestrate 强制) + 非 flow 场景

本 skill **非自动加载** (user-invocable)。触发由调用方驱动, 三场景:

### 硬门 1: PRD 编写中 — 边问边写 (轴 A/B 驱动循环)

**触发点**: trellisx-flow step2 planning / trellisx-orchestrate step1 PRD 编排, **写 PRD 过程中** (非写完后审)。

**模式**: grill 轴 A (目标) + 轴 B (产出) 当提问引擎, 循环:
1. grill 就轴 A/B 出问题 (目标一句话能否说清? deliverable 矩阵是否可验收?) → `AskUserQuestion` 问用户, 给推荐答案
2. 用户答 → **即时更新 PRD** (写入对应 section, 非听完所有才写)
3. 再就更新后的 PRD 出下一组轴 A/B 问题 (目标是否因此细化? 产出验收是否随之变?)
4. 循环至轴 A/B 双 ✓ (目标封闭 + deliverable 可验收) 才算 PRD 完成

**与 brainstorm 关系**: brainstorm 主导需求探索流程, grill 是其**提问质量引擎** —— brainstorm 逐问用户时, 每问经 grill 轴 A/B 校验 (问题是否击中目标/产出盲点), 答完 grill 驱动更新 PRD。非取代 brainstorm, 是给 brainstorm 的提问上对抗性保险。

**禁**: 写完整 PRD 才调 grill (本末倒置)。本硬门要的就是**边写边问**, PRD 成型过程即受对抗校对。

### 硬门 2: 需求确认 (start 前) — 全轴对抗校对

**触发点**: trellisx-flow step3 激活前 / trellisx-orchestrate L69 STOP 门 / phase 1.4 `task.py start` 前。

**模式**: PRD + design + implement 全部写完后, **start 前最后一遍**: 跑全轴 A-L (按工件类型动态裁剪), 重点确认用户想法:
- 轴 A/B/E (目标/产出/依赖): 用户要的 = PRD 写的?
- 轴 C (验证): 验收断言真能验用户要的结果?
- 轴 G (检查点): 关键决策有用户确认?

弱点表交用户过一遍, 用户确认"这就是我要的" + 弱点补齐后才放行 start。**未跑本门不准 start** (硬门, 调用方强制)。

### 非 flow 场景 (原生 trellis / 普通 task)

用户未走 `/trellisx-flow` 但在写 prd / 收到新 task / 准备 `task.py start`:
- **model 应主动调本 skill** (user-invocable, model 识别 phase 1.1/1.4 场景触发)
- 同样两硬门: 写 prd 时边问边写 (硬门 1) + start 前全轴确认 (硬门 2)
- 无强制脚本拦截, 靠 model 遵守 (诚实边界: 非 flow 路径无脚本保证, model 可能漏调)

### 用户显式

"grill 这个" / "审下设计" / "红队" / "确认下需求" → 直接进流程 (5 步), 跑全轴或按用户指定轴。

## 流程 (5 步)

### 第 1 步: 读工件 + 量规模

```bash
# 读被审工件 (prd/design/implement/spec/subtask 或任一 planning/架构产物: task-tree/调度图/scheduling/config hook/架构决策等, 按项目实际动态选)
# 缺省 = active task 全部 planning + 架构产物
python3 ./.trellis/scripts/task.py current 2>/dev/null  # 定位 active task
```

读全文。统计: 工件行数 + 引用的 references 数 (轴 I token 生命周期基线)。

### 第 2 步: 逐轴 grill (可一次多问)

按骨架轴 A→L 顺序 (默认骨架; 按 §可扩展骨架轴 动态裁剪), 每轴:
1. **自己先查 codebase** (Read/Grep 相关文件 / 邻居 skill) —— 能答的不问用户, 直接填评估
2. **codebase 答不了的决策点** → `AskUserQuestion` 工具问用户 (**可一次多问**: 强相关/同源决策点批量问提效; 互不相关或需先答才能定下一问的仍分批。每问给推荐答案作首选项)
3. 该轴结论: ✓ 通过 / ⚠️ 弱点 (记行号 + 弱点 + 推荐改法) / ⛔ 硬伤 (会致功能失效)

> 🔴 **CHECKPOINT (每批问)**: 用 `AskUserQuestion` 工具问, 禁纯文本提问代替 (用户交互决策点, grill-me 法)。每问给推荐答案作 options 首项。可批量问多个相关问题; 等用户答完该批再进下一轴。

### 第 3 步: 内联批注 (不改写工件)

在工件**副本** (或主会话展示, 不动原文件) 内联标注:

```
prd.md:14   ⚠️ 轴A 目标: "实现登录功能" 开放式, 无 deliverable 矩阵
            →推荐: 拆为 D1 OAuth2 / D2 session / D3 权限, 各附验收
prd.md:28   ⛔ 轴C 验证: 铁律要求"行为闭环"但无可执行断言
            →推荐: 补 `grep -q 'task.py create' workflow.md` 等 3 条断言
```

**禁改原工件**。批注是建议, 改盘交 orchestrate / spec。

### 第 4 步: 弱点汇总表

```
grill 报告
═══════════
工件: prd.md (120 行, 引 4 references)
轴覆盖: A-L 全过 (12/12)
弱点: 3 ⚠️ + 1 ⛔
  ⛔ 轴C 验证断言缺失 (L28) — 高, 会致验证形同虚设
  ⚠️ 轴A 目标开放式 (L14) — 中
  ⚠️ 轴H 缺 should-not-trigger 对 (L9) — 中
  ⚠️ 轴I references 累积 (12 个, auto-trigger) — 中, token 风险
推荐: 先修 ⛔ (轴C), 再 ⚠️; 或路由 trellisx-spec 做破坏式重构
```

### 第 5 步: 路由

- 弱点属执行编排 (subtask/并行/依赖) → 路由 `trellisx-orchestrate` 改 prd/design/implement
- 弱点属 spec 规则 (命令式/可验证) → 路由 `trellisx-spec` 做破坏式重构
- 弱点少且明确 → 用户自行改, grill 退场

## 失败处理 (三段式)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 用户非 trellis 项目 (无 .trellis/) | 提示 grill 也可审独立 prd/design 文件 (非 trellis 专属) | 用户提供工件路径直接审, 不依赖 task.py |
| 工件行数超大 (>500 行) | 分段 grill (先 prd, 再 design, 再 implement), 不一次性过 12 轴 | 标记"未全审", 列已审轴 |
| 用户答 "不知道" / "你定" | 给推荐答案 + 理据, 标"推测:", 继续 | 该轴标 ⚠️ 决策未定, 进弱点表 |
| AskUserQuestion 不可用 | 退化为主会话逐问 (纯文本), 标降级 | 降级后 grill 质量降, 标注 |
| 找不到弱点 (全 ✓) | 警告: 可能 grill 不够深, 再过一轮轴 H/J/K (最易漏) | 仍无 → 报告"结构合规, 未发现实质盲点", 但标注"非保证有效" |

## 反例黑名单 (禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 改写原工件 | 职责越界 (改盘是 orchestrate/spec) | 只内联批注 + 弱点表, 改交邻居 |
| 2 | 互不相关问题一次性轰炸用户 | 用户 bewildered, 违 grill-me 逐问审 | 强相关/同源决策点可批量问 (提效); 互不相关或需先答才能定下一问的分批, 每批等反馈 |
| 3 | 纯文本提问代替 AskUserQuestion | 用户无法用工具 UI 选 = 失去决策门 | 决策点必经 AskUserQuestion 工具 |
| 4 | codebase 能答的问用户 | 浪费用户时间, 暴露 grill 没做功课 | 先 Read/Grep 查, 答不了的才问 |
| 5 | 找不到弱点就盖章"通过" | 结构合规 ≠ 实质有效, 盖章 = grill 失败 | 再过轴 H/J/K; 仍无则标"未发现, 非保证" |
| 6 | 跳过轴 I (token) / 轴 J (自举) | 这两轴最易漏且杀伤最大 (零可见度故障/routing 死结) | 必过, 即使工件短 |
| 7 | 只审主文不审 references 深处 | 过时脚注/矛盾判断藏 references, 主文清理带不掉 | `grep -rn` 关键声明跨 references 全扫 |

## 边界

- 只读 + 批注, **禁写盘** (工件原文件零改动)
- **grill 不改盘, 异步修复归 main 非 grill**: grill 只产弱点表 + 推荐改法; 拿 grill 产出派 orchestrate/spec/agent 去改是 **main 层动作** (编排调度), 非 grill skill 本身在改写。grill 退场后改不改、派谁改, 由 main 决定
- 不替代 orchestrate (编排) / spec (破坏式重构); grill 是**贯穿 plan 全程**的审查工具 (前/中/后), 路由交后者改
- 与 darwin-skill dim8 实测互补: darwin 跑 test prompt 看触发准确性, grill 跑轴 H 看边界声明 —— 前者实证, 后者逻辑审查
- 非 trellis 专属: 独立 prd/design 文件也能 grill (退化为不含 task.py 调用)

## References

| 文件 | 用途 |
| --- | --- |
| (按需建) `references/axis-deep-dive.md` | 12 轴各自的深挖问题清单 + 历史盲点实例 |

## 调研来源

- **grill-me** / **grilling** (用户级 skill): relentless interview, 逐分支审设计树, 可一次多问 (批量确认提效) + 推荐答案 + codebase 优先。本 skill 方法论基底
- **项目盲点实证** (memory `skill-review-blindspots`): grilling red-team 实战沉淀的 9 条高频盲点 → 本 skill **默认骨架轴** (可扩展, 非固定)
- **darwin-skill** dim3/dim4/dim9: 失败模式编码 / 检查点 / 反例黑名单维度 → 轴 F/G/L

## 相关 skill

- `trellisx-orchestrate` — planning 编排 (grill 路由目标: 编排类弱点)
- `trellisx-spec` — spec 破坏式重构 (grill 路由目标: spec 类弱点)
- `darwin-skill` — dim8 实测验证 (grill 互补: 逻辑审查 vs 实测)
