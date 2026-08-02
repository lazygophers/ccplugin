# skills + agents 全量适配 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 脚本能力已就位, 但 AI 侧的**提示词**还在讲旧模型 (「两层」/ `core 超 8000` / `--layer`) —— 提示词不改则新能力等于不存在
- [ ] 覆盖 5 个 skill (含 12 个 reference 文件) + 9 个 agent + `plugin.json` description
- [ ] 顺手补一个**现存断链**: `skills/skein-spec/SKILL.md:68` 引用了 `references/prune-workflow.md`, 但该文件不存在
- [ ] 顺手修正一处**文档与实现矛盾**: SKILL.md 通篇写「两层」, 实现是三层 (漏 external); 且 SKILL.md 与 specer agent 里 core 预算写死 8000, 而代码默认曾是 1000
- [ ] 成功长什么样: 任一 agent 拿到 dispatch 后, 从提示词就能正确使用 `--namespace` / `--inclusion` / `amend` / `analyze`, 不会退回旧命令; 全部改后文件过 CLAUDE.md 的 `claude -p` 质量门

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `skills/skein-spec/` (SKILL.md + 5 references + 2 templates + 新增 3 文件)
- [ ] 范围内: `skills/skein-flow/references/` 4 个文件 (for-plan / for-finish / for-check / sediment-protocol)
- [ ] 范围内: `skills/skein-setup/` (SKILL.md + trellis-migration.md)
- [ ] 范围内: 9 个 agent (specer / recaller / dedup / checker / finisher / researcher / setup / clean / executor)
- [ ] 范围内: `.claude-plugin/plugin.json` 的 description
- [ ] 范围外: `docs/` 与 `examples/` (归 `spec-docs-examples`)
- [ ] 范围外: 任何脚本代码改动 —— 本 task **纯文档/提示词**, 若发现脚本缺能力, 报告而非顺手改
- [ ] 约束: 依赖前 6 个 task 全部完成 (提示词要写的是**已落地**的能力, 不是设想)
- [ ] 约束: **必须过 CLAUDE.md 的质量门** —— `cat <文件> | claude -p --bare "<问题>" --output-format stream-json 2>/dev/null | jq -r '...'`; predictability 验法: 同一 prompt 连跑 3 次主流程描述一致才算过
- [ ] 约束: macOS 无 `timeout` 命令, 质量门调用禁包 `timeout`

## 验收标准
可执行、可核对的完成断言 (逐条):

### skein-spec skill
- [x] `SKILL.md` 的 `description` frontmatter 重写: 「两层」→ 四 namespace × 四 inclusion; 含 `product` wiki / `amend` / `map` / `analyze` / `migrate` 触发词
- [x] `SKILL.md` 正文: 层表 → namespace×inclusion 正交两维表; 新增 `product` wiki 章节 (delta vs state 区分 + 按功能域切页) / `amend` 章节 / `map` 章节 / `migrate` 章节
- [x] `SKILL.md` 判据表按 namespace 分表 (product 只报告)
- [x] `SKILL.md` 正向配方表加 wiki 条目 (含「amend 找不到章节→报错, ❌ 静默追加」)
- [x] `SKILL.md` 内 `core 超 8000` 措辞 → `always 层超 spec_always_budget`
- [x] **补建 `references/prune-workflow.md`** (现存断链) 或改 SKILL.md 的引用为存在的文件
- [x] `references/sediment-workflow.md`: 分层判定 → namespace + inclusion 判定; 加 `amend` vs `sediment` 抉择树 (改写现状 vs 新增条目)
- [x] `references/maintain.md`: 5 判据 → 按 namespace 分表
- [x] `references/reconstruct-memory.md`: 六档 archive 范围 `--layer` → `--namespace`; 8 型探针产物加 `product` 页
- [x] `references/bootstrap-seeding.md`: 五维扫描产物加 `product` overview 页
- [x] `templates/core.md.tmpl` → `rules-always.md.tmpl`; `templates/recall.md.tmpl` → `rules-auto.md.tmpl`
- [x] **新增** `templates/product.md.tmpl` (现状 / 边界 / 为什么这样 / anchors / 关联)
- [x] **新增** `templates/map.md.tmpl` (职责 / 入口 / 数据流 / anchors)
- [x] **新增** `references/migration-v2.md` (两阶段迁移全流程 + 阶段 2 语义分拣作业指引)

### skein-flow skill
- [x] `for-plan.md`: recall 段加 `--src product` 检索 wiki 当前真值; prd 六段; seam 确认门
- [x] `for-finish.md`: sediment 段 → **sediment + wiki 回写 (amend)** 双动作; 含 `finish-candidates` 三路降级与「无候选→建议新建, 禁硬凑」
- [x] `for-check.md`: 一致性核查改调 `skein-spec analyze <tid>`
- [x] `sediment-protocol.md`: 加 `proposed → active/superseded` 转态 (plan 期沉淀未验证决策, finish 时依 diff 证据转态)

### skein-setup skill
- [x] `SKILL.md`: `init` 建四 namespace; 已初始化仓检出旧结构 (`spec/core/` 存在) → 提示跑 `migrate`
- [x] `references/trellis-migration.md`: 目标结构从两层 → 四 namespace

### agents
- [x] `skein-specer.md`: description 与工作流从四类写路径 → **五类** (加 `amend` wiki 回写); `--layer` → `--namespace`/`--inclusion`; 返回 JSON 加 `amended[]`; `core 超 8000` 措辞更正
- [x] `skein-recaller.md`: 「只召 recall 层」→「召 `inclusion: auto` 的全 namespace, 跳过 `always` (已常驻)」; 加 `--src` 分源; 回传区分 rules / product 命中
- [x] `skein-finisher.md`: 收尾勘察加「diff → `finish-candidates` → 报候选 product 页」供 main 派 specer amend
- [x] `skein-checker.md`: 一致性核查段改调 `analyze <tid>`
- [x] `skein-dedup.md`: 加一句可选增强 —— 可走 `--src product` 判「该需求 wiki 里已是现状」则 task 本身多余 (**主体不动**)
- [x] `skein-researcher.md`: bootstrap/reconstruct 五维产物加 `product` overview
- [x] `skein-setup.md`: 迁移目标结构更新 + 旧结构识别调 `migrate`
- [x] `skein-clean.md`: `.archive/` 清理**保护最近一次 migrate 快照**, 不清它
- [x] `skein-executor.md`: 措辞 (`core 全文注入` → `always 层注入`)

### 接线与质量门
- [x] `plugin.json` description 更新 (namespace×inclusion 模型 + skill/agent 职责同步)
- [x] `plugin.json` 的 hooks 段**零改动** (命令名与 matcher 均不变, 这是本轮设计的隐性收益, 需验证确实没改)
- [ ] [⚠️] 每个改动过的 skill/agent 文件均过 `claude -p` 质量门, 且同 prompt 连跑 3 次主流程描述一致 (**环境阻塞: 端点不可用 API retry unknown error**)
- [x] 质量门调用严格按 CLAUDE.md 规范: stdin 管道 + `--bare` + `2>/dev/null`, 禁 `claude -p "$(cat ...)"` 插值, 禁包 `timeout`

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-skills-agents-adapt`)
