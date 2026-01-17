---
description: 自动更新版本号到下一个版本（默认更新 build 版本）
argument-hint: [build] | patch | minor | major
allowed-tools: Bash(uv*,*/version.py)
---

# bump

## 命令描述

根据指定的级别自动更新项目版本号。遵循 Semantic Versioning 标准，更新指定部分并重置后续部分。

**默认行为**：不带参数时默认更新 build 版本号。

## 工作流描述

1. **验证参数**：确认版本级别有效 (major/minor/patch/build)
2. **读取现有版本**：从 `.version` 文件读取当前版本
3. **增加指定级别**：将目标级别版本号加 1
4. **重置低级别**：重置所有后续级别为 0
5. **写入新版本**：更新 `.version` 文件

## 使用方法

```bash
/version bump            # 默认：构建版本 +1
/version bump build      # 构建版本 +1（显式指定）
/version bump patch      # 补丁版本 +1
/version bump minor      # 次版本 +1
/version bump major      # 主版本 +1
```

## 版本级别说明

| 级别 | 说明 | 版本变化 |
|------|------|---------|
| `build` | 构建版本号增加 1 | 0.1.2.3 → 0.1.2.4 |
| `patch` | 补丁版本号增加 1 | 0.1.2.4 → 0.1.3.0 |
| `minor` | 次版本号增加 1 | 0.1.3.0 → 0.2.0.0 |
| `major` | 主版本号增加 1 | 0.2.0.0 → 1.0.0.0 |

## 示例

```bash
# 完成任务，更新构建版本（默认）
/version bump
# 输出: ✓ 版本已更新: 1.2.3.4 → 1.2.3.5

# 或显式指定 build
/version bump build
# 输出: ✓ 版本已更新: 1.2.3.4 → 1.2.3.5

# 修复 bug，更新补丁版本
/version bump patch
# 输出: ✓ 版本已更新: 1.2.3.5 → 1.2.4.0

# 完成新功能，更新次版本
/version bump minor
# 输出: ✓ 版本已更新: 1.2.4.0 → 1.3.0.0

# 架构重构，更新主版本
/version bump major
# 输出: ✓ 版本已更新: 1.3.0.0 → 2.0.0.0
```

## 相关命令

- `/version show` - 显示当前版本
- `/version info` - 显示版本详情
- `/version set` - 手动设置版本号
- `/version init` - 初始化版本文件

## 相关 Skills

- `@${CLAUDE_PLUGIN_ROOT}/skills/version/SKILL.md` - 版本号管理最佳实践

## 注意事项

- **默认行为**：不带参数时默认更新 build 版本号
- **级联重置**：只要更新任何级别，所有后续级别都会被重置为 0
- **版本文件**：确保项目根目录存在 `.version` 文件（不存在会自动创建）
- **Git 状态**：更新版本号后需要手动提交到 Git
- **规范遵循**：遵循 Semantic Versioning 标准

## 执行时机

- 完成一个任务或小改进：执行 `/version bump`（默认更新 build）
- 修复 bug：执行 `/version bump patch`
- 完成新功能：执行 `/version bump minor`
- 架构重构或重大变更：执行 `/version bump major`
