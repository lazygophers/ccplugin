---
name: skill-author
description: 创建与优化 Claude skills 和 subagents 的方法论框架。当用户要编写 SKILL.md、创建新 skill、设计 subagent / agent.md、配置 frontmatter、拆分 progressive disclosure、优化现有 skill 质量时使用。仅手动 /skill-author 触发。
disable-model-invocation: true
---

# Skill Author — Skill / Agent 编写方法论

> 本 skill 是 meta-skill：它教如何编写其他 skill 与 subagent。基于 Anthropic 官方规范 + darwin-skill 9 维实证 + 社区反模式汇总。完整调研素材见 `references/research/01-06.md`。

## 🔴 硬规（违反即失效）

1. **显式触发**：本 skill `disable-model-invocation: true`，仅 `/skill-author` 手动调用。不要建议改为自动触发——它是创作工具，不是背景知识。
2. **产物定位**：帮用户造 skill 或 subagent，不造人物/主题视角 skill（那是 nuwa 的职责）。
3. **诚实标注**：禁编造引用。无法核实的来源直接弃用（本 skill 调研中 SkillLens/SkillOpt 论文即因无法核实而弃用）。

## 何时用本 skill

| 场景 | 例子 |
|------|------|
| 从零创建 skill | 「帮我做一个部署 skill」「写个 PR review skill」 |
| 创建 subagent | 「加一个 code-reviewer subagent」「配只读 db agent」 |
| 优化现有 skill | 「这个 skill 不触发」「太长了」「效果不好」 |
| 结构决策 | 「这段该进 SKILL.md 还是拆 reference？」「该用 context:fork 吗？」 |
| frontmatter 配置 | 「description 怎么写」「该不该 disable-model-invocation」 |

## 编写流程（5 Phase）

### Phase 1: 定位

先回答 4 个问题，再动笔：

1. **skill 还是 subagent？**
   - 可复用 prompt/工作流、在主对话跑 → **skill**
   - 产出冗余输出需隔离、需强制工具限制、自包含回摘要 → **subagent**
   - 背景知识（不应作为命令触发）→ skill + `user-invocable: false`
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
├── SKILL.md              # 主指令（≤500 行）
├── references/           # 按需加载的细节（只深一层）
│   ├── <domain-a>.md
│   └── <domain-b>.md
└── scripts/              # 可执行脚本（执行而非加载）
    └── <tool>.py
```

- 多域 skill 按域拆 `references/<domain>.md`，避免加载无关 context。
- >100 行的 reference 文件顶部放目录，便于 Claude 预读见全貌。
- **引用只深一层**：禁 a→b→c 嵌套（Claude 对嵌套会 `head -100` 预读致信息不全）。

### Phase 3: frontmatter

```yaml
---
name: <lowercase-kebab>           # ≤64 字符，禁 anthropic/claude 保留词，禁 XML 标签
description: <做什么 + 何时用>      # ≤1024 字符，第三人称，key use case 前置
disable-model-invocation: true    # 副作用操作必加
allowed-tools: Bash(git *)         # 预授权工具（可选）
paths: packages/api/**             # monorepo 按包触发（可选）
---
```

**description 铁律**（P0 反模式）：
- 第三人称（禁「I can」「You can use」）
- 含 key terms（用户会说的词）
- 同时写「做什么」+「何时用」
- **key use case 必须前置**：description+when_to_use 合计上限 1536 字符，长 skill 列表会按「最少 invoke 先丢」裁剪

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

### Phase 5: 验证

1. **结构自检**（跑下方「反模式黑名单」逐项查）
2. **AI 可发现性质检**：
   ```bash
   claude -p "列出所有可用 skill 并说明何时触发" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
3. **反拷问**（可选）：用 `/grilling` red-team 框架漏洞
4. **9 维评分**（可选）：用 darwin-skill 跑自主优化
5. **A/B eval**（可选）：`/plugin install skill-creator@claude-plugins-official`，跑 with vs without skill 对比

## 共识铁律（全源一致，不可违反）

| # | 铁律 | 理由 |
|---|------|------|
| 1 | SKILL.md ≤500 行 | 加载后整 session 常驻，每行持续占 context |
| 2 | description 第三人称 + key use case 前置 + 做什么+何时用 | description 是 100+ skill 中的发现入口，会裁剪 |
| 3 | 引用只深一层 | 嵌套致 head 预读信息不全 |
| 4 | eval 先于文档 | 解决真实问题而非臆想 |
| 5 | 反例黑名单 > 正例清单 | 反例抓住指令遗漏的失败模式 |
| 6 | 一致术语 + 正斜杠路径 + 无 voodoo 常量 | 跨平台 + 可维护 |

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
- skill：可复用 prompt，主对话 context 内跑

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
| 1 | vague description（「Helps with marketing」） | 第三人称 + key terms + 做什么+何时用 |
| 2 | frontmatter YAML 缩进/引号错误 | `--debug` 查 parse 错误 |
| 3 | description 关键词被截断丢 | key use case 前置；长列表用 skillOverrides `name-only` 释放预算 |
| 4 | 路径错误 / skill 孤立 | 验证目录结构 + `What skills are available?` |

### P1 严重（效果劣化）

| # | 反模式 | 正例 |
|---|--------|------|
| 5 | 解释 Claude 已知的事 | 只加 Claude 不知道的 |
| 6 | SKILL.md >500 行 | 拆 references/ |
| 7 | 给太多选项 | 给 default + escape hatch |
| 8 | 嵌套引用过深 | 只深一层 |
| 9 | 无 eval 就发布 | 先建 ≥3 场景 eval |
| 10 | Windows 反斜杠路径 | 统一正斜杠 |

### P2 中等（质量损耗）

| # | 反模式 | 正例 |
|---|--------|------|
| 11 | 术语混用（field/box/element） | 选定一个贯穿 |
| 12 | 时间敏感信息内联 | 放 old patterns `<details>` |
| 13 | 脚本 punt 错误给 Claude | 显式 try/except + 默认值 |
| 14 | voodoo constants（TIMEOUT=47） | 注释为何这个值 |
| 15 | 假设包已安装 | 显式 `pip install` |

### P3 结构性

| # | 反模式 | 正例 |
|---|--------|------|
| 16 | 只写正例不写反例 | 反例黑名单成章（本节即示范） |
| 17 | 「必须」措辞代替视觉标记 | 🔴 / 🛑 视觉标记（LLM 扫标记优先于语义） |
| 18 | 两列 fallback（症状/解法） | 三段式（触发条件/一线修复/兜底） |
| 19 | 过度优化硬凑轮数 | Δ<2 连续 2 轮即停 |
| 20 | runtime 钉死单一平台 | 中立 badge + 中立措辞 |

## 验证 checklist（产物发布前逐项查）

### 结构
- [ ] SKILL.md ≤500 行
- [ ] description 第三人称 + key use case 前置 + 做什么+何时用
- [ ] 引用只深一层
- [ ] >100 行 reference 顶部有目录
- [ ] frontmatter YAML 语法正确（`--debug` 验证）

### 内容
- [ ] 无时间敏感信息（或放 old patterns）
- [ ] 术语一致
- [ ] 正斜杠路径
- [ ] 复杂工作流有 checklist
- [ ] 质量关键操作有 feedback loop

### 代码（若含脚本）
- [ ] 脚本 solve 不 punt（显式错误处理）
- [ ] 无 voodoo constants
- [ ] 依赖显式列出
- [ ] MCP 工具用全限定名 `Server:tool`

### 验证
- [ ] `claude -p` 质检通过（AI 能正确理解识别）
- [ ] ≥3 eval 场景已建（或指向 skill-creator）
- [ ] 反例黑名单成章

## 诚实边界

- 本 skill 针对 Claude 生态（Agent Skills 开放标准），跨平台迁移需调整触发机制。
- 调研中 darwin-skill 引用的 SkillLens / SkillOpt 论文（arXiv 2605.23899 / 2605.23904）经独立检索无法核实，已弃用；方法论内核以独立成立 + 官方 eval 交叉验证保留。
- 本 skill 不教人物/主题视角蒸馏（那是 nuwa 职责，见 memory）。
- 9 维 rubric / HL-1~4 来自 darwin-skill 本地实证，非同行评审学术来源。

## 调研来源

完整素材见 `references/research/`：

| 文件 | 维度 | 主源 |
|------|------|------|
| 01-anthropic-official.md | 官方规范 | platform.claude.com / code.claude.com（3 份一手） |
| 02-academic-best-practices.md | 学术方法论 | darwin-skill 本地实证 + Anthropic eval |
| 03-community-ecosystem.md | 社区生态 | awesome-claude-skills / anthropics/skills / alchaincyf |
| 04-cross-platform-comparison.md | 跨平台对照 | Cursor / Codex / OpenCode / Gemini 对比 |
| 05-anti-patterns.md | 反模式 | 106 skills / Charlie O'Brien / SitePoint / darwin dim9 |
| 06-toolchain-validation.md | 工具链 | darwin-skill / grill-me / skill-creator |

信息源黑名单（永远排除）：知乎、微信公众号、百度百科。

---

> 调研时间：2026-06-26。本 skill 由 huashu-nuwa 主题 skill 变体流程生成，产物为功能型（框架概览 + 流派对比），非角色扮演型。
