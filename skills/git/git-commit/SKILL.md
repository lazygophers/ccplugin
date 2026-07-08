---
name: git-commit
description: 提交变更前先自动识别并排除临时/备份/日志/构建产物等不该进版本库的文件,再合理更新忽略清单(项目通用噪声→.gitignore、个人机器噪声→全局 excludesFile/.git/info/exclude),疑似密钥则拒交并报警,最后生成规范 commit message 提交。触发词:「提交」「commit」「把改动交了」「暂存并提交」。仅本地提交,不 push、不开 PR。
when_to_use: '有工作区改动要 commit 时。禁用于开 PR/MR(→git-pr)、rebase(→git-rebase)、merge(→git-merge)。'
argument-hint: "[commit message]"
arguments: [commit message (可选, 用户指定则采用; 缺省按项目风格自动生成)]
---

# git-commit — 干净提交 + 智能忽略

提交前先把噪声挡在版本库外,再写规范信息。核心是**排除清单 + 忽略落点决策**两件事,git 提交本身是末端。

## 🔴 硬规(违反即失效)

1. **不 push**。只 `add` + `commit`,推送归用户显式指令。
2. **疑似密钥/凭证一律不提交**。命中即 🔴 STOP 报警,不 add、不忽略了事(忽略只挡未追踪,已泄露的要用户 rotate + 清史)。检测清单见 [references/secrets-and-cleanup.md](references/secrets-and-cleanup.md)。
3. **删已追踪文件(`git rm --cached`)前必确认**。改动会传播到协作者工作区,报清单待批准。
4. **禁 `git add -A` / `git add .` 一把梭**,逐项 add,防裹挟噪声与密钥。

## 工作流

### 1. 看改动

```bash
git status --porcelain
git diff --stat        # 已追踪改动量
```

### 2. 分类:应提交 vs 噪声

逐个文件归类。**高频噪声速判**(完整分语言全表见 [references/noise-and-ignore.md](references/noise-and-ignore.md) §1):

| 类别 | 典型 pattern | 处置 |
| --- | --- | --- |
| 临时/备份 | `*.tmp` `*.bak` `*.orig` `*.rej` `*~` `*.swp` `.#*` | 排除 |
| 日志 | `*.log` `logs/` `npm-debug.log*` | 排除 |
| 构建产物 | `dist/` `build/` `out/` `target/` `*.pyc` `__pycache__/` `.next/` `*.class` `*.o` | 排除 |
| 依赖目录 | `node_modules/` `vendor/` `.venv/` `venv/` | 排除 |
| 覆盖率/缓存 | `coverage/` `.coverage` `.pytest_cache/` `.ruff_cache/` `.mypy_cache/` | 排除 |
| OS/编辑器 | `.DS_Store` `._*` `Thumbs.db` `.idea/` `*.iml` | 排除(个人级,落全局) |
| **密钥/凭证** | `.env` `.env.*`(除 `.env.example`) `*.pem` `*.key` `id_rsa*` `*credentials*` | 🔴 STOP,走硬规 2 |

> ⚠️ **锁文件应提交,非噪声**:`package-lock.json` `pnpm-lock.yaml` `yarn.lock` `uv.lock` `Cargo.lock` `poetry.lock` `composer.lock` `Gemfile.lock` `go.sum`。误删破坏 CI 可复现。完整保留清单见 [references/noise-and-ignore.md](references/noise-and-ignore.md) §2。

### 3. 忽略落点决策(用户核心诉求)

排除的噪声要不要写忽略清单、写到哪。git 三档 exclude 源(细则 + `git check-ignore` 去重命令见 [references/noise-and-ignore.md](references/noise-and-ignore.md) §3):

| 判据 | 落点 | 理由 |
| --- | --- | --- |
| 项目所有人都产生(构建/依赖/覆盖率/`.env`) | `.gitignore` | 随 clone 分发,防他人误提交 |
| 只你的机器/编辑器/OS(`.DS_Store` `.idea/` `*.swp`) | 全局 `core.excludesFile` 或 `.git/info/exclude` | 本地生效,不污染项目 |
| 已被上一档覆盖 | 不重复写 | 先 `git check-ignore -v <path>` 查来源 |

- 追加前先 `git check-ignore -v <path>`:有输出=已被某规则忽略(附来源档),不重复加。
- 全局档查法:`git config --get core.excludesfile`。
- 只追加命中的 pattern,不塞百行模板。白名单写 `dir/*` + `!dir/keep`(父目录整个忽略后无法再 include,见 reference §3)。

### 4. 已被追踪的噪声

`.gitignore` 只管未追踪文件;已追踪的需从索引移除(**必带 `--cached`**,否则删本地文件):

```bash
git rm -n --cached <path>   # 先 dry-run 预演(🔴 硬规 3 报清单确认)
git rm --cached <path>      # 单文件;目录加 -r
# 再把 pattern 写入对应忽略落点
```

### 5. 暂存 + 提交

```bash
git diff --cached | grep -nE -- '-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_|glpat-|sk-(ant-|proj-)?'  # 密钥预扫,命中 STOP
git add <应提交项...>        # 逐个加,禁 -A
git diff --cached --quiet && echo "无暂存改动,不空提交"   # 防空提交
git commit -m "<type>(<scope>): <subject>"
```

commit message:**用户已在入参给出 message → 直接采用,不再自造**;未给才自动生成——`feat/fix/docs/refactor/chore/test/perf/build/ci` + 祈使句主题,**先 `git log --oneline -20` 采样项目风格再写**(本项目实测:type/scope 用英文、subject 用中文,如 `feat(trellisx): 异步等待...`)。规范细则见 [references/secrets-and-cleanup.md](references/secrets-and-cleanup.md) §message。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 命中疑似密钥 | 🔴 STOP,列文件报警,`git restore --staged <file>` 移出 | 已追踪 → 提示密钥已入历史,须 rotate + `git filter-repo` 清史(不代执行) |
| `git add` 报路径不存在/特殊字符 | 用 `--` 分隔 + 引号:`git add -- '<path>'` | 逐文件 add,跳过报错项并列出 |
| 无实质改动(全是噪声) | 报「无可提交内容,已更新忽略清单」,不空提交 | 用户坚持 → `--allow-empty` 需显式要求 |
| pre-commit hook 拦截失败 | 读 hook 输出,修根因(lint/format)后重提 | 修不动 → 报原文,禁 `--no-verify` 绕过除非用户明示 |
| 大文件(>50MB)误入暂存 | 提示 Git LFS(`git lfs track`)或移出 | 用户坚持 → 警告仓库膨胀不可逆后再交 |
| 整文件虚假 diff(CRLF/mode) | `.gitattributes` `* text=auto` / `core.fileMode false` | 确认非真内容改动则不提交该项 |

## 反例黑名单(禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | `git add -A` / `git add .` 一把梭 | 裹挟噪声与密钥进库 | 按分类逐项 add |
| 2 | 提交后 `git push` | 越权,推送需用户指令 | 只提交 |
| 3 | 密钥当普通文件提交 | 泄露不可逆 | STOP 报警 |
| 4 | 个人编辑器噪声写进项目 `.gitignore` | 污染团队清单 | 归全局 excludesFile / `.git/info/exclude` |
| 5 | 塞百行 `.gitignore` 模板 | 大量用不上的 pattern 噪声 | 只加命中的 |
| 6 | `git rm --cached` 不确认直接删 | 传播删除,协作者丢文件 | 先 `-n` 预演 + 报清单确认 |
| 7 | 忽略锁文件 / `git rm --cached` 锁文件 | 破坏 CI 可复现 | 锁文件是应提交项 |

## 诚实边界

- 只挡**未追踪**噪声与新增忽略;已在历史里的密钥/大文件本 skill 不清史(需用户跑 `git filter-repo`)。
- 噪声 pattern 是高频项非穷尽,冷门产物目录需用户补充判断。
- 密钥检测是启发式(文件名 + 内容线索),可能漏报/误报;精确规则以 gitleaks/GitHub secret-scanning 为准。
- 不改 commit 历史(不 amend/rebase),要改历史走 git-rebase 或用户显式指令。
