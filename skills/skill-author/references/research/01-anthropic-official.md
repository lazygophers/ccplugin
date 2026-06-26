# 维度 1：Anthropic 官方规范（skill / agent 编写权威基准）

> 一手源，权重最高。本维度是产物框架的理论支柱。

## 来源清单

| # | 来源 | URL | 类型 |
|---|------|-----|------|
| A | Skill authoring best practices | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | 官方一手 |
| B | Extend Claude with skills | https://code.claude.com/docs/en/skills | 官方一手 |
| C | Create custom subagents | https://code.claude.com/docs/en/sub-agents | 官方一手 |

## A. best-practices 提炼

### 核心原则三律

1. **Concise is key**：context window 是公共品。启动仅 metadata（name+description）预加载；SKILL.md 仅在相关时读取；加载后每 token 与对话历史竞争。默认假设「Claude 已很聪明」，只为它不知道的内容加 context。
2. **Set appropriate degrees of freedom**：按任务脆弱度匹配指令具体度。
   - High freedom（文本指令）：多解皆可、依赖上下文。例：code review 流程。
   - Medium freedom（带参数伪代码/脚本）：有首选模式、允许变体。例：report 模板。
   - Low freedom（具体脚本、零参数）：操作脆弱易错、一致性关键、必须固定序列。例：DB migration。
   - 类比：悬崖窄桥给护栏（low），开阔田野给方向（high）。
3. **Test with all models you plan to use**：Skill 是模型的加法，效果依赖底层模型。Haiku 要够指引、Sonnet 要清晰高效、Opus 要别过度解释。跨模型须取交集。

### Skill 结构铁律

- frontmatter 必填 `name`（≤64 字符、小写字母/数字/连字符、禁 XML 标签、禁保留词 anthropic/claude）+ `description`（≤1024 字符、非空、禁 XML 标签）。
- **description 三律**：第三人称；含 key terms；同时写「做什么」+「何时用」。description 是 skill 选择唯一入口——Claude 从 100+ skill 中靠它挑。
- naming：推荐 gerund（processing-pdfs）；可接受名词短语（pdf-processing）/动作式（process-pdfs）；禁 vague（helper/utils/tools）。
- **SKILL.md body ≤ 500 行**。超了就拆。

### Progressive Disclosure（渐进披露）模式

SKILL.md 像目录，指向按需加载的细节文件。

- **Pattern 1 高层指南+引用**：SKILL.md 放 quick start，细节见 FORMS.md / REFERENCE.md。
- **Pattern 2 按域组织**：多域 skill 按域拆 reference/ 子目录，避免加载无关 context（bigquery-skill: finance.md/sales.md/product.md）。
- **Pattern 3 条件细节**：基础内联，高级链接。
- **引用只深一层**：禁 a→b→c 嵌套。Claude 对嵌套引用会 head -100 预读导致信息不全。
- **>100 行的 reference 文件须顶部放目录**，便于 Claude 预读时看到全貌。

### Workflow / Feedback Loop 模式

- 复杂任务拆顺序步骤，提供**可复制 checklist** 让 Claude 逐项打勾。
- **Feedback loop**：run validator → fix → repeat。大幅提升输出质量。
- **Plan-validate-execute 模式**：对批量/破坏性操作，先产 structured plan 文件 → 脚本验证 plan → 执行 → verify。机器可验证、错误早捕获、可逆规划。

### Content 规范

- 禁时间敏感信息（会过期）。旧信息放 `<details>` old patterns。
- 一致术语：选定一个词贯穿全文（API endpoint 而非混用 URL/route/path）。

### Evaluation-driven 开发

1. 先建 eval 再写文档——确保解决真实问题而非臆想。
2. 流程：无 skill 跑任务记录失败 → 建 ≥3 场景测 gap → 立基线 → 写最小指令通过 eval → 迭代。
3. **Claude A/B 协作**：Claude A（专家）帮设计/精炼指令，Claude B（agent）实测，观察 B 行为回传 A 改进。
4. 观察 Claude 实际导航 skill 的路径：意外读取顺序=结构不直觉；漏跟引用=链接不够显眼；重复读同一文件=该内容该进 SKILL.md；从不访问的 bundled 文件=不必要或信号弱。

### Anti-patterns

- 禁 Windows 路径（统一正斜杠）。
- 禁给太多选项（给 default + escape hatch，而非列 5 个库）。
- 脚本要 solve 不 punt：显式处理错误而非甩给 Claude；禁 voodoo constants（常量须注释为何这个值）。
- MCP 工具用全限定名 `ServerName:tool_name`，否则多 server 时 tool not found。
- 禁假设包已安装（须 `pip install` 显式写出）。

## B. skills（Claude Code 扩展）提炼

### 关键机制（best-practices 未覆盖）

- **Custom commands 已并入 skills**。`.claude/commands/deploy.md` 与 `.claude/skills/deploy/SKILL.md` 都产生 `/deploy`，等价。skill 优先级更高。
- **Skill 内容生命周期**：invoke 后 SKILL.md 渲染为单条消息，整 session 常驻，不重读。auto-compaction 时保留最近一次 invoke 的前 5000 token，合计预算 25000 token，超则旧 skill 被丢。
- **description 截断**：所有 skill name 恒保留，description 在预算溢出时按「最少 invoke 的先丢」裁剪。预算 = context window 的 1%。`/doctor` 查看裁剪状况。`skillListingBudgetFraction` / `SLASH_COMMAND_TOOL_CHAR_BUDGET` 调整。每条 description+when_to_use 合计上限 1536 字符。→ **key use case 必须放最前**。

### frontmatter 字段全集（CC 扩展）

`name` `description` `when_to_use` `argument-hint` `arguments` `disable-model-invocation` `user-invocable` `allowed-tools` `disallowed-tools` `model` `effort` `context`(fork) `agent` `hooks` `paths` `shell`

关键三组：
- **调用控制**：`disable-model-invocation: true`（仅手动，防 Claude 自动触发 deploy 等副作用操作）；`user-invocable: false`（仅 Claude 触发，背景知识类）。
- **子代理执行**：`context: fork` + `agent: Explore/Plan/general-purpose/自定义`。skill 内容成为 subagent prompt，无对话历史。fork 只适合有明确任务的 skill，不适合放纯 guidelines。
- **路径触发**：`paths: glob` 限制仅在匹配文件时激活（monorepo 按包触发）。

### 动态上下文注入

`!`<command>`` 在 skill 内容发给 Claude 前执行，输出替换占位符。Claude 只见结果不见命令。多行用 ```! 围栏。

### eval 工具

`/plugin install skill-creator@claude-plugins-official`：自动化 A/B 对比循环。test case 存 `evals/evals.json`，子代理隔离跑，写 grading.json + benchmark.json（with-skill vs without-skill 通过率/耗时/token），还支持版本盲测 A/B 与 description 调优（生成 should-trigger / should-not-trigger prompt 测命中率）。

## C. sub-agents 提炼

### 核心定位

subagent = 独立 context 窗口 + 自定义 system prompt + 特定工具 + 独立权限。用例：side task 会淹没主对话（搜索结果/日志/文件内容）时，subagent 在自己 context 干活只回摘要。

### frontmatter 字段全集

`name` `description`（必填）+ `tools` `disallowedTools` `model` `permissionMode` `maxTurns` `skills` `mcpServers` `hooks` `memory` `effort` `isolation`(worktree) `color` `background` `initialPrompt`

### 关键设计点

- **description 决定委派**：Claude 靠 description 决定何时委派。写「use proactively」鼓励主动委派。
- **body = system prompt**：subagent 只收 body + 环境细节，**不收完整 CC system prompt**。所以关键约定必须在 body 内显式写。
- **工具继承**：默认继承主对话所有 internal+MCP 工具。例外（即使列了也不给）：AskUserQuestion / EnterPlanMode / ExitPlanMode(非 plan 模式) / ScheduleWakeup / WaitForMcpServers。
- **Explore / Plan 跳过 CLAUDE.md + git status**，保持 context 小。其他 subagent 都加载。→ 若规则必须到达 subagent（如「忽略 vendor/」），须在委派 prompt 里重述。
- **skills 字段**：注入完整 skill 内容到 subagent context（非仅 description）。不能 preload `disable-model-invocation: true` 的 skill。
- **memory 字段**：`user`/`project`/`local` 三 scope，跨会话学习。project 可版本控制共享，推荐默认。
- **嵌套**：subagent 可 spawn 自己的 subagent（v2.1.172+），深度限制 5 层。fork 不能再生 fork。
- **PreToolUse hook 条件验证**：对需要细于 tools 字段的控制时用。例 db-reader 只允许 SELECT，hook 脚本 grep 写操作 exit 2 阻断。

### 选 subagent vs 主对话 vs skill

- 主对话：频繁往返/迭代、多阶段共享 context、快速小改、延迟敏感。
- subagent：产出冗余输出、需强制工具限制、自包含可回摘要。
- skill：可复用 prompt/workflow，在主对话 context 内跑（非隔离）。

### 委派三模式

自然语言点名 / @-mention（保证运行）/ `--agent` 会话级（整个 session 用该 subagent 的 prompt+tools+model）。

## 产物框架应用点

本维度直接定义产物 SKILL.md 的：frontmatter 字段选择、progressive disclosure 目录结构、checklist + feedback loop 工作流、eval-driven 开发流程、description 截断对策（key use case 前置）。
