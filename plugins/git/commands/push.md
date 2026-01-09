---
name: Git 推送代码
description: 安全地推送本地提交到远程仓库
allowed-tools: Bash(git:*)
---

## 知识库

**code-review-standards**：推送前代码质量验证

## 当前 Git 状态

- 当前分支：!`git branch --show-current`
- 远程仓库：!`git remote -v`
- 本地领先提交：!`git log origin/$(git branch --show-current 2>/dev/null || echo main)..HEAD --oneline 2>/dev/null || echo "无远程跟踪"`
- 远程领先提交：!`git log HEAD..origin/$(git branch --show-current 2>/dev/null || echo main) --oneline 2>/dev/null || echo "无远程跟踪"`

## 任务

安全地将本地提交推送到远程仓库。

## 执行步骤

1. **检查本地提交**：无提交→提示无需推送
2. **检查远程变更**：有新提交→建议先pull | 确认覆盖→警告force push风险
3. **执行推送**：正常→`git push origin <branch>` | 首次→`git push -u origin <branch>` | Force（谨慎）→需明确确认
4. **验证推送**：`git status`确认成功，显示推送提交数量

## 推送失败处理

如果推送失败（网络连接失败或超时）：

1. **设置代理后重试**
   ```bash
   # 方式 1：设置环境变量（当前会话）
   export http_proxy=http://127.0.0.1:7890
   export https_proxy=http://127.0.0.1:7890
   git push

   # 方式 2：单次命令使用代理
   http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890 git push

   # 取消代理（当前会话）
   unset http_proxy
   unset https_proxy
   ```

2. **其他常见错误**
   - 认证失败：检查 SSH 密钥或凭据
   - 分支冲突：先 `git pull`，解决冲突后再推送

## 注意事项

推送前确保本地测试通过 | 避免force push到主分支（main/master）| 有冲突先解决再推送 | 网络失败时尝试设置环境变量代理
