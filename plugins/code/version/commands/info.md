---
description: 显示版本号详细信息
allowed-tools: Bash(uv*,*/version.py)
---

# info

## 命令描述

显示项目版本号的详细信息，包括各个版本部分的具体数值和 Git 提交状态。

## 工作流描述

1. **读取版本文件**：获取当前版本号
2. **解析版本**：将版本号分解为 Major、Minor、Patch、Build 四个部分
3. **显示详情**：输出每个版本部分的值和含义
4. **检查 Git 状态**：显示版本文件是否已提交到 Git

## 使用方法

```bash
/version info
```

## 示例

```bash
# 显示版本详情
/version info

# 输出示例:
# 当前版本: 1.2.3.4
#   Major: 1 (主版本号)
#   Minor: 2 (次版本号)
#   Patch: 3 (补丁版本号)
#   Build: 4 (构建版本号)
#
# Git 状态: ✓ 已提交
```

## 相关命令

- `/version show` - 显示当前版本
- `/version bump` - 更新版本号
- `/version set` - 手动设置版本号
- `/version init` - 初始化版本文件

## 相关 Skills

- `@${CLAUDE_PLUGIN_ROOT}/skills/version/SKILL.md` - 版本号管理最佳实践

## 版本号含义

按照 Semantic Versioning (SemVer) 标准：

- **Major (主版本号)**：不兼容的 API 修改时增加
- **Minor (次版本号)**：向后兼容的功能新增时增加
- **Patch (补丁版本号)**：向后兼容的 bug 修复时增加
- **Build (构建版本号)**：每次完成一个任务或修复时增加，不影响其他版本号
