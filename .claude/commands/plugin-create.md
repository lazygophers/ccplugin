---
description: 创建新的 Claude Code 插件，使用模板快速搭建插件结构
argument-hint: <plugin-name>
allowed-tools: Bash, Write, Edit, Read
---

# plugin-create

创建新的 Claude Code 插件。

## 使用方法

/plugin-create <plugin-name>

## 参数

- `plugin-name`: 插件名称（kebab-case，如 my-awesome-plugin）

## 执行步骤

1. 验证插件名称格式（kebab-case）
2. 复制模板目录
3. 重命名目录
4. 更新 plugin.json
5. 提示用户完善信息

## 示例

创建一个名为 code-formatter 的插件：

```bash
plugin-create code-formatter
```

## 输出

```
✓ Created plugin: code-formatter
✓ Copied from template
✓ Updated plugin.json

Next steps:
1. Edit ./code-formatter/.claude-plugin/plugin.json
2. Add commands to ./code-formatter/commands/
3. Add agents to ./code-formatter/agents/
4. Add skills to ./code-formatter/skills/
5. Test locally: /plugin install ./code-formatter
```

## 注意事项

- 插件名称必须使用 kebab-case
- 避免使用特殊字符
- 名称应简洁描述性
