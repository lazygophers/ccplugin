---
description: 显示当前项目版本号
allowed-tools: Bash(uv*,*/version.py)
---

# show

## 命令描述

显示项目当前的版本号。版本号存储在项目根目录的 `.version` 文件中。

## 工作流描述

1. **查找项目根目录**：从当前目录向上查找包含 `.git` 或 `pyproject.toml` 的目录
2. **读取版本文件**：读取 `.version` 文件的内容
3. **显示版本**：输出当前版本号

## 使用方法

```bash
/version show
```

## 示例

```bash
# 显示当前版本
/version show

# 输出示例:
# 1.2.3.4
```

## 相关命令

- `/version info` - 显示版本详情
- `/version bump` - 更新版本号
- `/version set` - 手动设置版本号
- `/version init` - 初始化版本文件

## 相关 Skills

- `@${CLAUDE_PLUGIN_ROOT}/skills/version/SKILL.md` - 版本号管理最佳实践
