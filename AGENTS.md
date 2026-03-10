# CCPlugin Market (ccplugin)

> Claude Code 插件市场仓库（monorepo）：根包只发布 `scripts/` CLI；插件实现集中在 `plugins/`；共享能力在 `lib/`。

## 结构速览

```
./
├── plugins/                 # Claude Code 插件（marketplace.json 的 pluginRoot）
│   ├── tools/               # 工具类插件（git/deepresearch/version/env/notify/...）
│   ├── languages/           # 语言规范类插件（python/typescript/.../markdown）
│   ├── themes/              # 主题/设计规范插件集合
│   ├── office/              # Office 文件插件（docx/pptx/xlsx）
│   └── ...
├── lib/                     # 共享库（独立 pyproject；作为根包依赖引入）
├── scripts/                 # 根包 CLI（clean/update/info/check/install）
├── docs/                    # 文档集合（开发指南 / API / 最佳实践等）
├── .claude-plugin/
│   └── marketplace.json     # 市场注册表（插件清单与 source 路径）
├── CLAUDE.md                # 仓库开发约定（uv/测试/结构等）
├── pyproject.toml           # 根包元数据（只打包 scripts；排除 plugins/lib）
└── .version                 # 版本号（含 build 段）
```

## 去哪里找

| 目标 | 位置 | 说明 |
|---|---|---|
| 新增/维护插件清单 | `.claude-plugin/marketplace.json` | `pluginRoot=./plugins`，每个条目有 `name/source/version/...` |
| 插件元数据/组件入口 | `plugins/**/.claude-plugin/plugin.json` | 每个插件的命令/agents/skills/hooks/lsp/mcp 都在这里声明 |
| 共享库能力 | `lib/` | 插件复用：日志、hooks、环境等（另有 `lib/llms.txt`） |
| 根命令（发布物） | `scripts/` + `pyproject.toml` | 根包仅包含 `scripts*`（`exclude = ["plugins*", "lib*"]`） |
| 插件开发规范 | `docs/` + `CLAUDE.md` | 开发流程、API schema、最佳实践 |

## 约定（项目特异）

- Python 版本：根包 `requires-python = ">=3.11"`，本仓库固定 `.python-version = 3.11`。
- 执行方式：本仓库约定用 `uv` 管理/执行 Python（示例：`uv run pytest`、`uv run ruff check .`）。
- 打包边界：根 `pyproject.toml` 只打包 `scripts*`，`plugins/` 与 `lib/` 不随根包发布。
- 文档落点：根目录使用 `AGENTS.md`；其余目录使用 `llms.txt`（本仓库已有大量分层 `llms.txt`）。

## 常用命令

```bash
# 安装依赖（按 uv.lock）
uv sync

# 代码质量
uv run ruff check .
uv run ruff format .

# 测试（更推荐按子项目/目录执行）
uv run pytest lib/tests
# 例：运行某个插件的测试/脚本（若插件有独立 pyproject）
uv run --directory plugins/memory pytest

# 版本同步（跨所有插件/根包）
uv run scripts/update_version.py
```

## 常见坑

- 修改/新增插件：别只改 `plugins/**/.claude-plugin/plugin.json`，还要同步 `.claude-plugin/marketplace.json`（市场索引）。
- 根包依赖 `lib`：根 `pyproject.toml` 通过 `[tool.uv.sources.lib]` 指向本仓库 `lib/` 子目录；调试依赖问题时要区分“根包环境”和“lib 子项目环境”。
