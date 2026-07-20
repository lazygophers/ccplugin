# design.md 写入界限文档化 — PRD

## 目标
明确 design.md (详细设计) 写入界限: 仅 planning 阶段写 (含 check 失败回 planning 二次进入), exec/check/finish 禁动。exec/check 发现方案需调整 → 回 planning 改 design 后重派。将界限写到 skill 文档。

## 边界
- 范围内: skein-plan / skein-flow / skein-exec / skein-check 四个 SKILL.md 加界限声明
- 范围外: skein.py 脚手架模板 (已含 design.md 说明, 不改); skein-grill (只审查不写); skein-finish (不碰 design); 其他
- 约束: 文案类变更, 样例已用户确认

## 改动
- skein-plan/SKILL.md L60: design.md 行加写入界限声明
- skein-flow/SKILL.md: 加一行 "exec/check/finish 禁动 design.md, 方案调整回 planning"
- skein-exec/SKILL.md: 加一行 "禁动 design.md (写入归 planning)"
- skein-check/SKILL.md: 加一行 "禁动 design.md, 方案冲突回 planning 改后重派"

## 验收标准
- [ ] skein-plan L60 含写入界限声明
- [ ] skein-flow/exec/check 各含禁动 design.md 约束
- [ ] 四文件 claude -p 质量门过 (AI 能正确识别 design.md 写入界限)
- [ ] grep "design.md" 四文件均有界限相关表述

## 索引
- 任务/子任务/调度: task.json
