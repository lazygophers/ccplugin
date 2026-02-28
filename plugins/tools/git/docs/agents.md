# 代理系统

Git 插件提供两个专业代理，覆盖开发和审查场景。

## 代理列表

| 代理 | 描述 | 适用场景 |
|------|------|----------|
| `git-developer` | Git 开发专家 | Git 操作、工作流管理 |
| `git-reviewer` | Git 审查专家 | 提交评估、PR 审查 |

## git-developer - Git 开发专家

### 职责

- 执行 Git 操作
- 管理工作流
- 解决 Git 问题
- 优化 Git 配置

### 技能

- `commit` - 提交规范
- `pr` - PR 规范

### 使用示例

```
帮我创建一个新分支并推送到远程
```

```
解决合并冲突
```

### 常见操作

**创建分支**：

```bash
git checkout -b feature/new-feature
git push -u origin feature/new-feature
```

**合并分支**：

```bash
git checkout main
git merge feature/new-feature
git push
```

**解决冲突**：

```bash
# 查看冲突文件
git status

# 编辑冲突文件
# 然后标记为已解决
git add <conflicted-file>
git commit
```

## git-reviewer - Git 审查专家

### 职责

- 评估提交质量
- 审查 PR 完整性
- 检查代码规范
- 提供改进建议

### 技能

- `commit` - 提交规范
- `pr` - PR 规范
- `issue` - Issue 规范

### 使用示例

```
审查最近的提交是否符合规范
```

```
评估 PR #123 的质量
```

### 审查清单

**提交审查**：

- [ ] 提交信息格式正确
- [ ] 变更范围合理
- [ ] 无敏感信息泄露
- [ ] 无大文件提交

**PR 审查**：

- [ ] PR 标题清晰
- [ ] PR 描述完整
- [ ] 变更范围合理
- [ ] 测试覆盖充分
- [ ] 文档已更新

## 调用方式

代理会在相关场景自动激活，也可以显式请求：

```
使用 Git 开发专家帮我管理分支
```

```
使用 Git 审查专家审查我的提交
```
