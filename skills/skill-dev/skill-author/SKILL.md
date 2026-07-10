---
name: skill-author
description: 创建与维护 Claude skills 和 subagents 的方法论框架。当用户要编写 SKILL.md、创建新 skill、设计 subagent / agent.md、配置 frontmatter、拆分 progressive disclosure、调整现有 skill 的结构/触发/维护陷阱时使用。纯 9 维质量评分优化（不改结构）→ 路由 skill-optimizer。仅手动 /skill-author 触发。
disable-model-invocation: true
argument-hint: "[skills 功能] <路径>"
arguments: "[skills 功能] <路径>"
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
| 优化/改现有 skill | 「这个 skill 不触发」「太长了」「改了没生效」（纯 9 维质量评分优化→skill-optimizer；结构/触发/维护陷阱→本 skill） |
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

## 失败处理（触发条件 → 一线修复 → 仍失败兜底）

高频故障内联于此（正文自包含）；完整 22 条反模式 fallback 见 [references/anti-patterns.md](references/anti-patterns.md)。

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| skill 写完不触发 | description 太泛/缺 key terms → 加用户会说的词 + 收窄边界 (Phase 5 测试 4) | 跑可发现性质检 (`claude -p "列出所有可用 skill"`) 看是否被列出；未列出查 name/description 是否含保留词或超 512 截断 |
| 改了 SKILL.md 没生效 | 已 invoke 的 session 常驻旧版 → 通知用户开新 session 或重新 invoke | 确认改的是被加载路径 (非 references 副本)；`disable-model-invocation` skill 需 `/name` 重新手动触发 |
| 多 skill session 里本 skill 行为丢失 | token 预算 25000 跨 skill 共享、旧 invoke 被 auto-compaction 丢 (零错误信息) → 精简 SKILL.md、细节拆 references 按需加载 | 缩到 ≤500 行仍丢 → 关键指令上移到 SKILL.md 顶部 5000 token 内 (compaction 保留窗) |
| reference 内容 Claude 读不全 | 嵌套引用 (a→b→c) 致 `head -100` 预读截断 → 拍平成只深一层 | >100 行 reference 顶部加目录，让预读见全貌 |
| description/when_to_use 被截断 | 超项目底线 (512/128) → 按「最少 invoke 先丢」裁剪，触发短语分流 when_to_use | 仍超 → 拆成多个更窄的 skill，各自 description 更聚焦 |
| 结构/触发正确但输出跑偏 | 缺反例黑名单 → 补「不要做 Y」清单 (铁律 #5) | 跑 `/grilling` red-team 找指令遗漏的失败模式 |

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

## subagent 编写要点 + 流派分歧

subagent frontmatter / body 设计点（错误处理约定 / 工具继承例外 / hook 条件验证 / fork vs named 等）+ 常驻vs按需 / 显式vs隐式触发 / runtime 中立取舍，详见 [references/subagent-authoring.md](references/subagent-authoring.md)。

## 反模式黑名单

P0 致命 / P1 严重 / P2 中等 / P3 结构性共 22 条，详见 [references/anti-patterns.md](references/anti-patterns.md)。

## 验证 checklist

产物发布前逐项查（结构 / 触发 / 内容 / 代码 / 验证 5 组），详见 [references/validation-checklist.md](references/validation-checklist.md)。

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
