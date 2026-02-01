# Git 提交信息规范

## Conventional Commits 格式

```
<type>: <subject>

<body>

<footer>
```

### 类型（type）

| 类型       | 说明      | 示例                     |
| ---------- | --------- | ------------------------ |
| `feat`     | 新功能    | feat: 添加用户认证功能   |
| `fix`      | 缺陷修复  | fix: 修复登录超时问题    |
| `docs`     | 文档更新  | docs: 更新 API 文档      |
| `style`    | 代码格式  | style: 统一代码缩进      |
| `refactor` | 代码重构  | refactor: 优化数据库查询 |
| `test`     | 测试相关  | test: 添加单元测试       |
| `chore`    | 构建/工具 | chore: 更新依赖版本      |

## 提交信息示例

### ✅ 好的提交信息

```bash
# 清晰、具体、遵循规范
gitcommit -m "feat: 添加用户认证功能"
gitcommit -m "fix: 修复登录超时问题"
gitcommit -m "docs: 更新 API 文档"
gitcommit -m "refactor: 优化数据库查询性能"
```

详细提交信息示例：

```
feat: 添加用户认证功能

实现用户注册、登录和会话管理
- 用户注册：邮箱验证
- 用户登录：JWT Token 认证
- 会话管理：Token 刷新机制

Closes #123
```

### ❌ 不好的提交信息

```bash
# 模糊、不具体、不遵循规范
gitcommit -m "update"
gitcommit -m "fix bug"
gitcommit -m "done"
gitcommit -m "tmp"
```

## 提交粒度最佳实践

### ✅ 好的提交（单一职责）

- "feat: 添加用户注册功能"
- "feat: 添加用户登录功能"
- "test: 添加认证测试"
- 每个提交只做一件事
- 提交可以独立审查和回滚

### ❌ 不好的提交（过大）

- "feat: 添加用户模块"（太宽泛，包含注册、登录、验证等多个功能）
- 一个提交包含多个不相关的变更
- 难以审查和定位问题

## 提交前检查清单

- [ ] 提交信息格式正确（`<type>: <subject>`）
- [ ] 提交类型选择正确
- [ ] 提交信息清晰具体
- [ ] 提交粒度适当（单一职责）
- [ ] 暂存区内容与提交信息一致
- [ ] 不包含敏感信息（.env、credentials.json）
- [ ] 不包含调试代码（console.log、print）
- [ ] 文件大小合理（避免 > 10MB）

## 提交策略

### 分批提交流程

```bash
# 1. 添加并提交第一个功能
gitadd feature1.py
gitcommit -m "feat: 添加功能1"

# 2. 添加并提交第二个功能
gitadd feature2.py
gitcommit -m "feat: 添加功能2"

# 3. 添加测试代码
gitadd tests/
gitcommit -m "test: 添加功能测试"

# 4. 推送到远程
gitpush
```

### 快速提交流程

```bash
# 当所有变更属于同一主题时
gitcommit -am "feat: 初始化项目"
gitpush
```

## 常见问题

**Q: 提交信息应该有多详细？**
A: 一行概括（Subject）应该 < 50 字符，清晰说明做了什么。详细说明放在 Body 部分。

**Q: 如何处理提交失败？**
A:

1. 检查错误信息
2. 修复问题（如移除敏感文件、修复 hooks 错误）
3. 创建新提交（不要使用 amend）

**Q: 提交信息可以中文吗？**
A: 可以。团队可以选择中文或英文，保持一致即可。建议优先选择英文以便国际协作。
