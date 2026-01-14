---
description: 初始化项目版本文件
allowed-tools: Bash(uv*,*/version.py)
---

# init

## 命令描述

创建并初始化项目的版本文件 `.version`。如果文件已存在则不做任何操作。

## 工作流描述

1. **检查版本文件**：判断 `.version` 文件是否存在
2. **创建文件**：如果不存在，在项目根目录创建 `.version` 文件
3. **初始化内容**：写入默认版本号 `0.0.1.0`
4. **验证**：确认文件创建成功

## 使用方法

```bash
/version init
```

## 示例

```bash
# 初始化版本文件
/version init
# 输出: ✓ 已创建版本文件: /path/to/project/.version
```

## 相关命令

- `/version show` - 显示当前版本
- `/version info` - 显示版本详情
- `/version bump` - 更新版本号
- `/version set` - 手动设置版本号

## 相关 Skills

- `@${CLAUDE_PLUGIN_ROOT}/skills/version/SKILL.md` - 版本号管理最佳实践

## 注意事项

- **自动创建**：脚本会自动创建 `.version` 文件，无需手动初始化
- **默认版本**：初始版本号为 `0.0.1.0`
- **Git 管理**：创建后建议提交到 Git

## 执行时机

- 项目首次使用版本管理
- 删除 `.version` 文件后需要重新初始化
- 迁移项目版本管理系统时
