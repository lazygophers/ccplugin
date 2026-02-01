# 版本号管理插件

一个完整的 Semantic Versioning (SemVer) 版本管理解决方案，为 Claude Code 项目提供自动和手动版本号管理功能。

## 特性

✨ **完整的 SemVer 支持** - 支持 Major.Minor.Patch.Build 四部分版本号

🤖 **自动版本更新** - 通过 Claude Code Hooks 自动检测任务完成并更新版本

🎯 **灵活的版本控制** - 支持手动 bump 和自动更新两种模式

📝 **Git 集成** - 智能检测 .version 文件的 Git 提交状态

🔧 **CLI 工具** - 支持本地脚本运行

## 快速开始

### 安装

```bash
# 作为 Claude Code 插件自动加载（已内置）
# 或手动安装最新版本
/plugin install ./plugins/version
```

### 基本用法

```bash
# 显示当前版本
/version show

# 显示版本详情（包括 Git 状态）
/version info

# 自动更新版本
/version bump build     # 构建版本 +1
/version bump patch     # 补丁版本 +1
/version bump minor     # 次版本 +1
/version bump major     # 主版本 +1

# 手动设置版本
/version set 1.0.0.0
```

## 版本号含义

采用 Semantic Versioning 标准，格式为 `X.Y.Z.W`：

| 部分  | 名称  | 何时增加                    |
| ----- | ----- | --------------------------- |
| **X** | Major | 不兼容的 API 变更或重大功能 |
| **Y** | Minor | 向后兼容的新功能            |
| **Z** | Patch | bug 修复和性能优化          |
| **W** | Build | 完成任务和小改进            |

### 版本更新示例

```
初始版本：0.0.1.0

新功能完成：
0.0.1.0 → 0.1.0.0 (bump minor)

Bug 修复：
0.1.0.0 → 0.1.1.0 (bump patch)

任务完成：
0.1.1.0 → 0.1.1.1 (bump build)
0.1.1.1 → 0.1.1.2 (bump build)

架构重构：
0.1.1.2 → 1.0.0.0 (bump major)
```

## 命令详解

### /version show

显示项目当前版本号。

```bash
/version show
# 输出: 1.2.3.4
```

### /version info

显示版本详细信息，包括各部分数值和 Git 提交状态。

```bash
/version info
# 输出:
# 当前版本: 1.2.3.4
#   Major: 1 (主版本号)
#   Minor: 2 (次版本号)
#   Patch: 3 (补丁版本号)
#   Build: 4 (构建版本号)
#
# Git 状态: ✓ 已提交
```

### /version bump \<level\>

根据指定级别自动更新版本号，高级别重置时自动清零低级别。

```bash
# 更新构建版本（常用）
/version bump build    # 1.2.3.4 → 1.2.3.5

# 更新补丁版本（bug 修复）
/version bump patch    # 1.2.3.5 → 1.2.4.0

# 更新次版本（新功能）
/version bump minor    # 1.2.4.0 → 1.3.0.0

# 更新主版本（重大变更）
/version bump major    # 1.3.0.0 → 2.0.0.0
```

### /version set \<version\>

手动设置版本号到指定值（用于特殊场景）。

```bash
# 初始化版本
/version set 1.0.0.0   # 0.0.1.0 → 1.0.0.0

# 修正版本错误
/version set 2.1.3.5   # 1.0.0.0 → 2.1.3.5

# 简化格式（自动补全）
/version set 2.0       # 2.1.3.5 → 2.0.0.0
```

## 工作流

### 标准开发流程

```
1. 完成一项工作（功能、修复、任务）
   ↓
2. 确定版本级别（Major/Minor/Patch/Build）
   ↓
3. 执行 /version bump <level> 更新版本
   ↓
4. 提交到 Git
   gitadd .version
   gitcommit -m "chore: bump version to X.Y.Z.W"
   ↓
5. 推送到远程
   gitpush origin master
```

### 自动版本更新（Hooks）

Claude Code Hooks 在以下情况会自动提示或更新版本：

- **SubagentStop**：子任务完成时触发（仅更新 Build 版本）
- **Stop**：会话结束时触发（提示更新相应版本）

**限制条件**：

- `.version` 文件必须已提交到 Git
- SubagentStop 仅能自动更新 Build 版本
- Major/Minor/Patch 版本需手动通过命令更新

## 文件结构

```
plugins/version/
├── scripts/
│   ├── version.py           # 主脚本
│   └── __init__.py
├── commands/
│   ├── version-show.md      # 显示版本命令
│   ├── version-info.md      # 显示详情命令
│   ├── version-bump.md      # 更新版本命令
│   └── version-set.md       # 设置版本命令
├── hooks/
│   └── hooks.json           # Claude Code Hooks 配置
├── skills/
│   └── version/
│       └── SKILL.md         # 版本管理最佳实践
├── .claude-plugin/
│   └── plugin.json          # 插件配置
└── README.md                # 本文件
```

## 版本文件管理

### 版本文件位置

版本号存储在项目根目录的 `.version` 文件中（纯文本）。

```bash
cat .version
# 输出: 1.2.3.4
```

### Git 管理

版本文件应被提交到 Git 以保持团队一致：

```bash
# 添加到 Git
gitadd .version

# 提交
gitcommit -m "chore: initialize version management"

# 推送
gitpush origin master
```

### 创建发布标签

重要版本发布时创建 Git 标签：

```bash
# 创建标签
gittag v1.2.3.4

# 推送标签
gitpush origin v1.2.3.4

# 列出所有标签
gittag -l
```

## 最佳实践

### 何时更新各级版本

**Major 版本**：

- ✅ 不兼容的 API 修改
- ✅ 架构重构
- ✅ 主要功能删除或重写
- ❌ 新增可选功能

**Minor 版本**：

- ✅ 新增功能模块
- ✅ 新增可选 API
- ✅ 向后兼容的功能增强
- ❌ Bug 修复

**Patch 版本**：

- ✅ Bug 修复
- ✅ 性能优化
- ✅ 安全补丁
- ✅ 文档改进

**Build 版本**：

- ✅ 完成单个任务
- ✅ 代码小改进
- ✅ 持续集成自动更新
- ❌ 功能性变更（应使用 Major/Minor/Patch）

### DO ✅

1. 遵循 SemVer 规范
2. 及时更新版本号
3. 提交版本文件到 Git
4. 维护 CHANGELOG 记录
5. 重要发布创建 Git 标签
6. 使用清晰的 commit message

### DON'T ❌

1. 跳跃版本级别
2. 随意重置版本号
3. 忽视 .version 文件
4. 混淆版本级别的用途
5. 过度更新构建版本
6. 不同步提交版本文件

## 常见问题

### Q: 初次使用如何初始化版本？

A: 第一次使用时，脚本会自动创建 `.version` 文件并初始化为 `0.0.1.0`：

```bash
/version show
# 自动创建 .version 文件
# 输出: 0.0.1.0
```

或手动初始化：

```bash
/version init
```

### Q: 版本号能否自动同步到其他文件？

A: 当前版本不自动同步，建议：

- 手动更新 `pyproject.toml` 中的 version 字段
- 手动更新 `package.json` 中的 version 字段
- 使用构建脚本在发布时同步版本

### Q: Hooks 为什么没有自动更新版本？

A: 检查以下条件：

1. `.version` 文件是否已提交到 Git（未提交会拒绝更新）
2. 任务是否确实完成（Hooks 需要检测到完成信号）
3. 插件是否已启用

### Q: 支持的版本格式有哪些？

A: 支持以下格式（自动补全至 4 部分）：

- `1`
- `1.0`
- `1.0.0`
- `1.0.0.0`

### Q: 如何在生产环境中使用此插件？

A: 在 CI/CD 流程中使用 Python 直接调用脚本：

```bash
# 在 CI/CD 中自动更新版本
python scripts/version.py bump patch

# 在 package.json 中定义脚本（需先确保依赖可用）
{
  "scripts": {
    "version:show": "python scripts/version.py show",
    "version:bump": "python scripts/version.py bump"
  }
}
```

## 技术细节

### 项目根目录检测

脚本从当前目录向上查找，优先级如下：

1. 存在 `.git` 目录
2. 存在 `pyproject.toml` 文件
3. 存在 `.version` 文件

### Git 状态检查

运行 `git status .version` 检查文件是否有未提交的修改。

### 级联重置

更新任何级别的版本号时，所有后续级别自动重置为 0：

- 更新 Major → Minor/Patch/Build 重置为 0
- 更新 Minor → Patch/Build 重置为 0
- 更新 Patch → Build 重置为 0
- 更新 Build → 无重置

## 依赖

- Python 3.7+
- Git（用于检查提交状态）

## 许可证

AGPL-3.0-or-later

## 相关资源

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [版本管理最佳实践](./skills/version/SKILL.md)

## 反馈和贡献

遇到问题或有建议？请提出 Issue 或 Pull Request：

- GitHub: https://github.com/lazygophers/ccplugin/issues
- Email: admin@lazygophers.dev
