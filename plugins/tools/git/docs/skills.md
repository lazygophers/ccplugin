# 技能系统

Git 插件提供三个核心技能，覆盖提交、PR 和 Issue 管理。

## 技能列表

| 技能 | 描述 | 自动激活 |
|------|------|----------|
| `commit` | 提交规范 | Git 操作时 |
| `pr` | PR 规范 | PR 操作时 |
| `issue` | Issue 规范 | Issue 操作时 |

## commit - 提交规范

### Conventional Commits

```
<type>: <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加用户认证 |
| `fix` | Bug 修复 | fix: 修复登录问题 |
| `docs` | 文档更新 | docs: 更新 README |
| `style` | 代码格式 | style: 格式化代码 |
| `refactor` | 代码重构 | refactor: 优化查询 |
| `test` | 测试相关 | test: 添加测试 |
| `chore` | 构建/工具 | chore: 更新依赖 |

### 提交信息规则

**好的提交信息**：

```
feat: 添加用户认证功能

- 实现登录/注册
- 添加 JWT 支持
- 添加单元测试

Closes #123
```

**不好的提交信息**：

```
update
fix bug
done
WIP
```

### 提交粒度

**推荐**：

- 一个提交做一件事
- 提交信息清晰描述变更
- 变更范围适中

**避免**：

- 一个提交包含多个不相关变更
- 提交信息过于简单或模糊
- 变更范围过大

## pr - PR 规范

### PR 标题

```
<type>: <description>
```

示例：

```
feat: 添加用户认证功能
fix: 修复登录超时问题
docs: 更新 API 文档
```

### PR 描述模板

```markdown
## Summary

简要描述本次变更的目的和内容。

## Changes

- 变更点1
- 变更点2
- 变更点3

## Test Plan

- [ ] 测试项1
- [ ] 测试项2
- [ ] 测试项3

## Screenshots

如有必要，添加截图。

## Related Issues

Closes #123
```

### PR 质量标准

**必须包含**：

- [ ] 清晰的标题
- [ ] 完整的描述
- [ ] 测试计划
- [ ] 关联 Issue

**推荐包含**：

- [ ] 变更截图
- [ ] 性能影响说明
- [ ] 破坏性变更说明

## issue - Issue 规范

### Issue 标题

```
<type>: <description>
```

示例：

```
bug: 登录页面无法加载
feature: 添加用户导出功能
docs: API 文档缺少示例
```

### Issue 描述模板

```markdown
## Description

详细描述问题或需求。

## Steps to Reproduce (Bug)

1. 步骤1
2. 步骤2
3. 步骤3

## Expected Behavior

描述期望的行为。

## Actual Behavior

描述实际的行为。

## Environment

- OS: macOS 14.0
- Browser: Chrome 120
- Version: 1.0.0

## Additional Context

其他相关信息。
```

### Issue 标签

| 标签 | 说明 |
|------|------|
| `bug` | Bug 报告 |
| `feature` | 功能请求 |
| `docs` | 文档问题 |
| `good first issue` | 适合新手 |
| `help wanted` | 需要帮助 |
| `priority: high` | 高优先级 |
