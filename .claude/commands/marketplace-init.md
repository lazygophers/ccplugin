---
description: 初始化新的插件市场，创建 marketplace.json 和基础结构
argument-hint: <market-name>
allowed-tools: Bash, Write, Edit
---

# marketplace-init

初始化新的 Claude Code 插件市场。

## 使用方法

/marketplace-init <market-name>

## 参数

- `market-name`: 市场名称（kebab-case，如 my-market）

## 执行步骤

1. 创建市场目录结构
2. 创建 marketplace.json
3. 创建 plugins 目录
4. 创建 README.md
5. 创建 LICENSE

## 目录结构

```
market-name/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── .gitkeep
├── README.md
└── LICENSE
```

## marketplace.json 模板

```json
{
  "name": "market-name",
  "version": "1.0.0",
  "description": "Market description",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/org/market",
  "license": "MIT",
  "owner": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "plugins": []
}
```

## 输出

```
✓ Created market: market-name
✓ Created marketplace.json
✓ Created directory structure
✓ Created README.md
✓ Created LICENSE

Next steps:
1. Edit ./market-name/.claude-plugin/marketplace.json
2. Add plugins to ./market-name/plugins/
3. Update plugins list in marketplace.json
4. Commit and push to GitHub
5. Share marketplace URL
```

## 示例

创建一个名为 company-tools 的市场：

```bash
marketplace-init company-tools
```

## 使用市场

创建后，其他用户可以这样使用：

```bash
# 添加市场
/plugin marketplace add https://github.com/org/company-tools

# 列出市场插件
/plugin list

# 安装插件
/plugin install plugin-name@company-tools
```

## 注意事项

- 市场名称必须使用 kebab-case
- 确保有权限创建目录
- marketplace.json 格式必须正确
- 插件路径可以是本地或远程
