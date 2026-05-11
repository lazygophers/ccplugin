# Research: Yakitrak/obsidian-cli (现 notesmd-cli) 命令面

- **Query**: 调研 https://github.com/Yakitrak/obsidian-cli 命令面，替代 `mcp__obsidian__*`
- **Scope**: external (GitHub repo: Yakitrak/obsidian-cli, 默认分支 main, Go 实现)
- **Date**: 2026-05-11
- **重要前置**: 项目已重命名为 **notesmd-cli**（避让官方 Obsidian CLI），二进制名变为 `notesmd-cli`。旧的 `obsidian-cli` v0.2.3 用户需迁移（见 repo `MIGRATION.md`）。

## 1. 安装方式

| 平台 | 包管理器 | 命令 |
|---|---|---|
| macOS / Linux | Homebrew | `brew tap yakitrak/yakitrak && brew install yakitrak/yakitrak/notesmd-cli` |
| Windows | Scoop | `scoop bucket add scoop-yakitrak https://github.com/yakitrak/scoop-yakitrak.git && scoop install notesmd-cli` |
| Arch | AUR | `yay -S notesmd-cli-bin`（二进制）/ `yay -S notesmd-cli`（源码） |
| 源码 | Go ≥ 1.19 | `git clone … && go build -o notesmd-cli . && sudo install -m 755 notesmd-cli /usr/local/bin/` |

- **非 Node.js 项目**：用 Go 写的单文件二进制，**不需要 Node.js / npm**。无 npm 包。
- 二进制名：`notesmd-cli`（不是 `obsidian-cli`）。

## 2. 依赖的 Obsidian 插件

**无需任何 Obsidian 插件**，也**无需 Obsidian 在运行**。这是关键差异点：

- 直接读写 vault 目录下的 markdown 文件（`create` / `daily` / `print` / `frontmatter` / `delete` / `move` / `list` / `search-content`）。
- `open` 命令通过 Obsidian URI scheme 唤起 GUI；如不需要 GUI，用 `--editor` 走 `$EDITOR`。
- 不依赖 Advanced URI 插件，不依赖 Local REST API 插件。

## 3. 命令清单

| 命令 (别名) | 用途 | 对应 mcp__obsidian__ 工具 |
|---|---|---|
| `add-vault` (`av`) | 注册 vault 到 `~/.config/obsidian/obsidian.json` | — (MCP 无对应) |
| `remove-vault` (`rv`) | 注销 vault（不删文件） | — |
| `list-vaults` (`lv`) | 列出所有 vault，支持 `--json` / `--path-only` / `--default` | — |
| `set-default-vault` | 设默认 vault 和 `--open-type` (`obsidian`/`editor`) | — |
| `open` | 在 Obsidian/editor 打开 note，`--section` 跳标题 | — (GUI 操作) |
| `daily` | 创建/打开 today 日记，读 `.obsidian/daily-notes.json`；`--content` 追加 | append_content (日记场景) |
| `search` | 交互式 fuzzy 文件名 search | list_files / search |
| `search-content` | 全文搜索；`--no-interactive` / `--format json` / `--page` / `--page-size` | search |
| `list` | 列 vault 路径下文件夹/文件 | list_files_in_dir / list_files_in_vault |
| `print` | stdout 输出 note 内容 | get_file_contents |
| `create` | 创建 note，`--content` / `--overwrite` / `--append` / `--open` | put_content / patch_content / append_content |
| `move` | 移动/重命名 note，**自动更新所有 wikilink** | rename / move (无原生 MCP 等价) |
| `delete` | 删除 note | delete_file |
| `frontmatter` (`fm`) | YAML frontmatter 读写：`--print` / `--edit --key K --value V` / `--delete --key K` | get_frontmatter / patch_frontmatter |

来源（`cmd/` 目录）：`add_vault.go create.go daily.go delete.go frontmatter.go list.go list_vaults.go move.go open.go print.go remove_vault.go search.go search_content.go set_default.go`。

### 代码示例

```bash
# 读取
notesmd-cli print "Notes/Idea.md" --vault "brain"
notesmd-cli frontmatter "Notes/Idea.md" --print --vault "brain"

# 写入
notesmd-cli create "Notes/Idea.md" --content "$(cat body.md)" --overwrite
notesmd-cli create "Notes/Idea.md" --content "新增段落" --append
notesmd-cli frontmatter "Notes/Idea.md" --edit --key "status" --value "done"

# 搜索（脚本友好）
notesmd-cli search-content "TODO" --format json --page 1 --page-size 50
notesmd-cli list "001 Notes" --vault "brain"
notesmd-cli list-vaults --json

# 移动 / 删除（move 会更新 wikilink）
notesmd-cli move "old/path.md" "new/path.md"
notesmd-cli delete "trash/note.md"

# 日记
notesmd-cli daily --content "12:30 lunch" --vault "brain"
```

## 4. Vault 定位机制

- **配置文件**：`~/.config/obsidian/obsidian.json`（Linux/macOS；Obsidian 官方位置，Windows 类似 `%APPDATA%\obsidian\obsidian.json`）。
- **结构**：

  ```json
  { "vaults": { "<unique-id>": { "path": "/absolute/path/to/vault" } } }
  ```

  CLI 使用 **目录名** 作为 vault name（如 `/home/u/vaults/my-brain` → name `my-brain`）。**不要用 `~`**，必须绝对路径。
- **默认 vault** 通过 `set-default-vault` 设置，命令省略 `--vault` 时使用默认。
- **多 vault** 通过 `--vault "<name-or-path>"` 显式切换。
- **若 Obsidian 已安装**：Obsidian 启动时自动注册 vault；headless 环境用 `add-vault` 注册。

## 5. 输出格式

| 命令 | 默认 | JSON | 其他 |
|---|---|---|---|
| `list-vaults` | 人类可读（default 标 `(default)`） | `--json` | `--path-only`、`--default`、`--default --path-only` |
| `search-content` | 交互 fuzzy 选择 | `--format json`（隐含 non-interactive） | `--no-interactive`（grep 风格） + `--page` / `--page-size`（默认 25，最大 100） |
| `print` | 原始 markdown 到 stdout | — | — |
| `frontmatter --print` | YAML 文本 | — (待确认) | — |
| `list` | 文件/文件夹纯文本 | — (待确认) | — |
| `search` (文件名) | 交互式 TUI | — | — |

JSON 输出主要集中在 `list-vaults` 和 `search-content`。其他命令 stdout 是 plain text（脚本可用 `print` + 自行解析 frontmatter）。

## 6. 错误处理 / 退出码

- 标准 Go cobra CLI：错误打到 stderr，退出码非 0。
- Deprecation 警告 → stderr（不污染 stdout pipe）。
- `create` 在文件存在且未传 `--overwrite`/`--append` 时**保持文件不变**（幂等）。
- README 未列出具体退出码常量；按 cobra 惯例：0 成功 / 1 用户错误 / 其他视命令而定。**调用方应检查 `$?` 而非具体码**。

## 7. 已知限制（CLI 做不到、必须走 MCP / 其他途径）

| 操作 | CLI 支持 | 备注 |
|---|---|---|
| 读取 note 全文 | ✅ `print` | — |
| 按名/路径写 note | ✅ `create` (+ `--overwrite`/`--append`) | — |
| Patch 任意位置（heading / block-id 锚点插入） | ❌ | MCP `patch_content` 可按 heading 插；CLI 只能整文件追加/覆盖 |
| 读/写 frontmatter 字段 | ✅ `frontmatter` | 按 `--key/--value`；不支持复杂嵌套结构 / 数组 append |
| 重命名并更新 wikilink | ✅ `move` | **比 MCP 更强**（MCP 通常不更新引用） |
| 删除 note | ✅ `delete` | — |
| 列文件 | ✅ `list` | 按目录 |
| 全文搜索 | ✅ `search-content --format json` | 支持分页 |
| 文件名 fuzzy 搜索（脚本） | ⚠️ `search` 仅交互 TUI | 脚本场景用 `list` + grep / `search-content` 文件名匹配 |
| Daily note（读 `daily-notes.json` 模板） | ✅ `daily` | — |
| 打开 note 到 Obsidian GUI | ✅ `open` | 需要 Obsidian 安装 |
| 跳 heading | ✅ `open --section` | 仅打开时 |
| **创建/操作 canvas / excalidraw / 非 md** | ❌ | 只处理 `.md` |
| **执行 Obsidian command（如 `:graph`、插件命令）** | ❌ | 必须 Advanced URI + MCP |
| **读取 Obsidian 内部 metadata cache（反向链接图）** | ❌ | 必须 MCP 或 dataview |
| **批量 tag 操作 / 标签查询** | ❌ | 走 frontmatter 字段近似，或 MCP |
| **block reference (`^block-id`) 解析** | ❌ | MCP 也弱，通常需 dataview |

## Caveats / Not Found

- **不是 npm 包**：原任务问“npm 包名”不适用。它是 Go 二进制，分发走 brew/scoop/AUR/source。
- **二进制名漂移**：仓库 url `Yakitrak/obsidian-cli` 仍可访问，但仓库已 rename 为 `notesmd-cli`，命令前缀也是 `notesmd-cli`。cortex 插件配置应以 `notesmd-cli` 为准；若需向后兼容 `obsidian-cli` 旧版（v0.2.3），命令子集相似但缺 `add-vault` / `frontmatter` / `search-content --format json` 等新特性。
- **退出码细节** README 未文档化，需读源码 `cmd/*.go` 或运行时探测。
- `frontmatter --print` 和 `list` 的 JSON 输出选项 README 未提及，**未确认**支持。脚本化解析建议优先用 `list-vaults --json` 和 `search-content --format json`。
- **Windows 配置路径** README 未明示；Obsidian 官方为 `%APPDATA%\obsidian\obsidian.json`，但 CLI 行为以源码 `pkg/` 为准（未深读）。
