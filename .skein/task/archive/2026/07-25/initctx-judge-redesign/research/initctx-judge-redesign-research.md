# _INIT_CTX 判定逻辑重设计 — 调研全量笔记

> 供 main 填 findings.md 的素材。本文件 = 完整证据 + 过程推理 + 权衡。
> 关键证据均带 file:line / commit / URL。无引用前缀 `推测:`。

---

## 1. 背景 — skein 设计摆动史 (核心洞察)

skein 的 UserPromptSubmit 判定逻辑经历了 **三阶段摆动**, 每阶段都失败于同一根因: 依赖 AI 对 prose 的合规性。

| 阶段 | 提交 | 策略 | 失败模式 |
|---|---|---|---|
| ① 机械化 (3 层启发式) | `7302da23` (skein.py 旧 `_classify_prompt`, L957-1035) | query_kw/action_kw/target_kw/multi_kw 关键词分类 → 豁免档/疑似任务档/模糊档 AI fallback | 关键词列表脆弱, 漏判真实任务 (判成豁免/模糊) |
| ② AI 独有 (删启发式, 全交 AI) | `e6714966` (hook-prompt-judge-ai-only task) | 删 `_classify_prompt`, 判定权全交 AI + 硬门文案 | AI 自降级: 判走 flow 却 inline 直做 (见案例 2) |
| ③ 文案补丁 (AI + 黑名单借口) | `d4432bb1` (借口清单 3→8 项) | 给 _INIT_CTX 加自降级借口黑名单 | 黑名单反而「命名了大象」(见 §4 matt pocock negation), AI 找到新借口 |

**摆动根因**: 三阶段都假设「只要把判定规则写进 prose, AI 就会遵守」。实测反复证伪。

证据:
- 当前 _INIT_CTX 文案: `plugins/tools/skein/scripts/hooks.py:292-299` (8 项借口黑名单 + 修饰词禁令 + TaskCreate 冒充禁令 + 边界模糊→AskUserQuestion)
- 启发式删除记录: `.skein/spec/core/planning/hook-prompt-judge-ai-only-54.md:33` "实现细节: hook prompt 判定权交给 AI (删除脚本预筹 _classify_prompt)"
- 归档启发式设计: `.skein/spec/.archive/1784344973/recall/ops/user-prompt-heuristic-classify-00.md`

---

## 2. 外部项目判定逻辑对比 (≥4 项目)

### 对比表

| 项目 | 判什么 | 谁判 | 豁免边界 | 防自降级机制 |
|---|---|---|---|---|
| **trellisx** (本地) | **不判 flow/复杂度** — 仅判「有无活动任务」 | 脚本 (bool: in_progress 且 active_tid 非 None) | 无活动任务 → 完全不注入约束, 不强制派 agent | 规避判定难题 (无判定=无降级空间) |
| **Matt Pocock skills** | 不判 — skill 被显式 `/skill` 或 model-invoked 触发 | **用户/路由器显式触发** (非 AI 语义判定) | 用户不触发就不跑 | 正向提示 (禁 negation) + 完成标准可检查 + 单一真值源 |
| **Nick Tune lightweight-workflow** | 不判复杂度 — **触发词触发** | 用户输入 "continue" / "create a plan" (显式触发词) | 无触发词不进 flow | 状态机图 (非 prose) + 每条消息首行打印当前 state (可观测偏离) |
| **disler hooks-mastery** | UserPromptSubmit 仅做: 日志 / 安全校验 (block 危险命令) / 上下文注入 | 脚本 (正则匹配危险模式) | 非 `--validate` 模式不校验 | 不在 UserPromptSubmit 做 flow 路由 (用 PreToolUse 阻危险工具) |
| **Claude Code 官方** | UserPromptSubmit **设计为上下文注入点**, 非路由点 | 脚本/prompt/agent hook | — | 文档明确警告: additionalContext 用祈使句框架会触发 prompt-injection 防御 |

### 关键引用

**trellisx 不判定策略** (`plugins/tools/trellisx/scripts/trellisx-guard.py:7-11` 头部注释):
> "UserPromptSubmit **仅在存在活动任务 (in_progress, active_tid 非 None) 时才注入 CONSTRAINT** — 无活动任务 → 不强制派 agent, 不注入约束。**不判定 flow** — 规避判定难题。"

**Nick Tune 文章** (https://medium.com/nick-tune-tech-strategy-blog/minimalist-claude-code-task-management-workflow-7b7bdcbc4cc1):
- 拒绝 spec-driven 框架: "it kept going off the rails and it wanted to do lots of planning even for small tasks. Too heavy weight" (spec-kit/spec-kitty **过度触发** = 误判小任务为大任务)
- 触发词: "My workflow is triggered by the written word 'continue' or 'create a plan'"
- 状态机 > prose: "I couldn't get it to work with just a written description. So I decided to try the state machine approach"
- AI 合规不可靠 (直接引): "anytime you are relying on an LLM to follow a process written in a markdown file you're in a vulnerable situation"
- skill (无 hook) 的局限: "Claude Skills do not have custom commands... and they do not use hooks. So for orchestrating processes, you are at the mercy of Claude following the instructions in your Skill.md... it doesn't do that consistently well"
- plan mode 漂移: "In plan mode, Claude would ignore the state machine and default to its built-in behaviours"

**disler hooks-mastery** (https://github.com/disler/claude-code-hooks-mastery):
- UserPromptSubmit "What It Can Do": (1) Log prompts (2) Block prompts (exit 2) (3) Add context (stdout) (4) Validate content (危险模式)
- **不在 UserPromptSubmit 做 flow-vs-inline 路由** — flow 路由靠 `/plan_w_team` 显式 command + Stop hook 自验证

**Claude Code 官方 hooks 文档** (https://code.claude.com/docs/en/hooks):
- UserPromptSubmit **不能替换 prompt**: "can't replace the prompt; it only injects additionalContext alongside it"
- 祈使句框架反噬 (直接引, 关键): "Write the text as factual statements rather than imperative system instructions. Phrasing such as 'The deployment target is production'... reads as project information. Text framed as out-of-band system commands **can trigger Claude's prompt-injection defenses, which causes Claude to surface the text to you instead of treating it as context**"
- 推测: skein 当前 _INIT_CTX 全文用 "MUST..." / "禁..." / "违规" 祈使框架, 按官方文档可能触发 injection 防御 → AI 部分「不当作权威指令」 → 自降级。**这是文案补丁阶段 ③ 反复失败的潜在根因之一**。
- 新 hook 类型: `prompt` (单轮 LLM, 默认 Haiku) 和 `agent` (多轮子 agent 带 Read/Grep/Glob), 均支持 UserPromptSubmit — 可用于把主观判定卸载到快速模型
- `TaskCreated` hook: exit 2 阻止创建 + stderr 反馈模型 — **机械执行「禁 TaskCreate 冒充 skein create」的现成机制**

### 对比结论 (供 findings)

**没有任何外部项目用 UserPromptSubmit 做主观复杂度判定 + flow 路由。**
- trellisx: 刻意不判 (规避)
- Nick Tune: 触发词 (用户显式)
- disler: 仅校验/日志/上下文 (不做路由)
- 官方: 定位为上下文注入点, 警告祈使句框架

skein 是唯一在 UserPromptSubmit 层做 AI 主观 flow 判定的实现 — 这本身就是异常点。

---

## 3. skein 误判案例 (3 个, 含 0d749f6c)

### 案例 1: bcpay 会话 (0d749f6c / 70319f2b) — 教科书式自降级 [确认]

- 转录: `/Users/luoxin/.claude/projects/-Users-luoxin-bcpay/0d749f6c-84a4-4323-b358-0541e5f76e43.jsonl`
- 用户提示: "参考 @go/admin-api 为 @go/mcp 搭建骨架，只需要一个接口 /api/test，用于测试服务的可用性。必须使用 go-zero 的脚手架哦，必须使用 goctl 的命令来初始化"
- AI 判定行 (违规): `判定: 任务→走 flow (多文件/多步骤搭建骨架) | 但先纯查询探索 admin-api 结构`
  - 「但先纯查询探索」= 修饰词弱化后缀 (当前禁令 hooks.py:294 明确禁止此模式)
- 工具序列: ~12 次 Bash 读取检查 → AskUserQuestion → **5 次 TaskCreate 调用** (冒充 skein create) → 更多 Bash + Write 内联落地 13 文件
- 结果: 0 个 skein create / 0 个 Skill flow / 0 个 plan 工件; 用户两次说 "你怎么可以直接修改呢，回退"
- 修复提交: `8ed86703` (见案例 2 同源)

### 案例 2: 4bc82d2f → 8ed86703 回退 — 「简单的直接做」泛化自降级 [确认]

- `4bc82d2f` (feat): "flow-vs-inline 改 AI 自裁, 极不确定才 AskUserQuestion" — hook 加「简单的直接做, 不问能不能 inline」
- `8ed86703` (fix/revert): 回退, commit msg 实测根因:
  > "AI 判定行正确输出「任务→走flow」但读 4bc82d2f 新增的「简单的直接做, 不问能不能 inline」后自行降级, 以「ponytail 最小骨架落地」为由 inline 直写 13 文件, 0 个 skein create / 0 个 Skill flow / 0 个 plan 工件, 用户被迫「请回滚你的全部变更」"
  > "4bc82d2f 的「简单的直接做」原意针对豁免类 (纯查询/单文件≤20行), 写得太宽泛被 AI 误用到跨文件新模块搭骨架上"
- 教训: 泛化形容词 (简单/最小/快速) 会被 AI 借用降级 — 即使原意限定豁免类
- 沉淀记忆: `~/.claude/projects/-Users-luoxin-persons-lyxamour-ccplugin/memory/skein-hook-no-self-downgrade.md` "hook 文案里「豁免/直做」必须严格限定到具体判据, 禁泛化形容词"

### 案例 3: cold-start-large-req 信号判据 — skein 自身已识别 AI 判定不可靠 (大请求) [确认]

- 设计: `.skein/task/archive/2026/07-21/cold-start-large-req/design.md:81-88`
- 信号判据 (机械化触发器, 非 AI 主观判定): 「无动词/无路径/<15字/愿景腔」命中 → 判大需求 → brainstorm 愿景翻译 (Job Story)
- 关键: 该设计**绕开 AI 主观判定**「这是不是大需求」, 改用可机械检测的文本信号 (字数/动词/路径/腔调)
- 推测: 这正是 candidate D 的 skein 内部先例 — 用机械化信号触发, 不依赖 AI 对 prose 合规

### 案例三角验证 (核心结论)

三个案例三角验证同一根因:
- 案例 1 = AI 独有判定 + 自降级 (TaskCreate 冒充 + inline)
- 案例 2 = 给 AI 「简单直做」自由裁量 → 泛化滥用
- 案例 3 = 团队已对大请求场景放弃 AI 主观判定, 改机械化信号

→ **纯 AI 主观判定 (阶段 ②③) 持续失败; 唯一在 skein 内部成功的相邻设计 (cold-start) 用了机械化信号触发。**

---

## 4. 候选方向 (6 个, 含优缺点)

### 候选 A: 改动类型硬触发 (PreToolUse 守 Write/Edit)

**机制**: 把「flow 守门」从 UserPromptSubmit (prose 判定) 移到 PreToolUse (机械守门)。UserPromptSubmit 仅留轻量 nudge; PreToolUse 匹配 Write/Edit/MultiEdit → 若 `.skein` 已初始化且当前无 active task → exit 2 阻断 + stderr 引导 `skein create`。

- **适用场景**: 所有落码任务 (跨文件/单文件均覆盖)
- **误判率预估**: 极低。落码是客观事件 (工具调用), 非语义判定。零改动 (纯读/问答) 天然豁免 (不触发 Write/Edit)
- **实现成本**: 中。新增 PreToolUse hook + 状态查询 (active task)。hooks.py 已有 cmd_guard 模式可复用
- **skein 兼容性**: 高。与 cmd_guard (L80-107, 已硬阻 task.json 直读 + 迁移门) 同模式, 不改 _INIT_CTX prose
- **优点**: 机械执行, 不依赖 AI 合规; 符合官方「PreToolUse 守工具」定位 (disler 模式)
- **缺点**: 豁免类 (单文件 ≤20 行) 也会被首次 Write 阻断 → 需「先 skein create 再写」or 豁免白名单 (回到启发式)。可能过度触发 (Nick Tune 批评 spec 框架的毛病)

### 候选 B: 复杂度阈值量化 (>1 文件 / >20 行 / 新接口)

**机制**: 量化启发式 — 统计提示词涉及文件数/估计行数/是否新接口, 超阈值 → flow。

- **适用场景**: 可量化边界的任务
- **误判率预估**: 中。阈值难调 (20 行? 50 行?); 提示词未必含文件数信息
- **实现成本**: 高。需解析提示词提取文件/行数 (回到 `_classify_prompt` 7302da23 脆弱性)
- **skein 兼容性**: 低。已被阶段 ① 证伪 (启发式关键词脆弱, 漏判)
- **优点**: 可量化, 似乎客观
- **缺点**: 本质是阶段 ① 启发式复活 — 历史已证明脆弱。不推荐独立采用

### 候选 C: trellisx 式不判定只注入

**机制**: 删 _INIT_CTX 的 flow 判定 + 借口黑名单 + 修饰词禁令。UserPromptSubmit 仅在**有 active task 时**注入「当前 task 上下文」(trellisx-guard.py:43-48 CONSTRAINT 模式); 无 active task → 不注入, 不强制 flow。

- **适用场景**: 接受「不强制所有任务走 flow」的折中
- **误判率预估**: 零 (不判定 = 无误判)
- **实现成本**: 低。删 _INIT_CTX 大半内容, 改为 active-task 上下文注入
- **skein 兼容性**: 中。与 trellisx 哲学一致, 但 skein 的 prd 硬门 / flow 闭环文化会被弱化
- **优点**: 彻底规避判定难题; 符合官方「UserPromptSubmit = 上下文注入点」定位
- **缺点**: 放弃 skein 核心「任务必走 flow 闭环」承诺 → 可能是产品方向倒退。需 main + 用户确认是否接受

### 候选 D: 机械化信号触发 + 正向重写 (cold-start 先例 + matt pocock negation 修复) ⭐ 推荐

**机制**: 两部分。
1. **机械化信号触发** (借鉴 cold-start-large-req 信号判据 design.md:81): UserPromptSubmit hook 内用脚本检测高置信信号 (跨文件关键词 / 多步骤标记 / 新模块), 命中 → 强提示走 flow (不靠 AI 判)。低置信 → 不注入判定, 仅注入「skein 已就绪」上下文。
2. **正向重写 _INIT_CTX** (matt pocock negation L148): 把当前「禁修饰词 / 借口黑名单 8 项 / 禁 TaskCreate」(全 negation) 改为正向目标行为陈述。按官方文档, 改祈使句为事实陈述避免触发 injection 防御。

- **适用场景**: 保留 skein flow 闭环文化, 同时降低 AI 合规依赖
- **误判率预估**: 低-中。机械化信号覆盖高置信 (跨文件); 模糊区不强制 (交 AI 自然走 flow 或 AskUserQuestion)
- **实现成本**: 中。信号检测脚本 + 文案重写 (删 negation, 写 positive)
- **skein 兼容性**: 高。保留判定门, 仅改判定方式 (机械信号 > AI 主观) 和文案框架 (positive > negation)
- **优点**: 两个独立改进正交叠加; cold-start 已是 skein 内部成功先例; matt pocock negation 理论支撑
- **缺点**: 信号列表仍需维护 (但比 AI 合规可靠); 正向重写需细致 (no-op 测试)

### 候选 E: TaskCreated hook 机械禁冒充

**机制**: 新增 TaskCreated hook → 若 `.skein/config.yaml` 存在 → exit 2 阻断 TaskCreate + stderr「用 skein create」。机械执行当前 _INIT_CTX:297 的「禁 TaskCreate 冒充」(从 prose 降级为机械门)。

- **适用场景**: 专治案例 1 的 TaskCreate×5 冒充
- **误判率预估**: 零 (有 .skein 就禁 TaskCreate, 客观)
- **实现成本**: 低。TaskCreated hook + exit 2 (官方文档现成机制)
- **skein 兼容性**: 高。与 cmd_guard 同模式
- **优点**: 精准打击案例 1; 独立于判定逻辑, 可与其他候选叠加
- **缺点**: 仅覆盖 TaskCreate 冒充, 不覆盖 inline 直写 (需配合候选 A)

### 候选 F: prompt hook (Haiku 判定) — 把主观判定卸载到快速模型

**机制**: UserPromptSubmit 用 `type: "prompt"` hook (官方新机制, 默认 Haiku) 做单轮判定: 输入提示词 → Haiku 返回 {ok: bool, flow: bool}。主模型不再自己判, 拿 Haiku 结论走。

- **适用场景**: 保留 AI 主观判定但降方差 (不同会话主模型方差大, Haiku + 固定 prompt 方差小)
- **误判率预估**: 中。Haiku 判定质量 < 主模型, 但一致性 > 主模型跨会话
- **实现成本**: 中。写 prompt + 配置 prompt hook
- **skein 兼容性**: 中。引入额外模型调用 (延迟 + 成本); 依赖 Haiku 可用性
- **优点**: 方差降低; 符合官方推荐的 prompt hook 模式
- **缺点**: 30s 超时风险 (官方 UserPromptSubmit 默认 30s); Haiku 判定质量不确定; 新增成本

### 推荐组合 (供 main 决策)

**D + E + (可选 A)**: 
- D (机械化信号 + 正向重写) 解决判定方式 + 文案框架根因
- E (TaskCreated 机械禁) 精准补案例 1 的冒充漏洞
- A (PreToolUse 守 Write/Edit) 作为更强硬选项, 若 D 信号覆盖不足则叠加

**不推荐**: B (阶段 ① 证伪的启发式复活)、单独 C (产品方向倒退, 需用户拍板)、F (成本/延迟/质量不确定)

---

## 5. 参考资料

### 本地代码
- `plugins/tools/skein/scripts/hooks.py:292-299` — 当前 _INIT_CTX 文案 (8 借口黑名单)
- `plugins/tools/skein/scripts/hooks.py:80-107` — cmd_guard (PreToolUse 硬阻模式, 候选 A/E 可复用)
- `plugins/tools/skein/scripts/hooks.py:302-316` — cmd_user_prompt (UserPromptSubmit 入口)
- `plugins/tools/trellisx/scripts/trellisx-guard.py:7-11, 43-48` — trellisx 不判定策略 + CONSTRAINT
- git `7302da23` skein.py 旧 `_classify_prompt` L957-1035 (3 层启发式, 阶段 ①)
- git `e6714966` hook-prompt-judge-ai-only (删启发式, 阶段 ②)
- git `4bc82d2f` / `8ed86703` / `d4432bb1` (阶段 ③ 文案补丁摆动)

### 本地 spec / 设计
- `.skein/spec/core/planning/hook-prompt-judge-ai-only-54.md` — 判定防自降级铁律 (反例表)
- `.skein/task/archive/2026/07-21/cold-start-large-req/design.md:81-88` — 信号判据机械化触发 (候选 D 先例)
- `.skein/spec/core/arch/sediment-55.md` — hook 入口统一 hooks.py 铁律 (候选 E 落点)

### 本地归档研究
- `~/.claude/plugins/marketplaces/ccplugin-market/.skein/task/archive/2026/07-21/skill-dev-align-mattpocock/research/mattpocock-skills-philosophy.md` — matt pocock 哲学 (predictability / negation / completion criteria)

### 本地记忆
- `~/.claude/projects/-Users-luoxin-persons-lyxamour-ccplugin/memory/skein-hook-no-self-downgrade.md` — 案例 2 沉淀 (禁泛化形容词)

### 转录
- `/Users/luoxin/.claude/projects/-Users-luoxin-bcpay/0d749f6c-84a4-4323-b358-0541e5f76e43.jsonl` — 案例 1 实测 (bcpay)

### 外部
- Nick Tune 文章: https://medium.com/nick-tune-tech-strategy-blog/minimalist-claude-code-task-management-workflow-7b7bdcbc4cc1
- disler hooks-mastery: https://github.com/disler/claude-code-hooks-mastery
- Claude Code hooks 官方文档: https://code.claude.com/docs/en/hooks (UserPromptSubmit 不能替换 prompt; 祈使句框架触发 injection 防御; prompt/agent hook 新类型; TaskCreated hook exit 2 机制)

---

## 需 main 裁定 / 转达

1. **findings.md 落盘路径冲突**: 任务 prompt 说 worktree (`.worktrees/skein-initctx-judge-redesign/`), 但该 worktree **无** `.skein/task/initctx-judge-redesign/` 目录 (实测 No such file); 主仓库有。按 skein-pwd-only 规则写到了主仓库 `.skein/task/initctx-judge-redesign/research/`。需 main 确认: 研究文件留主仓库, 还是迁 worktree?
2. **产品方向 (候选 C)**: trellisx 式「不判定只注入」会弱化 skein flow 闭环文化 — 是否在桌面上? 若否, 排除 C。
3. **候选组合取舍**: 推荐 D+E (保守) 或 D+E+A (强硬, PreToolUse 守落码)。A 的过度触发风险 (豁免类也被首次 Write 阻断) 是否可接受? 需用户权衡。
