# 按 writing-great-skills 优化 skills/git/ 四个 skill (试点) — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:

- [ ] `skills/git/` 下 4 个 SKILL.md (git-commit / git-merge / git-pr / git-rebase) 按 Matt Pocock `writing-great-skills` 方法论完成诊断与改写，predictability (同一 process 每次复现) 可观察地提升
- [ ] 消除跨 skill 重复：git-merge 与 git-rebase 的共有内容 (前置检查 / 冲突判定 / 实质改动判据 / 恢复手段) 收敛到单一真值源
- [ ] 每份 description 剪到「一 branch 一 trigger + leading word 前置」，去掉 body 已有的身份复述，降低常驻 context load
- [ ] 6 类 failure mode 逐个排查并修复；negation 表述改为正向配方 (硬 guardrail 保留但配「改做什么」)
- [ ] 产出一份可复用的优化 checklist，后续 9 个 skill (design / skill-dev / project / code-quality) 照此推广，不必重新推导方法论

## 边界
范围内 / 范围外 (非目标) / 已知约束:

- [ ] 范围内：`skills/git/` 下 4 个 SKILL.md 及其 `references/` 子文件的改写、拆分、合并、删除
- [ ] 范围内：调研产物落 `.skein/task/git-skills-optimize/research/`；checklist 落点在 design 定
- [ ] 范围外：`plugins/tools/` 下 7 个已发布插件一律不动
- [ ] 范围外：`skills/` 下另外 9 个 skill 本轮不改，只被 checklist 覆盖
- [ ] 约束：4 个 skill 的对外行为语义不得改变 (触发场景、硬规、失败兜底的实际效果保持)，本轮只改表达与结构
- [ ] 约束：方法论词汇统一用 `writing-great-skills` 那套 (predictability / information hierarchy / progressive disclosure / leading word / pruning / 6 failure modes)，不另起评分体系
- [ ] 约束：中文正文；frontmatter 字段与触发词写法以官方规范为准

## 验收标准
可执行、可核对的完成断言 (逐条):

- [ ] 4 个 SKILL.md 均已改写并落盘，`git diff --stat skills/git/` 显示 4 份均有实质改动
- [ ] 每份 frontmatter 字段合规 (字段集合与官方规范一致，无非标字段残留)，`name` 与目录名一致
- [ ] 每份 description 中不存在同一 branch 的同义改写 (逐条列出 branch 清单，条目数 = 去重后触发场景数)
- [ ] git-merge 与 git-rebase 之间无重复段落：任一段内容只在一处定义，另一处经 context pointer 引用
- [ ] 4 份逐句跑过 no-op 测与 relevance 测，删除记录写入 checklist 的「实测删除项」小节
- [ ] 每份的 negation 表述已逐条审过：保留的硬 guardrail 均配有正向「改做什么」，非 guardrail 的否定句已改写为正向
- [ ] 每份改写后跑质量门 `claude -p "<内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'`，返回非空且能正确说出该 skill 的触发场景与主流程
- [ ] 质量门对 git-merge 与 git-rebase 的 `--ours` / `--theirs` 方向判定回答正确 (两者语义相反，是最易错项)
- [ ] 可复用 checklist 已落盘，含：诊断维度、逐项判据、改写动作、质量门命令模板、本次实测踩坑
- [ ] `research/` 下调研文档齐备，事实声明均带出处

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list git-skills-optimize`)
