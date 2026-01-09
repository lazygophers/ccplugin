---
name: 准备 Pull Request
description: 基于当前分支变更生成 PR 标题和描述
allowed-tools: Bash(git:*), Read
---

## 知识库

**code-review-standards**：代码审查标准 | **documentation-standards**：PR 文档最佳实践

## 当前分支信息

- 当前分支：!`git branch --show-current`
- 基准分支：main（或根据项目约定）
- 变更统计：!`git diff main...HEAD --stat 2>/dev/null || git diff master...HEAD --stat 2>/dev/null || echo "无法确定基准分支"`
- 提交列表：!`git log main..HEAD --oneline 2>/dev/null || git log master..HEAD --oneline 2>/dev/null || echo "无法确定基准分支"`

## 任务

生成高质量 Pull Request 标题和描述。

### PR 标题格式

```text
类型(范围): 简洁描述变更
```

示例：`feat(用户): 添加用户登录功能` | `fix(API): 修复分页查询返回错误` | `refactor(数据库): 优化查询性能`

### PR 描述格式

```markdown
## 变更摘要

[1-3 句话描述 PR 做了什么]

## 技术实现

- [关键技术点 1]
- [关键技术点 2]

## 测试说明

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试场景：[描述]

## 相关 Issue

Closes #[issue-number]（如适用）

## 注意事项

[如有破坏性变更、迁移步骤等，在此说明]
```

### 执行步骤

1. 分析所有提交变更内容
2. 生成清晰 PR/MR 标题
3. 编写详细 PR/MR 描述
4. 创建 PR/MR：
   - **GitLab**：`glab mr create --title "标题" --description "描述"`
   - **GitHub**：`gh pr create --title "标题" --body "描述"`

### 要求

标题 ≤50 字符 | 描述覆盖所有重要变更 | 测试说明具体可执行 | 使用简体中文
