# CCPlugin Market

> Claude Code 插件市场 - 提供常用插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率。

## 快速开始

### 安装市场

```bash
# 从 GitHub 安装
/plugin marketplace add https://github.com/ccplugin/market.git

# 或从本地目录安装
/plugin marketplace add /path/to/ccplugin
```

### 列出可用插件

```bash
/plugin
```

### 安装插件

```bash
# 安装特定插件
/plugin install code-quality-kit

# 查看插件详情
/plugin info code-quality-kit
```

## 可用插件

| 插件名称 | 描述 | 版本 | 标签 |
|---------|------|------|------|
| `code-quality-kit` | 代码质量检查工具集 | 1.0.0 | quality, review, security |
| `web-dev-helper` | Web 开发助手 | 1.0.0 | web, react, vue |
| `data-processor` | 数据处理工具 | 1.0.0 | data, etl, validation |

## 插件开发

### 使用模板创建新插件

```bash
# 复制模板
cp -r plugins/template my-new-plugin

# 修改配置
cd my-new-plugin/.claude-plugin
vi plugin.json

# 实现功能
cd ../commands  # 添加命令
cd ../agents    # 添加代理
cd ../skills    # 添加技能
```

### 插件结构

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json         # 插件清单（必需）
├── commands/               # 自定义命令
│   └── my-command.md
├── agents/                 # 子代理
│   └── my-agent.md
├── skills/                 # 技能
│   └── my-skill/
│       └── SKILL.md
├── hooks/                  # 钩子（可选）
│   └── hooks.json
└── README.md
```

### 提交插件

1. Fork 本仓库
2. 在 `plugins/` 目录下创建插件
3. 更新 `marketplace.json`
4. 提交 Pull Request

## 文档

### 开发文档

- [插件开发指南](docs/plugin-development.md) - 完整的插件开发教程
- [API 参考](docs/api-reference.md) - 完整的 API 参考
- [最佳实践](docs/best-practices.md) - 开发最佳实践
- [支持的语言](docs/supported-languages.md) - 插件开发语言选择指南
- [编译型语言指南](docs/compiled-languages-guide.md) - Go/Rust 等编译型语言使用指南
- [贡献指南](docs/contributing.md) - 贡献指南

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- 主页: https://docs.ccplugin.dev
- 仓库: https://github.com/ccplugin/market
- 邮箱: admin@ccplugin.dev
