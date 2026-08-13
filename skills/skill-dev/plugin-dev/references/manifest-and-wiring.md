# Manifest 与组件接线

> plugin.json 全字段 + 组件目录完整清单 + 接线双向核对 + namespace 机制 + 路径规则 + 作用域。主 SKILL.md 流程 A 步骤 3-4 的细节层。

## 目录结构（官方规范 + 本仓库约定）

```
<plugin-name>/                 # 插件根（= 目录名 = manifest name）
├── .claude-plugin/
│   └── plugin.json            # 可选：清单（此目录只放这一个文件）
├── skills/                    # 可选：skill 目录 <name>/SKILL.md
├── commands/                  # 可选：扁平 .md 命令文件
├── agents/                    # 可选：agent 定义 *.md
├── hooks/
│   └── hooks.json             # 可选：事件处理器
├── scripts/                   # 可选：可执行脚本
├── bin/                       # 可选：插件启用时加入 Bash PATH 的可执行文件
├── monitors/
│   └── monitors.json          # 可选：后台监控（experimental，见 advanced-components.md）
├── themes/                    # 可选：颜色主题（experimental）
├── output-styles/             # 可选：输出样式
├── .mcp.json                  # 可选：MCP server 配置
├── .lsp.json                  # 可选：LSP 语言服务器配置
├── settings.json              # 可选：插件启用时的默认 settings（见 advanced-components.md）
├── requirements.txt / pyproject.toml  # 可选：Python 依赖
├── README.md                  # 推荐
└── LICENSE                    # 推荐
```

### 🔴 结构硬规

- **组件目录在插件根，禁进 `.claude-plugin/`** — `.claude-plugin/` **只放 `plugin.json`**。`commands/ agents/ skills/ hooks/ scripts/` 放进去 = 不加载。插件根 = 含 `.claude-plugin/plugin.json` 的那个目录，**绝不是 `~/.claude/`**（`~/.claude/.mcp.json` 不被读取）。
- **`SKILL.md` 文件名大写** — 小写 `skill.md` 不识别。
- **manifest 可选** — 无 `plugin.json` 时 Claude Code 自动发现默认位置的组件，name 从目录名推导。需要元数据或自定义路径才写 manifest。
- **单 skill 插件可省 `skills/`** — 只有一个 skill 时，`SKILL.md` 直接放插件根（v2.1.142+ 自动当单 skill 插件加载），用 frontmatter `name` 做调用名。多 skill 必须 `skills/<name>/SKILL.md`。
- **新插件优先 `skills/` 而非 `commands/`** — 官方建议；`commands/` 是扁平 `.md`（旧式），`skills/` 是目录式（支持 `references/` `scripts/` 伴随文件）。

## plugin.json 完整 schema

```jsonc
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "deployment-tools",           // 必填 kebab-case，= namespace 前缀
  "displayName": "Deployment Tools",    // 可选 min-v2.1.143：UI 显示名（可含空格/任意大小写）
  "version": "1.2.0",                   // 可选 semver；省略则 git commit SHA 充当版本
  "description": "做什么 + 差异化",
  "author": { "name": "...", "email": "...", "url": "..." },
  "homepage": "...", "repository": "...",
  "license": "MIT",                     // SPDX 标识符
  "keywords": ["deployment", "ci-cd"],
  "defaultEnabled": false,              // 可选 min-v2.1.154：默认装即禁用

  // 组件路径
  "skills":   "./custom/skills/",       // 添加到默认 skills/（见路径规则）
  "commands": ["./commands/c.md"],      // 替换默认 commands/
  "agents":   ["./agents/a.md"],        // 替换默认 agents/
  "hooks":    "./config/hooks.json",    // 自有 merge 规则
  "mcpServers": "./mcp-config.json",    // 自有 merge 规则
  "lspServers": "./.lsp.json",          // 自有 merge 规则
  "outputStyles": "./styles/",          // 替换默认 output-styles/

  // experimental（声明在 experimental. 下，顶层仍可但 validate 警告）
  "experimental": {
    "themes":   "./themes/",            // 替换默认 themes/
    "monitors": "./monitors.json"       // 替换默认 monitors/
  },

  "userConfig": { /* 见 advanced-components.md */ },
  "channels":  [ /* 见 advanced-components.md */ ],
  "dependencies": [ "helper-lib", { "name": "secrets-vault", "version": "~2.1.0" } ]
}
```

### 元数据字段速查

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `name` | ✅ | string | kebab-case `^[a-z0-9-]+$`，namespace 前缀（`/my-plugin:skill`）|
| `$schema` | — | string | JSON Schema URL（编辑器自动补/校验，加载时忽略）|
| `displayName` | — | string | `{min-v2.1.143}` UI 显示名，可含空格/任意大小写；fallback 到 `name` |
| `description` | 推荐 | string | 一句话：做什么 + 差异化 |
| `version` | — | string | semver；省略则 commit SHA。`plugin.json` 版本**高于** marketplace 条目同名 |
| `author` | 推荐 | object | `{name, email?, url?}` |
| `homepage`/`repository` | 推荐 | string | 文档/源码 URL |
| `license` | 推荐 | string | SPDX 标识符 |
| `keywords` | — | string[] | 发现/分类标签 |
| `defaultEnabled` | — | boolean | `{min-v2.1.154}` 默认 `true`。设 `false` = 装即禁用（外部服务/加成本插件用）|

### 🔴 路径行为规则（替换 vs 添加）

| 规则 | 字段 |
|------|------|
| **替换默认目录**（指定后默认目录不再扫）| `commands` `agents` `outputStyles` `experimental.themes` `experimental.monitors` |
| **添加到默认目录**（默认目录照扫 + 额外加载）| `skills`（例外：marketplace 根的 source 指定子目录时替换）|
| **自有 merge 规则** | `hooks` `mcpServers` `lspServers`（见各组件段）|

- 想保留默认 + 加更多（替换型字段）→ 显式列：`"commands": ["./commands/", "./extras/"]`
- v2.1.140+ 若同时有默认目录和 manifest key，`plugin list` 和 `/plugin` 详情会警告忽略的目录
- 所有路径 **相对插件根 + 以 `./` 开头**
- manifest key 指进默认目录内（如 `"commands": ["./commands/deploy.md"]`）不警告

### 未识别字段（兼容多生态）

- Claude Code **忽略**顶层未识别字段（可留 VS Code/Cursor/npm/MCPB manifest 元数据，插件照载）
- `claude plugin validate` 把未识别字段报**警告**（非错）；差一两个字符的会提示可能的意图字段
- 仅未识别字段警告的插件**仍通过校验并加载**
- 类型错（如 `keywords` 写成 string）= 加载错误
- **CI 加 `--strict`** 把警告当错，发布前抓拼写错误：
  ```bash
  claude plugin validate ./my-plugin --strict
  ```

## namespace 机制（防冲突）

插件 skill 调用名带插件名前缀：`/<plugin-name>:<skill-name>`。

- 插件 `my-plugin` 的 `hello` skill → 调用 `/my-plugin:hello`
- 单 skill 插件（SKILL.md 在根）→ 用 frontmatter `name` 做调用名，仍带前缀
- 想改前缀 → 改 `plugin.json` 的 `name`
- **`.claude/` 独立配置覆盖插件 agent**（同名）；skill 则共存（namespace 隔离，`/skill` 和 `/plugin:skill` 都可用）
- marketplace 条目可列不同 name → `enabledPlugins` key 和 `/plugin` 用 marketplace 条目 name

## 接线双向核对（硬规 3）

manifest 的 `skills[]/agents[]/commands[]` 每条路径都要有真实文件；反过来每个组件文件都要被挂载。

- **漏挂**（文件存在但 manifest 没列）= 组件不加载，无报错（最阴险）
- **悬挂**（manifest 列了但文件不存在）= 启动报错
- **大小写敏感** — macOS 不敏感会掩盖错误，Linux 报错；统一小写目录 + 大写 `SKILL.md`

机械检查见 `optimize-rubric.md` 体检命令。

## 组件 frontmatter 速查

| 组件 | 文件 | 必填 frontmatter | 常用可选 |
|------|------|-----------------|---------|
| command | `commands/*.md` | `description` | `argument-hint` `allowed-tools` `model` |
| agent | `agents/*.md` | `name` `description` | `tools` `disallowedTools` `model` `effort` `maxTurns` `skills` `memory` `background` `isolation:"worktree"`（🛓 插件 agent **不支持** `hooks`/`mcpServers`/`permissionMode`）|
| skill | `skills/<n>/SKILL.md` | `description` | `disable-model-invocation` `allowed-tools` `paths` |

- command 正文用 `$ARGUMENTS`（全参）/ `$1` `$2`（位置）
- 单组件（skill/agent/command）的深度编写与 9 维质量评分路由 `/skill-dev`，本 skill 只保证接线正确

## version 语义

- **设了 `version`** — 用户只在 bump 该字段时收到更新（适合稳定发布）
- **省略 `version`**（本仓库多数插件如此）+ git 分发 — commit SHA 充当版本，每次 commit = 新版本（适合快速迭代）
- marketplace 条目 `version` 与 `plugin.json` 一致；**`plugin.json` 版本优先**（两边都设时 plugin.json wins）

## ${CLAUDE_PLUGIN_DATA} 持久化目录

- 解析为 `~/.claude/plugins/data/{id}/`，`{id}` = 插件标识（非 `[a-zA-Z0-9_-]` 字符替换为 `-`）。如 `formatter@my-marketplace` → `formatter-my-marketplace`
- **首次引用时创建**，**跨插件更新存活**（插件更新后旧目录约 7 天清理，但插件根视为 ephemeral 别写状态）
- 典型用途：装一次语言依赖（`node_modules` / Python venv），跨 session 和更新复用
- 🔴 **检测依赖更新**：只检查目录存在**不够**（目录跨更新存活，检测不到依赖 manifest 变化）。推荐范式：对比 bundled manifest 和 data 目录里的副本，不同则重装（SessionStart hook 范式见 advanced-components.md LSP 段）
- 更新中会话：hook / monitor / MCP / LSP 仍用旧路径；`/reload-plugins` 切 hook/MCP/LSP 到新路径，**monitor 需重启 session**

## plugin 缓存隔离（禁跨目录引用）

安装时 Claude Code 把插件目录复制到 `~/.claude/plugins/cache`。

- **禁** `../shared-utils` 引用插件外的文件（不会被复制）
- 需跨插件共享 → 用 **symlink**，或走 git submodule / npm 依赖（version 插件用 `[tool.uv.sources.lib]` 引本仓库 `lib/` 子目录，见 `multi-language.md`）
- skills-directory 插件（见下）不走 cache，原地发现

## 🔴 安装作用域（4 类）

安装插件时选 scope 决定在哪可用 + 谁能用：

| Scope | settings 文件 | 用途 |
|-------|--------------|------|
| `user` | `~/.claude/settings.json` | 个人插件，跨所有项目（默认）|
| `project` | `.claude/settings.json` | 团队插件，经版本控制共享 |
| `local` | `.claude/settings.local.json` | 项目特定，gitignored |
| `managed` | managed settings | 托管插件（只读，只能 update）|

插件用与 Claude Code 其他配置相同的 scope 系统。

## skills-directory 插件（@skills-dir）

skills 目录下含 `.claude-plugin/plugin.json` 的文件夹 = 加载为插件 `<name>@skills-dir`，无 marketplace 无安装步骤。用 `plugin init` 脚手架。

| 你有什么 | 它是什么 |
|---------|---------|
| `<skills-dir>/foo/SKILL.md`（无 manifest）| 普通 skill `foo` |
| `<skills-dir>/foo/.claude-plugin/plugin.json` | 插件 `foo@skills-dir`（可 bundle 自己的 skills/agents/hooks 等）|
| `<plugin>/skills/bar/SKILL.md` | 插件内 skill `bar` |

| skills 目录 | Scope | 加载情况 |
|------------|-------|---------|
| `~/.claude/skills/` | personal | 每个项目都加载 |
| `<cwd>/.claude/skills/` | project | 仅接受该文件夹 workspace trust 后加载 |

🔴 project-scope `@skills-dir` 限制：
- 从仓库根 `<cwd>/.claude/skills/` 加载，**不向上走到仓库根**（子目录启动会漏掉仓库根的插件）→ 从仓库根启动或 `/reload-plugins`
- MCP server 走项目 `.mcp.json` 同级 server 审批
- LSP server 仅信任 workspace 后启动
- **background monitors 不加载**

编辑/重载/禁用：
- skill 的 `SKILL.md` 改动**当前 session 立即生效**；hooks / `.mcp.json` / agents / output-styles 改动需 `/reload-plugins` 或重启
- 停止加载：删文件夹或 `claude plugin disable my-tool@skills-dir`（无 uninstall 步骤）

## 参考实例

| 插件 | 看什么 |
|------|--------|
| skein | 大型 manifest（9 skill + 5 agent + hooks + userConfig）|
| cortex | `agents[]`/`skills[]` 逐条挂 + SessionStart/UserPromptSubmit async hook |
| version / notify | pyproject.toml + uvx 分发 + `.lazygophers/` 元数据 |
| deepresearch / novelist | 中型：agents + skills 组合 |
