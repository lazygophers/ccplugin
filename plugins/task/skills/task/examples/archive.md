# 任务归档示例

本文件展示 @.claude/task/archive/ 中任务文件的正确格式和组织方式。

## 目录结构示例

```
archive/
├── ccplugin/                       # 主项目
│   ├── features.md                # 功能开发任务
│   ├── plugins.md                 # 插件相关任务
│   ├── infrastructure.md           # 基础设施和工具
│   └── documentation.md            # 文档和规范
├── website/                        # 其他项目
│   ├── frontend.md
│   └── backend.md
└── README.md
```

## ccplugin/features.md 示例

```markdown
# CCPlugin 项目 - 功能开发

## 2026年1月 完成任务

### [P0] TASK-015 重新设计任务管理系统 ✓

- **类别**: 功能重构
- **说明**:
  将 task-skills 插件从 Python 脚本方式改为基于 hooks 和文件系统的设计，提高任务管理的可用性和灵活性。新系统不依赖数据库，完全使用 Markdown 文件存储任务。

- **关键交付物**:
  - .claude/task/ 目录结构 (todo.md, in-progress.md, done.md, archive/)
  - @${CLAUDE_PLUGIN_ROOT} 的 multi-file skills 文档 (SKILL.md, reference.md)
  - 三个 hooks 配置 (SessionStart, UserPromptSubmit, Stop)
  - examples/ 文件夹，包含完整的样例文件
  - 删除了所有旧的 Python 脚本

- **关联提交**: 7494344, abc123def

### [P1] TASK-016 优化版本更新脚本 ✓

- **类别**: 工具优化
- **说明**:
  适配新的插件目录结构（plugins/code/、plugins/style/），使脚本能够递归扫描所有 plugin.json 文件。现在能正确处理所有 27 个插件（13+12+2）。

- **关键交付物**:
  - scripts/update_version.py 更新
  - 支持递归扫描 \*\*/.claude-plugin/plugin.json
  - 改进的错误处理和显示格式

- **关联提交**: 7494344

### [P2] TASK-017 整理插件文档 ✓

- **类别**: 文档
- **说明**:
  为 plugins/code/ 和 plugins/style/ 目录分别创建 README.md，提供导航和选择指南。更新了主项目 CLAUDE.md 以反映新的目录结构。

- **关键交付物**:
  - plugins/code/README.md - 13 个代码插件的导航
  - plugins/style/README.md - 12 个样式插件的选择指南
  - CLAUDE.md - 更新的架构文档

- **关联提交**: adb3f0e

## 2026年1月初 完成任务

### [P1] TASK-018 插件 Skills 结构化重建 ✓

- **类别**: 重构
- **说明**:
  将所有 17 个插件（code 和 style）的 skills 改造为 multi-file 结构，遵循 Anthropic 的进度披露（Progressive Disclosure）模式。

- **关键交付物**:
  - 17 个插件都有完整的 SKILL.md（300-400 行）
  - 每个插件有 reference.md（详细规范）
  - 创建了 .claude/skills/plugin-skills-authoring.md（编写规范）

- **关联提交**: 8e464de, cfe4d0e
```

## 说明

### 为什么需要归档？

1. **保持清洁** - 避免 `done.md` 文件变得过大
2. **历史记录** - 保留项目历史，便于后续参考
3. **组织管理** - 按项目/模块组织，易于查找

### 何时归档？

- 当 `done.md` 中的任务超过 5 个时考虑归档
- 完成一个主要里程碑时进行集中归档
- 定期（如每月）整理一次

### 如何组织？

1. **按项目** - 每个项目一个文件夹
2. **按模块** - 每个模块/功能域一个文件（如 features.md、infrastructure.md）
3. **按月份** - 可在文件中添加月份标题组织内容

### 文件命名规范

- 使用 kebab-case：`backend.md`, `ui-components.md`
- 清晰描述内容：`api-development.md` 而不是 `tasks.md`
- 一致的扩展名：`.md`

---

参考：[reference.md](../reference.md) | [SKILL.md](../SKILL.md)
