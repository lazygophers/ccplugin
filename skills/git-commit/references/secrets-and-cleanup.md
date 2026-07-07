# 密钥检测 · 已追踪清理 · message 规范 —— git-commit 详表

主流程见 [../SKILL.md](../SKILL.md)。

## §secrets 密钥/凭证检测

启发式两层:**文件名** + **内容线索**。命中任一 → 🔴 STOP,不 add、不用忽略了事。

### 文件名线索
`.env`(及 `.env.*`,放行 `.env.example/.sample`)、`*.pem` `*.key` `*.p12` `*.pfx` `*.keystore`、`id_rsa*` `id_dsa*` `id_ecdsa*` `id_ed25519*` `*.ppk`、`*credential*` `*secret*` `*password*`、`.npmrc` `.pypirc` `.netrc` `.aws/credentials` `.ssh/`、`serviceAccount*.json` `*-key.json`(GCP)。

### 内容线索(暂存区预扫)
提交前跑:
```bash
git diff --cached | grep -nE -- \
'-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|gho_|ghs_|glpat-[A-Za-z0-9_-]{20}|sk-(ant-|proj-)?[A-Za-z0-9]|xox[baprs]-|AIza[0-9A-Za-z_-]{35}|eyJ[A-Za-z0-9_-]{10,}\.'
```
覆盖:PEM 私钥、AWS AccessKey、GitHub token(`ghp_/gho_/ghs_`)、GitLab PAT(`glpat-`)、OpenAI/Anthropic key(`sk-`)、Slack token(`xox`)、Google API key(`AIza`)、JWT(`eyJ`)。

### 命中处置
1. 未追踪 → `git restore --staged <file>`(若已 add),报警列文件,建议写 `.gitignore` 并用 `.env.example` 占位。
2. **已追踪**(密钥历史里已有)→ 提示:忽略挡不住已入库的,须 ① rotate 泄露的凭证 ② `git filter-repo` / BFG 清历史。本 skill 不代执行清史(破坏历史,需用户显式授权)。
3. 是启发式,可能漏/误报;精确扫描建议 `gitleaks detect` 或启用 GitHub secret-scanning。

## §cleanup 已被追踪的噪声移除

`.gitignore` 只挡未追踪文件;已 `git add` 过的噪声需从索引移除:
```bash
git rm -n --cached <path>          # 🔴 硬规 3:先 dry-run,列清单待用户确认
git rm --cached <path>             # 单文件
git rm -r --cached <dir>           # 目录(如误提交的 node_modules/)
# 移除后把 pattern 写入对应忽略落点(见 noise-and-ignore.md §3)
```
⚠️ **必带 `--cached`**:不带会连本地文件一起删。`git rm --cached` 会在协作者下次 pull 时删除他们的对应文件(改动传播),故硬规 3 要求先报清单确认。

## §message commit message 规范

### 格式
```
<type>(<scope>): <subject>

[body 可选]
[footer 可选,如 BREAKING CHANGE / Closes #123]
```

### type 取值
`feat`(功能) `fix`(修 bug) `docs`(文档) `style`(格式,不影响逻辑) `refactor`(重构) `perf`(性能) `test`(测试) `build`(构建/依赖) `ci`(流水线) `chore`(杂项)。

### 写法要点
- subject 用祈使句/概括句,不加句号,建议 ≤ 50 字符(中文酌情)。
- **先 `git log --oneline -20` 采样本项目实际风格再写**——各项目约定不同。本 ccplugin 实测:type/scope 用英文、subject 用中文(如 `feat(trellisx): 异步等待 MUST 输出任务清单表格`)。
- 多项无关改动 → 拆多个 commit,不要一个 commit 塞杂物。
- body 解释「为什么」而非「改了什么」(diff 已说明改了什么)。
