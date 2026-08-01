# 按 writing-great-skills 优化 skills/ 全部 13 个 skill — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:

- [ ] `skills/` 下全部 13 个 SKILL.md (git 4 + design 2 + code-quality 3 + project 2 + skill-dev 2) 按 Matt Pocock `writing-great-skills` 方法论完成诊断与改写
- [ ] `skills/git/` 4 个先作试点跑通并收敛出 checklist，其余 9 个照 checklist 推，不各自重推方法论
- [ ] 消除跨 skill 重复：git-merge 与 git-rebase 的方向无关共有内容 (前置检查 / 实质改动判据 / 冲突循环骨架) 收敛到单一真值源；design 两份的四平台目录与通用目录之间同理
- [ ] 每份 description 剪到 leading word 前置、去掉 body 已有的身份复述，降低常驻 context load
- [ ] 6 类 failure mode 逐个排查并修复；negation 表述改为正向配方 (硬 guardrail 保留但配「改做什么」)
- [ ] predictability 以「同一 prompt 连跑 3 次质量门答案一致」证实，而非主观判断

## 边界
范围内 / 范围外 (非目标) / 已知约束:

- [ ] 范围内：`skills/` 下全部 13 个 SKILL.md 及其 `references/` 子文件的改写、拆分、合并、删除
- [ ] 范围内：`skills/skill-dev/skill-dev/references/skill-quality-checklist.md` 并入本轮方法论 (并入既有文件，不新建第四份 checklist)
- [ ] 范围内：调研产物落 `.skein/task/git-skills-optimize/research/`
- [ ] 范围外：`plugins/tools/` 下 7 个已发布插件一律不动
- [ ] 约束：13 个 skill 的对外行为语义不得改变 (触发场景、硬规、失败兜底的实际效果保持)，本轮只改表达与结构
- [ ] 约束：四个 git skill 保持 model-invoked，不上 `disable-model-invocation: true` (用户裁定；改触发方式即改语义)
- [ ] 约束：中文同义触发词删不删由实测定夺 —— `git-commit` 作实验组，删后口语触发率下降则还原，不降才对其余 12 份照删
- [ ] 约束：方法论词汇统一用 `writing-great-skills` 那套 (predictability / information hierarchy / progressive disclosure / leading word / pruning / 6 failure modes)，不另起评分体系
- [ ] 约束：中文正文；frontmatter 字段与触发词写法以官方规范为准

## 验收标准
可执行、可核对的完成断言 (逐条):

- [x] 13 个 SKILL.md 均已改写并落盘，`git diff --stat skills/` 显示 13 份均有实质改动
- [x] 每份 frontmatter `name` 与目录名一致，`arguments:` 数组已删 (与 `argument-hint` 同一信息写两处)，`argument-hint` 保留
- [x] 每份 description 中不存在同一 branch 的同义改写 —— 除非 s1 的触发词实测证明中文同义词确实撑触发率，该结论一体适用于 13 份
- [x] git-merge 与 git-rebase 之间：`--ours`/`--theirs` 反转表已建且两侧互指；方向无关的共有内容只在一处定义
- [x] `recovery.md` 一对保持不合并 (merge 侧 abort/reset/revert/ff 与 rebase 侧 backup/reflog/force-with-lease 是真实差异)
- [x] 13 份逐句跑过 no-op 测与 relevance 测，删除记录写入 checklist 的「实测删除项」小节
- [x] 每份的 negation 表述已逐条审过：保留的硬 guardrail 均配有正向「改做什么」，非 guardrail 的否定句已改写为正向
- [x] 每份每个工作流步骤末有 checkable 且 exhaustive 的完成判据
- [x] 每份改写后跑质量门 (stdin 形式，见 design)，返回非空且能正确说出该 skill 的触发场景与主流程
- [x] 每份主流程那问**连跑 3 次答案一致**
- [x] 质量门对 git-merge 与 git-rebase 的 `--ours` / `--theirs` 方向判定回答正确 (两者语义相反，是最易错项；改写前基线两份均答对，答错即回归)
- [x] 方法论已并入 `skills/skill-dev/skill-dev/references/skill-quality-checklist.md`，未新建第四份 checklist，与该文件既有条目冲突处已收敛
- [x] `research/` 下调研文档齐备，事实声明均带出处

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list git-skills-optimize`)
