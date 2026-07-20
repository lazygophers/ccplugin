# skill-dev 两插件融合 darwin+nuwa 方法论 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 融合映射
- darwin(优化单skill) → skill-dev **流程B 优化线** + result-card 模板。
- nuwa(蒸馏生成单skill) → skill-dev **流程A 创建线**。
- plugin-dev 是插件级, 优化线自带 8维 rubric, 仅组件质量维原外包 /darwin → 改指内部 skill-dev。

## 共享文件冲突
skill-dev/SKILL.md + references/ 被 darwin下沉(S1) 和 nuwa下沉(S2) 共改 → **串行** (S2 deps S1)。
plugin-dev/SKILL.md(S3)、README/CLAUDE.md/skill-author(S4) 独立文件。

## 子任务
| id | 名称 | 改动面 | 依赖 |
|----|------|--------|------|
| fuse-darwin-optimize | skill-dev 优化线下沉 darwin + result-card 模板 | skill-dev/SKILL.md 流程B + references(dimensions/validation-checklist/optimizer-sources) + templates/result-card.html + 优化线外链改内链 | — |
| fuse-nuwa-create | skill-dev 创建线下沉 nuwa | skill-dev/SKILL.md 流程A + references(workflow/subagent-authoring 等 nuwa核) + 创建线外链改内链 | fuse-darwin-optimize |
| plugin-dev-internalize | plugin-dev 外链内化 | plugin-dev/SKILL.md:32,:113 改指内部 skill-dev 优化能力 | — |
| readme-cleanup | README 外链改内链 + 附带清理 | README.md:14,15 改内链 + CLAUDE.md:29,32 死链修 + 删 skill-author/ | fuse-darwin-optimize, fuse-nuwa-create, plugin-dev-internalize |

## 调度波次 (并发上限2)
1. fuse-darwin-optimize ‖ plugin-dev-internalize
2. fuse-nuwa-create (S1完)
3. readme-cleanup (S1&S2&S3完)

## 关键取舍
- 重资产: 只下沉方法论文字 + 落 result-card HTML 模板; 不建 screenshot.mjs/swarm 脚本 (源头无实体, 靠 agent 现场执行)。
- 质量门: S1/S2/S3 改 SKILL.md 后各过 `claude -p` 门; check 阶段 skein-checker 统一验 + 一致性核查 (外链残留 grep / 契约对齐)。
