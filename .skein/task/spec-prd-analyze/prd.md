# prd 六段 + seam 门 + analyze 一致性核查 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] **补 prd 缺的两段** (对齐 `/to-spec` 模板): skein 现在 prd 是四段 (目标/边界/验收标准/索引), 缺 **User Stories** 与 **Testing Decisions**
- [ ] User Stories 要求「A LONG, numbered list... extremely extensive」—— 这是 to-spec 最反直觉也最有效的一条: **穷举 user story 是逼出边界情况的机械手段**, 比让 AI「想想边界」有效得多。现在验收标准是结果, 缺了这个推导过程就靠猜
- [ ] **加 seam (测试接缝) 确认门** —— `/to-spec` 全流程只有一处要跟用户确认, 就是测试接缝: 优先复用现有接缝、取最高接缝、越少越好 (理想 = 1)。skein 的 `confirm` 门现在只确认需求不确认接缝, 而 `skein-checker` 的验证质量完全取决于有没有接缝
- [ ] **加 `analyze` 只读一致性核查** (对齐 spec-kit 的 `/speckit.analyze`, 「需求错配的最后一道防线」) —— 三个检索源 (记忆/知识库/代码地图) 不是三个搜索框, 是一个一致性核查的三个输入。检索是手段, 核查是目的
- [ ] 成功长什么样: `confirm` 前能机械核出「验收标准没被 subtask 覆盖」「design 决策违反常驻硬规」「subtask 干了 prd 没提的事」

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `skein.py` 的 prd/design 脚手架模板 + `_prd_ready` 章节校验 + `spec.py analyze <tid>` 新命令 + golden 快照重生
- [ ] 范围内: design.md 脚手架加「测试接缝」段, 并进 `confirm` 硬门校验
- [ ] 范围外: `skein-flow` 的提示词改造 (归 `spec-skills-agents-adapt`); 本 task 只做脚手架与脚本门
- [ ] 范围外: `reqs` FTS 表 —— **本轮不做** (用户已定: 只建 product wiki, 不索引历史 prd)。`analyze` 直接读 task 目录文件, 不建索引
- [ ] 约束: **不禁止已有 task 的旧四段 prd** —— 校验对新建 task 生效, 旧 task 缺新段只 warning 不阻断 (否则两个已完成 task + 本轮 8 个在途 task 全部卡死)
- [ ] 约束: prd 模板遵守 to-spec 的「**禁写具体文件路径与代码片段**」(「They may end up being outdated very quickly」); 例外同 to-spec: prototype 产出的精确编码决策的片段 (状态机/schema/type shape) 可内联
- [ ] 约束: 改 prd 模板会破 `views_golden.json` 与 `test_views_char.py` 快照, 需同轮重生
- [ ] 约束: 纯 stdlib

## 验收标准
可执行、可核对的完成断言 (逐条):

### prd 六段
- [ ] `create` 落的 `prd.md` 脚手架含六段且顺序固定: 目标 / 边界 / **User Stories** / 验收标准 / **Testing Decisions** / 索引
- [ ] User Stories 段脚手架含格式提示 `1. As a <actor>, I want <feature>, so that <benefit>` 与「要极其详尽, 覆盖功能各方面」的要求
- [ ] Testing Decisions 段脚手架含: 什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例
- [ ] `_prd_ready` 校验六段齐备且顺序正确; **旧四段 prd 只 warning 不阻断**
- [ ] `fmt` 对六段均生效 (章节内一级 list 补 `- [ ]`)
- [ ] prd 模板内含「禁写具体文件路径与代码片段」提示 (含 prototype 片段例外)

### seam 门
- [ ] `design.md` 脚手架含「测试接缝 (seam)」段, 提示: 优先复用现有接缝 / 取最高接缝 / 越少越好 (理想 1 个)
- [ ] `confirm` 校验 design.md 的接缝段非占位 (旧 task 只 warning)
- [ ] 接缝段占位未填时 `confirm` 报出具体缺失项而非笼统报错

### analyze 一致性核查 (只读)
- [ ] `spec.py analyze <tid>` **只读不写盘** (可验: 前后 `git status` 一致)
- [ ] 检出「验收覆盖率」: prd 验收标准条目 ↔ subtask 的 `--check` 项, 报未被任何 subtask 覆盖的验收条
- [ ] 检出「硬规冲突」: design.md 内容 ↔ `inclusion: always` 页, 报可能违反的硬规 (关键词/否定式命中, 报候选交人判)
- [ ] 检出「范围蔓延」: subtask 描述 ↔ prd, 报 prd 未提及的 subtask
- [ ] 检出「置信度」: design 引用的 spec 规则中 `status: proposed` 的, 标为未验证结论
- [ ] 检出「接缝」: design 声明的接缝在 codebase 中是否存在 (走 `map` 骨架或 grep), 不存在则报
- [ ] `analyze --json` 机器可读, 供 `skein-checker` 消费
- [ ] 五类检查任一项无问题时如实报「零冲突」, 不硬凑问题

### 兜底
- [ ] `views_golden.json` 与 `test_views_char.py` 快照已重生且通过
- [ ] 新增用例覆盖: 六段校验 / 旧四段只 warning / 接缝门 / analyze 五类检查各命中与不命中 / analyze 不写盘
- [ ] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-prd-analyze`)
