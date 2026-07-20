# skill-dev 两插件融合 darwin+nuwa 方法论 — PRD (主入口)

## 目标
就地蒸馏 darwin-skill(优化线) + huashu-nuwa(创建线) 的方法论核心, 融入 `skills/skill-dev/` 的 skill-dev + plugin-dev 两个插件, 使其**完全自包含** — 不再靠外链依赖外部 darwin/nuwa。用户价值: skill-dev 单插件即可完成"创建单 skill(nuwa 蒸馏法) + 优化单 skill(darwin 爬山法)"全链, 无需装外部 skill。

成功长什么样:
- 两个 SKILL.md 内含 darwin 优化核 + nuwa 创建核完整方法论文字, 可离线自洽执行。
- 全部指向 darwin/nuwa 的外链 (README + 两 SKILL.md) 改为指向内部融合能力/references。
- 落一份可直接用的 result-card HTML 模板 (darwin 截图卡片)。
- 附带清理: CLAUDE.md 死链修 + skill-author 空壳删。

## 边界
**范围内**:
- darwin 优化核下沉 skill-dev **流程B(优化线)**: 9维 SkillLens rubric / validation-gated 爬山门(new>old 留否则 git revert) / 独立盲评(≥2 judge 共识) / HL-4 触顶break(2轮 Δ<2) / 一轮一维 / 体积护栏(×1.5) / 反模式黑名单。
- nuwa 创建核下沉 skill-dev **流程A(创建线)**: 分维度并行调研(落盘即真值) / Phase1.5 调研审查门 / 三重验证漏斗(跨域·生成·独特) / 模板+映射表装配 / 量化质量门(迭代上限2) / if-then 降级表。
- 创建常用 result-card HTML 模板 (对齐直接可用), 落 skill-dev/templates/。
- plugin-dev 外链(SKILL.md:32,:113 指向 /darwin-skill)改指内部 skill-dev 优化能力。
- README 路由外链(:14→darwin, :15→nuwa)改内链。
- CLAUDE.md:29/32 死链(指向不存在的 `.claude/skills/plugin-skills/`)修正。
- 删 `skills/skill-dev/skill-author/` 空壳目录。
- 每个改 SKILL.md 的产物过 `claude -p` 质量门 (CLAUDE.md:8 权威定义)。

**范围外(非目标)**:
- 不新建 screenshot.mjs 自动化脚本 / nuwa swarm 编排实体脚本 (源头 darwin/nuwa 磁盘本就无, 靠 agent 现场执行; 下沉其**文字方法论 + 接口约定**即可)。
- 不改 darwin-skill / huashu-nuwa 本体 (它们仍是独立用户级 skill, 保留)。
- nuwa 人物特定部分(表达DNA / 角色扮演)不下沉 (skill-dev 蒸方法论不蒸人物)。

**已知约束**:
- darwin/nuwa 磁盘均仅 SKILL.md (darwin 另有 results.tsv), 无 references/templates/scripts → 下沉源是 SKILL.md 文字。
- skill-dev/SKILL.md 被优化线+创建线共改 → 顺序敏感, 串行处理。
- `claude -p` 端点抖动, 长 prompt 易 400, 需重试循环。

## 验收标准
- [ ] skill-dev/SKILL.md 流程B 含 darwin 9维rubric + validation-gated门 + 盲评 + 触顶break + 体积护栏 (文字自洽, 无 `/darwin-skill` 外链残留)。
- [ ] skill-dev/SKILL.md 流程A 含 nuwa 分维度并行调研 + 1.5审查门 + 三重验证 + 质量门 + 降级表 (无 `/huashu-nuwa` 外链残留)。
- [ ] skill-dev/templates/ 下有可直接用的 result-card HTML 模板。
- [ ] plugin-dev/SKILL.md 无指向外部 darwin 的外链, 改指内部 skill-dev 优化能力。
- [ ] README.md 无指向 darwin/nuwa 的外链, 改内链。
- [ ] CLAUDE.md:29/32 死链已修 (指向真实存在路径或删除)。
- [ ] `skills/skill-dev/skill-author/` 已删。
- [ ] 三个改 SKILL.md 的产物均过 `claude -p` 质量门, 返回非空且符合预期。
- [ ] grep 全仓无 skill-dev/plugin-dev/README 指向 `darwin-skill`/`huashu-nuwa` 的外链残留。

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skill-dev-methodology-fusion`)
