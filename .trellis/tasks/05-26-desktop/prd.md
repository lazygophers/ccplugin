# 完全移除 @desktop 相关内容

## Goal

彻底清除项目中所有 @desktop 相关的代码、文档、配置和记忆记录，因为 desktop 应用已废弃，相关内容不再需要维护。

## What I already know

### 需删除的文件清单

**Memory 文件 (3 个)**:
- `.claude/memory/desktop-event-driven-architecture.md` — 事件驱动架构规则
- `.claude/memory/desktop-testing.md` — 测试体系约定
- `.claude/memory/desktop-code-quality-2026-04-05.md` — 代码质量规则

**文档文件**:
- `docs/brainstorms/2026-03-20-desktop-app-brainstorm.md` — 早期设计讨论

**Spec 文件 (新发现)**:
- `.trellis/spec/backend/` 整个目录（包含 error-handling.md、quality-guidelines.md、tauri-patterns.md 等，全部引用 desktop memory）

**desktop/ 目录**:
- 整个 Tauri 应用目录（包含 src-tauri、node_modules、构建产物等）

### 需编辑的文件清单

**CLAUDE.md**:
- 删除第 5-7 行：三条 Desktop 相关的复盘防回归规则

**MEMORY.md**:
- 删除第 26-28 行：三个 desktop memory 文件的索引
- 删除第 36 行：`**@desktop 架构**` 核心约定段落
- 删除第 49-52 行：复盘防回归中的 Desktop 相关内容

**plugins/tools/cortex/docs/_internal/contributing.md**:
- 删除第 223 行：保留 @desktop 风格的提及

### 约束条件

- 所有变更自动暂存（CLAUDE.md §1）
- 不需要 bump `.version`（仅文档/记忆清理，无用户可见功能变更）
- 删除 desktop/ 目录会移除大量文件（构建产物、node_modules），需确认 git 正确处理

## Assumptions (temporary)

- desktop/ 目录无其他项目引用
- 三个 memory 文件无其他文档引用（MEMORY.md 之外）
- .venv 中的 pygments 自动生成内容不需处理

## Open Questions

无（范围已明确）

## Requirements

1. **删除文件**:
   - 删除 `.claude/memory/desktop-event-driven-architecture.md`
   - 删除 `.claude/memory/desktop-testing.md`
   - 删除 `.claude/memory/desktop-code-quality-2026-04-05.md`
   - 删除 `docs/brainstorms/2026-03-20-desktop-app-brainstorm.md`
   - 删除整个 `.trellis/spec/backend/` 目录（backend spec 已废弃）
   - 删除整个 `desktop/` 目录

2. **编辑 CLAUDE.md**:
   - 删除第 3-7 行（`## 复盘防回归规则` 整个段落，因为剩余内容全是 Desktop）

3. **编辑 MEMORY.md**:
   - 删除 Memory 索引中的三个 desktop 文件条目（第 26-28 行）
   - 删除核心约定中的 `**@desktop 架构**` 段落（第 36 行）
   - 删除复盘防回归中的 Desktop 相关内容（第 49-52 行）

4. **编辑 plugins/tools/cortex/docs/_internal/contributing.md**:
   - 删除第 223 行提及保留 @desktop 风格的语句

## Acceptance Criteria

- [ ] 所有 @desktop 相关 memory 文件已删除
- [ ] desktop/ 目录已删除
- [ ] CLAUDE.md 不再包含 Desktop 相关规则
- [ ] MEMORY.md 不再索引或描述 @desktop 内容
- [ ] cortex contributing.md 不再提及 @desktop
- [ ] `grep -r "@desktop" --include="*.md"` 仅返回 .venv 中的 pygments（不相关）
- [ ] Git status 显示所有删除已暂存

## Definition of Done

- 所有文件删除/编辑完成
- 所有变更自动暂存
- 无需测试（纯文档清理）
- 无需更新文档（本身就是清理文档）

## Out of Scope

- 不处理 .venv 中 pygments 的自动生成内容（与项目无关）
- 不 bump `.version`（无用户可见功能变更）
- 不创建 git commit（仅暂存，等待用户确认）

## Technical Notes

### 文件位置
- Memory: `.claude/memory/desktop-*.md`
- 文档: `CLAUDE.md`, `.claude/rules/MEMORY.md`, `plugins/tools/cortex/docs/_internal/contributing.md`
- 应用目录: `desktop/`
- 早期设计: `docs/brainstorms/2026-03-20-desktop-app-brainstorm.md`

### 删除顺序
1. 先删除独立文件（memory、brainstorm、desktop/）
2. 再编辑引用文件（CLAUDE.md、MEMORY.md、contributing.md）
3. 最后验证无残留引用

### 搜索命令（用于验证）
```bash
grep -r "@desktop" --include="*.md" . | grep -v ".venv"
find . -type f -name "*desktop*" | grep -v node_modules | grep -v ".git" | grep -v ".venv"
```
