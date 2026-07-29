# 官方 Agent Skills 编写规范 (调研留档)

来源全部为官方: `platform.claude.com/docs` (原 docs.claude.com, 302 跳转) 与 `code.claude.com/docs`、`github.com/anthropics/skills`。
检索通道: WebFetch + WebSearch (无 agent-reach, FALLBACK 模式; 本主题未覆盖 anthropic.com engineering blog — 未取到, 见文末)。

## 结论摘要 (可直接落地的准则)

1. frontmatter 只有 `name` / `description` 必填, 其余 (`license` / `allowed-tools` / `metadata` / `compatibility`) 可选 — [best-practices §Skill structure](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
2. `name` ≤64 字符, 只允许小写字母/数字/连字符, 禁 XML 标签, 禁保留词 "anthropic"/"claude", 且必须与父目录同名 — 同上
3. `description` ≤1024 字符, 非空, 禁 XML 标签, 必须同时写「做什么 + 何时用」 — 同上
4. description **必须第三人称**; "I can help you…" / "You can use this to…" 都会因视角不一致伤 discovery — 官方以 Warning 级别标注
5. description 要含具体触发词/上下文 (`Use when the user asks…`, `when the user mentions PDFs, forms, or document extraction`) — 官方给了 Git Commit Helper 的范例, 与本任务 git/ 四技能同域
6. SKILL.md body **≤500 行**为最佳性能线, 超了就拆文件 — 官方 §Token budgets 明确
7. progressive disclosure: 启动只预载 name+description; body 命中才读; 引用文件/脚本按需读, 未读不耗 token
8. **引用只允许一层深** (SKILL.md → reference.md), 嵌套引用会导致 Claude 用 `head -100` 预览、信息不全 — 官方 §Avoid deeply nested references
9. reference 文件 >100 行必须带 Table of Contents, 保证部分读取也能看到全貌
10. 自由度分级 (degrees of freedom): 多解走文字步骤(高)、有偏好模式走带参脚本(中)、脆弱/顺序敏感走「照抄这条命令, 禁改 flag」(低)
11. 复杂多步任务给可勾选 checklist, 让 Claude 抄进回复逐条勾 — 官方 §Use workflows for complex tasks
12. feedback loop 模式 (跑校验 → 修 → 重跑 → 只有过了才继续) 显著提升质量; 「validator」可以是脚本, 也可以是一份 STYLE_GUIDE.md
13. 术语必须全篇统一 (别混用 extract/pull/get/retrieve); 禁时间敏感表述 (「2025年8月前用旧 API」), 过时内容塞 `## Old patterns` + `<details>`
14. 禁给多选项 (「你可以用 pypdf 或 pdfplumber 或 PyMuPDF…」), 给一个默认 + 一个逃生口
15. 禁 Windows 反斜杠路径; 引用 MCP 工具必须全限定名 `ServerName:tool_name`
16. Claude Code 扩展字段: `disable-model-invocation: true` (仅用户可调, 适合 /commit /deploy 这类有副作用的)、`user-invocable: false` (仅模型可调, 适合背景知识) — [code.claude.com/docs/en/skills §Control who invokes a skill](https://code.claude.com/docs/en/skills)
17. 三态载入表 (官方原表): 默认=description 常驻+调用时载 body; `disable-model-invocation` = description **不进 context**; `user-invocable:false` = description 常驻但无斜杠命令
18. **skill 内容只注入一次**: 调用时 SKILL.md 渲染成一条消息留在会话里, Claude 后续回合不会重读文件 → 「全程适用的规则」要写成 standing instructions, 别写成一次性步骤 — code.claude.com §Skill content lifecycle
19. `allowed-tools` 授权在用户下一条消息后失效 (与 skill 文本常驻不同) — 同上
20. 命名建议动名词 (`processing-pdfs`), 可接受名词短语 (`pdf-processing`) / 动宾 (`process-pdfs`); 禁 `helper`/`utils`/`tools` 一类空名; 一套 skill 集合内命名模式要一致
21. 先写 evaluation 再写文档 (evaluation-driven): 无 skill 跑基线 → 建 ≥3 个场景 → 写最小指令 → 迭代; 交付前至少 3 条 eval, 且 Haiku/Sonnet/Opus 都测
22. anthropics/skills 的 skill-creator 额外主张: description 调优阶段造 ~20 条 eval query (含 should-trigger 与 should-not-trigger) 验触发准确率

## 与 writing-great-skills 词汇的对应 (映射, 非官方原文)

| 官方条目 | writing-great-skills 词汇 |
|---|---|
| description 写「什么 + 何时」、含触发词 | invocation 选择 (model-invoked 的准入面) |
| `disable-model-invocation` / `user-invocable` | invocation 二选: 付 context load vs 付 cognitive load, 官方把它做成了 frontmatter 开关 |
| body ≤500 行 + 一层引用 + 按需读 | information hierarchy 三级阶梯 (in-skill step → in-skill reference → external reference) |
| 域内拆分 reference/finance.md 等 | progressive disclosure 按 branch 切分 |
| 「Claude 已经很聪明, 每段都要为 token 辩护」 | pruning 的 relevance 测 |
| 「避免 offering too many options」「术语统一」 | no-op / sprawl failure mode |
| Old patterns 折叠段 | sediment 的官方处置方式 |
| checklist + feedback loop「只有过了才继续」 | premature completion 的解药 |

推测: 官方没有 negation / duplication 的对位表述, 这两条只能靠 writing-great-skills 自带判据。

## 证据明细 (原文片段)

### frontmatter 约束
> `name`: Maximum 64 characters / Must contain only lowercase letters, numbers, and hyphens / Cannot contain XML tags / Cannot contain reserved words: "anthropic", "claude"
> `description`: Must be non-empty / Maximum 1,024 characters / Cannot contain XML tags / Should describe what the Skill does and when to use it
— https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices §Skill structure

### 第三人称硬规
> **Always write in third person**. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems.
> * **Good:** "Processes Excel files and generates reports"
> * **Avoid:** "I can help you process Excel files"
— 同上 §Writing effective descriptions

### 官方给的 git commit description 范例 (可直接对标本仓 git-commit)
> ```yaml
> description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
> ```
— 同上

### 体量
> Keep SKILL.md body under 500 lines for optimal performance. If your content exceeds this, split it into separate files using the progressive disclosure patterns described earlier.
— 同上 §Token budgets

### 一层引用
> Claude may partially read files when they're referenced from other referenced files. When encountering nested references, Claude might use commands like `head -100` to preview content rather than reading entire files, resulting in incomplete information. **Keep references one level deep from SKILL.md**.
— 同上 §Avoid deeply nested references

### 自由度
> **Low freedom** (specific scripts, few or no parameters): Use when: Operations are fragile and error-prone / Consistency is critical / A specific sequence must be followed … "Run exactly this script: `python scripts/migrate.py --verify --backup`. Do not modify the command or add additional flags."
— 同上 §Set appropriate degrees of freedom

### checklist / feedback loop
> For particularly complex workflows, provide a checklist that Claude can copy into its response and check off as it progresses.
> **Common pattern:** Run validator → fix errors → repeat … "**Only proceed when validation passes**"
— 同上 §Workflows and feedback loops

### 交付前 checklist (官方原表, 可直接当验收项)
> Description is specific and includes key terms / Description includes both what the Skill does and when to use it / SKILL.md body is under 500 lines / Additional details are in separate files (if needed) / No time-sensitive information / Consistent terminology throughout / Examples are concrete, not abstract / File references are one level deep / Progressive disclosure used appropriately / Workflows have clear steps
— 同上 §Checklist for effective Skills

### Claude Code 扩展 (invocation 控制)
> * **`disable-model-invocation: true`**: Only you can invoke the skill. Use this for workflows with side effects or that you want to control timing, like `/commit`, `/deploy`, or `/send-slack-message`. You don't want Claude deciding to deploy because your code looks ready.
> * **`user-invocable: false`**: Only Claude can invoke the skill. Use this for background knowledge that isn't actionable as a command.

| Frontmatter | You can invoke | Claude can invoke | When loaded into context |
|---|---|---|---|
| (default) | Yes | Yes | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes | No | Description not in context, full skill loads when you invoke |
| `user-invocable: false` | No | Yes | Description always in context, full skill loads when invoked |
— https://code.claude.com/docs/en/skills §Control who invokes a skill

### 内容生命周期 (对「步骤 vs 常驻规则」写法有直接影响)
> When you or Claude invoke a skill, the rendered `SKILL.md` content enters the conversation as a single message and stays there for the rest of the session. … an `allowed-tools` grant clears when you send your next message. Claude Code does not re-read the skill file on later turns, so write guidance that should apply throughout a task as standing instructions rather than one-time steps.
— 同上 §Skill content lifecycle

### 自定义命令已并入 skills
> **Custom commands have been merged into skills.** A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way.
— 同上

### skill-creator (官方仓库)
> Keep instructions lean and explain the "why" behind requirements … Spawn with-skill and baseline runs simultaneously … Generalize from feedback rather than overfitting to examples … Optimize Description: fine-tune skill triggering language
— https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

### 允许的 frontmatter 键集合 (二手, 非一手官方页面)
> allowed keys are name, description, license, allowed-tools, metadata, and compatibility
— WebSearch 汇总 (来源含 https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview 与第三方 cheat sheet)。推测: 该键集合与 overview 页一致, 但本次未逐字抓到 overview 页原文校验。

## 未取到 / 缺口

- anthropic.com engineering blog 的 skills 文章: 本轮未检索到具体 URL, **未取到** (尝试通道: WebSearch 两轮 + WebFetch 官方 docs; 未再扩轮, 因 platform.claude.com 已给出权威约束)。
- `agent-reach` 不可用 → 全程 WebSearch/WebFetch, 社区平台 (Reddit/HN/X) 数据未覆盖。
