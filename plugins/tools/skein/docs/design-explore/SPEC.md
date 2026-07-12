# SKEIN 看板视觉系统重设计 — 共享 spec

## 是什么
SKEIN 是 Claude Code 任务管理插件。看板 = 离线单文件 HTML (`task.html`),
由 `scripts/skein.py` 用字符串拼 HTML 生成, 链接式 CSS。展示 AI 编排的 task/subtask
执行状态: 完成度、DAG 执行顺序、subtask 明细表。

## 受众 / 场景
开发者在浏览器看 AI 干活进度。1m 笔记本距离。信息密度型 dashboard, 不是营销页。
情感基调: 冷静、专业、可信、克制。不要炫技渐变/emoji/slop。

## 信息架构 (markup 已定, 见 _content.html)
- **概览 card** ×1: "任务进展" 标题 + 状态 chips + meta 行 + 总体/加权完成度进度条 + task 级 DAG (SVG)
- **task card** ×7: `<h2>` id+状态 badge, `<p class=name>` 标题, `<p class=meta>` 元信息,
  耗时条, subtask 计数条, subtask 级 DAG (SVG), `<table>` (列: sid/名称/状态/进度/预期/agent/skills/依赖/验收标准)

## 硬约束 (违反即废)
1. **只改视觉系统 = base.css 布局+组件骨架** (+ 允许极小 markup 调整, 但 markup 改动要在预览注释里标出, 因为要回写 Python 拼接)。
2. **颜色全走 CSS 变量, 禁写死色值。** 变量契约 (由 palette 提供, 勿改名):
   `--bg --fg --head --muted --card --brd --line --accent --accent2`
   `--st-pending --st-active --st-check --st-done --st-failed --sel-bg --sel-fg --font --radius`
3. **主题中立**: base.css 是骨架, 17 个 theme 用 `html[data-theme=X]` 覆盖装饰 (边框/阴影/纹理/字体)。
   你的骨架必须让 theme 覆盖仍能生效 — 别把结构写死到某一主题。
4. **组件类名保留** (Python 拼接依赖): `.card .badge .name .meta .bar .fill .pct .dag .switcher .empty`
   + badge 状态类 `.s-pending .s-active .s-check .s-done .ss-*` + `.bar.sub .bar.est .bar.time .bar.time.over .bar.prog`。
   可新增类, 但别删除/改名已有类 (否则 Python 需大改)。
5. 离线单文件, 无 React, 无构建, 仅 CSS + 现有 switcher.js。可读性底线: 正文 ≥13px, 对比度 ≥4.5:1。

## 进度条现状 (勿丢失的能力)
`.bar.prog .fill` 按 `--p` 百分比在 `--st-failed`→`--st-done` 间 color-mix 插值 + 混 --bg 得轻渐变。
保留这个"主题自适应渐变"能力。est/time/over 条用 st-check/st-active/st-failed 语义色。

## 输出
每个 subagent 产出 1 个自包含 HTML (内联 base 重设计 + sketch theme + stone palette),
用 `docs/examples/sample-skein/_content.html` 的真实 markup 作 body, 视口 1440 宽截图。
