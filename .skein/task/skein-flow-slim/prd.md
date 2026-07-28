# skein-flow skill 瘦身 (降 token + 去重复/冲突) — PRD (主入口)

## 目标
- [ ] SKILL.md 从 37KB(≈12k token/次调用) 降到 ~10KB, 骨架 = 参数路由表 + 全局硬门 + 四阶段各自(硬门+完成判据) + 合并去重后的失败模式总表
- [ ] 四阶段流程步骤细则下沉到 references/for-{plan,exec,check,finish}.md 按需加载; 底层 20 个主题文件保留为单一真值源, 聚合层只引不复制正文
- [ ] 消除 8 处 SKILL.md 与 references 的逐字/近逐字重复
- [ ] 修 4 处硬冲突: 自降级口子 / max_parallel 幽灵配置名 / 文件数阈值三套 / plan-ahead 是否自动 confirm
- [ ] 删低价值内容: matt-pocock-mapping.md(8KB) + 正文 5 处 ask-matt 出处标注 + 场景路由表 + 闭环完成判据
- [ ] frontmatter description 从 330 字压到 ~120 字 (常驻注入, 单位成本最高)
## 边界
- 只动 plugins/tools/skein/skills/skein-flow/ 目录内文件 (SKILL.md + references/)
- 禁改行为语义: 所有硬门/铁律/状态机约束在精简后必须仍然生效, 只改组织方式不改规则本身
- 禁动 skein.py / agents/ / commands/ / 其他 skill (skein-grill/research/setup/spec)
- 非目标: 不重构 skein CLI, 不改状态机, 不动看板 webapp
- 其他 skill 若引用了被删文件, 只做引用修正不改其正文
- design.md 豁免: 方案已由三轮 AskUserQuestion 拍板(精简力度/骨架形态/references 结构/删除面/合并与删除裁定), s1 本身即定骨架的 tracer subtask, 不另出详细设计
- 质量门口径: 用户裁定跳过 claude -p 质量检测, check 只做 grep/结构/引用可达 类逻辑检测
- 契约表以第 6-11 条为准, 第 1-5 条已作废(CLI 无删除能力), 详见 contracts
## 验收标准
- [x] SKILL.md ≤12KB (原 37185 字节), frontmatter description ≤150 字
- [x] references/ 新增 for-plan.md / for-exec.md / for-check.md / for-finish.md 四个 per-consumer 聚合入口, 只写流程步骤 + 引用底层文件路径, 无正文复制
- [x] 已删三文件: matt-pocock-mapping.md(8KB) / priority-scale.md(4.8KB 全仓孤儿) / scheduling-algorithm.md(13.0KB 与 dag-scheduling.md 同主题, 独有内容已并入后者)
- [x] SKILL.md 已删: 场景路由表 / 闭环完成判据 / ask-matt 同源标注; 四阶段失败模式表与通用失败模式表合并为单一总表; 正向配方表并入 carrier-rules.md
- [x] 4 处硬冲突已修: 自降级口子 / max_parallel 幽灵配置名 / 文件数阈值三套并存 / plan-ahead 是否自动 confirm
- [x] grep 零命中 (范围: plugins/tools/skein/skills/skein-flow/ + plugins/tools/skein/README.md — 契约 8 作业面): matt-pocock, scheduling-algorithm, priority-scale, max_parallel。目录外 docs/ scripts/ skein-setup 的 max_parallel 9 处经用户裁定另开独立 task, 不在本 task 范围
- [x] 外部引用已同步无死链: README.md:11 指向 dag-scheduling.md; skein.py:729 注释与 4 个兄弟 skill 引用行仍可达
- [x] 行为语义零变更 — 逻辑检测(用户裁定跳过 claude -p 质量门): 状态先行三硬门 / grill 硬门 / exec禁验收 / check未绿禁finish / 禁自降级 / 载体铁律 六项在正文可定位, 每项给 file:line 证据
- [x] SKILL.md 全部 references 引用路径逐条核验文件存在
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-flow-slim`)
