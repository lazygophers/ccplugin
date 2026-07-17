# Marketplace 与发布

> marketplace.json 完整 schema + source 5 类型 + 发布流程。主 SKILL.md 流程 A 步骤 6 + 流程 B 维度 6 的细节层。

## marketplace.json 位置

仓库根 `.claude-plugin/marketplace.json`（与各插件目录同级，非插件内部）。

## 顶层 schema

```jsonc
{
  "$schema": "https://...",               // 可选：编辑器自动补全，加载时忽略
  "name": "ccplugin-market",              // 必需：kebab-case，public-facing（用户装时 @<name>）
  "owner": {                              // 必需
    "name": "DevTools Team",              // 必需
    "email": "devtools@example.com"       // 可选
  },
  "description": "...",                   // 可选
  "version": "...",                       // 可选：marketplace manifest 版本
  "metadata": {
    "pluginRoot": "./plugins"             // 可选：相对 source 前缀基目录（省则每个 source 写全）
  },
  "allowCrossMarketplaceDependenciesOn": [], // 可选：允许依赖的其他 marketplace
  "renames": { "old-name": "new-name" }, // 可选（v2.1.193+）：改名/删除自动迁移
  "plugins": [ /* 见下 */ ]
}
```

### 顶层必填

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | kebab-case；每个用户同名只能注册一个，后加覆盖前 |
| `owner` | object | `{name 必填, email 可选}` |

## plugin 条目 schema

每个 `plugins[]` 条目可含 plugin.json 的任何字段 + marketplace 专属字段：

```jsonc
{
  "name": "my-plugin",                  // 必需：kebab-case，= 目录名 = plugin.json name
  "source": "./plugins/tools/my-plugin", // 必需：string | object（见 source 5 类型）
  "displayName": "My Plugin",           // 可选（v2.1.143+）：UI 显示名，可含空格
  "description": "...",                 // 可选
  "version": "1.0.0",                   // 可选：设了则 pin，省略走 commit SHA
  "author": { "name": "...", "email": "..." },
  "homepage": "...",
  "repository": "...",
  "license": "MIT",                     // SPDX 标识符
  "keywords": ["..."],
  "category": "...",                    // 可选：分类
  "tags": ["..."],                      // 可选：搜索标签
  "strict": true,                       // 可选（默认 true）：plugin.json 是否为组件定义权威
  "defaultEnabled": true,               // 可选（v2.1.154+）：装后是否默认启用
  "relevance": { /* v2.1.152+ */ },     // 可选：管理员 allowlist 时建议插件的信号
  // 组件配置（覆盖/补充 plugin.json）
  "skills": ["./skills/x"],
  "commands": ["./commands/y.md"],
  "agents": ["./agents/z.md"],
  "hooks": { /* */ },
  "mcpServers": { /* */ },
  "lspServers": { /* */ }
}
```

### 条目必填

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | kebab-case；用户装时 `/plugin install my-plugin@market` |
| `source` | string\|object | 哪里取插件 |

## source 5 类型

| source | 形态 | 字段 | 说明 |
|--------|------|------|------|
| **Relative path** | `string` `"./my-plugin"` | 无 | 同仓库本地目录，必须 `./` 开头，相对 marketplace 根解析 |
| **github** | `object` | `repo` `ref?` `sha?` | GitHub 仓库 |
| **url** | `object` | `url` `ref?` `sha?` | 任意 git URL（GitLab/Bitbucket 等）|
| **git-subdir** | `object` | `url` `path` `ref?` `sha?` | git 仓库子目录（sparse clone，省带宽，monorepo 用）|
| **npm** | `object` | `package` `version?` `registry?` | `npm install` |

### ref vs sha

- `ref` = 分支/tag（marketplace source 与 plugin source 都支持）
- `sha` = 完整 40 字符 commit（**仅 plugin source** 支持；marketplace source 不支持）
- 两者都设 → **sha 为准**（直接 checkout 该 commit，ref 删了也能装，除 AWS CodeCommit 外）

### 各类型示例

```jsonc
// Relative（本仓库主用）
{ "name": "skein", "source": "./plugins/tools/skein" }

// GitHub + pin
{ "name": "x", "source": { "source": "github", "repo": "owner/repo", "ref": "v2.0.0", "sha": "a1b2...e7f8" } }

// Git URL
{ "name": "x", "source": { "source": "url", "url": "https://gitlab.com/team/plugin.git" } }

// git-subdir（monorepo）
{ "name": "x", "source": { "source": "git-subdir", "url": "https://github.com/owner/mono.git", "path": "plugins/x" } }

// npm
{ "name": "x", "source": { "source": "npm", "package": "@scope/pkg", "version": "1.0.0" } }
```

### ⚠️ Relative path 限制

- 相对 marketplace 根（含 `.claude-plugin/` 的目录），**禁 `../`** 引外部
- 用户从 **git source / 本地目录** 加 marketplace 时 relative 生效
- 用户从 **直接 URL** 加 `marketplace.json` 时 relative **失效**（只下了那一个文件）→ URL 分发用 github/url/npm source

## version 解析

- 条目 `version` 或 `plugin.json` `version` 任一设置 → pin 该字符串，bump 才更新
- 都省略 + git 分发 → commit SHA 充当版本，每次 commit = 新版本
- 本仓库多数插件省略（快速迭代，走 SHA）

## strict mode

`strict: true`（默认）= `plugin.json` 是组件定义权威。marketplace 条目里的 `skills`/`agents`/`commands` 等字段在 strict 下作为补充/覆盖。

## CLI 命令族

```bash
# 开发测试
claude --plugin-dir ./my-plugin           # 加载本地插件（开发用，非安装）
claude --plugin-dir ./my-plugin.zip       # v2.1.128+，加载 zip
claude --plugin-url https://.../x.zip     # 加载远程 zip（CI 产物）
/reload-plugins                           # 重载（改后生效，免重启）

# 脚手架
claude plugin init my-tool                # 在 ~/.claude/skills/ 建插件，自动加载

# 校验
claude plugin validate                    # 提交前必跑（官方审查 pipeline 跑同一检查）

# marketplace
/plugin marketplace add ./my-marketplace  # 加本地 marketplace
/plugin marketplace add owner/repo        # 加 git marketplace
/plugin marketplace update                # 刷新本地副本
/plugin install my-plugin@market-name     # 装插件

# 社区提交
# claude.ai:    claude.ai/admin-settings/directory/submissions/plugins/new (Team/Enterprise)
# Console:      platform.claude.com/plugins/submit (个人作者)
```

## 官方两市场

| 市场 | 性质 | 加入方式 |
|------|------|---------|
| `claude-plugins-official` | Anthropic 策展（精选）| Anthropic 自行决定，无申请流程；首次交互启动自动注册 |
| `claude-community` | 社区提交审查后收录 | `/plugin marketplace add anthropics/claude-plugins-community`；经审查 pinned 到 commit SHA，CI 自动 bump |

- 社区提交：走 in-app 表单（claude.ai 需 Team/Enterprise + 目录管理权；个人用 Console）
- 审查跑 `claude plugin validate` + 自动安全筛查
- approved 后 pinned 到具体 commit SHA，nightly sync 到公开 catalog

## 私有 marketplace（团队内部）

- host 在私有 git 仓库，用户 `/plugin marketplace add` 加（需 repo 访问权）
- 细节见官方 plugin-marketplaces Private repositories 段

## 发布前 checklist

- [ ] `claude plugin validate` 过
- [ ] `marketplace.json` 条目 `name`/`source`/`description`/`author`/`license`/`keywords` 与 `plugin.json` 一致
- [ ] `source` 路径存在（relative）/ `repo` 拼写对（github）
- [ ] README 有装/用/例
- [ ] version 策略定（省略走 SHA / 设 semver + tag）
- [ ] **禁 push**（等明确指令）
