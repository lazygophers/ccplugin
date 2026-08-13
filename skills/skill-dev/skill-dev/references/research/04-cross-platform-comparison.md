# 维度 4：跨平台对照（Claude / Cursor / Codex / OpenCode / Gemini / Kiro）

> 理解各平台 agent 配置范式差异，让产物（Claude 生态 skill）在设计时知晓边界与可迁移性。

## 来源清单

| # | 来源 | URL |
|---|------|-----|
| A | cursorrules vs AGENTS.md vs CLAUDE.md 对比 | https://serenitiesai.com/articles/cursorrules-vs-agents-md-vs-claude-md-comparison |
| B | AGENTS.md vs .cursorrules vs Claude Skills 2026 | https://blog.buildbetter.ai/agents-md-vs-cursorrules-vs-claude-skills-2026-comparison/ |
| C | Cross-Platform Agent Skills Guide | https://zazencodes.substack.com/p/cross-platform-agent-skills-guide |
| D | Reddit: Cursor Rules vs Skills | https://www.reddit.com/r/cursor/comments/1rlpyvt/ |
| E | Claude Code vs Codex vs Cursor vs OpenCode | https://www.developersdigest.tech/blog/claude-code-vs-codex-vs-cursor-vs-opencode |

## 平台范式对照

| 平台 | 配置文件 | 触发方式 | 结构 | 作用范围 |
|------|---------|---------|------|---------|
| **Claude Code** | SKILL.md + CLAUDE.md | 显式 `/skill` + 模型自动 invoke | 目录 + frontmatter + 多文件 | skill 按需加载，CLAUDE.md 常驻 |
| **Cursor** | .cursorrules / rules/ | 文件上下文智能应用 | 单文件规则 | 全局/按 glob |
| **Codex** | AGENTS.md | 启动加载 | 单 markdown | 仓库级常驻 |
| **OpenCode** | agents 配置 | 类 Codex | — | — |
| **Gemini CLI** | GEMINI.md | 启动加载 | 单 markdown | 仓库级 |
| **Kiro** | specs/ | spec 驱动 | 结构化 spec | 任务级 |

## 关键差异洞察

### 1. Claude Skills = 显式触发，Cursor Rules = 隐式触发（来源 D）

Reddit 明确：Claude Code skills 设计为显式 invoke，Cursor 的「智能应用」rules 基于文件上下文自动触发。这意味着：
- Claude skill 的 description 是**发现**入口（让 Claude 知道何时用）
- Cursor rule 的文件匹配是**强制**入口（命中 glob 即生效）

### 2. Vercel eval 数据：AGENTS.md 100% vs Skills 53%（来源 A）

SerenitiesAI 引用 Vercel eval 数据称 AGENTS.md（常驻、仓库级）达 100% 通过率，Skills（按需加载）53%。
> 推测：此数据可能针对特定场景（规则遵守类任务）。常驻配置在「全局约定遵守」上确实优于按需加载，但按需加载在 token 成本和上下文洁净度上更优。产物应说明二者取舍，而非简单宣布谁赢。

### 3. Agent Skills 开放标准（来源 C）

Claude Code skills 遵循 Agent Skills 开放标准，跨多工具兼容。darwin-skill 据此强调 runtime 中立——SKILL.md 不应写死「在 Claude Code 里」，badge 应用中立标识。

### 4. AGENTS.md 生态（Codex / 跨平台）

AGENTS.md 正成为跨平台约定（Codex 原生，其他工具也读）。darwin-skill 的 runtime-neutral 倾向与此一致：好的 agent 配置应尽量平台中立，把平台特有字段（Claude 的 frontmatter 扩展）与通用指令分离。

## 设计取舍矩阵

| 取舍 | 常驻（CLAUDE.md/AGENTS.md） | 按需（Skills） |
|------|---------------------------|---------------|
| 规则遵守一致性 | 高（常在 context） | 中（依赖触发） |
| token 成本 | 持续消耗 | 仅触发时消耗 |
| 适合内容 | 全局约定、编码标准、安全硬规 | 工作流、领域知识、可复用流程 |
| 迭代灵活性 | 改动影响全 session | 改动只影响触发后 |

## 产物框架应用点

产物应：
- 明确 skill vs CLAUDE.md 的分工边界（可复用流程 → skill；全局硬规 → CLAUDE.md）
- runtime 中立措辞（不写死 Claude Code，除非用 CC 扩展字段）
- 在诚实边界中说明：本产物针对 Claude 生态（Agent Skills 标准），跨平台迁移需调整触发机制
