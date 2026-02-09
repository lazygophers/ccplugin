---
name: plugin-development
description: 插件开发指南 - 当用户需要创建新的插件或从模板初始化插件时使用。覆盖插件规划、目录创建、manifest 配置和完整开发流程。
context: fork
agent: plugin
---

# 插件开发指南

## 快速开始

### 从模板创建

```bash
# 使用模板创建新插件
cp -r plugins/template my-new-plugin
cd my-new-plugin
```

### 手动创建

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件清单
├── commands/                 # 命令目录
├── agents/                  # 代理目录
├── skills/                  # 技能目录
├── hooks/                   # 钩子目录
├── scripts/                 # 脚本目录
└── README.md                # 插件文档
```

## 开发流程

1. **规划插件功能**
   - 确定插件类型（工具/语言/框架/主题/功能）
   - 定义命令、代理、技能、钩子

2. **配置 plugin.json**
   ```json
   {
     "name": "my-plugin",
     "version": "0.0.1",
     "description": "我的插件描述",
     "author": "Your Name",
     "commands": ["./commands/"],
     "agents": ["./agents/"],
     "skills": "./skills/"
   }
   ```

3. **实现组件**
   - 创建命令文件
   - 实现代理
   - 开发技能
   - 配置钩子

4. **测试插件**
   ```bash
   /plugin install ./my-plugin
   ```

## 相关技能

- [plugin-skill-development](plugin-skill-development/SKILL.md) - 插件技能开发
- [plugin-command-development](plugin-command-development/SKILL.md) - 插件命令开发
- [plugin-hook-development](plugin-hook-development/SKILL.md) - 插件钩子开发
- [plugin-script-development](plugin-script-development/SKILL.md) - 插件脚本开发
- [plugin-mcp-development](plugin-mcp-development/SKILL.md) - 插件 MCP 开发
- [plugin-agent-development](plugin-agent-development/SKILL.md) - 插件 AGENT.md 开发
