# 调试与故障排除

> 插件装不上 / 不加载 / 组件不生效 / hook 不触发 / MCP/LSP 不起的排查层。主 SKILL.md 失败模式速查 + hooks.md/advanced-components.md 的细节补充。

## 两个核心调试工具

### `claude --debug`（看加载实况）

显示：哪些插件被加载 / manifest 错误 / skill-agent-hook 注册 / MCP server 初始化 / LSP server 跳过原因（含 v2.1.205 前 restartOnCrash/shutdownTimeout 静默跳过）/ hook 触发与 stderr。

```bash
claude --debug                    # 启动 session 并打 plugin 细节
claude --debug 2>&1 | grep -i plugin   # 过滤 plugin 相关
```

### `claude plugin validate` / `/plugin validate`

校验：`plugin.json` + skill/agent/command frontmatter + `hooks/hooks.json` 的语法和 schema 错误。

```bash
claude plugin validate ./my-plugin          # 基础（未识别字段只警告）
claude plugin validate ./my-plugin --strict # CI：警告当错（抓拼写/残留字段）
```

## `claude plugin` CLI 全集（开发/发布常用）

| 命令 | 作用 | 关键选项 |
|------|------|---------|
| `init <name>` | 脚手架到 `~/.claude/skills/<name>/`（加载为 `<name>@skills-dir`）| `--with skills,hooks,mcp,lsp,...` `--force` |
| `install <plugin@market>` | 从 marketplace 装 | `-s user\|project\|local` `--config k=v` |
| `uninstall <plugin>` | 移除（默认删 `${CLAUDE_PLUGIN_DATA}`）| `--keep-data` `--prune` `-s` |
| `prune` | 清理无人依赖的自动装的依赖（v2.1.121+）| `--dry-run` |
| `enable <plugin>` / `disable <plugin>` | 启用/禁用（有依赖时级联/连锁）| `-a --all`（disable）`-s` |
| `update <plugin>` | 更新到最新 | `-s user\|project\|local\|managed` |
| `list` | 列装了的（版本/源/启用状态）| `--json` `--available` |
| `details <name>` | **组件清单 + 投影 token 成本**（always-on / on-invoke）| — |
| `tag [path]` | 为插件打 release git tag（版本解析用）| `--push` `--dry-run` `-f` `-m "msg %s"` |
| `validate [path]` | manifest + frontmatter + hooks.json 校验 | `--strict` |

## 常见错误信息速查表

| 错误信息 | 原因 | 修复 |
|---------|------|------|
| `Invalid JSON syntax: Unexpected token } in JSON at position 142` | manifest 缺逗号/多逗号/字符串未引 | `jq .` 验 JSON |
| `Validation errors: name: ... expected string, received undefined` | 必填字段缺失 | 补 `name` 等 |
| `JSON parse error: ...` | manifest JSON 语法错 | `jq .` 逐行定位 |
| `No commands found in plugin ... custom directory: ./cmds` | command 路径存在但无有效 `.md`/`SKILL.md` | 补文件或改路径 |
| `Plugin directory not found at path: ./plugins/my-plugin` | marketplace `source` 指向不存在的目录 | 修 marketplace source |
| `conflicting manifests: both plugin.json and marketplace entry specify components` | plugin.json 和 marketplace 条目都定义了组件 | 删一处重复 |
| LSP `Executable not found in $PATH` | language server 二进制未装 | 装（如 `npm i -g typescript-language-server typescript`）|
| `plugin-command-references-user-config` | hook shell-form / monitor command / MCP headersHelper 用了 `${user_config.*}` | 改 exec form / 从 config 文件读 / 读环境变量 |
| `/plugin` Errors 标签报错 | 同上各类加载错误 | 逐条按提示修 |

## 分场景排查

### 插件不加载

1. `claude plugin validate` / `/plugin validate` 查 manifest + frontmatter + hooks.json
2. `claude --debug` 看 "loading plugin" / 是否报 manifest 错
3. 组件目录在插件根**不在 `.claude-plugin/`**（最常见）
4. marketplace source relative 路径：用户从 URL 加 marketplace 时 relative 不解析 → 改 github/url/npm source

### 组件（skill/agent/command）不出现

1. 漏挂（文件在 manifest 没列）= 静默不加载，最阴险 → 用体检命令反查（optimize-rubric.md）
2. 大小写：`SKILL.md` 必须大写；目录名 kebab-case
3. 调用名带前缀：`/<plugin>:<skill>` 不是 `/<skill>`
4. 误放 `.claude-plugin/` 内 → 移到插件根
5. `/reload-plugins` 或重启 session 重载（SKILL.md 改动 session 内立即生效；hooks/MCP/agents 需 reload）

### hook 不触发

1. event 名大小写：`PostToolUse` 正确，`postToolUse`/`post_tool_use` 错
2. matcher 拼写 + 是否匹配工具：`"matcher": "Write|Edit"`
3. hook type 合法：`command` / `http` / `mcp_tool` / `prompt` / `agent`
4. 脚本可执行：`chmod +x`；shebang 正确（`#!/bin/bash` / `#!/usr/bin/env bash`）
5. command 路径用 `${CLAUDE_PLUGIN_ROOT}` 且**含空格加引号**：`"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"`
6. `mcp_tool` 调自带 server：server 用 scoped 名 `plugin:<plugin>:<server>`，matcher 用 `mcp__plugin_<plugin>_<server>__<tool>`——裸 server key 永不触发
7. 手动测脚本：`./scripts/your-script.sh`

### hook 阻断会话

1. 加 `timeout` + 改 `${CLAUDE_PLUGIN_ROOT}` + 失败 `exit 0` 兜底
2. guard 用 `exit 2`（阻断+stderr 回灌），**禁 `exit 1`**
3. stdin 非法 JSON 要静默 exit 0（禁崩会话）
4. 一线兜底：**先从 manifest 摘掉该 hook 恢复可用，再单独调**

### MCP server 不起 / 工具不出现

1. command 存在且可执行
2. 所有路径用 `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}`
3. `claude --debug` 看初始化错误
4. `.mcp.json` 或 `plugin.json` 的 `mcpServers` 配置正确
5. server 正确实现 MCP 协议
6. session 外手动测 server
7. debug 输出查连接超时

### LSP server 不起

1. `Executable not found in $PATH` → 用户机器装 language server 二进制
2. 必填 `command` + `extensionToLanguage`，缺则该 server 跳过（其他仍起）
3. 🔴 **v2.1.205 陷阱**：旧版本设了 `restartOnCrash` 或 `shutdownTimeout` → 该 server **静默被跳过**，只在 `--debug` 可见。要么升 v2.1.205+，要么先注释这两个字段
4. 同扩展名多 server → 第一个注册的处理，其余永不起；`/plugin` 警告并指出活跃插件
5. project-scope `@skills-dir` 插件的 LSP 仅信任 workspace 后起

### monitor 不起

1. 只在**交互式 CLI session** 跑（Monitor tool 不可用的 host 跳过）
2. project-scope `@skills-dir` 插件：**monitors 不加载**
3. `command` 拒绝 `${user_config.*}`，且不收 `CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量 → 从脚本拥有的 config 文件读
4. session 中途 disable 插件不停已跑 monitor（session 结束才停）；更新插件后 monitor 需**重启 session**（不像 hook/MCP/LSP 可 `/reload-plugins`）

## 版本解析（4 层，从上到下取第一个）

1. `plugin.json` 的 `version` 字段（**最高优先级**，plugin.json wins over marketplace）
2. marketplace 条目的 `version` 字段
3. git commit SHA（`github` / `url` / `git-subdir` / git-hosted marketplace 的 relative-path source）
4. `unknown`（`npm` source 或非 git 仓库的本地目录）

- **设了 `version`** → 必须 bump 才推更新给用户；只 push commit 不 bump = 用户收不到
- **省略 `version`** → commit SHA 充当版本，每 commit = 新版本（快速迭代用）
- 跟随 semver：MAJOR=breaking / MINOR=feature / PATCH=fix；维护 CHANGELOG.md

## 持久化数据目录（${CLAUDE_PLUGIN_DATA}）模式

- 路径：`~/.claude/plugins/data/{id}/`（`{id}` = 非 `[a-zA-Z0-9_-]` 字符替换为 `-`）
- 跨更新存活；插件根视为 ephemeral（更新后旧目录约 7 天清理）
- 卸载最后一个 scope 时自动删 data 目录，`/plugin` 显示大小并提示，CLI 默认删（`--keep-data` 保留）

### 装依赖并随更新重装（官方范式）

SessionStart hook 对比 bundled manifest 和 data 目录副本，不同则重装：

```jsonc
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\""
      }]
    }]
  }
}
```

- `diff` 非零（副本缺失或不同）= 首跑或依赖更新 → 重装
- `npm install` 失败 → trailing `rm` 删副本，下个 session 重试
- MCP server 脚本经 `NODE_PATH=${CLAUDE_PLUGIN_DATA}/node_modules` 跑持久化的依赖

## plugin 缓存 + symlink 规则（跨插件共享）

- marketplace 插件复制到 `~/.claude/plugins/cache`（非原地用）
- 每版本独立目录；update/uninstall 后旧版本标记 orphaned，7 天后自动删（让并发 session 继续跑旧版）
- Glob/Grep 跳过 orphaned 目录，搜结果不含过时代码
- 🔴 **禁 `../shared-utils` 跨出插件根**（不会被复制）

### symlink 分情况

| symlink 目标 | 缓存时行为 |
|-------------|----------|
| 插件自己目录内 | 保留为相对 symlink，运行时解析到复制后的目标 |
| 同 marketplace 内他处 | 解引用，目标内容复制进缓存（meta-plugin 的 `skills/` 链兄弟插件的 skill）|
| marketplace 外 | 跳过（安全，防拉任意 host 文件）|

- `--plugin-dir` / 本地路径装的插件：只有指向插件自己目录内的 symlink 保留，其余跳过
- Windows：`mklink /D`（elevated CMD 或 Developer Mode）

## 开发加载（非安装）

```bash
# 临时 session 加载（不写入 enabledPlugins）
claude --plugin-dir ./plugins/tools/<name>
claude --plugin-url <url>

# 进会话后
/reload-plugins          # 重载 hook/MCP/LSP/agent 改动（SKILL.md 改动 session 内立即生效；monitor 需重启）
```

- `--plugin-dir` 装的插件出现在 `/plugin` 界面；`claude plugin list` 仅当前缀同 flag 时才显示（`claude --plugin-dir <dir> plugin list`），无安装记录
