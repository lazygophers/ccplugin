# Manifest 与组件接线

> plugin.json 全字段 + 组件目录完整清单 + 接线双向核对 + namespace 机制。主 SKILL.md 流程 A 步骤 3-4 的细节层。

## 目录结构（官方规范 + 本仓库约定）

```
<plugin-name>/                 # 插件根（= 目录名 = manifest name）
├── .claude-plugin/
│   └── plugin.json            # 必需：清单（此目录只放这一个文件）
├── skills/                    # 可选：skill 目录 <name>/SKILL.md
├── commands/                  # 可选：扁平 .md 命令文件
├── agents/                    # 可选：agent 定义 *.md
├── hooks/
│   └── hooks.json             # 可选：事件处理器
├── scripts/                   # 可选：可执行脚本
├── bin/                       # 可选：插件启用时加入 Bash PATH 的可执行文件
├── monitors/
│   └── monitors.json          # 可选：后台监控（见 advanced-components.md）
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
- **单 skill 插件可省 `skills/`** — 只有一个 skill 时，`SKILL.md` 直接放插件根，用 frontmatter `name` 做调用名。多 skill 必须 `skills/<name>/SKILL.md`。
- **新插件优先 `skills/` 而非 `commands/`** — 官方建议；`commands/` 是扁平 `.md`（旧式），`skills/` 是目录式（支持 `references/` `scripts/` 伴随文件）。

## plugin.json 字段全表

```jsonc
{
  // 必需
  "name": "my-plugin",                 // kebab-case ^[a-z0-9-]+$，= 目录名 = marketplace name

  // 推荐元数据
  "description": "做什么 + 差异化核心",   // 出现在插件管理器
  "version": "1.0.0",                  // 可选；省略则 git commit SHA 充当版本（每次 commit = 新版本）
  "author": { "name": "...", "email": "...", "url": "..." },
  "homepage": "https://github.com/owner/repo/tree/master/plugins/tools/my-plugin",
  "repository": "https://github.com/owner/repo/tree/master/plugins/tools/my-plugin",
  "license": "AGPL-3.0-or-later",      // SPDX 标识符
  "keywords": ["tag1", "tag2"],

  // 组件路径（字符串=整目录，数组=逐条）
  "skills":   ["./skills/foo", "./skills/bar"],   // 或 "./skills/" 挂整目录
  "agents":   ["./agents/a.md"],
  "commands": ["./commands/c.md"],                // 或 "./commands/"
  "hooks":    { /* 内联 hook 配置，见 hooks.md */ },  // 或 "./hooks/hooks.json"
  "mcpServers": { /* 见 advanced-components.md */ },
  "lspServers": { /* 见 advanced-components.md */ },
  "outputStyles": ["./themes/x.json"],            // 可选：自定义输出样式

  // 用户配置（见 advanced-components.md）
  "userConfig": { /* 暴露给用户的配置项 schema */ }
}
```

### 字段速查

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `name` | ✅ | string | kebab-case，命名空间前缀（`/my-plugin:skill`） |
| `description` | 推荐 | string | 一句话：做什么 + 差异化 |
| `version` | 可选 | string | 省略则用 commit SHA |
| `author` | 推荐 | object | `{name, email?, url?}` |
| `homepage`/`repository` | 推荐 | string | 文档/源码 URL |
| `license` | 推荐 | string | SPDX 标识符 |
| `keywords` | 可选 | string[] | 发现/分类标签 |
| `skills`/`agents`/`commands` | 按需 | string\|string[] | 组件路径 |
| `hooks` | 按需 | object\|string | hook 配置或路径 |
| `mcpServers`/`lspServers` | 按需 | object\|string | server 配置或路径 |
| `outputStyles` | 可选 | string\|string[] | 输出样式 |
| `userConfig` | 可选 | object | 用户配置 schema |

## namespace 机制（防冲突）

插件 skill 调用名带插件名前缀：`/<plugin-name>:<skill-name>`。

- 插件 `my-plugin` 的 `hello` skill → 调用 `/my-plugin:hello`
- 单 skill 插件（SKILL.md 在根）→ 用 frontmatter `name` 做调用名，仍带前缀
- 想改前缀 → 改 `plugin.json` 的 `name`
- **`.claude/` 独立配置覆盖插件 agent**（同名）；skill 则共存（namespace 隔离，`/skill` 和 `/plugin:skill` 都可用）

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
| agent | `agents/*.md` | `name` `description` | `tools` `model` `skills` |
| skill | `skills/<n>/SKILL.md` | `description` | `disable-model-invocation` `allowed-tools` `paths` |

- command 正文用 `$ARGUMENTS`（全参）/ `$1` `$2`（位置）
- 单组件（skill/agent/command）的深度编写与 9 维质量评分路由 `/skill-dev`，本 skill 只保证接线正确

## version 语义

- **设了 `version`** — 用户只在 bump 该字段时收到更新（适合稳定发布）
- **省略 `version`**（本仓库多数插件如此）+ git 分发 — commit SHA 充当版本，每次 commit = 新版本（适合快速迭代）
- marketplace 条目 `version` 与 `plugin.json` 一致；两边都省略则都走 SHA

## plugin 缓存隔离（禁跨目录引用）

安装时 Claude Code 把插件目录复制到 `~/.claude/plugins/cache`。

- **禁** `../shared-utils` 引用插件外的文件（不会被复制）
- 需跨插件共享 → 用 **symlink**，或走 git submodule / npm 依赖（version 插件用 `[tool.uv.sources.lib]` 引本仓库 `lib/` 子目录，见 `multi-language.md`）

## 参考实例

| 插件 | 看什么 |
|------|--------|
| skein | 大型 manifest（9 skill + 5 agent + hooks + userConfig）|
| cortex | `agents[]`/`skills[]` 逐条挂 + SessionStart/UserPromptSubmit async hook |
| version / notify | pyproject.toml + uvx 分发 + `.lazygophers/` 元数据 |
| deepresearch / novelist | 中型：agents + skills 组合 |
