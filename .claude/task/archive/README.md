# 任务存档 (Archive)

已完成的任务存档，按项目/功能模块组织。

## 目录结构

```
archive/
├── project-name/
│   ├── module-a.md    (模块A的所有完成任务)
│   └── module-b.md    (模块B的所有完成任务)
├── plugin-X/
│   └── features.md    (插件X的功能开发)
└── infrastructure/
    └── devops.md      (基础设施和运维)
```

## 存档规则

1. **按项目/模块组织** - 使用项目名或模块名作为文件夹
2. **文件内容** - 每个 `.md` 文件包含该项目/模块的所有完成任务
3. **文件大小** - 确保文件大小可控（建议单个文件<500KB）
4. **不记录时间** - 避免按月份组织，应按功能模块组织

## 何时存档

- 一个会话内完成的任务应该在 `done.md` 中保留一段时间
- 当 `done.md` 超过200行时，考虑存档到相应的项目/模块文件中
- 或按照用户的存档规则定期整理

## 示例

### ccplugin/features.md

```markdown
# CCPlugin 项目 - 功能开发

## 2026年1月

### [P0] 重新设计任务管理系统 ✓

- **完成时间**: 2026-01-18
- **类别**: 功能重构
- **说明**: 将task插件从Python脚本方式改为基于hooks和文件系统的设计
- **关键交付物**:
  - .claude/task/ 目录结构 (todo.md, in-progress.md, done.md, archive/)
  - @plugins/task 的multi-file skills文档
  - SessionStart, UserPromptSubmit, Stop hooks
- **关联提交**: abc123def456
```

## 浏览存档

要查找历史任务：

1. 确定相关的项目/模块
2. 打开相应的 `.md` 文件
3. 使用搜索功能查找特定任务
