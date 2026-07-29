---
name: git-pr
description: 把当前分支提交为 PR/MR——自动识别远端是 GitHub(用 gh)还是 GitLab(用 glab),据 commit 与 diff 生成标题正文并提交,回传 PR/MR 链接;`--base` 可指定目标分支,缺省取仓库默认分支;提交后自动查 CI 状态与合并冲突,有问题时用 AskUserQuestion 给方案候用户裁决。

argument-hint: "[--base <目标分支>]"
---

# git-pr — 自动开 PR/MR

真正费工夫的在两头:提交前确认已推到远端,提交后必查 CI 与冲突并给方案;中间那句「开 PR」本身只是一行 CLI 调用。gh/glab 平台差异全部下沉 references/,本文件只留分叉指针。

## 🔴 硬规(唯一 guardrail)

**不主动 push**。改做什么:只在提交 PR/MR 前才 `git push -u origin <branch>`(开 PR 的必要前提,非越权 push);此外任何时机、任何其它分支都不推,推送范围以外一律留给用户显式指令。

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
- ⚠️ 自建 GitLab / GH Enterprise 域名识别、`glab` 的 `GITLAB_HOST` 配置、RTK wrapper 拦截 gh/glab 输出等坑,唯一真值源见 [references/platform-and-content.md](references/platform-and-content.md) §platform。

✅ **完成判据**:平台已判定为 GitHub/GitLab 之一(或已 STOP 问用户),对应工具 `gh`/`glab` 已确认可用,`$BASE` 已定(用户传参或已取到仓库默认分支)。

### 2. 生成 PR/MR 内容

```bash
BASE=<目标分支>
git log --oneline "origin/$BASE...HEAD"     # 三点:本分支相对 merge-base 的提交(非双点)
git diff --stat "origin/$BASE...HEAD"        # 改动概览
```

标题 + 结构化正文(变更/影响范围/验证)的写法、仓库 PR 模板复用,唯一真值源见 [references/platform-and-content.md](references/platform-and-content.md) §content。

✅ **完成判据**:已拿到三点 range 的 commit 列表与 diff 概览,据此写出的标题 + 结构化正文已备好(或已套用仓库既有 PR/MR 模板填完对应段)。

### 3. 提交(只创建,不合并)

```bash
# GitHub
gh pr create --base "$BASE" --head "$(git branch --show-current)" --title "<标题>" --body "<正文>"
# GitLab
glab mr create --target-branch "$BASE" --title "<标题>" --description "<正文>"
```

提交后止步于「已创建」——是否合并、何时合并留给用户在平台上按按钮决定,本 skill 不碰。回传 CLI 输出的 **PR/MR URL**(必须给到用户)。命令全参数(draft/reviewer/label 等)见 [references/platform-and-content.md](references/platform-and-content.md) §create。

✅ **完成判据**:`gh pr create`/`glab mr create` 已成功返回退出码 0 且 PR/MR URL 已回传给用户(或已判定同分支已有 PR/MR,转用现有 URL)。

### 4. 查 CI + 冲突 → 🔴 CHECKPOINT

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
| `mergeable=UNKNOWN` | GitHub 还在后台算,稍等重查一次再判(别当无冲突),见 [references/ci-and-conflict.md](references/ci-and-conflict.md) §mergeable |
| CI 还在跑 | 报当前 pending,给「稍后 `gh pr checks`/`glab ci status` 复查」提示 |

CI 字段含义、失败日志取法、冲突判定细节见 [references/ci-and-conflict.md](references/ci-and-conflict.md)。

✅ **完成判据**:已按上表逐项判定并给出对应动作;CI 失败或有冲突时已实际发出 AskUserQuestion 让用户裁决(是否修/是否解冲突),未自行改代码或替用户合并。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| `gh`/`glab` 未登录 | 提示 `gh auth login` / `glab auth login`(用户自己在终端跑) | 未登录不重试,STOP 待用户授权 |
| PR/MR 已存在(同分支) | 改为回传现有 PR/MR URL,不重复创建 | 列现有 PR 状态供用户决定 |
| 目标分支不存在 | 列远端分支,AskUserQuestion 让用户选正确 base | 用默认分支并明确告知 |
| CI 失败但日志取不到 | 给 PR 页 URL 让用户在网页看 checks | 标「CI 失败,日志需网页查」,不瞎猜原因 |

## 诚实边界

- 只支持 GitHub(gh)/GitLab(glab);Bitbucket/Gitea/自建其它平台不覆盖,识别不到即 STOP。
- 不解 CI 失败根因,只取日志摘要 + 建议;是否修由用户定。
- PR 正文质量取决于 commit 质量,提交零散/message 空则正文只能据 diff 粗写。
- 不碰 PR 合并、不改分支保护规则。
