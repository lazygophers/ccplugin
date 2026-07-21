# PRD: skein-trellis-optimize-v2

## 目标
深度学习 Trellis + obra/superpowers + AI coding 任务/流程框架 + spec-driven/方法论框架 + 前端 UI 展示类项目, 以 **skein 插件本身为基石罗盘**, 产整体优化建议 (非补充, 允许破坏性, 但须更省 token / 更符合预期 / 更贴合 skein)。

## 罗盘 (skein 本身 = 判据)
每个优化点必须回问: 是否贴合 skein 设计/定位/不变量? skein 差异化优势 (两层 core/recall 记忆 + grill 硬门 + DAG 双层调度 + worktree 隔离 + 根因复盘 + bootstrap) 不回退。

## 范围
- 瘦身去重 (单一真值源 / hook 瘦身 / 死代码 / 术语统一)
- Trellis 借鉴 (sediment 7段模板 / code-spec-guide 二分 / checker 孤立失败自修 / per-task context manifest)
- skein.py 拆分 (serve.py/board.py/migrate.py)
- skill/agent 写法借鉴 (Trellis + superpowers + 各框架具体 skill/agent 文件)
- 前端 UI (task.html 看板) 优化

## 流程铁律 (用户硬规)
**每发现一个可优化点 → 4 步**:
1. 向用户问一次"基石罗盘" (该点是否贴合 skein)
2. 建独立 Task + 写 PRD 记录修复方案
3. 修复前再确认完整方案
4. 读 PRD + 确认方案 → 才修复

**所有修复方案必须逐个与用户确认后才动手。**

## 已完成调研
- skein 现状审计 (8 维, 205 行): .skein/task/skein-audit/research/skein-current-state-audit.md
- Trellis 设计深挖 (7 维, 246 行): .skein/task/trellis-comparison/research/trellis-design-deep-dive.md

## 待调研
- obra/superpowers 设计 + skill/agent 写法
- AI coding 流程框架 (Claude Flow/Cline/Roo/Claude Engineer 等)
- spec-driven/方法论框架 (BMAD/Aichaku/spec-kit 等)
- 前端 UI 展示类 (任务看板/进度可视化)

## 验收标准
- 产完整优化方案矩阵 (每项: 现状/问题/改法/收益/风险/改前→改后样例)
- 每项以 skein 罗盘判定 (借鉴/拒绝/演进)
- 用户逐条确认后才实施
