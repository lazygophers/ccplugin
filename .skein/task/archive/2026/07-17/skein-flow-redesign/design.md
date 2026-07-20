# skein 流程闭环重设计 — 详细设计

## 现状勘误 (关键)

UserPromptSubmit hook **已存在并生效**: `bin/skein` → `scripts/skein.py user_prompt` (plugin.json:95 接线)。当前注入 task 判定提示 (判定任务→走 skein-flow / 豁免→直接做)。本次会话开头提示即此 hook 产出。

故改动**落现有 hook 体系** (`bin/skein`→skein.py + `bin/skein-hooks`→hooks.py) + SKILL 文档 + 新 agent, **非**新建 hooks.json。

## 现状 vs 目标差距

| 维度 | 现状 | 目标 | 改动落点 |
|------|------|------|------|
| 任务判定触发 | `skein.py user_prompt` 已注入判定 | 强化: 加查重提醒 | skein.py user_prompt |
| check 失败语义 | 保持进行中 + 补 subtask 回 exec | 回 planning (重跑确认) | skein-check/flow SKILL |
| 记忆沉淀 | finish 同步阻塞 | 异步 fire-and-forget | skein-finish/memory SKILL |
| 查重 | AI 自查 (user_prompt 未提查重) | AI 自查 + haiku dedup agent 异步扫 | skein.py user_prompt 加查重句 + 新 dedup agent + plan SKILL |

5 要求: ①及时建=hook判定已强(核对) ②无重复=dedup agent+查重句 ③worktree=config+start(已满足,核对) ④并行=双层DAG(已满足,核对) ⑤记忆异步=sediment fire-and-forget

## 0. 漏建 task 根因修复 (最高优先 · 用户点名)

**根因 (勘误后)**: 漏建 task 不是因为"缺硬阻", 是因为**判定不可靠** — user_prompt 把"任务 vs 豁免"全交 AI 语义判断, 无脚本辅助。AI 不同 session/模型判得宽严不一, 判完也无持久标记, 易漏建。

**修复: hook 脚本预筹 + AI 兜底** (用户选定)。user_prompt 不只注入空提示, 先跑**预筹脚本**给 AI 可靠输入:

1. **明显豁免预筹放行** (脚本判定, 注入"豁免"标记): 输入为纯问句 (以 ?/？结尾且无改动动词) / 明确查询指令 (什么是/解释/查一下/看看) / 含 `--skip` → 脚本标 `预筹:豁免`, AI 直接做
2. **疑似任务预筹标记** (脚本启发式, 注入"疑似"强提示): 输入含改动动词 (改/修/加/删/重构/实现/优化 + 代码/文件/模块) / 跨多文件关键词 / 多步交付意图 / 多句复合指令 → 脚本标 `预筹:疑似任务, 建议走 skein-flow`, AI 须认真判 (倾向建 task)
3. **模糊带 AI 兜底**: 脚本不命中任一 → 现有判定骨架 (AI 自判)

预筹规则放 `scripts/skein.py user_prompt` 内 (纯 Python 启发式, 无外部依赖), 结果拼进注入 ctx。启发式不求完美 (会漏判), 但把**高置信度判定从 AI 脑内挪到脚本**, AI 只判模糊带 — 判定可靠性提升, 漏建概率降。

**与原 s1 (查重句) 合并**: user_prompt 改造一并做 (预筹 + 查重句 + 判定骨架)。

## 1. user_prompt 注入强化 (skein.py:956-977)

当前注入: 判定任务→走flow / 豁免→直接做。**缺查重句 + 缺脚本预筹**。

改: 判定为任务后, 加一句 "走 flow 前**先 `skein list --status open --json` 查重**, 命中相关 active task → 并入补 subtask, 禁重复建"。保留现有判定骨架 + --skip 豁免。

## 2. check 失败回 planning (SKILL 语义)

skein 现无 planning status 枚举。**取舍: 复用现有 `待处理`/`进行中` + 语义描述, 不加新枚举** (避免改状态机)。

skein-check + skein-flow SKILL 改描述: check 不过 → main **重新 grill/AskUserQuestion 确认修复方向** (非直接补 subtask 回 exec) → 确认后 `subtask add` 修复子任务 (--deps 挂失败源) → 重新 claim 派发。语义从"保持进行中跳过确认"改为"回炉确认再 exec"。

## 3. sediment 异步 (skein-finish/memory SKILL)

skein-finish SKILL 改: finish 时派 skein-memorier **后台异步** (Agent 调用即结束回合, 不等回传)。写盘由 memorier 自跑 `skein-memory sediment`。main 收 memorier 回传再 output trace, 但 finish 已完成不阻塞。skein-memory SKILL 同步标注 sediment 可异步。

## 4. skein-dedup agent (haiku)

新建 `agents/skein-dedup.md`: haiku, 只读 (无 Write/Edit/Agent/Task, Recursion Guard)。跑 `skein list --status open --json` + 各 task subtask list, 扫重复 (同目标/同模块/共享改动面), 回传重复清单 (task-id pair + 归一/保留建议)。

skein-plan SKILL 加: 所有 task planning 完成 (batch 末或每个 task plan 收尾) 异步派 skein-dedup (fire-and-forget, 不阻塞 exec)。

## 调度 (task.json)

```
s1-user-prompt-dedup (skein.py, 无dep) ∥ s2-check-replanning (SKILL, 无dep) ∥ s3-sediment-async (SKILL, 无dep) ∥ s4-dedup-agent (新agent+plan SKILL, 无dep) → s5-quality-gate (deps: all)
```
4 改动面独立 (skein.py / check SKILL / finish SKILL / dedup agent+plan SKILL), 无文件重叠, 全并行。s5 收尾跑 claude -p 质量门 + 5 要求核对。
