# Claude Code Skills & Agents 官方规范与最佳实践

**资料日期**: 2026-05-16  
**知识截止**: 2026-01  
**参考源**: https://code.claude.com 官方文档

---

## 1. Skill (SKILL.md) 写作规范

### 1.1 SKILL.md 结构

每个 skill 是一个**目录**，包含必需的 `SKILL.md` 文件。

```text
my-skill/
├── SKILL.md              # 必需：入口点 + 指令
├── reference.md          # 可选：详细文档
├── examples.md           # 可选：示例集合
└── scripts/
    └── helper.py         # 可选：可执行脚本
```

**关键点**：
- SKILL.md 是**必需的唯一**文件（能让 Claude Code 识别该目录为 skill）
- 支持文件目录保持 SKILL.md 简洁（< 500 行推荐）
- 支持文件不会自动加载，需要从 SKILL.md 显式引用

### 1.2 Frontmatter 字段完整列表

```yaml
---
name: my-skill                    # 可选（默认目录名）字母/数字/连字符 (max 64)
description: What this skill does # 推荐（触发条件） ≤1536字符
when_to_use: Additional triggers  # 可选（附加触发短语）
argument-hint: [filename]         # 可选（参数提示）
arguments: [arg1, arg2]           # 可选（命名位置参数）
disable-model-invocation: true    # 可选（仅手动触发）
user-invocable: false             # 可选（仅模型可调）
allowed-tools: Read Grep          # 可选（无权限检查工具列表）
model: sonnet                     # 可选（覆盖会话模型）
effort: high                      # 可选（覆盖努力级别）
context: fork                     # 可选（forked subagent 执行）
agent: Explore                    # 可选（与 context:fork 配合）
paths: src/**/*.py               # 可选（文件模式限制触发）
shell: powershell                # 可选（bash 或 powershell）
hooks:                           # 可选（skill 生命周期钩子）
  PreToolUse: [...]
---
```

### 1.3 Description 写法（最关键）

官方要求：
- **第一句话包含关键用例**：描述框架上限为 1,536 字符，超过部分截断
- **动作导向语言**，第三人称，说明何时使用
- **触发短语示例**：如果用户可能说 "分析代码", 就在 description 中提及
- **同时满足** Claude 自动触发 + 用户 `/skill-name` 调用

**示例**：
```yaml
description: |
  Summarizes uncommitted changes and flags risky patterns. 
  Use when asking what changed, wanting a commit message, 
  or reviewing a diff. Also triggers on "what did I change?" or "review my changes".
```

### 1.4 Body 内容原则

**关键约束**：Skill content **一次加载后持久化到本轮对话**，Claude 不会重新读 SKILL.md。

最佳实践：
- **声明式**而非过程式：写出**应该做什么**，而非**怎么做**
- **引用支持文件**显式加载详细内容（如 `see [reference.md](reference.md)`)
- **动态上下文注入**用 `` !`command` `` 或 ` ```! ` 块
  ```markdown
  ## Live context
  Current diff:
  !`git diff HEAD`
  
  ## Task
  Summarize the changes above...
  ```

### 1.5 Advanced: 动态上下文注入

Shell 命令**在发送给 Claude 前执行**，输出替换占位符：

```yaml
---
name: pr-summary
context: fork
agent: Explore
---

## PR Info
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`

Summarize this PR...
```

禁用方式：`settings.json` 中 `"disableSkillShellExecution": true`

### 1.6 参数和字符串替换

支持的占位符：

| 占位符 | 含义 | 示例 |
|-------|------|-----|
| `$ARGUMENTS` | 所有参数 | `/my-skill foo bar` → `$ARGUMENTS` = `foo bar` |
| `$ARGUMENTS[0]` 或 `$0` | 第一个参数 | 同上 → `$0` = `foo` |
| `$name` | 命名参数 | 若 `arguments: [file, format]`，则 `$file` = 第一个值 |
| `${CLAUDE_SESSION_ID}` | 会话 ID | 用于日志、临时文件命名 |
| `${CLAUDE_EFFORT}` | 努力级别 | `low`, `medium`, `high`, `xhigh`, `max` |
| `${CLAUDE_SKILL_DIR}` | Skill 目录 | 脚本路径基准（不依赖 cwd） |

### 1.7 控制调用权限

| 字段 | 效果 |
|-----|------|
| `disable-model-invocation: true` | Claude 无法自动调用；仅 `/skill-name` 可用 |
| `user-invocable: false` | `/` 菜单隐藏；仅 Claude 可调用 |
| `allowed-tools: Read Bash(git *)` | 列出的工具无需权限提示 |
| （默认） | 两方都可调用；描述始终在上下文中 |

### 1.8 Skill 存储位置与优先级

| 位置 | 范围 | 优先级 | 自动发现 |
|-----|------|--------|---------|
| 托管设置 (`.claude/` in org admin path) | 组织范围 | 1 (最高) | ✓ |
| `~/.claude/skills/<name>/SKILL.md` | 所有项目 | 2 | ✓ |
| `.claude/skills/<name>/SKILL.md` | 当前项目 | 3 | ✓ |
| Plugin `skills/` 目录 | 插件启用位置 | 4 (最低) | ✓ |

**上游搜索**：项目 skills 从工作目录向上搜索至仓库根

---

## 2. Agent (Subagent .md) 写作规范

### 2.1 Agent 文件结构

Subagent 是一个 **Markdown 文件**，带 YAML frontmatter + 系统提示体。

```markdown
---
name: code-reviewer
description: Reviews code for quality. Use proactively after changes.
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer specialized in $ARGUMENTS.
Analyze code and provide specific, actionable feedback on:
- Quality and readability
- Security vulnerabilities
- Best practices alignment
```

### 2.2 Frontmatter 字段完整列表

只有 `name` 和 `description` **必需**：

| 字段 | 必需 | 值 | 说明 |
|-----|-----|-----|------|
| `name` | ✓ | kebab-case | 唯一标识符，[Hooks](/en/hooks#subagentstart) 接收此值 |
| `description` | ✓ | 文本 | Claude 何时委派到此 agent（触发条件） |
| `tools` | | 逗号/列表 | 允许工具（无则继承所有） |
| `disallowedTools` | | 逗号/列表 | 禁止工具（与 `tools` 配合） |
| `model` | | `sonnet`/`opus`/`haiku`/full ID/`inherit` | 模型（默认 `inherit`） |
| `permissionMode` | | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan` | 权限模式 |
| `maxTurns` | | 数字 | 最大代理转数 |
| `skills` | | 逗号/列表 | 预加载 skill 名称（完整内容注入） |
| `mcpServers` | | 名称或内联配置 | MCP 服务器 |
| `hooks` | | 钩子配置 | 生命周期钩子（plugin agents 不支持） |
| `memory` | | `user`/`project`/`local` | 跨会话记忆范围 |
| `background` | | `true`/`false` | 后台任务模式 |
| `effort` | | `low`/`medium`/`high`/`xhigh`/`max` | 努力级别 |
| `isolation` | | `worktree` | git worktree 隔离 |
| `color` | | `red`/`blue`/`green`/`yellow`/`purple`/`orange`/`pink`/`cyan` | UI 显示颜色 |
| `initialPrompt` | | 文本 | 首个自动提交提示（命令 + skill 处理） |

### 2.3 Description 写法

**必须清楚说明 Claude 何时委派**：

```yaml
description: |
  Specialized code reviewer analyzing security vulnerabilities.
  Use proactively after code changes to flag unsafe patterns,
  auth issues, and injection risks. Also on request for "security review" 
  or "audit this code".
```

对比不好的例子：
```yaml
# ❌ 不好：太宽泛，无触发条件
description: A code reviewer

# ❌ 不好：能力导向，非任务导向
description: Can review Python, JavaScript, and Go code
```

### 2.4 Tools 字段写法

**两种模式**：

**模式 A：白名单（allowlist）**
```yaml
tools: Read, Grep, Glob, Bash
```
agent 仅能使用这些工具

**模式 B：黑名单（denylist）**
```yaml
disallowedTools: Write, Edit
```
agent 继承所有工具，除了这些

**模式 C：限制子代理生成**
```yaml
tools: Agent(worker, researcher), Read, Bash
```
该 agent 仅能生成 `worker` 和 `researcher` 子代理

### 2.5 系统提示体（Body）

- **角色定义**：清楚说明 agent 的身份和专长
- **约束和边界**：列出禁止行为、工具限制
- **工作流步骤**：细分任务流程
- **输出格式**：如何呈现结果

```markdown
You are a security auditor specializing in web applications.

## Your expertise
- OWASP Top 10 vulnerabilities
- Auth and crypto patterns
- Input validation

## Process
1. Scan code for security issues
2. Rate severity (HIGH/MEDIUM/LOW)
3. Suggest fixes with code examples

## Output format
- Issue title
- Severity badge
- Root cause
- Proposed fix with code
- Test recommendation
```

### 2.6 Agent 存储位置与优先级

| 位置 | 范围 | 优先级 | 文件发现 |
|-----|------|--------|---------|
| 托管设置 | 组织范围 | 1 | 递归，按 `name` 去重 |
| `--agents` CLI flag | 当前会话 | 2 | JSON 格式 |
| `.claude/agents/` | 当前项目 | 3 | 递归，`name` 唯一 |
| `~/.claude/agents/` | 所有项目 | 4 | 递归，`name` 唯一 |
| Plugin `agents/` 目录 | 插件启用位置 | 5 | 递归，路径成为 scoped ID |

**Plugin agent 特殊性**：子目录路径成为作用域标识，如 `my-plugin:review:security`

### 2.7 Plugin Agents 限制

由于安全原因，plugin agents **不支持**：
- `hooks`
- `mcpServers`
- `permissionMode`

若需要这些，复制到 `.claude/agents/` 或 `~/.claude/agents/`。

---

## 3. Plugin 打包规范

### 3.1 plugin.json 结构

```json
{
  "name": "language-tools",
  "version": "1.0.0",
  "description": "C/C++/Go/Rust language support",
  "author": "Your Name",
  "homepage": "https://...",
  "repository": "https://github.com/...",
  "license": "MIT",
  "keywords": ["language", "tools"],
  
  "commands": "./commands",
  "skills": ["./skills", "./custom-skills"],
  "agents": "./agents",
  "hooks": "./hooks.json",
  "mcpServers": "./.mcp.json"
}
```

**要点**：
- `skills` 和 `agents` 可以是**数组**（多路径）
- 路径相对于插件根目录
- 默认目录自动发现（无需显式列出）

### 3.2 目录结构约定

```
language-tools/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── lint/
│   │   ├── SKILL.md
│   │   └── config.md
│   ├── format/
│   │   └── SKILL.md
│   └── ...
├── agents/
│   ├── code-reviewer.md
│   ├── debugger.md
│   └── ...
├── commands/           (deprecated, 但向后兼容)
│   └── ...
└── README.md
```

### 3.3 Skills vs Agents 差异

| 特性 | Skill | Agent |
|-----|-------|-------|
| 文件类型 | 目录 + SKILL.md | Markdown + frontmatter |
| 可由 Claude 自动触发 | ✓ (description 匹配) | ✓ (description 匹配) |
| 支持参数 | ✓ (`$ARGUMENTS`, `$name`) | 间接（通过委派) |
| 运行上下文 | 当前会话或 forked subagent | 独立会话 + 隔离上下文 |
| 持久化到对话 | ✓ (内容加载后留存) | 返回值摘要 + 原始内容不留存 |
| 支持文件 | ✓ (reference.md, scripts/) | ✗ (仅 frontmatter + body) |
| 最佳用途 | 参考、工具集、工作流 | 搜索密集、需隔离上下文 |

### 3.4 Commands 状态

官方文档说："Custom commands have been merged into skills."

- 旧式 `.claude/commands/deploy.md` **仍可用**
- 新建议用 `.claude/skills/deploy/SKILL.md`
- 两者创建相同的 `/deploy` 快捷方式
- Skill 方式支持更多功能（目录、支持文件、frontmatter）
- **Plugin 中不建议用 commands**，改用 skills

---

## 4. 最小可行示例

### 4.1 最小 Skill

`.claude/skills/hello-world/SKILL.md`：

```yaml
---
description: |
  Simple greeting skill that demonstrates triggers.
  Use when user says hello or greets you.
---

## Greeting

Hello! You've invoked the hello-world skill.

Current session ID: ${CLAUDE_SESSION_ID}
Effort level: ${CLAUDE_EFFORT}

How can I help you today?
```

### 4.2 最小 Agent

`.claude/agents/simple-reviewer.md`：

```yaml
---
name: simple-reviewer
description: |
  Reviews code files for bugs and improvements.
  Use proactively after code changes to suggest fixes.
tools: Read, Grep, Glob
model: sonnet
---

You are a code reviewer. When invoked, analyze the provided code
and offer three specific, actionable improvements focusing on:
1. Correctness (does it work as intended?)
2. Readability (can others understand it?)
3. Performance (can it be optimized?)

Format your response as a bulleted list with code snippets.
```

### 4.3 Plugin manifest

`.claude-plugin/plugin.json`：

```json
{
  "name": "my-language-tools",
  "version": "1.0.0",
  "description": "Language support plugin",
  "author": "Me",
  "license": "MIT",
  "skills": ["./skills"],
  "agents": "./agents"
}
```

目录结构：
```
my-language-tools/
├── .claude-plugin/plugin.json
├── skills/
│   ├── lint/SKILL.md
│   └── format/SKILL.md
├── agents/
│   └── reviewer.md
└── README.md
```

---

## 5. 官方权威参考

| 资源 | 用途 | URL |
|-----|------|-----|
| Skills 完整文档 | SKILL.md frontmatter、动态注入、生命周期 | https://code.claude.com/docs/en/skills |
| Subagents 完整文档 | Agent frontmatter、工具、内存、隔离 | https://code.claude.com/docs/en/sub-agents |
| Plugin 参考 | 打包、发布、组件路径、安全 | https://code.claude.com/docs/en/plugins-reference |
| Commands 参考 | 内置命令、bundled skills | https://code.claude.com/docs/en/commands |
| Plugin Marketplace 指南 | 发布到市场、版本管理 | https://code.claude.com/docs/en/plugin-marketplaces |

---

## 6. 快速检查清单

### Skill SKILL.md

- [ ] `name` 使用 kebab-case（可选但推荐）
- [ ] `description` < 1,536 字符，包含触发短语
- [ ] Body < 500 行（大文档移到支持文件）
- [ ] 支持文件从 SKILL.md 显式引用
- [ ] 动态命令用 `` !`cmd` `` 或 ` ```! ` 块
- [ ] 若仅手动触发，设 `disable-model-invocation: true`
- [ ] 若有敏感工具，设 `allowed-tools: ...`

### Agent .md

- [ ] `name` 和 `description` 必需
- [ ] `description` 明确说明触发条件（Claude 何时委派）
- [ ] `tools` 或 `disallowedTools` 只设其一（除非 `Agent(...)`)
- [ ] Body 明确角色、流程、输出格式
- [ ] Plugin agent 无 `hooks`/`mcpServers`/`permissionMode`
- [ ] `model` 默认 `inherit`（成本优化时改 `haiku`）

### Plugin manifest

- [ ] `.claude-plugin/plugin.json` 必须存在
- [ ] `skills` 和 `agents` 指向正确的目录
- [ ] 所有路径相对于插件根
- [ ] 不含 `commands` 字段（用 `skills` 代替）

---

## 7. 常见陷阱

| 陷阱 | 后果 | 修复 |
|-----|------|------|
| Description 不含触发条件 | Claude 不知道何时调用 | 列举用户可能说的短语 |
| Skill body 过大 | 上下文浪费 | 移大文档到 supporting files |
| Reread Skill content after invocation | 指令不再适用（模型选其他方式） | 作为"standing instructions"写 |
| Tools 和 disallowedTools 都设 | 行为不确定 | 仅用其一 |
| Plugin agent 设 `hooks` | 加载时忽略，无警告 | 复制到 `.claude/agents/` |
| 命名冲突（同级 skill/agent） | 高优先级胜出，无警告 | 保持名称唯一 |
| Skill 参数未用 `$ARGUMENTS` | 参数当作 ARGUMENTS: 追加 | 若支持参数，显式使用占位符 |

---

## 8. 代码质量验证

项目 CLAUDE.md 要求对 skills/agents 优化后验证：

```bash
claude \
  -p "<待测内容>" \
  --output-format stream-json | \
  jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

确保输出非空 + 符合预期识别。

