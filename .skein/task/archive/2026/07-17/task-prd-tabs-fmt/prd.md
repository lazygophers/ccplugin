# task详情PRD章节化为tab/todo + prd.md fmt规范化hook — PRD (主入口)

## 目标
两件事:
1. **PRD 章节化展示**: webapp task 详情页的 PRD tab 从"整篇 md 一次性 v-html"改为**按二级章节 (目标/边界/验收标准/索引) 拆 card/accordion 竖排**, 每章节内 `- [ ]`/`- [x]` 一级 list 渲染为 **todo 样式 (只读展示勾选态)**。用户价值: PRD 结构一目了然, 验收项勾选进度可视, 不必读整篇 md。
2. **prd.md fmt 规范化**: 新增 `skein fmt <id>` CLI 子命令 (一级 list 转 todo 语法 + 规范化章节输出, 不规范报错) + PostToolUse hook 写 prd.md 后自动调 fmt。用户价值: prd.md 始终结构规范, 前端解析有稳定锚点。

成功长什么样:
- [ ] task 详情 PRD tab 竖排四章节 card, 各带 todo 勾选态 (复用旧 board prdBlock 视觉语言)。
- [ ] `skein fmt <id>` 手动可跑, 幂等; 写 prd.md 后 hook 自动跑一次 fmt, 无循环触发。

## 边界
**范围内**:
- [ ] 前端: `plugins/tools/skein/assets/webapp/src/pages/task.js` — 仅 **PRD tab** 内容区改章节 card + todo 只读展示 (design/findings tab 保持整篇 md 不动)。前端解析 docs.prd 原文按 `^##\s+` 分节, 零后端改动。
- [ ] CLI: `skein.py` 加 `fmt` 子命令 (add_parser + dispatch + MUTATING 上锁 + `def fmt`)。fmt 逻辑: 各章节内一级 `-` list 项规范为 `- [ ]` todo (已是 checkbox 的保留勾选态); 章节缺失/顺序错/非标题 → 报错非零退出; 幂等 (再跑不变)。
- [ ] hook: `plugin.json` 加 PostToolUse (matcher Edit|Write|MultiEdit) → `skein-hooks fmt`; `hooks.py` 加 `cmd_fmt` 分派 (判 file_path 匹配 `.skein/task/*/prd.md` 才调 `skein fmt <id>`, 否则放行; 防循环: fmt 改文件后不再递归触发 / 或内容无变化跳过)。

**范围外 (非目标)**:
- [ ] 不改后端 `_task_detail`/`prd_data`/endpoint (前端自解析, 不动 docs 契约)。
- [ ] todo **不可点击持久化** (只读展示勾选态; 不回写 prd.md)。
- [ ] design/findings tab 不章节化。
- [ ] 不动 skein 任务引擎其他部分 / task.json 结构。

**已知约束**:
- [ ] webapp task.js: DOC_TABS 三文档 tab (task.js:106); PRD 现整块 `<div class="md-body" v-html="renderedDoc">` (task.js:57); docs.prd 是原文字符串 (api /__skein__/task/{tid})。软刷 onLive 整体重挂丢 tab 选择 (task.js:146) — 章节化实现别引入新的 state 丢失。
- [ ] PRD 标准章节 = 目标/边界/验收标准/索引 (`_scaffold` skein.py:355-358 模板); 章节标题是稳定锚点。
- [ ] skein 现**无 PostToolUse hook** (仅 PreToolUse guard, hooks.py); 新增需 plugin.json hooks 段 + hooks.py DISPATCH (hooks.py:138)。guard BLOCKED 只含 task.json/task.md, prd.md 不在内 (放行)。
- [ ] 旧 board prdBlock (board-render.js:266) 用后端 prd_data 结构化 — 视觉可参, 但本 task 走前端解析不复用其后端。
- [ ] petite-vue 顶层条件指令崩溃坑: 章节渲染的条件 (空章节/todo 态) 禁放页面模板顶层。

## 验收标准
- [ ] task 详情 PRD tab 渲染为四章节 card/accordion 竖排 (目标/边界/验收标准/索引), 各章节内一级 checkbox 渲染为 todo 只读勾选态。
- [ ] design/findings tab 仍整篇 md, 未受影响。
- [ ] 软刷 (onLive) 后 PRD 章节展示不崩、tab 选择行为不退化。
- [ ] `skein fmt <id>` 可手动跑: 一级 list→todo 规范化 + 幂等 (连跑两次结果一致); 不规范 prd.md 报错非零退出。
- [ ] fmt 写命令已加入 MUTATING 上锁。
- [ ] plugin.json PostToolUse hook + hooks.py cmd_fmt 接线: 写 `.skein/task/*/prd.md` 后自动调 fmt, 非 prd.md 放行, 无循环触发。
- [ ] 启 serve 实测 task 详情页加载不崩; fmt hook 实测写 prd.md 触发一次规范化。
- [ ] 顶层无条件指令 (规避 petite-vue 崩溃坑)。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 代码勘察: [research/prd-tabs-fmt-recon.md](research/prd-tabs-fmt-recon.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein subtask list task-prd-tabs-fmt`)
