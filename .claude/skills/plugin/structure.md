# 插件目录结构

## 标准结构

每个插件必须遵循以下目录结构：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 插件清单（必需）
├── commands/                 # 命令目录
│   └── *.md                 # 命令文件
├── agents/                  # 代理目录
│   └── *.md                 # 代理文件
├── skills/                  # 技能目录
│   └── skill-name/         # 技能目录
│       └── SKILL.md        # 技能入口
├── hooks/                   # 钩子目录
│   └── hooks.json          # 钩子配置
├── scripts/                 # 脚本目录
│   ├── __init__.py
│   ├── main.py             # CLI 入口
│   └── <module>.py         # 业务逻辑
├── .mcp.json              # MCP 配置（可选）
├── .lsp.json              # LSP 配置（可选）
├── AGENT.md               # 代理文档（可选）
├── README.md              # 插件文档（可选）
└── pyproject.toml         # 依赖配置（可选）
```

## 目录角色

| 目录/文件 | 必需 | 用途 |
|-----------|------|------|
| `.claude-plugin/plugin.json` | ✅ | 插件清单 |
| `commands/*.md` | ❌ | 命令定义 |
| `agents/*.md` | ❌ | 代理定义 |
| `skills/skill-name/SKILL.md` | ❌ | 技能定义 |
| `hooks/hooks.json` | ❌ | 钩子配置 |
| `scripts/main.py` | ❌ | CLI 入口点 |
| `AGENT.md` | ❌ | 系统提示注入 |
| `.mcp.json` | ❌ | MCP 服务器配置 |
| `.lsp.json` | ❌ | LSP 服务器配置 |

## 命名约定

### 插件目录名

```bash
# ✅ 正确
task
semantic
git
python
style-dark

# ❌ 避免
Task              # 大写
semantic_skills   # 下划线
gitOperations     # 驼峰
```

### 命令文件名

```bash
# ✅ 正确
add.md
list.md
commit.md

# ❌ 避免
AddTask.md        # 大写
list_tasks        # 无扩展名
```

### 代理文件名

```bash
# ✅ 正确
dev.md
review.md
explore.md

# ❌ 避免
Developer.md      # 大写
code-review       # 无扩展名
```

### 技能目录名

```bash
# ✅ 正确
python/
git-workflow/
code-review/

# ❌ 避免
PythonCoding     # 大写
python_skills    # 下划线
```

## 路径变量

所有文件路径使用相对路径或 `${CLAUDE_PLUGIN_ROOT}`：

```json
// plugin.json 中的路径
{
  "commands": ["./commands/command.md"],
  "agents": ["./agents/agent.md"],
  "skills": "./skills/"
}
```

## 完整示例

### 简单插件

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── commands/
    └── hello.md
```

### 完整插件

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── add.md
│   ├── list.md
│   └── delete.md
├── agents/
│   └── dev.md
├── skills/
│   └── coding/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── AGENT.md
└── README.md
```
