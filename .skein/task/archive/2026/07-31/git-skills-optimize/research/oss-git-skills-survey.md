# 开源 git 类 Claude Code skill 横向对比 (调研留档)

样本 5 个, 4 个独立来源 (obra/superpowers 贡献 2 个)。全部为公开 GitHub 仓库, 抓取方式: `curl raw.githubusercontent.com` + `gh api repos/*/git/trees`。行数 = SKILL.md 实际行数 (`wc -l`, 2026-07-29 抓取的 main 分支)。

## 结论摘要 (对本仓 git/ 四技能可落地的准则)

1. 主流体量 167–378 行, 本仓 82–96 行属**偏轻**一档 — 官方 500 行上限远未触顶, 说明「变长」不是风险, 「变散」才是。
2. description 两种流派: ①**触发词穷举流** (conventional-commits / claude-commit-skill / pr-reviewer, 把 "commit"、"/commit"、"review this PR"、URL 形态全列出来) ②**when-clause 流** (superpowers 的 `Use when …  - ensures …`, 单句、无关键词罗列)。前者对 model-invoked 触发率友好, 后者更省 token 且不易误触。
3. 有副作用的 git 动作普遍**不靠模型自主判断**: conventional-commits 用 `user-invocable: false` 反过来让它只由模型注入 (它是纯规则、无副作用); 而 pr-reviewer / finishing-a-development-branch 用「两阶段审批 / 选项菜单」把副作用挡在用户确认后 — 即在 skill body 内建人工闸门, 而非依赖 frontmatter。
4. references/ 分层是主流: 5 个样本里 4 个有 `references/`, 且都只有一层, 与官方「引用一层深」一致。
5. 脚本化只在 I/O 重的场景出现 (pr-reviewer 的 3 个 python 脚本抓 PR 数据/生成评审文件/发内联评论); 纯「消息格式规则」类 (conventional-commits) 零脚本, 纯文本规则表。
6. 失败处理写法有清晰共识: **失败即停, 禁自动重试, 禁 `--no-verify`, 禁 force-push** — claude-commit-skill 与 finishing-a-development-branch 措辞几乎一致。
7. superpowers 独有的两张表值得直接借鉴: 「Quick Reference 决策矩阵」(选项 × 副作用) 与 **「Common Rationalizations 借口→事实表」**(直接对着 premature completion / negation 类 failure mode 下药)。
8. 「Announce at start」模式 (superpowers 两个 skill 都有: `I'm using the X skill to …`) 让 skill 是否真被触发可观测, 便于调 description。
9. Edge Cases 表 (claude-commit-skill: 二进制文件/lock 文件/超大 diff/submodule/hook 失败/暂存区空) 是把「散落的 if」收敛成一处的有效手法, 避免步骤段落被条件分支撑爆。
10. 反面样本: pr-reviewer 在 SKILL.md 里带 §Table of Contents + §Purpose + §When to Use + 完整 Scripts Reference, 378 行里相当一部分是**对自己的描述**与脚本 usage 复述 — 属 sprawl + duplication, 本仓不要学。

## 对比表

| 来源 | 行数 | description 写法 | 结构分层 | 脚本化程度 | 失败处理 / 用户确认写法 |
|---|---|---|---|---|---|
| [inprojectspl/conventional-commits](https://github.com/inprojectspl/conventional-commits) `SKILL.md` | 209 | YAML 块标量 `>-` 多行; 穷举触发短语 ('commit','create a commit','save changes','write a commit message','stage and commit'); 声明强制项 (英文/禁 Co-Authored-By); `user-invocable: false` | SKILL.md + `references/specification.md` (一层) | 无脚本, 纯规则 + 7 个 example | 无用户确认 (纯规则集); 用 `## CRITICAL — Forbidden Patterns` 8 条 NEVER 兜底 |
| [mustafakbaser/claude-commit-skill](https://github.com/mustafakbaser/claude-commit-skill) `SKILL.md` | 223 | 单行长句; 含斜杠形态触发词 `"/commit"`, `"/commit --all"`, `"commit my changes"`; 说明双模式 (single/batch) | SKILL.md + `references/grouping-algorithm.md` (一层) + `bin.js` 安装器 | 无执行脚本, 但把 git 命令并行块写死 | 交互问 (scope / 语言) 用 **Question + Options** 结构; batch 模式 Step 3 先「Present Plan」再执行; 「If any commit fails: stop immediately, report the error, do NOT continue」+ 「Never use `--no-verify` unless the user explicitly requests it」; 末尾 Edge Cases 表 7 行 |
| [SpillwaveSolutions/pr-reviewer-skill](https://github.com/SpillwaveSolutions/pr-reviewer-skill/blob/main/SKILL.md) | 378 | YAML 块标量 `>`; 触发短语 + PR URL 形态 `github.com/*/pull/*`; 额外自定义键 `version`/`category`/`triggers`/`author`/`license` (非官方字段) | SKILL.md + `references/` ×4 (review_criteria / gh_cli_guide / scenarios / troubleshooting) + `scripts/` ×3 | 高: `fetch_pr_data.py` / `generate_review_files.py` / `add_inline_comment.py`, SKILL.md 只写调用行 | **两阶段审批**: 「Nothing is posted to GitHub until explicit approval with `/send` or `/send-decline`」; 中间产物落盘成评审文件供人工编辑 (verifiable intermediate output) |
| [obra/superpowers](https://github.com/obra/superpowers) `skills/using-git-worktrees/SKILL.md` | 167 | 单行 when-clause: `Use when starting feature work that needs isolation … - ensures an isolated workspace exists via native tools or git worktree fallback`; 无关键词罗列 | 单文件, 无 references | 无脚本; 内嵌 bash 探测片段 (`git rev-parse --git-common-dir` 等) | Step 0 先检测已隔离状态防重复创建; submodule 误判专门加 guard; 「ask for consent before creating a worktree」 |
| [obra/superpowers](https://github.com/obra/superpowers) `skills/finishing-a-development-branch/SKILL.md` | 201 | 同上流派 (when-clause) | 单文件, 无 references | 无脚本; 每个选项给可复制 bash 块 | 测试不绿即停; 「present exactly these 3 options」菜单; 销毁类操作要求**用户逐字输入 `discard`**; force-push 仅在明确请求下; 末尾 Quick Reference 矩阵 + Common Rationalizations 借口表 |
| (对照) 本仓 `skills/git/*` | 82–96 | 中文触发词 | 单文件 | — | — |

## 证据明细

### conventional-commits — 触发词穷举 + 只由模型调用
```yaml
name: conventional-commits
description: >-
  Formats all git commit messages following the Conventional Commits v1.0.0 specification.
  Activates when the user asks to 'commit', 'create a commit', 'save changes', 'write a commit message',
  'stage and commit', or any git commit-related task. …
user-invocable: false
```
— repo:inprojectspl/conventional-commits SKILL.md:1-12

禁令段写法 (全 NEVER 前缀, 每条带对照示例):
> 2. **NEVER use past tense** in the description — Write "add feature" not "added feature"
> 6. **NEVER exceed 72 characters** on the first line
— 同上 SKILL.md:107-129

### claude-commit-skill — 交互 + 失败即停
> **Question:** "Both staged and unstaged changes detected. What would you like to commit?" **Options:** …
— repo:mustafakbaser/claude-commit-skill SKILL.md:45-49

> **If any commit fails** (pre-commit hook, etc.): stop immediately, report the error, do NOT continue to next group. Never use `--no-verify` unless the user explicitly requests it.
— 同上 SKILL.md:200

Edge Cases 表 (节选):
| Scenario | Handling |
|---|---|
| Lock files | Always group with their manifest file, never standalone commit |
| Pre-commit hook failure | Report clearly, do NOT retry, suggest user fix and re-run `/commit` |
— 同上 SKILL.md:213-223

引用分层: `Read references/grouping-algorithm.md for the detailed grouping procedure.` + 紧跟 4 行 Quick summary — 即「引用外置 + 就地留摘要」, 保证不读引用也能兜底 (同上 SKILL.md:158-168)。

### pr-reviewer — 两阶段审批 + 脚本化
> **IMPORTANT**: This skill uses a **two-stage approval process**. Nothing is posted to GitHub until explicit approval with `/send` or `/send-decline`.
— repo:SpillwaveSolutions/pr-reviewer-skill SKILL.md:65

> Use `fetch_pr_data.py` to automatically collect all PR information:
> `python scripts/fetch_pr_data.py <pr_url> [--output-dir <dir>] [--no-clone]`
— 同上 SKILL.md:74-99

引用表 (一层, 4 个文件):
| `references/review_criteria.md` | Complete checklist covering functionality, security, testing, and more |
— 同上 SKILL.md:257-266

### superpowers using-git-worktrees — 先探测再动作
> **Core principle:** Detect existing isolation first. Then use native tools. Then fall back to git. Never fight the harness.
> **Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."
— repo:obra/superpowers skills/using-git-worktrees/SKILL.md:11-15

> **Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule
— 同上

### superpowers finishing-a-development-branch — 菜单 + 借口表
> **Core principle:** Verify tests → Detect environment → Present options → Execute choice → Clean up.
> **Normal repo and named-branch worktree — present exactly these 3 options**
— repo:obra/superpowers skills/finishing-a-development-branch/SKILL.md:10, 55

Common Rationalizations (节选, 借口 → 事实):
| "Tests passed earlier this session" | Run the suite on the tree you are about to integrate. A green run only proves the tree it ran on. |
| "They obviously want it merged" | Integration is your human partner's decision. Present the menu and wait. |
| "'Yeah, get rid of it' counts as confirmation" | Only the typed word `discard` authorizes deletion. |
| "The push was rejected — force-push will fix it" | A rejected push means the remote moved. Investigate; force-push only on your human partner's explicit request. |
— 同上 SKILL.md:189-201

## 缺口 / 未取到

- 未找到公开的 **git-merge / git-rebase 专项** skill (最接近的是 abubakarsiddik31/claude-skills-collection 索引里提到的「resolving in-progress git merge/rebase conflicts」条目, 该条目仅见于聚合列表描述, **未取到其 SKILL.md 原文**; 尝试通道: WebSearch ×2、gh search code (返回空 `[]`)、GitHub code search API (401 需鉴权))。→ merge/rebase 两个 skill 只能靠 commit/finish-branch 的写法迁移, 无同题先例。
- `gh search code` 对 `filename:SKILL.md "git rebase"` 返回空; 未再扩轮。
- 无 agent-reach → 社区平台 (Reddit/HN/X) 上的实践讨论未覆盖。
