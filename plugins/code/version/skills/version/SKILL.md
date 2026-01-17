---
name: 版本号管理最佳实践
description: 语义化版本控制 (SemVer) 规范和项目版本管理指南
---

# 版本号管理最佳实践

## 概述

本指南规范项目版本管理，采用 Semantic Versioning (SemVer) 标准，确保版本号的一致性和可追踪性。

**核心原则**：除非用户明确要求，否则任何场景（命令无参数、hooks 自动触发）都默认更新 **Build 版本号**。

## 版本号格式

采用 **Major.Minor.Patch.Build** 四部分格式：

```
X.Y.Z.W
│ │ │ └─ Build (构建版本号)   : 每次完成小的改进或任务时增加
│ │ └─── Patch (补丁版本号)   : 修复 bug 时增加
│ └───── Minor (次版本号)     : 新增功能时增加
└─────── Major (主版本号)     : 不兼容变更或重大功能时增加
```

### 各部分含义

| 版本号 | 名称      | 增加条件 | 级联规则 | 示例 |
|--------|----------|---------|---------|------|
| Major  | 主版本   | 不兼容的 API 修改、重大功能 | 自动重置 Minor/Patch/Build 为 0 | 1.0.0.0 → 2.0.0.0 |
| Minor  | 次版本   | 向后兼容的新功能 | 自动重置 Patch/Build 为 0 | 1.0.0.0 → 1.1.0.0 |
| Patch  | 补丁版本 | bug 修复、性能优化 | 自动重置 Build 为 0 | 1.1.0.0 → 1.1.1.0 |
| Build  | 构建版本 | 完成任务、小改进 | 无级联重置 | 1.1.1.0 → 1.1.1.1 |

## 版本更新规则

### 何时更新 Major 版本

**条件**：
- 存在不兼容的 API 变更
- 架构发生重大改变
- 功能完全重写或删除
- 主要依赖升级导致不兼容

**示例**：
- 从 monolithic 架构切换到 microservices
- 删除或重命名公共 API
- 改变数据存储方式

**执行**：
```bash
/version bump major
# 0.5.2.3 → 1.0.0.0
```

### 何时更新 Minor 版本

**条件**：
- 完成一个功能模块（不影响现有功能）
- 新增可选功能或参数
- 新增导出 API 或工具函数
- 向后兼容的增强功能

**示例**：
- 新增用户认证模块
- 实现新的报表功能
- 添加新的数据导入格式支持

**执行**：
```bash
/version bump minor
# 1.0.2.3 → 1.1.0.0
```

### 何时更新 Patch 版本

**条件**：
- 修复已知 bug
- 性能改进（不改变 API）
- 安全补丁
- 文档和测试改进

**示例**：
- 修复列表排序错误
- 优化数据库查询
- 修补安全漏洞
- 改进错误处理

**执行**：
```bash
/version bump patch
# 1.1.0.3 → 1.1.1.0
```

### 何时更新 Build 版本

**条件**：
- 完成单个任务或需求
- 代码小改进（不影响功能）
- 持续集成的自动更新
- 完成设计工作、文档更新

**示例**：
- 完成一个故事卡 (story card)
- 改进代码注释或格式
- 完成代码审查并合并
- 完成单元测试编写

**执行**：
```bash
# 默认更新 build 版本（推荐）
/version bump
# 1.1.1.0 → 1.1.1.1

# 或显式指定 build
/version bump build
# 1.1.1.0 → 1.1.1.1
```

## 版本更新工作流

### 标准工作流

```
1. 完成工作后更新版本号
   ├─ 默认: /version bump（更新 Build）
   └─ 或按需指定: /version bump <level>

2. 提交到 Git
   └─ git add .version && git commit -m "chore: bump version to X.Y.Z.W"

3. 可选：打标签和发布
   └─ git tag vX.Y.Z.W

**重要原则**：除非用户明确要求，否则任何场景都默认更新 Build 版本。
```

### 自动版本更新（Hooks）

Claude Code hooks 会自动检测任务完成并更新版本：

- **SubagentStop Hook**：子任务完成时触发（默认更新 Build 版本）
- **Stop Hook**：会话结束时触发（默认更新 Build 版本）

**原则**：除非用户明确要求，否则任何自动化场景都只更新 Build 版本。

**限制**：
- 仅在 `.version` 文件已提交到 Git 时有效
- 自动化场景只能更新 Build 版本
- Major/Minor/Patch 版本需要用户手动通过命令更新

## 命令参考

### 查看版本

```bash
# 显示当前版本
/version show

# 显示版本详情（包含 Git 状态）
/version info
```

### 更新版本

```bash
# 默认更新 build 版本（推荐用于日常任务完成）
/version bump

# 手动更新其他级别
/version bump major|minor|patch|build

# 手动设置版本
/version set 1.0.0.0
```

### 初始化

```bash
# 初始化版本文件（默认 0.0.1.0）
/version init

# 显示脚本帮助
uvx --from git+https://github.com/lazygophers/ccplugin version --help
```

## 版本文件管理

### 文件位置

版本号存储在项目根目录的 `.version` 文件中（纯文本格式）。

```bash
# 查看版本文件
cat .version
# 输出: 1.2.3.4
```

### Git 管理

版本文件应该被提交到 Git 版本控制中：

```bash
# 添加版本文件到 Git
git add .version

# 提交版本更新
git commit -m "chore: bump version to 1.2.3.4"

# 推送到远程
git push origin master
```

### .gitignore 配置

**建议不要忽略** `.version` 文件，以便所有开发者保持版本同步。

## 最佳实践

### DO ✅

1. **定期更新版本**
   - 完成重要功能后立即更新版本
   - 维持版本号与功能进度的对应关系

2. **遵循 SemVer 规范**
   - 严格按照版本等级规则更新
   - 保证版本号的可读性和可预测性

3. **同步提交**
   - 版本号更新和代码变更一起提交
   - 使用清晰的 commit message 标识版本更新

4. **使用版本标签**
   - 重要发布时创建 Git 标签：`git tag vX.Y.Z.W`
   - 便于版本追踪和发布管理

5. **维护 CHANGELOG**
   - 记录每个版本的重要变更
   - 帮助用户了解版本特性

6. **沟通和文档**
   - 在 README 中记录最新版本信息
   - 发布时提供升级指南

### DON'T ❌

1. **不要跳跃版本级别**
   - ❌ `1.0.0.0 → 3.0.0.0`（跳过 2.0）
   - ✅ `1.0.0.0 → 2.0.0.0 → 3.0.0.0`

2. **不要随意重置已发布的版本**
   - ❌ 版本号应该只增不减

3. **不要忽视 .version 文件**
   - ❌ 删除或不提交 .version 文件
   - ✅ 始终维护版本文件

4. **不要过度更新构建版本**
   - ❌ 每行代码改变都更新 Build 版本
   - ✅ 完成一个完整任务再更新

## 常见场景

### 场景 1：完成新功能功能

```bash
# 当前版本：1.0.2.5
# 完成了：用户登录功能（完整模块）

/version bump minor
# 结果：1.1.0.0

git add .version
git commit -m "feat: add user authentication module"
```

### 场景 2：修复紧急 Bug

```bash
# 当前版本：1.1.3.2
# 完成了：修复生产环境数据丢失 bug

/version bump patch
# 结果：1.1.4.0

git add .version
git commit -m "fix: prevent data loss in sync process"

git tag v1.1.4.0
git push origin master --tags
```

### 场景 3：完成单个任务

```bash
# 当前版本：1.1.4.3
# 完成了：实现用户头像上传功能（STORY-123）

version bump
# 结果：1.1.4.4

git add .version
git commit -m "feat: add user avatar upload - STORY-123"
```

### 场景 4：架构重构

```bash
# 当前版本：1.5.2.8
# 完成了：从单体应用重构为微服务架构

/version set 2.0.0.0
# 结果：2.0.0.0

git add .version
git commit -m "refactor!: migrate to microservices architecture"

# 创建发布分支
git branch release/2.0
git tag v2.0.0.0
```

## 与 CHANGELOG 的配合

### CHANGELOG.md 格式

```markdown
# Changelog

所有显著的变更都会记录在本文件中。

## [1.1.0.0] - 2024-01-15

### Added
- 用户认证模块
- OAuth2 支持

### Fixed
- 修复数据库连接超时问题

### Changed
- 更新依赖包版本

## [1.0.2.5] - 2024-01-10
...
```

### 更新原则

- 每个 Major/Minor/Patch 版本更新时更新 CHANGELOG
- Build 版本的日常任务完成可选更新 CHANGELOG
- 发布时确保 CHANGELOG 已更新

## 故障排除

### 问题：版本号格式错误

```bash
# 显示版本详情查看问题
/version info

# 手动纠正
/version set 1.0.0.0
```

### 问题：版本号与 Git 状态不同步

```bash
# 检查 .version 文件是否已提交
git log --oneline .version | head -5

# 强制同步
git add .version
git commit -m "fix: sync version with git"
```

### 问题：Hooks 不自动更新版本

**原因**：`.version` 文件未提交到 Git

```bash
# 初次提交版本文件
git add .version
git commit -m "chore: initialize version file"
```

## 相关文件

- `.version` - 项目版本文件
- `CHANGELOG.md` - 变更日志
- `pyproject.toml` 或 `package.json` - 项目元数据（可同步版本号）

## 参考链接

- [Semantic Versioning (SemVer)](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
