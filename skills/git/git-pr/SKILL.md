---
name: git-pr
description: 创建 PR/MR。自动识别远端是 GitHub(用 gh)还是 GitLab(用 glab),从 commit 与 diff 自动写标题正文,通过 CLI 提交,回传最终 PR/MR 链接;--base/参数指定目标分支;提交后检查 CI action 与合并冲突,有问题则提醒用户并给解决方案。触发词:「创建 pr」「提 mr」「发 pull request」「开合并请求」。

argument-hint: "[--base <目标分支>]"
arguments: [--base (可选, PR/MR 目标分支; 缺省取仓库默认分支)]
---

# git-pr — 自动开 PR/MR

识别平台 → 写内容 → 提交 → 回传链接 → 查 CI/冲突并给方案。深表见 references/。

## 🔴 硬规

1. **提交前当前分支必须已推到远端**。未推 → 先 `git push -u origin <branch>`(开 PR 的必要前提,非越权 push)。
2. **不自动合并 PR/MR**。只创建,merge 归用户决定。
3. **CI 失败或有冲突 → 必用 AskUserQuestion 问用户是否解决**,不自主改代码。

## 工作流

### 1. 识别平台 + 目标分支

```bash
git remote get-url origin
```

| 远端 host | 工具 | 默认目标分支取法 |
| --- | --- | --- |
| `github.com` / GH Enterprise | `gh` | `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` |
| `gitlab.*` / 自建 GitLab | `glab` | `glab repo view` 取 default branch |
| 其它/识别不了 | 🔴 STOP | AskUserQuestion 问用户平台与工具 |

- 目标分支优先级:用户 `--base <branch>` 参数 > 仓库默认分支。
- 工具缺失(`which gh`/`which glab` 空)→ 报安装指引,不硬跑。
- ⚠️ **自建 GitLab / GH Enterprise 域名识别、`glab` 的 `GITLAB_HOST` 配置、RTK wrapper 拦截 gh/glab 输出**等坑,见 [references/platform-and-content.md](references/platform-and-content.md) §platform。

### 2. 生成 PR/MR 内容

```bash
BASE=<目标分支>
git log --oneline "origin/$BASE...HEAD"     # 三点:本分支相对 merge-base 的提交(非双点)
git diff --stat "origin/$BASE...HEAD"        # 改动概览
```

标题 + 结构化正文(变更/影响范围/验证)的写法、仓库 PR 模板复用,见 [references/platform-and-content.md](references/platform-and-content.md) §content。

### 3. 提交

```bash
# GitHub
gh pr create --base "$BASE" --head "$(git branch --show-current)" --title "<标题>" --body "<正文>"
# GitLab
glab mr create --target-branch "$BASE" --title "<标题>" --description "<正文>"
```

回传 CLI 输出的 **PR/MR URL**(必须给到用户)。命令全参数(draft/reviewer/label 等)见 [references/platform-and-content.md](references/platform-and-content.md) §create。

### 4. 提交后:查 CI + 冲突 → 🔴 CHECKPOINT

```bash
# GitHub
gh pr checks                                   # CI 状态
gh pr view --json mergeable,mergeStateStatus   # 冲突/可合并
# GitLab
glab ci status
glab mr view
```

| 检查结果 | 动作 |
| --- | --- |
| CI 全绿 + 可合并 | 报「PR/MR 已建、CI 通过、无冲突」+ URL,完成 |
| CI action 失败 | 取失败 job 日志摘要,AskUserQuestion:是否要我修?附诊断+建议方案 |
| 有合并冲突 | AskUserQuestion:是否把目标分支 merge/rebase 进来解冲突?(指路 git-merge/git-rebase) |
| `mergeable=UNKNOWN` | GitHub 还在后台算,**稍等重查**一次再判(别当无冲突),见 [references/ci-and-conflict.md](references/ci-and-conflict.md) §mergeable |
| CI 还在跑 | 报当前 pending,给「稍后 `gh pr checks`/`glab ci status` 复查」提示 |

CI 字段含义、失败日志取法、冲突判定细节见 [references/ci-and-conflict.md](references/ci-and-conflict.md)。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| `gh`/`glab` 未登录 | 提示 `gh auth login` / `glab auth login`(用户自己在终端跑) | 未登录不重试,STOP 待用户授权 |
| 当前分支未推远端 | `git push -u origin <branch>` 后重试 create | push 被拒(需先 pull)→ 指路 git-rebase/git-merge 同步 |
| PR/MR 已存在(同分支) | 改为回传现有 PR/MR URL,不重复创建 | 列现有 PR 状态供用户决定 |
| 目标分支不存在 | 列远端分支,AskUserQuestion 让用户选正确 base | 用默认分支并明确告知 |
| CI 失败但日志取不到 | 给 PR 页 URL 让用户在网页看 checks | 标「CI 失败,日志需网页查」,不瞎猜原因 |
| 自建 GitLab 域名 | `glab` 已配 `GITLAB_HOST` 则直接用 | 未配 → 提示 `glab auth login --hostname <host>` |
| gh/glab 输出被 RTK wrapper 改写 | 用原始二进制路径 bypass(见 reference) | 仍乱 → 让用户网页确认 URL |

## 反例黑名单(禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 创建后直接 `gh pr merge`/`glab mr merge` | 越权合并 | 只创建,合并待用户 |
| 2 | CI 失败自作主张改代码 | 未经确认改动 | AskUserQuestion 先问 |
| 3 | PR 正文空/只有一行 | 评审无上下文 | 结构化正文(变更/影响/验证) |
| 4 | 编造 PR 里没有的「测试已通过」 | 虚假声明 | 验证栏据实填或标「待补」 |
| 5 | 识别不出平台就硬套 gh | 命令必败 | STOP 问用户 |
| 6 | 用双点 `origin/$BASE..HEAD` 拉正文 | 漏算 base 领先的提交,范围偏 | 用三点 `...` |

## 诚实边界

- 只支持 GitHub(gh)/GitLab(glab);Bitbucket/Gitea/自建其它平台不覆盖,识别不到即 STOP。
- 不解 CI 失败根因,只取日志摘要 + 建议;是否修由用户定。
- PR 正文质量取决于 commit 质量,提交零散/message 空则正文只能据 diff 粗写。
- 不碰 PR 合并、不改分支保护规则。
