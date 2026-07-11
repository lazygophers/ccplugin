# git 技能分类

Git 工作流 skill 合集: 提交、合并、rebase、PR。

| skill | 用途 |
|---|---|
| [git-commit](git-commit/) | 规范 commit, 排除噪声文件与疑似密钥 |
| [git-merge](git-merge/) | 把源分支 merge 进当前分支, 保留合并历史 |
| [git-rebase](git-rebase/) | 线性变基到源分支, 强制备份分支兜底 |
| [git-pr](git-pr/) | 自动识别 GitHub/GitLab, 创建 PR/MR |

## 路由

- 本地提交 → git-commit (不开 PR、不 push)
- 保留分叉历史 → git-merge
- 线性历史 → git-rebase
- 开评审 → git-pr
