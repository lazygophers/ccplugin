# 插件定义

## 什么是插件

插件是**扩展 Claude Code 功能的独立模块化单元**：

- **独立性**：每个插件是自包含的单元
- **可组合**：插件可组合构建复杂工作流
- **可复用**：一次创建，多次使用

### 与 Skills/Commands/Agents 的关系

| 组件 | 角色 | 触发方式 |
|------|------|----------|
| **Plugin** | 功能容器 | 运行时加载 |
| **Command** | 命令入口 | `/command` |
| **Agent** | 任务执行 | `@agent` |
| **Skill** | 行为指导 | 自动匹配 |
| **Hook** | 事件响应 | 事件触发 |

## 插件价值

### 场景 1：功能扩展

```
# 安装 Git 操作插件
/plugin install git@ccplugin-market

# 使用 Git 功能
/commit-all "feat: new feature"
/update-ignore
/create-pr
```

### 场景 2：语言支持

```
# 安装 Python 开发支持
/plugin install python@ccplugin-market

# 自动获得编码规范指导
```

### 场景 3：工作流自动化

```
# 版本管理插件
/version show
/version inc minor
```

## 插件元数据

### 必需字段

```json
{
  "name": "plugin-name",
  "version": "0.0.1",
  "description": "插件简短描述"
}
```

### 可选字段

```json
{
  "author": {
    "name": "Author Name",
    "email": "email@example.com",
    "url": "https://github.com/username"
  },
  "homepage": "https://github.com/...",
  "repository": "https://github.com/...",
  "license": "MIT",
  "keywords": ["tag1", "tag2"]
}
```

## 版本格式

插件版本遵循语义化版本：

```
major.minor.patch

# 示例
0.0.1  # 初始版本
0.1.0  # 新功能
1.0.0  # 重大变更
```
