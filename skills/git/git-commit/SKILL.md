---
name: git-commit
description: 提交变更前自动识别并排除临时/备份/日志/构建产物等不该进版本库的文件,再合理更新忽略清单(项目通用噪声→.gitignore、个人机器噪声→全局 excludesFile/.git/info/exclude),疑似密钥则拒交并报警,最后生成规范 commit message 提交。仅本地提交,不 push、不开 PR。

argument-hint: "[commit message]"
---

# git-commit — 干净提交 + 智能忽略

提交前先把噪声挡在版本库外,再写规范信息。核心是**排除清单 + 忽略落点决策**两件事,git 提交本身是末端。

## 🔴 硬规(guardrail,违反即失效)

1. **不主动 push**。改做什么:只 `add` + `commit`,推送需用户显式指令后再执行。
2. **疑似密钥/凭证一律不提交**。改做什么:命中即 🔴 STOP 报警并列出文件,提示用户 rotate 凭证 + 视情况清史(忽略只挡未追踪,已泄露的不会因为忽略而消失)。检测清单见 [references/secrets-and-cleanup.md](references/secrets-and-cleanup.md)。

## 正向配方(原否定项改写)

- 删除已追踪文件(`git rm --cached`)前,先 `git rm -n --cached` dry-run 出清单,报给用户确认后再执行——该改动会传播到协作者工作区。
- 逐个 `git add <path>` 添加,路径取自上一步 `git status --porcelain` 的输出,避免噪声与密钥被一并裹挟进暂存区。

## 工作流

### 1. 看改动

```bash
git status --porcelain
git diff --stat        # 已追踪改动量
```

**完成判据**:已拿到本次全部改动的文件清单(含新增/修改/删除)与已追踪改动的行数统计,可据此逐项分类。

### 2. 分类:应提交 vs 噪声

逐个文件归类。高频噪声/保留清单/落点判据的完整分类表**唯一真值源**见 [references/noise-and-ignore.md](references/noise-and-ignore.md)(§1 噪声分类、§2 应保留的锁文件与元文件、§3 忽略落点决策)。

**完成判据**:清单中每个文件都已归入「应提交」或「噪声(待排除)」二选一,无遗漏项;命中 §1 密钥类 pattern 的文件已单独标记转硬规 2 处理。

### 3. 忽略落点决策(用户核心诉求)

排除的噪声要不要写忽略清单、写到哪,判据见 [references/noise-and-ignore.md](references/noise-and-ignore.md) §3。

- 追加前先 `git check-ignore -v <path>`:有输出=已被某规则忽略(附来源档),不重复加。
- 只追加命中的 pattern,不塞百行模板。

**完成判据**:每条本次新增的忽略 pattern 都已确认 `git check-ignore -v` 此前无输出(未被覆盖),且已写入 §3 判据对应的落点文件。

### 4. 已被追踪的噪声

`.gitignore` 只管未追踪文件;已追踪的需从索引移除(**必带 `--cached`**,否则删本地文件):

```bash
git rm -n --cached <path>   # dry-run 预演,列清单待用户确认(见正向配方)
git rm --cached <path>      # 单文件;目录加 -r
# 再把 pattern 写入对应忽略落点
```

**完成判据**:本次判定为「已追踪噪声」的每个文件,索引移除清单均已经用户确认;确认后已实际执行 `git rm --cached` 且对应忽略 pattern 已落盘。

### 5. 暂存 + 提交

```bash
git diff --cached | grep -nE -- '-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_|glpat-|sk-(ant-|proj-)?'  # 密钥预扫,命中 STOP
git add <应提交项...>        # 逐个加(见正向配方)
git diff --cached --quiet && echo "无暂存改动,不空提交"   # 防空提交
git commit -m "<type>(<scope>): <subject>"
```

commit message:**用户已在入参给出 message → 直接采用,不再自造**;未给才自动生成——`feat/fix/docs/refactor/chore/test/perf/build/ci` + 祈使句主题,**先 `git log --oneline -20` 采样项目风格再写**(本项目实测:type/scope 用英文、subject 用中文,如 `feat(trellisx): 异步等待...`)。规范细则见 [references/secrets-and-cleanup.md](references/secrets-and-cleanup.md) §message。

**完成判据**:密钥预扫命令已跑且无命中(或命中已按硬规 2 处置并中止);`git commit` 已成功返回新 commit hash,或已明确报告「无可提交内容」。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 命中疑似密钥 | 🔴 STOP,列文件报警,`git restore --staged <file>` 移出 | 已追踪 → 提示密钥已入历史,须 rotate + `git filter-repo` 清史(不代执行) |
| `git add` 报路径不存在/特殊字符 | 用 `--` 分隔 + 引号:`git add -- '<path>'` | 逐文件 add,跳过报错项并列出 |
| 无实质改动(全是噪声) | 报「无可提交内容,已更新忽略清单」,不空提交 | 用户坚持 → `--allow-empty` 需显式要求 |
| pre-commit hook 拦截失败 | 读 hook 输出,修根因(lint/format)后重提 | 修不动 → 报原文,`--no-verify` 仅在用户明示时使用 |
| 大文件(>50MB)误入暂存 | 提示 Git LFS(`git lfs track`)或移出 | 用户坚持 → 警告仓库膨胀不可逆后再交 |
| 整文件虚假 diff(CRLF/mode) | `.gitattributes` `* text=auto` / `core.fileMode false` | 确认非真内容改动则不提交该项 |

## 诚实边界

- 只挡**未追踪**噪声与新增忽略;已在历史里的密钥/大文件本 skill 不清史(需用户跑 `git filter-repo`)。
- 噪声 pattern 是高频项非穷尽,冷门产物目录需用户补充判断。
- 密钥检测是启发式(文件名 + 内容线索),可能漏报/误报;精确规则以 gitleaks/GitHub secret-scanning 为准。
- 不改 commit 历史(不 amend/rebase),要改历史走 git-rebase 或用户显式指令。
