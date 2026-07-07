# 平台识别 · 内容生成 · 命令全参 —— git-pr 详表

主流程见 [../SKILL.md](../SKILL.md)。

## §platform 平台识别细则

### 从 remote URL 判定
```bash
git remote get-url origin
```
| URL 形态 | 平台 | 工具 |
| --- | --- | --- |
| `git@github.com:` `https://github.com/` | GitHub | `gh` |
| `https://<company>.ghe.com/` GH Enterprise | GitHub | `gh`(已 `gh auth login --hostname`) |
| `git@gitlab.com:` `https://gitlab.com/` | GitLab | `glab` |
| `https://gitlab.<company>.com/` 自建 GitLab | GitLab | `glab`(需 `GITLAB_HOST`) |
| SSH alias / 无 host(如 `git@myalias:repo`) | 不确定 | 读 `~/.ssh/config` 解析真实 host;仍不明 → STOP 问用户 |

### 自建 GitLab / GH Enterprise
- `glab` 认自建域名靠环境变量 `GITLAB_HOST` 或 `glab auth login --hostname <host>` 存的配置。远端是自建域名但 `glab` 未配 → 提示用户先 `glab auth login --hostname <host>`,不硬跑(会连错到 gitlab.com)。
- `gh` Enterprise 同理:`gh auth login --hostname <host>`。

### ⚠️ RTK wrapper 拦截
本机 `/opt/homebrew/bin/rtk` 会 wrap `gh`/`glab` 子命令,可能改写 stdout / 吞 exit code,导致解析 JSON、判断成败失真。需要**原始 JSON / 精确 exit code** 时 bypass wrapper:
```bash
command gh pr view --json mergeable   # command 前缀绕过函数/alias
# 或用绝对路径
/opt/homebrew/bin/gh pr view --json mergeable
```
拿不到干净输出 → 让用户网页确认,别基于被改写的输出下结论。

### 工具缺失
`which gh` / `which glab` 为空 → 报安装指引(`brew install gh` / `brew install glab`),不硬跑。

## §content 内容生成

### 拉取范围(三点 vs 双点)
```bash
git log --oneline "origin/$BASE...HEAD"   # ✅ 三点:symmetric,列本分支相对共同祖先的独有提交
git diff --stat "origin/$BASE...HEAD"
```
- 三点 `A...B` 在 `git log` 里 = 两分支对称差集(自 merge-base 起的双方独有提交),开 PR 看「本分支带来什么」正合适;`git diff A...B` = 从 merge-base 到 B 的改动(即本分支净变更),不含 base 分支新提交的干扰。
- **别用双点 `origin/$BASE..HEAD` 拉 diff 正文**:base 若领先会算漏,范围偏。

### 标题
- 单 commit → 直接用该 commit 主题。
- 多 commit → 概括本分支整体意图(不是罗列每条 commit)。

### 正文结构
```markdown
## 变更
- <按提交/模块分条列做了什么>

## 影响范围
- <git diff --stat 涉及的关键文件/模块>

## 验证
- <相关测试/手动验证方式;无则写「待补」,禁编造已通过>
```

### 复用仓库模板
存在则优先套用,把上面结构填进模板对应段:
- GitHub:`.github/PULL_REQUEST_TEMPLATE.md` 或 `.github/PULL_REQUEST_TEMPLATE/*.md`
- GitLab:`.gitlab/merge_request_templates/*.md`

## §create 命令全参数

### GitHub `gh pr create`
```bash
gh pr create \
  --base "$BASE" \
  --head "$(git branch --show-current)" \
  --title "<标题>" \
  --body "<正文>" \
  [--draft] [--reviewer user1,user2] [--assignee @me] [--label bug] [--milestone M1]
```
- `--fill` 可用 commit 自动填标题正文(省手写,但不如结构化正文);`--web` 打开网页编辑。
- 回传:命令 stdout 末行即 PR URL。

### GitLab `glab mr create`
```bash
glab mr create \
  --target-branch "$BASE" \
  --title "<标题>" \
  --description "<正文>" \
  [--draft] [--reviewer user1] [--assignee @me] [--label bug] \
  [--remove-source-branch] [--squash]
```
- `--fill` 同 gh。
- 回传:stdout 的 MR URL。
