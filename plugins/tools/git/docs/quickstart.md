# 快速开始

Git 插件快速入门指南。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin git@ccplugin-market
```

## 基本使用

### 首次提交

```bash
# 1. 更新 .gitignore
/update-ignore

# 2. 提交所有变更
/commit-all "feat: 初始化项目"

# 3. 推送到远程
git push -u origin master
```

### 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/user-auth

# 2. 开发并提交
git add src/auth/
/commit "feat: 添加用户注册功能"

git add tests/
/commit "test: 添加注册功能测试"

# 3. 推送并创建 PR
git push -u origin feature/user-auth
/create-pr
```

### 更新 PR

```bash
# 1. 根据审查反馈修改
vim src/auth/login.py
git add src/auth/login.py
/commit "fix: 修复登录验证逻辑"

# 2. 推送并更新 PR
git push
/update-pr 123
```

## 命令速查

| 命令 | 描述 |
|------|------|
| `/commit-all "msg"` | 提交所有变更 |
| `/commit "msg"` | 提交暂存区变更 |
| `/update-ignore` | 更新 .gitignore |
| `/create-pr` | 创建 PR |
| `/update-pr <n>` | 更新 PR 描述 |

## 提交信息规范

### 格式

```
<type>: <subject>
```

### 常用类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `test` | 测试相关 |
| `refactor` | 代码重构 |

### 示例

```bash
/commit-all "feat: 添加用户认证功能"
/commit "fix: 修复登录超时问题"
/commit "docs: 更新 API 文档"
```

## 下一步

- 阅读 [命令系统](commands.md) 了解所有命令
- 查看 [技能系统](skills.md) 学习规范
- 参考 [最佳实践](best-practices.md) 提高效率
