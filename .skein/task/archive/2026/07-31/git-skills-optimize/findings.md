# git-skills-optimize — 调研收敛

## 主题一: 官方 Agent Skills 编写规范 (research/official-skill-authoring.md)

**结论**: 官方硬约束只有 4 条数字线 (name ≤64 字符/小写连字符/与目录同名; description ≤1024 字符非空; body ≤500 行; 引用一层深), 其余全是写法建议。本仓 git/ 四技能 82–96 行, 距 500 行上限极宽裕 — 优化方向不是「砍字数」, 是「按 information hierarchy 重排 + 补 predictability 缺口」。

**关键依据**
- frontmatter 必填仅 name/description; 可选 license/allowed-tools/metadata/compatibility — platform.claude.com best-practices §Skill structure
- description 必须第三人称 + 「做什么 + 何时用」+ 具体触发词; 官方给的 git commit 范例: `Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.`
- Claude Code 扩展 invocation 开关 = writing-great-skills「invocation 二选」的落地形态: `disable-model-invocation: true` (description 不进 context, 仅斜杠调用, 官方点名适用 `/commit` `/deploy` 这类有副作用的) / `user-invocable: false` (仅模型调) — code.claude.com/docs/en/skills
- skill 内容一次性注入且**后续回合不重读** → 全程规则要写成 standing instructions 而非一次性步骤; allowed-tools 授权下一条用户消息即失效
- 嵌套引用会触发 `head -100` 部分读取导致信息不全 → references 只允许一层; >100 行的 reference 必须带 TOC
- 自由度分级: 脆弱/顺序敏感操作走「照抄这条命令, 禁改 flag」低自由度写法 (git rebase/merge 正属此类)
- 交付前官方 checklist 10 条可直接当本次验收项

**未决**: anthropic.com engineering blog 未取到 (WebSearch 未命中具体 URL); 社区平台数据未覆盖 (无 agent-reach)。

## 主题二: 开源 git 类 skill 横向对比 (research/oss-git-skills-survey.md)

**结论**: 5 个样本 (4 独立来源) 体量 167–378 行, 全部 >本仓 2 倍。共识做法: ①references/ 一层分层 (5 中 4 有) ②有副作用动作靠 body 内的人工闸门 (两阶段审批 / 选项菜单 / 逐字 `discard`) 而非模型自觉 ③失败即停、禁自动重试、禁 `--no-verify`、禁 force-push ④脚本化只在 I/O 重场景出现, 纯规则类零脚本。description 分「触发词穷举流」与「when-clause 单句流」两派。

**关键依据**
- obra/superpowers `finishing-a-development-branch` 的 **Common Rationalizations 借口→事实表** 与 **Quick Reference 决策矩阵** 是对 premature completion / negation 类 failure mode 最直接的解药, 本仓 merge/rebase 可直接借鉴形态
- superpowers 两个 skill 都有 `Announce at start: "I'm using the X skill…"` — 让触发可观测
- claude-commit-skill 的 Edge Cases 表 (lock 文件/二进制/超大 diff/hook 失败/暂存区空) 把条件分支从步骤段收敛到一张表, 防步骤 sprawl
- claude-commit-skill 引用外置同时就地留 4 行 Quick summary — 不读引用也能兜底, 契合三级阶梯
- pr-reviewer 378 行是反面样本: TOC/Purpose/When to Use/Scripts usage 复述 = sprawl + duplication, 不要学
- pr-reviewer 用了非官方 frontmatter 键 (version/category/triggers/author) — 不建议跟

**未决**: 公开生态里**没有 git-merge / git-rebase 专项 skill 先例** (gh search code 空 + GitHub code search API 401); 这两个 skill 的改写只能从 commit / finishing-branch 迁移写法。
