---
description: Git 推送代码 - 安全地推送本地提交到远程仓库
argument-hint: []
allowed-tools: Bash(git:*)
model: haiku
---

# push

## 命令描述

安全地将本地提交推送到远程仓库。自动检查本地和远程的提交状态，处理首次推送、远程冲突和网络异常等情况。

## 工作流描述

1. **检查本地提交**：确认本地有待推送的提交
2. **检查远程状态**：验证远程是否有新的提交
3. **冲突处理**：如有冲突，提示需要先 pull
4. **执行推送**：推送本地提交到远程仓库

## 命令执行方式

### 使用方法

```bash
git-skills push
```

### 执行时机

- 完成本地提交，需要推送到远程
- 定期同步本地变更到远程仓库
- 为后续创建 PR 做准备

### 执行参数

无参数，自动检测当前分支并推送。

### 命令说明

- 自动识别当前分支
- 首次推送自动设置上游分支（`-u origin <branch>`）
- 检查并提示远程有新提交的情况
- 处理网络连接失败（支持代理设置）

## 相关Skills（可选）

参考 Git 操作技能：`@${CLAUDE_PLUGIN_ROOT}/skills/git/SKILL.md`

## 依赖脚本

```bash
# 使用 git-skills 原生命令
```

## 示例

### 基本用法

```bash
# 推送当前分支到远程
git-skills push

# 首次推送，设置上游分支
git-skills push -u origin <branch>
```

### 首次推送分支

```bash
# 首次推送自动设置上游分支
git-skills checkout -b feature/new-feature
# ... 开发和提交 ...
git-skills push -u origin feature/new-feature
```

### 遇到冲突处理

```bash
# 如提示远程有新提交
git-skills pull origin <branch-name>
# 解决冲突后
git-skills push
```

## 检查清单

在推送前，确保满足以下条件：

- [ ] 已提交所有需要推送的变更
- [ ] 提交信息符合规范
- [ ] 本地测试已通过（推荐）
- [ ] 无需要保留的未提交改动

## 注意事项

**推送成功标志**：
- 输出显示 `git status` 为干净状态
- 本地分支领先提交数量变为 0

**常见问题处理**：
- **网络失败**：命令会提示设置代理的方式
  ```bash
  # 设置代理后重试
  export http_proxy=http://127.0.0.1:7890
  export https_proxy=http://127.0.0.1:7890
  git-skills push

  # 取消代理
  unset http_proxy
  unset https_proxy
  ```

- **认证失败**：检查 SSH 密钥或凭据配置
- **远程有新提交**：需要先执行 `git pull` 解决冲突

**禁止操作**：
- ❌ 不要使用 `--force` 或 `--force-with-lease` 推送（除非非常确定）
- ❌ 推送到主分支（main/master）前应确认代码质量
- ❌ 不要推送包含敏感信息的提交

## 其他信息

### 推送状态说明

推送命令会输出以下信息：

- **当前分支**：显示正在推送的分支名
- **远程仓库**：显示推送目标（origin）
- **本地领先提交**：显示有多少个提交待推送
- **远程领先提交**：提示是否需要 pull
- **推送结果**：显示成功或失败信息

### 推送失败处理步骤

1. **读取错误信息**：查看具体的失败原因
2. **分类错误类型**：
   - 网络错误 → 检查网络和代理
   - 认证错误 → 检查密钥或凭据
   - 冲突错误 → 执行 pull 解决冲突
3. **执行对应解决方案**
4. **重试推送**

### 代理配置

对于需要代理的网络环境：

```bash
# 临时设置代理（当前会话）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 永久配置 git（建议）
git-skills config --global http.proxy http://127.0.0.1:7890
git-skills config --global https.proxy http://127.0.0.1:7890

# 取消代理
unset http_proxy
unset https_proxy
```

### 与完整工作流配合

```bash
# 1. 开发和提交
git-skills add .
git-skills commit -m "feat: 新功能"

# 2. 推送到远程
git-skills push

# 3. 创建 PR（使用 GitHub CLI）
gh pr create --title "feat: 新功能" --body "描述内容"
```

### 性能考虑

- 小型仓库推送通常很快
- 大型仓库或网络慢时可能需要较长时间
- 考虑使用 Git LFS 处理大型二进制文件
