---
title: discipline
layer: recall
category: planning
keywords: [state-before-action,状态先行,硬门,STOP,task,subtask,check,自降级,claim,单一真值源,cross-ref,回链,skein-flow,hook,判定,修饰词,TaskCreate,flow,inline,防御,信号证据,证据展示]
status: active
---

## 状态先行铁律 (state-before-action) — 三环节硬门·STOP + 单源重述范式

### 铁律

- MUST：状态先行铁律 = main 操作 task / subtask / check 之前必须先把对应状态机走对，任一违反 = 流程错误 (非优化空间、非效率取舍)，回退到对应状态命令后再继续
- MUST：三环节同构硬门·STOP，统一格式 `🛑 <级>: 未 <状态命令> 禁 <动作> (硬门·STOP) ... 违反 → 回退先 <状态命令>`：
  - **task 级**：未 `skein confirm` + `skein start` 禁进 exec (待处理/就绪态 task 禁派 subtask、禁跑 exec)
  - **subtask 级**：未 `skein claim` / `skein subtask start` 占 `max_active` 槽禁派 agent (pending/failed 态 subtask 禁直接派)
  - **check 级**：未 `skein check` 进检查中态禁跑验证/lint/test/契约核对当 check 结果 (验证归 `skein-checker`)
- MUST：禁自降级 — 文案禁留「简单的可直接」「省一步」「状态机差不多对」类口子；任何"操作前状态机走对"的硬门 MUST 显式 deny 自降级措辞 (引 memory `skein-hook-no-self-downgrade`)
- MUST：核心铁律落地范式 = **单一真值源 (主入口 skill 顶部统一段) + 处处重述带 cross-ref 回链**，禁分散重复各写一份无主源 (状态先行铁律主源在 `skein-flow` SKILL.md 顶部，`skein-exec` / `skein-check` 各重述本环节并带「同 skein-flow 顶部状态先行铁律 X 环节」回链)

### 反例表

| 禁 | 改为 |
|---|---|
| main 待处理/就绪态 task 直接派 subtask | 先 `skein confirm` + `skein start` 进进行中再派 |
| subagent 派发前未 `claim` 占槽 (pending 直派) | 先 `skein claim` / `skein subtask start` 标 running 占槽再 dispatch |
| 全 subtask done 后 main 自跑 lint/test 当 check 结果 | 先 `skein check` 进检查中态，派 `skein-checker` 跑验证 |
| 硬门文案留「简单的可直接」类口子 | 显式 deny 自降级 (引 memory `skein-hook-no-self-downgrade`) |
| 三处 skill 各写一份状态机铁律无主源 | 单一真值源在 skein-flow 顶部 + 处处重述带 cross-ref 回链 |
| 违反 = 优化空间 / 效率取舍 | 违反 = 流程错误，回退到状态命令再继续 |

### 触发场景

- main 在 task/subtask/check 任一环节前跳过状态机直接执行 (主要症状: "先执行后改态")
- skill 文案设计硬门时 (统一 STOP 格式 + 显式 deny 自降级)
- 核心铁律跨多 skill 落地 (单一真值源 + cross-ref 回链范式)

### 落地范式

**三段同构硬门·STOP 文案格式** (本铁律的可复用骨架):

```
🛑 <级>: 未 <状态命令> 禁 <动作> (硬门·STOP) — <前置状态机步骤>。违反 → 回退: 先 <状态命令> 再继续。
```

**单一真值源 + cross-ref 回链** (跨 skill 铁律的组织范式):

- 主入口 skill (如 `skein-flow`) 顶部段定义铁律全貌 (本例三环节)
- 各分 skill (`skein-exec` / `skein-check`) 重述本环节相关条 + 显式回链 `(同 skein-flow 顶部「<铁律名>」<环节>)`
- 禁各 skill 自写一份无主源 (漂移 / 不一致)

**禁自降级显式 deny** (防 AI 自降级绕 flow):

- 硬门段末加独立行: `🔒 本铁律禁自降级 — 无"简单的可直接"口子`
- 引用 memory `skein-hook-no-self-downgrade` 作为依据
- 文案硬，禁留修饰词后缀

### 案例

- commit `07ad7a600` skein(state-before-action): flow 顶部 + exec/check 重述三段同构硬门 + 显式 deny 口子，堵 main 绕状态机
- 代码证据: plugins/tools/skein/skills/skein-flow/SKILL.md:16-24 (主源), skein-exec/SKILL.md:34 (重述), skein-check/SKILL.md:17 (重述)

### 关联

- 铁律: task 状态流转规则（单 task 全 done → check）(core/planning/sediment from skein-flow-align-64.md) — 五态机底层
- 铁律: skein 工作流连线 (core/planning/sediment from skein-flow-align-68.md) — 状态转移路径
- 铁律: skein-check 两步法 (core/planning/sediment from skein-flow-align-65.md) — check 状态先行的具体承载
- 铁律: 并写竞态禁止 (core/arch/reconstruct-47.md) — 互补，本铁律是操作前状态门，reconstruct-47 是并行批次写竞态
- recall: hook 判定防自降级护栏 (recall/planning/hook-prompt-judge-ai-only-57.md) — 同源防自降级范式
- memory: skein-hook-no-self-downgrade (禁泛化「简单的直接做」)

## hook 判定防自降级护栏

### 铁律
- MUST：hook prompt 判定行禁修饰词 — 判定结论尾部禁止附加「但/先/只是/不过」等弱化后缀
- MUST：判定行走 flow 即必须走 flow，禁转头 inline 自降级
- MUST：禁用 harness 内置 TaskCreate (TodoWrite 类) 冒充 skein create — 跨文件任务必须走正式建 task 流程
- MUST：信号从判官降为参谋 — _judge_signal 只检测命中信号作证据（返回 list[str]），走 flow/inline 完全交 AI 读 _CTX 判据自判，脚本不替判档位
- MUST：单一 _CTX 展示判据 + {evidence} 动态证据 + 建议语调（非强制），禁三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 分档注入

### 反例表
| 禁 | 改为 |
|---|--|
| 判定: 走 flow 但先纯查询探索 | 判定: 走 flow (直接走流程) |
| 判定: 豁免 只是改个常量 | 判定: 豁免 (直接做) |
| 用 TaskCreate 绕过建 task | skein create 正式建 task |
| _judge_signal 返回 flow/inline/grey 档位 | 返回 list[str] 证据清单（如 `["文件路径×2", "改动类动词"]`） |
| 三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 选档注入 | 单一 _CTX 含判据 + {evidence} + 建议语调 |

### 触发场景
- AI 判走 flow 后用修饰词借口自降级 inline (如「走 flow 但先探索」)
- 用 TaskCreate×5 冒充正式 task 绕过建 task 流程
- hooks.py cmd_user_prompt 实现（信号检测 + _CTX 注入）

### 信号证据展示范式
**从档位判定到证据收集**（落实「判定权交给 AI」）:

- 旧: `_judge_signal(prompt)` → `"flow"/"inline"/"grey"` 档位 → 三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 选档注入
- 新: `_judge_signal(prompt)` → `list[str]` 证据清单（如 `["文件路径×2", "改动类动词"]`） → 单一 _CTX 展示判据 + {evidence} 动态插入 + 建议语调，AI 读判据自判

**关键变化**:
1. `_judge_signal` 返回 `list[str]`（证据）而非 `"flow"/"inline"/"grey"` 档位
2. 三常量 `_CTX_FLOW`/`_CTX_INLINE`/`_CTX_GREY` 合并为单一 `_CTX`:
   ```
   _CTX = """# SKEIN 判定 (信号仅建议, AI 综合上下文定夺)
   判据: 走 flow = 跨≥2文件/多步骤/改动类动词/新建类 | 可 inline = 纯查询/问答/单文件单处 | 判不清 = AskUserQuestion。
   本次命中: {evidence}
   → 倾向 flow: skein create 建 task 走 skein-flow; 倾向 inline: 直接答/改; 判不清: AskUserQuestion。"""
   ```
3. `cmd_user_prompt` 直接 `_CTX.format(evidence=", ".join(_judge_signal(prompt)))` 注入，删 dict 选档逻辑

**证据检测维度**（保持原有启发式）:
- 文件路径（`_FLOW_PATH_RE` 检测 → `文件路径×N`）
- 改动类动词（`改/加/删/重构/修复/实现/迁移/替换/新增/修改/重写/调整`）
- 跨文件连接词（`和/与/及/同时`）
- 多步骤标记（`然后/接着/之后`）
- 新建类信号（`新模块/新功能/新接口/新页面/新组件/新端点`）
- 查询类词（`什么/为什么/怎么/如何/解释`）

**约束**:
- MUST：{evidence} 占位符必须被替换（脚本内 `format` 调用，非残留占位符）
- MUST：_CTX 文本禁 MUST/禁/违规/黑名单（正向化，避免 prompt-injection 防御触发自降级）
- MUST：判定语调为建议（"倾向 flow/可 inline/判不清"），非强制

### 关联
- 铁律: start 强制 prd 硬门 (planning)
- 实现细节: hook prompt 判定权交给 AI (删除脚本预筹 _classify_prompt)
- 代码证据: plugins/tools/skein/scripts/hooks.py `_judge_signal` + `_CTX` + cmd_user_prompt
- 演进 commits: 7302da23→e6714966→d4432bb1→8bf64241→6f2b153 (最终态 6f2b153)
