# 设计方向确认

## 展示了哪几版

三个 subagent 独立并行产出，同一份 `spec.md` 为唯一输入，互不参考：

| 版本 | 设计逻辑 | 产物 | 字号阶梯 |
|---|---|---|---|
| A | 秒数轮盘（`date +%S` = 42 → 3 号 = Memphis Maximalism） | `design-demos/A-wheel-memphis.html` / `.png` | 16–34px |
| A-alt | 同上，同一 agent 的第二稿 | `design-demos/A-wheel-memphis-alt.html` / `.png` | 16–32px |
| B | 现实参照（Linear / Vercel 谱系） | `design-demos/B-benchmark.html` / `.png` | 16–24px |
| B-primer | 同上，同一 agent 的第二稿 | `design-demos/B-benchmark-primer.html` / `.png` | — |
| C | 最佳设计师（瑞士国际主义 / Vignelli 谱系） | `design-demos/C-designer.html` / `.png` / `-dark.png` | 16–30px |

## 用户选择

**A-wheel-memphis-alt**

用户原话：「我选择 A-wheel-memphis-alt」

## 为什么这一版

相比 A 初稿，alt 版在同样的 Memphis 语言下把母题落得更实：

- 左栏标题从「问题队列」改成「**队列里还有谁在等**」，直接说出 spec 第 7 节的母题——Agent 停在那里等你。
- 当前题加了「**现在轮到这一题**」红色标签，被打断的用户扫一眼就知道从哪儿接上。
- 未答题用虚线边框、已答题用实线加硬阴影，状态编码不依赖颜色单一通道。
- 右上角常驻「暗色主题预览」三色板（已答 / 当前 / 未答），主题切换前就能预知效果。
- 推荐理由从行内小字升级为整条蓝色实底横幅，推荐信号不会被选项淹没。

## 前置需求确认（两轮 AskUserQuestion）

1. **字号范围** → 用户选「全部文字 ≥16px」，含徽标、计数器、选项描述，无例外。
2. **密度取舍** → 用户选「双栏布局：左侧问题导航 + 右侧当前问题」。
3. **会话中补充** → 用户要求界面额外承载项目名、背景信息，辅助理解问题。

## 落地范围

选定方向后需要改动：

- `skills/tools/ask-ui/references/schema.md` — 新增 `projectName` / `sessionBackground` / 题级 `background` 字段
- `skills/tools/ask-ui/scripts/ask-ui.mjs` — 读取并透传新字段
- `skills/tools/ask-ui/assets/app/fallback.css` — 按 Memphis alt 版重写
- `skills/tools/ask-ui/assets/app/app.js` — 双栏结构、左栏队列、当前题聚焦、新字段渲染
