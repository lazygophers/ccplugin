# Frontmatter 规范（官方 16 字段 + 项目底线）

> 权威来源：[code.claude.com/docs/zh-CN/skills#frontmatter-参考](https://code.claude.com/docs/zh-CN/skills#frontmatter-参考) + [best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)。所有字段可选，`description` 推荐。

## 🔴 项目底线（比官方更严，本仓库硬规）

| 字段 | 官方上限 | **项目底线** | 说明 |
|------|---------|------------|------|
| `description` | 独立 1024（best-practices）/ 组合计入 1536 截断（skills 参考页） | **< 512 字符** | key use case 前置；CJK 内容留更大余量 |
| `when_to_use` | 无独立上限，组合计 1536 | **< 128 字符** | 触发短语/示例请求；description 装不下的「何时用」放这里 |

> 官方 1536 是 description+when_to_use **合计** 在 skill 列表中的截断线；项目底线把两者各自压更紧，防长列表裁剪丢关键词。

## 字段全表（16 个，官方顺序）

| # | 字段 | 必需 | 类型 / 取值 | 作用 |
|---|------|------|------------|------|
| 1 | `name` | 否 | string，默认目录名 | skill 列表显示名（≠ `/` 后命令名，命令名来自目录名） |
| 2 | `description` | 推荐 | string，项目 < 512 | 做什么 + 何时用；Claude 据此自动加载 |
| 3 | `when_to_use` | 否 | string，项目 < 128 | 额外触发上下文（短语/示例），计入 1536 截断 |
| 4 | `argument-hint` | 否 | string，如 `[issue-number]` | `/` 自动完成时显示的参数提示 |
| 5 | `arguments` | 否 | 空格分隔 string 或 YAML list | 命名位置参数，映射到 `$name` 替换 |
| 6 | `disable-model-invocation` | 否 | bool，默认 false | `true` = 仅手动 `/name`，禁 Claude 自动触发，且不预加载进 subagent |
| 7 | `user-invocable` | 否 | bool，默认 true | `false` = 从 `/` 菜单隐藏（仅 Claude 调用的背景知识） |
| 8 | `allowed-tools` | 否 | 空格分隔或 list | skill 活动时预授权工具（不限制可用工具池，仅免批准） |
| 9 | `disallowed-tools` | 否 | 空格分隔或 list | skill 活动时从工具池移除（下条消息清除） |
| 10 | `model` | 否 | 与 `/model` 同值或 `inherit` | 覆盖当轮模型，不持久 |
| 11 | `effort` | 否 | `low`/`medium`/`high`/`xhigh`/`max` | 覆盖工作量级别 |
| 12 | `context` | 否 | `fork` | 在分叉 subagent 上下文运行（skill 内容成为 subagent prompt） |
| 13 | `agent` | 否 | `Explore`/`Plan`/`general-purpose`/自定义 | 配 `context: fork` 时的 subagent 类型 |
| 14 | `hooks` | 否 | hook 配置 | 限定 skill 生命周期的 hooks |
| 15 | `paths` | 否 | glob，逗号分隔或 list | 限制仅处理匹配文件时自动加载（monorepo 按包触发） |
| 16 | `shell` | 否 | `bash`（默认）/ `powershell` | `` !`cmd` `` 与 ``` ```! ``` 块的 shell |

## 调用控制矩阵（字段 6/7 组合）

| Frontmatter | 用户可调 | Claude 可调 | 何时加载到 context |
|-------------|---------|------------|------------------|
| （默认） | 是 | 是 | 描述常驻，调用时加载完整 skill |
| `disable-model-invocation: true` | 是 | 否 | 描述不在 context，用户调用时加载 |
| `user-invocable: false` | 否 | 是 | 描述常驻，调用时加载 |

## context: fork 语义

| 方法 | system prompt | 任务 | 额外加载 |
|------|--------------|------|---------|
| skill 带 `context: fork` | 来自 agent 类型 | SKILL.md 内容 | CLAUDE.md（Explore/Plan 除外） |
| subagent 带 `skills` 字段 | subagent 正文 | Claude 委派消息 | 预加载 skills + CLAUDE.md |

> `context: fork` 仅对**有明确任务**的 skill 有意义；纯参考指南（无任务）fork 后 subagent 收到指南但无可执行 prompt，会空返。

## 字符串替换变量（skill 正文内可用）

| 变量 | 含义 |
|------|------|
| `$ARGUMENTS` | 调用时传的全部参数；正文无此占位符则追加 `ARGUMENTS: <value>` |
| `$ARGUMENTS[N]` / `$N` | 0 基索引参数，`$0` = 第一个 |
| `$name` | `arguments` frontmatter 声明的命名参数，按位置映射 |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |
| `${CLAUDE_EFFORT}` | 当前工作量级别（`xhigh` 含 Ultracode） |
| `${CLAUDE_SKILL_DIR}` | 含 SKILL.md 的目录（插件 skill 指子目录非插件根） |

> 字面 `$` 在数字/`ARGUMENTS`/命名参数前需转义：`\$1.00`。

## 常见错误（P0）

| 错误 | 后果 | 正例 |
|------|------|------|
| description 写第一/第二人称（「I can」「You can use」） | 可发现性下降 | 第三人称 |
| description key use case 后置 | 长列表截断丢关键词 | key use case 前置 |
| description 太泛（「Helps with code」） | 误触发（false positive） | 收窄「何时用」边界 |
| YAML tab/空格混用或引号未闭合 | 元数据空，`/name` 仍可用但 Claude 无 description 匹配 | `claude --debug` 查 parse 错误 |
| 把 `disable-model-invocation` 当「隐藏」用 | 仅禁 Claude 触发，仍出现在 `/` 菜单 | 隐藏用 `user-invocable: false` |
| `allowed-tools` 误以为限制工具池 | 仅免批准，不限制可用 | 限制用 `disallowed-tools` 或 permissions deny |
| description 超 512 / when_to_use 超 128 | 违反项目底线 | 压缩或拆 when_to_use |

## 命令名来源（≠ name 字段）

| skill 位置 | `/` 后命令名 |
|-----------|------------|
| `~/.claude/skills/` 或项目 `.claude/skills/` 下目录 | 目录名 |
| 嵌套 `.claude/skills/` 重名时 | `<子目录路径>:<目录名>`，如 `apps/web:deploy` |
| `.claude/commands/` 下文件 | 文件名（无扩展名） |
| 插件 `skills/` 子目录 | `<plugin>:<目录名>` |
| 插件根 SKILL.md | frontmatter `name`（唯一 name 决定命令名的地方） |

## 参考链接

- frontmatter 参考：[code.claude.com/docs/zh-CN/skills#frontmatter-参考](https://code.claude.com/docs/zh-CN/skills#frontmatter-参考)
- best-practices（description 1024 出处）：[platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- skill-creator eval：[agentskills.io](https://agentskills.io)
