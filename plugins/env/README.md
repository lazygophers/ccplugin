# Env Plugin

环境处理插件 - 用于处理环境相关的问题。

## 安装

```bash
/plugin install ./plugins/env
```

## 结构

```
env/
├── .claude-plugin/
│   └── plugin.json       # 插件配置
├── hooks/
│   └── hooks.json        # Hooks 配置
├── scripts/
│   ├── __init__.py
│   └── main.py           # 主脚本
└── pyproject.toml        # Python 项目配置
```

## 使用

插件在会话开始时会自动运行（通过 SessionStart hook）。
