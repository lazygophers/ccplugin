---
name: skill-author
description: 创建与优化 Claude skills 和 subagents 的方法论框架。当用户要编写 SKILL.md、创建新 skill、设计 subagent / agent.md、配置 frontmatter、拆分 progressive disclosure、优化现有 skill 质量时使用。仅手动 /skill-author 触发。
disable-model-invocation: true
---

# Skill Author — Skill / Agent 编写方法论

> meta-skill：教如何编写其他 skill 与 subagent。基于 Anthropic 官方规范 + darwin-skill 9 维实证 + 社区反模式。完整调研素材见 `references/research/01-06.md`。

## 🔴 硬规（违反即失效）

1. **显式触发**：本 skill `disable-model-invocation: true`，仅 `/skill-author` 手动调用。不要建议改为自动触发——它是创作工具，不是背景知识。
2. **产物定位**：帮用户造 skill 或 subagent，不造人物/主题视角 skill（nuwa 职责）。
3. **诚实标注**：禁编造引用。无法核实的来源直接弃用。

## 何时用本 skill

| 场景 | 例子 |
|------|------|
| 从零创建 skill | 「帮我做一个部署 skill」「写个 PR review skill」 |
| 创建 subagent | 「加一个 code-reviewer subagent」「配只读 db agent」 |
| 优化/改现有 skill | 「这个 skill 不触发」「太长了」「改了没生效」 |
| 结构决策 | 「这段该进 SKILL.md 还是拆 reference？」「该用 context:fork 吗？」 |
| frontmatter 配置 | 「description 怎么写」「该不该 disable-model-invocation」 |

## 编写流程（6 Phase）

### Phase 1: 定位

先回答 4 个问题，再动笔：

1. **skill 还是 subagent？**
   - 可复用 prompt/工作流、在主对话跑 → **skill**
   - 产出冗余输出需隔离、需强制工具限制、自包含回摘要 → **subagent**
   - 背景知识（不应作为命令触发）→ skill + `user-invocable: false`
   - **混合**（主对话交互 + 子任务隔离，如部署需确认+验证+执行多段）→ skill + `context: fork` + `agent: <type>`（skill 内容成为 subagent prompt，见「subagent 编写要点」）
2. **触发方式？**
   - 副作用操作（deploy/commit/send）→ `disable-model-invocation: true`（仅手动）
   - 背景知识 → `user-invocable: false`（仅 Claude 触发）
   - 一般工作流 → 默认（两者皆可）
3. **内容类型？**
   - Reference（约定/模式/领域知识）→ 内联，常驻 context
   - Task（部署/提交/生成步骤）→ 常配 `disable-model-invocation: true`
4. **自由度？**
   - 多解皆可 → high freedom（文本指令）
   - 有首选模式 → medium（带参数模板）
   - 操作脆弱/一致性关键 → low（具体脚本，禁参数）

### Phase 2: 骨架

```
my-skill/
├── SKILL.md              # 主指令（≤500 行 / token 意识）
├── references/           # 按需加载的细节（只深一层）
│   ├── <domain-a>.md
│   └── <domain-b>.md
└── scripts/              # 可执行脚本（执行而非加载）
    └── <tool>.py
```

- 多域 skill 按域拆 `references/<domain>.md`，避免加载无关 context。
- >100 行的 reference 文件顶部放目录，便于 Claude 预读见全貌。
- **引用只深一层**：禁 a→b→c 嵌套（Claude 对嵌套会 `head -100` 预读致信息不全）。

> 🔴 **CHECKPOINT**：骨架定型后展示目录结构给用户确认，再进入 frontmatter。骨架方向错，后续全返工。

### Phase 3: frontmatter

**完整 16 字段表 + 调用控制矩阵 + 字符串替换变量见 [references/frontmatter-spec.md](references/frontmatter-spec.md)。** 下面只列最常用 5 个：

```yaml
---
name: <lowercase-kebab>           # 默认目录名；≤64 字符，禁 anthropic/claude 保留词，禁 XML 标签
description: <做什么 + 何时用>      # 🔴 项目底线 < 512 字符；第三人称；key use case 前置
when_to_use: <触发短语/示例>        # 🔴 项目底线 < 128 字符；description 装不下的「何时用」放这
disable-model-invocation: true    # 副作用操作必加（仅手动 /name）
allowed-tools: Bash(git *)         # 预授权工具（可选，仅免批准不限制工具池）
paths: packages/api/**             # monorepo 按包触发（可选）
---
```

**description 铁律**（P0 反模式）：
- 第三人称（禁「I can」「You can use」）
- 含 key terms（用户会说的词）
- 同时写「做什么」+「何时用」
- **key use case 必须前置**：🔴 **项目底线 description < 512 字符**（比官方 best-practices 1024 / skills 参考页组合 1536 截断更严）；长列表按「最少 invoke 先丢」裁剪
- **超长内容分流**：description 装不下的触发短语/示例放 `when_to_use`（项目底线 < 128 字符，计入官方 1536 组合截断）
- **收窄「何时用」边界**：太泛（「Helps with code」）会误触发——可发现性 ≠ 触发准确性（见 Phase 5 测试 4）

### Phase 4: 内容

**渐进披露**：SKILL.md 像目录，指向按需加载的细节。

```markdown
# <Skill Name>

## Quick start
<最小可执行示例>

## Advanced
**A 功能**：见 [references/a.md](references/a.md)
**B 功能**：见 [references/b.md](references/b.md)
```

**复杂工作流给可复制 checklist**（Claude 逐项打勾）：
```markdown
任务进度：
- [ ] Step 1: ...
- [ ] Step 2: ...
```

**Feedback loop**（质量关键操作必加）：run validator → fix → repeat。

**Plan-validate-execute**（批量/破坏性操作）：产 structured plan 文件 → 脚本验证 → 执行 → verify。

**只加 Claude 不知道的**：默认 Claude 已聪明。每段都问「这段值得它的 token 成本吗？」

> 🔴 **CHECKPOINT**：SKILL.md 初稿完成后展示给用户审阅，确认内容方向正确后进 Phase 5。方向性问题必须在验证前拦截。

### Phase 5: 验证

1. **eval 先行**（写内容前，落实铁律 #4）：跑 3 个代表性任务**不带** skill 记录失败 baseline → 写 ≥3 eval 场景（query + expected_behavior，格式见 `references/research/01-anthropic-official.md`）→ 写完对比
2. **结构自检**（跑下方「反模式黑名单」逐项查）
3. **AI 可发现性质检**：
   ```bash
   claude -p "列出所有可用 skill 并说明何时触发" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
4. **🛑 触发准确性测试**（关键，区别于可发现性）：用 skill-creator 的 should-trigger（该触发）+ should-not-trigger（不该触发）prompt 对，测 false positive / false negative。可发现性只测「能列出」，**测不到误触发/漏触发**——这是零可见度故障
5. **反拷问**（可选）：`/grilling` red-team 框架漏洞
6. **9 维评分**（可选）：darwin-skill 跑自主优化
7. **A/B eval**（可选）：`/plugin install skill-creator@claude-plugins-official`，with vs without skill 对比

### Phase 6: 维护（改已有 skill）

改已有 skill ≠ 从零写。关键差异：

- **invoke 后 session 不更新**：SKILL.md 渲染为单条消息整 session 常驻，改文件后**已 invoke 的 session 仍跑旧版**。通知用户需新 session 或重新 invoke。
- **改动范围判断**：行为/触发变更（影响用户 muscle memory 与下游发现逻辑）→ 评估是否新建 skill 而非原地改；仅 body 优化（不改触发/输出契约）→ 原地改。
- **回归**：改后跑原 eval 场景确认未 break。
- **版本语义**：description 触发词变更 = 破坏性（下游依赖发现逻辑会变）；仅 body 优化 = 兼容。

## 失败处理（dim3 三段式编码）

编写过程中常见失败的 if-then 三段式：

| 触发条件 | 一线修复 | 仍失败兜底 |
|----------|---------|-----------|
| `claude -p` 质检返回空/错误 | 查 frontmatter YAML（tab/空格混用、引号未闭合），`--debug` 看 parse 错误 | 最小化 frontmatter 只留 name+description 重试 |
| AI 识别错误（skill 被当别的用途） | description key use case 前置 + 删歧义词 | 拆成 2 个更聚焦的 skill |
| skill 不触发（false negative） | description 补用户会说的关键词 | 查是否被 `skillOverrides` 关闭 / 预算裁剪（`/doctor`） |
| skill 误触发（false positive） | description 收窄「何时用」边界 | 加 `disable-model-invocation: true` 改手动 |
| SKILL.md 超 500 行 / 超 token 预算 | 拆 `references/`（CJK 密度 2-3x 英文，表格/代码块密度更高） | 评估拆多个 skill |
| 改了 skill 但 session 没生效 | 新 session 或重新 `/skill-name` invoke | 见 Phase 6，invoke 后 session 不重读文件 |
| 反拷问暴露逻辑漏洞 | 补对应失败分支到本文 | 标记 known limitation，description 限制使用范围 |

## 共识铁律（全源一致，不可违反）

| # | 铁律 | 理由 |
|---|------|------|
| 1 | SKILL.md ≤500 行（**token proxy 非精确值**） | CJK/表格/代码块 token 密度高，500 行中文可能 8000+ token；加载后整 session 常驻 |
| 2 | description 第三人称 + key use case 前置 + 做什么+何时用 + **收窄边界防误触发** | description 是 100+ skill 中的发现入口，🔴 **项目底线 < 512 字符**（官方 best-practices 1024 / 组合 1536 截断）；超长分流到 `when_to_use`（底线 < 128） |
| 3 | 引用只深一层 | 嵌套致 head 预读信息不全 |
| 4 | eval 先于文档（Phase 5 步骤 1） | 解决真实问题而非臆想 |
| 5 | 反例黑名单 > 正例清单 | 反例抓住指令遗漏的失败模式 |
| 6 | 一致术语 + 正斜杠路径 + 无 voodoo 常量 | 跨平台 + 可维护 |
| 7 | token 生命周期意识 | auto-compaction 保留最近 invoke 前 5000 token、合计预算 25000 token 跨 skill 共享，多 skill session 旧 skill 会被丢——**且无错误信息**，是最难 debug 的零可见度故障 |

## subagent 编写要点

subagent ≠ skill：独立 context + 自定义 system prompt + 特定工具 + 独立权限。

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices. Use proactively after code changes.
tools: Read, Glob, Grep, Bash       # 不列则继承全部
model: sonnet                        # sonnet/opus/haiku/fable/inherit
---
<body = system prompt>
```

**关键设计点**：

- **body 就是 system prompt**：subagent 只收 body + 环境细节，**不继承完整 CC system prompt**。关键约定必须在 body 内显式写。
- **🛑 错误处理约定**（致命遗漏补全）：body 须指示 Claude 工具失败时（Bash 超时 / Read 文件不存在 / MCP 掉线）**显式标注 `[工具失败: <原因>]` 而非把错误输出当结果返回**。否则主对话会把 subagent 的错误摘要当有效数据消费——静默降级，且直到出事才发现不了。
- **工具继承例外**（即使列了也不给）：AskUserQuestion / EnterPlanMode / ExitPlanMode(非 plan) / ScheduleWakeup / WaitForMcpServers。
- **Explore / Plan 跳过 CLAUDE.md + git status**：其他 subagent 都加载。若规则必须到达（如「忽略 vendor/」），须在委派 prompt 里重述。
- **skills 字段**：注入完整 skill 内容（非仅 description）。不能 preload `disable-model-invocation: true` 的 skill。
- **memory 字段**：`user`/`project`/`local`，跨会话学习。`project` 可版本控制共享，推荐默认。
- **PreToolUse hook 条件验证**：需细于 tools 字段的控制时用（例只允许 SELECT 的 db agent，hook grep 写操作 exit 2 阻断）。
- **嵌套**：subagent 可 spawn 自己的 subagent，深度限 5 层。fork 不能再生 fork。
- **fork vs named**：fork 继承整段对话（省重新解释），named 从定义文件起步（隔离干净）。

**选 subagent vs 主对话 vs skill**：
- 主对话：频繁往返、多阶段共享 context、快速小改、延迟敏感
- subagent：产出冗余、需工具限制、自包含回摘要
- skill：可复用 prompt，主对话 context 内跑；`context: fork` 可在 skill 内嵌 subagent

## 流派分歧（取舍非二选一）

### 常驻 vs 按需

| 类型 | 适合 | 代表 |
|------|------|------|
| 常驻（CLAUDE.md / AGENTS.md） | 全局约定、编码标准、安全硬规 | 规则遵守一致性高，持续耗 token |
| 按需（Skills） | 工作流、领域知识、可复用流程 | token 省、上下文洁净，依赖触发 |

→ 硬规进 CLAUDE.md，流程进 skill。

### 显式 vs 隐式触发

- Claude skill = 显式（description 是发现入口，让 Claude 判何时用）
- Cursor rule = 隐式（文件 glob 命中即强制生效）

→ 本 skill 是显式（`disable-model-invocation: true`）。

### runtime 中立

好的 agent 配置应平台中立：SKILL.md 不写死「在 Claude Code 里」（除非用 CC 扩展字段如 `context: fork`）。badge 用 `Agent Skills Standard` 而非钉死单一 runtime。

## 🛑 反模式黑名单（dim9 反向约束）

### P0 致命（skill 失效）

| # | 反模式 | 正例 |
|---|--------|------|
| 1 | vague description（「Helps with marketing」） | `Processes marketing campaign data from CSV/Excel, generates ROI reports. Use when analyzing campaign metrics, conversion rates, or marketing spend.` |
| 2 | frontmatter YAML 缩进/引号错误 | `claude --debug` 查 parse 错误（常见：tab/空格混用、引号未闭合） |
| 3 | description 关键词被截断丢 | key use case 前置；🔴 控制在 **512 字符内**（项目底线）；超长分流 `when_to_use`（< 128）；长列表用 `skillOverrides` `name-only` 释放预算（`/doctor` 查裁剪） |
| 4 | 路径错误 / skill 孤立 | `find . -name SKILL.md` 确认存在 + `claude -p "列出所有可用 skill"` 验证发现 |
| 5 | description 太泛致误触发（false positive） | 收窄「何时用」边界 + should-not-trigger 测试（skill-creator） |

### P1 严重（效果劣化）

| # | 反模式 | 正例 |
|---|--------|------|
| 6 | 解释 Claude 已知的事 | 只加 Claude 不知道的 |
| 7 | SKILL.md 超 500 行 | 拆 `references/` |
| 8 | 给太多选项 | 给 default + escape hatch |
| 9 | 嵌套引用过深 | 只深一层 |
| 10 | 无 eval 就发布 | 先建 ≥3 场景 eval（Phase 5 步骤 1） |
| 11 | Windows 反斜杠路径 | 统一正斜杠 |
| 12 | token 超 compaction 预算（≠ 行数） | CJK/表格/代码块密度高，500 行中文可能 8000+ token，多 skill session 被反复踢出且无错误信息——控制实际 token 不只行数 |

### P2 中等（质量损耗）

| # | 反模式 | 正例 |
|---|--------|------|
| 13 | 术语混用（field/box/element） | 选定一个贯穿 |
| 14 | 时间敏感信息内联 | 放 old patterns `<details>` |
| 15 | 脚本 punt 错误给 Claude | 显式 try/except + 默认值 |
| 16 | voodoo constants（TIMEOUT=47） | 注释为何这个值 |
| 17 | 假设包已安装 | 显式 `pip install` |

### P3 结构性

| # | 反模式 | 正例 |
|---|--------|------|
| 18 | 只写正例不写反例 | 反例黑名单成章（本节即示范） |
| 19 | 「必须」措辞代替视觉标记 | 🔴 / 🛑 视觉标记（LLM 扫标记优先于语义） |
| 20 | 两列 fallback（症状/解法） | 三段式（触发条件/一线修复/兜底，见上方「失败处理」） |
| 21 | 过度优化硬凑轮数 | Δ<2 连续 2 轮即停 |
| 22 | runtime 钉死单一平台 | 中立 badge + 中立措辞 |

## 验证 checklist（产物发布前逐项查）

### 结构
- [ ] SKILL.md ≤500 行（CJK 内容留更大余量）
- [ ] description 第三人称 + key use case 前置 + 做什么+何时用 + 🔴 **< 512 字符**（项目底线）
- [ ] when_to_use < 128 字符（项目底线，若有）
- [ ] frontmatter 字段合法（16 字段全表见 [references/frontmatter-spec.md](references/frontmatter-spec.md)）
- [ ] 引用只深一层
- [ ] >100 行 reference 顶部有目录
- [ ] frontmatter YAML 语法正确（`--debug` 验证）

### 触发准确性（≠ 可发现性）
- [ ] `claude -p` 可发现性通过（能列出 + 说明何时触发）
- [ ] should-trigger 测试通过（该触发的 prompt 命中）
- [ ] should-not-trigger 测试通过（不该触发的 prompt 不命中）

### 内容
- [ ] 无时间敏感信息（或放 old patterns）
- [ ] 术语一致
- [ ] 正斜杠路径
- [ ] 复杂工作流有 checklist
- [ ] 质量关键操作有 feedback loop
- [ ] 失败模式有三段式 fallback 编码

### 代码（若含脚本）
- [ ] 脚本 solve 不 punt（显式错误处理）
- [ ] 无 voodoo constants
- [ ] 依赖显式列出
- [ ] MCP 工具用全限定名 `Server:tool`

### 验证
- [ ] eval 先行（≥3 场景，先 baseline 后对比）
- [ ] 反例黑名单成章

## 诚实边界（去自夸，真限制）

- 本 skill 针对 Claude 生态（Agent Skills 标准），跨平台迁移需调整触发机制。
- **调研来源含 3 个自媒体平台**（Medium / LinkedIn / Substack），无独立第三方复现；反模式频次基于这些来源的主观汇总，非系统性统计。
- **9 维 rubric / HL-1~4 只在 darwin-skill 自身测试集验证**（用自己出的题考自己），非同行评审、无第三方基准。
- 框架**未经真实第三方用户验证**，「覆盖所有编写场景」是设计意图非实证结论。
- 本 skill 不教人物/主题视角蒸馏（nuwa 职责）。

## 调研来源

完整素材见 `references/`（规范参考）与 `references/research/`（调研素材）：

| 文件 | 维度 | 主源 |
|------|------|------|
| frontmatter-spec.md | frontmatter 16 字段全表 + 项目底线 | code.claude.com/docs/zh-CN/skills（官方一手） |
| 01-anthropic-official.md | 官方规范 | platform.claude.com / code.claude.com（3 份一手） |
| 02-academic-best-practices.md | 学术方法论 | darwin-skill 本地实证 + Anthropic eval |
| 03-community-ecosystem.md | 社区生态 | awesome-claude-skills / anthropics/skills / alchaincyf |
| 04-cross-platform-comparison.md | 跨平台对照 | Cursor / Codex / OpenCode / Gemini 对比 |
| 05-anti-patterns.md | 反模式 | 106 skills / Charlie O'Brien / SitePoint / darwin dim9 |
| 06-toolchain-validation.md | 工具链 | darwin-skill / grill-me / skill-creator |

信息源黑名单（永远排除）：知乎、微信公众号、百度百科。

---

> 调研时间：2026-06-26。功能型 skill（框架概览 + 流派对比），非角色扮演型。
