# 状态先行铁律 (硬门·STOP)

**三环节硬门 — main 操作 task / subtask 前必须先把对应状态机走对。任一违反 = 流程错误 (非优化空间、非效率取舍), 回退到对应状态命令后再继续。**

本铁律与 skein-flow/SKILL.md 顶部「状态先行铁律」段定义一致，为单一真值源 (本文件写一次，SKILL.md 引用)。

---

## 🔒 禁自降级原则

**无「简单的可直接」口子。** 三环节任一违反 = 流程错误，必须回退到对应状态命令后再继续，禁以「这个简单」「省一步」「状态机差不多对」为由绕过。

> memory 锚点: `skein-hook-no-self-downgrade` — 禁泛化「简单的直接做」，AI 会自降级绕 flow；本铁律文案硬，不留口子。

---

## 三个硬门

### 🛑 硬门 1: Task 级 — 未 start 禁 exec

| 项 | 内容 |
|----|------|
| **门规** | task 必须先 `skein confirm` (待处理→就绪) + `skein start` (就绪→进行中) 才能进 exec 调度门 |
| **禁止行为** | 待处理 / 就绪态 task 禁派 subtask、禁跑 exec |
| **违反后果** | 流程错误，所做的 inline 改动 / 派发全部无效，必须回退重走 |
| **回退操作** | 先 `skein confirm` (若还在待处理) + `skein start` 进进行中，再继续 exec |
| **校验依据** | `skein start` 脚本硬卡：非就绪态直接拒 (skein.py:727-730) |

**典型违规场景**:
- 新建 task 后想「先做起来再说」，跳过 confirm/start 直接派 subtask
- 把就绪态 task 当 active 用，直接走 exec 调度
- 以「这个 task 很简单」为由跳过 start

---

### 🛑 硬门 2: Subtask 级 — 未 claim 占槽禁派

| 项 | 内容 |
|----|------|
| **门规** | subtask 必须先 `skein claim` / `skein subtask claim <tid>` / `skein subtask start <tid> <sid>` (标 running 占 `max_parallel` 槽) 才能派 agent |
| **禁止行为** | pending / failed 态 subtask 禁直接派 agent，必须先经 claim / start 占槽 |
| **违反后果** | 流程错误，已派出的 agent 视为无槽运行，必须回收或补占槽 |
| **回退操作** | 先把 subtask 标 running 占槽 (`skein subtask start <tid> <sid>` 或 `skein claim` 整批认领)，再派 agent |
| **校验依据** | `skein subtask start` 脚本硬卡：非 pending/failed 态拒 (skein.py:1826-1827)；满槽也拒 (skein.py:1832-1834) |

**典型违规场景**:
- subtask 还是 pending 就直接说「我派 agent 去做了」
- 跳过 claim 步骤，直接 dispatch，导致并发槽计数不准
- 把 failed 态 subtask 直接重派，不走 start 重启流程

---

### 🛑 硬门 3: Check 级 — 未 skein check 禁验证宣告

| 项 | 内容 |
|----|------|
| **门规** | 全 subtask done 后必须先 `skein check` (进行中→检查中) 才能跑验证 / lint / test / 契约核对 |
| **禁止行为** | 禁 main 在 task 仍「进行中」态自跑验证当 check 结果 |
| **违反后果** | 流程错误，验证结果无效，必须重新走 check 流程 |
| **回退操作** | 先 `skein check` 进检查中，再由 skein-checker 跑验证 |
| **校验依据** | `skein check` 脚本硬卡：非进行中态拒 (skein.py:778-779) |

**验证归属**:
- 验证归 `skein-checker` agent，在「检查中」态跑
- main 不跑验证、不判通过、不宣告全绿
- check 未过 → task 保持进行中，加修复 subtask 回 exec，不是「回退状态」

**典型违规场景**:
- exec 阶段 main 顺手跑了个 lint，说「没问题直接 finish 吧」
- 全 subtask done 后跳过 check 直接 finish
- main 自己跑测试当 check 结果，不派 skein-checker

---

## 判定速查表

| 场景 | 先做什么 | 再做什么 |
|------|---------|---------|
| 想派 subtask 执行 | `skein confirm` + `skein start` 进进行中 | `skein claim` 占槽 → 派 agent |
| 想派单个 subtask | `skein subtask start <tid> <sid>` 标 running | 派 agent |
| 想跑验证 / lint / test | `skein check` 进检查中 | 派 skein-checker |
| 想直接改代码 | 先建 task + 走 plan → confirm → start | 再走 exec |

---

## 违反后的标准回退步骤

1. **停手**: 立即停止当前违规操作，不继续推进
2. **补状态**: 按上表「先做什么」列，把缺的状态命令补上
3. **重做**: 从正确的状态重新开始该环节
4. **不回滚已做的工作**: 如果已经做了实质工作且正确，补状态后继续，不用撤销 (但流程上算违规，需注意下次不犯)

> 核心原则：**状态机是硬门，不是建议**。能过脚本校验的才叫合法状态，脚本拒的就是非法，没有中间地带。
