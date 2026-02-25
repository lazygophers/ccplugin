# Env 插件

> 环境处理插件 - 从 .env 文件加载环境变量并注入会话

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin env@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install env@ccplugin-market
```

## 功能特性

- **自动加载** - 会话开始时自动加载环境变量
- **多文件支持** - 支持 `.claude/.env` 和 `.claude/.env.local`
- **安全注入** - 自动注入到 Claude Code 会话中
- **优先级** - `.env.local` 优先于 `.env`

## 使用方式

### 1. 创建环境文件

在项目目录创建 `.claude/.env` 文件：

```bash
# .claude/.env
API_KEY=your_api_key
DATABASE_URL=postgresql://localhost:5432/mydb
DEBUG=true
```

### 2. 本地覆盖（可选）

创建 `.claude/.env.local` 用于本地开发覆盖：

```bash
# .claude/.env.local
API_KEY=local_api_key
DEBUG=false
```

### 3. 自动加载

插件在会话开始时会自动运行（通过 SessionStart hook），加载环境变量到会话中。

## 文件结构

```
env/
├── .claude-plugin/
│   └── plugin.json       # 插件配置
├── scripts/
│   ├── __init__.py
│   └── main.py           # 主脚本
└── pyproject.toml        # Python 项目配置
```

## 许可证

AGPL-3.0-or-later
