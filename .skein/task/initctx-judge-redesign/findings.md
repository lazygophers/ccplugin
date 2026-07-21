# Findings — _INIT_CTX 判定逻辑重设计

> 基于 [research/initctx-judge-redesign-research.md](research/initctx-judge-redesign-research.md) 收敛。main 据此进实施。

## 1. 问题定性

skein UserPromptSubmit 判定逻辑经**三阶段摆动**均失败, 同根因: **依赖 AI 对 prose 的合规性**。

| 阶段 | commit | 做法 | 失败 |
|---|---|---|---|
| ① 机械化启发式 | `7302da23` | `_classify_prompt` 3 层规则 | 启发式覆盖不全, 误判 |
| ② AI 独占判定 | `e6714966` | 删启发式, 全交 AI + prose 标准 | AI 自降级 (案例 1/2) |
| ③ 文案补丁 | `d4432bb1` 等 | 加借口黑名单 / 修饰词禁令 | prose 补丁反复失败 |

**根因 (researcher 新洞察)**: 官方 hooks 文档明示 additionalContext 用祈使句框架 (skein 当前全文 "MUST/禁/违规") **触发 prompt-injection 防御**, AI 部分「不当权威指令」→ 自降级。当前 _INIT_CTX 全 negation 框架是结构性问题, 非文案细节。

## 2. 外部实证

**无任何外部项目用 UserPromptSubmit 做 AI 主观 flow 判定**:
- trellisx: 刻意不判 (仅注入 active task 上下文)
- Nick Tune: 触发词显式 ("continue"/"create a plan") + 状态机图, 明言 "relying on LLM to follow a process in markdown = vulnerable"
- disler: UserPromptSubmit 仅日志/校验/上下文
- 官方: UserPromptSubmit 设计为**上下文注入点**非路由点

## 3. 误判案例 (3 例)

1. **bcpay 0d749f6c**: 判走flow + 「但先纯查询」修饰词 + TaskCreate×5 冒充 + inline 13 文件, 用户两次要求回退
2. **4bc82d2f→8ed86703**: 「简单的直接做」泛化 → AI 以「ponytail 最小骨架」自降级 inline 13 文件
3. **cold-start-large-req**: 团队对大请求已放弃 AI 主观判定, 改机械化信号触发 — **skein 内部 D 候选先例**

## 4. 决策 (用户拍板 2026-07-21)

**采用 D + E + A, 排除 C。激进策略 + 三分法分流。**

### 判定三分法 (用户 2026-07-21 定)

| 信号档 | 判定 | 行为 |
|---|---|---|
| **特别简单** (纯问答/单文件单处≤20行/零调研) | 自动判 inline | 直做, **不问用户** |
| **明确需 flow** (跨文件/多步骤/需调研/产出文档) | 自动判 flow | 走 flow 闭环, **不问用户** |
| **灰区** (保守判 flow 但实际可能不需 / 想 inline 但自动判不准) | 判不准 | **AskUserQuestion 问用户** |

核心: 两端自动 (简单 inline / 复杂 flow), **只中间灰区问用户**。禁把「能否 inline」抛给用户当常规问题。

### D: 机械化信号触发 + 正向重写

**D-1 信号触发 (激进阈值)**: UserPromptSubmit hook 内脚本三档分: 高置信 flow / 高置信 inline / 灰区。
- **flow 信号**: 任何文件路径 / 跨文件关键词 / 多步骤标记 / 新模块 / 改动类动词 (改/加/删/重构/修)
- **inline 信号**: 纯问答腔 / 单文件单处 / 无动词 / <15字
- **灰区**: 上述混杂或边界模糊 → AskUserQuestion

**D-2 正向重写 _INIT_CTX** (matt pocock negation): 删 negation (借口黑名单 8 项 / 修饰词禁令 / 禁 TaskCreate), 改正向目标行为陈述 + 事实陈述框架 (避 injection 防御)。

### E: TaskCreated hook 机械禁冒充

新增 TaskCreated hook → `.skein/config.yaml` 存在 → exit 2 阻 TaskCreate + stderr「用 skein create」。机械执行现 `_INIT_CTX:297` 的 prose。与 `cmd_guard` 同模式。

### A: PreToolUse 守 Write/Edit (激进版纳入)

**重新纳入** (用户「激进」指令): PreToolUse hook — `.skein/config.yaml` 存在 + 无 active task + Write/Edit 落非 `.skein/` 代码 → exit 2 阻, 提示先 `skein create`。
- **激进点**: 不为「豁免类首次 Write」留口 (原顾虑); 豁免判定上移到信号触发层, 到 Write 层一律硬阻无 active task 的落码。
- 覆盖案例 1/2 的 inline 直写 (D 信号 + E TaskCreated 未覆盖的部分)。

### 排除

- **C** (trellisx 不判定): 用户排除, 保 flow 闭环文化
- **B** (阈值量化): 阶段①证伪的启发式复活
- **F** (prompt hook Haiku): 成本/延迟/质量不确定

## 5. 实施计划 (下一步)

1. **E 先行** (独立、低成本): TaskCreated hook + exit 2
2. **A 次之** (机械硬阻, 覆盖 inline 直写): PreToolUse 守 Write/Edit 无 active task
3. **D-2 文案重写**: _INIT_CTX 正向化 + 删 negation
4. **D-1 信号触发**: 脚本检测 (激进阈值, 信号列表细化)
5. **验证**: 0d749f6c 场景重放 + 纯问答不误触 (唯一该放过类)

## 6. 证据指针

全量证据见 [research/initctx-judge-redesign-research.md](research/initctx-judge-redesign-research.md) §5 参考资料。
