---
name: marketplace-management
description: Claude Code 插件市场管理技能。当用户需要管理插件市场、添加/删除市场、列出可用插件或安装插件时自动激活。提供市场配置、marketplace.json 格式、市场管理和插件安装指导。
auto-activate: always:true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Claude Code 插件市场管理

## 市场配置

### marketplace.json 格式

市场清单文件位于 `.claude-plugin/marketplace.json`：

```json
{
  "name": "market-name",
  "version": "1.0.0",
  "description": "市场描述",
  "author": {
    "name": "市场维护者",
    "email": "admin@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/org/market",
  "license": "MIT",
  "owner": {
    "name": "维护者名称",
    "email": "admin@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "插件描述",
      "version": "1.0.0",
      "author": {"name": "作者"},
      "keywords": ["tag1", "tag2"],
      "strict": true
    }
  ]
}
```

### 必需字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `name` | string | 市场标识符（kebab-case） |
| `owner` | object | 市场维护者信息 |
| `plugins` | array | 可用插件列表 |

### 插件条目字段

| 字段 | 类型 | 描述 | 必需 |
|------|------|------|------|
| `name` | string | 插件标识符 | 是 |
| `source` | string\|object | 插件来源 | 是 |
| `description` | string | 插件描述 | 是 |
| `version` | string | 版本号 | 否 |
| `author` | object | 作者信息 | 否 |
| `keywords` | array | 标签 | 否 |
| `strict` | boolean | 是否要求 plugin.json | 否（默认 true） |

## 市场管理

### 添加市场

```bash
# 从 GitHub 添加
/plugin marketplace add owner/repo

# 从 Git 仓库添加
/plugin marketplace add https://gitlab.com/org/market.git

# 从本地目录添加
/plugin marketplace add ./path/to/market
```

### 列出市场

```bash
# 列出所有已添加的市场
/plugin marketplace list

# 查看特定市场的插件
/plugin marketplace show market-name
```

### 删除市场

```bash
# 删除市场
/plugin marketplace remove market-name
```

### 更新市场

```bash
# 更新市场索引
/plugin marketplace update market-name

# 更新所有市场
/plugin marketplace update --all
```

## 插件管理

### 搜索插件

```bash
# 搜索插件
/plugin search keyword

# 列出所有可用插件
/plugin list

# 查看插件详情
/plugin info plugin-name
```

### 安装插件

```bash
# 从市场安装
/plugin install plugin-name

# 从指定市场安装
/plugin install plugin-name@market-name

# 从本地路径安装
/plugin install ./path/to/plugin

# 从 GitHub 安装
/plugin install owner/repo
```

### 卸载插件

```bash
# 卸载插件
/plugin uninstall plugin-name

# 强制卸载
/plugin uninstall plugin-name --force
```

### 更新插件

```bash
# 更新所有插件
/plugin update --all

# 更新特定插件
/plugin update plugin-name
```

## 插件来源配置

### 本地路径

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin"
}
```

### GitHub 仓库

```json
{
  "name": "my-plugin",
  "source": {
    "source": "github",
    "repo": "username/plugin-repo"
  }
}
```

### Git 仓库

```json
{
  "name": "my-plugin",
  "source": "https://github.com/username/plugin-repo.git"
}
```

## 市场结构

### 标准市场结构

```
marketplace/
├── .claude-plugin/
│   └── marketplace.json     # 市场清单
├── plugins/
│   ├── plugin-a/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── commands/
│   │   ├── agents/
│   │   └── skills/
│   └── plugin-b/
│       └── ...
├── README.md
└── LICENSE
```

### 多仓库市场

```json
{
  "name": "multi-repo-market",
  "plugins": [
    {
      "name": "plugin-a",
      "source": "./plugins/plugin-a"
    },
    {
      "name": "plugin-b",
      "source": {
        "source": "github",
        "repo": "org/plugin-b"
      }
    }
  ]
}
```

## 市场最佳实践

### 组织插件

1. **单一仓库市场**：所有插件在一个仓库
   - 适合小型市场
   - 易于管理

2. **多仓库市场**：插件分布在多个仓库
   - 适合大型市场
   - 独立版本控制

3. **混合市场**：本地和远程插件混合
   - 灵活性高
   - 适合企业内部

### 版本管理

- 使用语义化版本
- 及时更新 marketplace.json 中的版本号
- 维护 CHANGELOG.md

### 插件发现

- 添加有意义的 keywords
- 提供清晰的 description
- 分类组织插件

## 常见问题

**Q: 如何创建新市场？**
A: 创建 marketplace.json 并配置 plugins 列表。

**Q: 如何更新市场中的插件？**
A: 修改插件后更新 marketplace.json 中的版本号，然后 `/plugin marketplace update`。

**Q: 可以有多个市场吗？**
A: 可以，使用 `/plugin marketplace add` 添加多个市场。

**Q: 如何解决插件冲突？**
A: 插件名称必须唯一，同名插件会覆盖。

## 参考资源

- [官方市场文档](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [项目 marketplace.json](../.claude-plugin/marketplace.json)
- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
