# PRD — HTML 模板 + SKILL 应用 Grok Live Artifacts 风格

## 参考

[Grok Live Artifacts 提示词](https://linux.do/t/topic/2163779) — yeahhe

核心约束:
1. **全 inline style** — 严禁 `<style>` 块, 每标签写 `style="..."`
2. **首字符 `<div`** — 严禁前导文字/Emoji/换行
3. **禁裸文本** — 全 wrap 在 `<span>` / `<p>` / `<h2>` / `<div>`
4. **禁 Markdown 符号** — 无 `#` / `**` / `- `
5. **视觉 token**:
   - 主容器: `border-radius:16px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); border:1px solid #eef0f2; padding:24px; font-family:sans-serif; color:#1a202c;`
   - 标题: `border-left:4px solid #3182ce; padding-left:12px; font-size:1.5rem; font-weight:700;`
   - 卡片: `border:1px solid #edf2f7; border-radius:12px; padding:16px;`
   - grid: `display:grid; grid-template-columns:repeat(N,1fr); gap:12px;`

## 目标

cortex HTML 输出统一 Grok 风格, 解决:
- 当前 templates/html/* 8 片段风格散乱 (有 inline 但 token 不统一)
- cortex-dashboard 输出依赖 AI 自由发挥, 视觉不稳定
- cortex-html SKILL 描述缺严格约束

## 设计

### 1. 升级 templates/html/ 8 片段

风格 token 统一:
- 容器: 16px 圆角 + box-shadow + 1px border (#eef0f2)
- 卡片: 12px 圆角 + 1px border (#edf2f7) + 16px padding
- 标题: 左 4px border (#3182ce 蓝)
- 主色: #3182ce 蓝 / #16a34a 绿 / #dc2626 红 / #ea580c 橙 / #ca8a04 黄 / #6b7280 灰
- 字体: sans-serif
- 文字色: #1a202c

升级文件 (保留原 8):
- `badge.html` — 圆角 12px + inline color + padding
- `card.html` — 16px shadow + 1px border + grid-friendly
- `timeline.html` — CSS-only 竖排, 圆点 + 连线
- `canvas-heatmap.html` — 容器 16px 圆角
- `progressive-disclosure.html` — `<details>` 含 inline summary 样式
- `mermaid-flowchart.md` — 围栏 + Grok 风容器外包
- `mermaid-sankey.md` — 同
- `mermaid-mindmap.md` — 同

每片段开头加 `<!-- cortex-template-version: 2 -->` (升级版本号), 触发 lint template-outdated autofix 自动 sync 到 vault。

### 2. cortex-html SKILL 加严约束

`skills/cortex-html/SKILL.md` 加 `## Grok Live Artifacts 风格契约`:
```
输出 HTML 必符合:
1. 首字符 `<div`, 严禁前导文字
2. 全 inline style, 无 `<style>` 块
3. 文本 wrap `<span>` / `<p>` / `<h2>` / `<div>`, 严禁裸文本
4. 主容器: border-radius:16px + box-shadow + border:1px solid #eef0f2 + padding:24px
5. 标题: border-left:4px solid #3182ce; padding-left:12px
6. 卡片: border-radius:12px; border:1px solid #edf2f7; padding:16px
7. grid: display:grid + repeat + gap:12px
8. 主色 token: 蓝#3182ce / 绿#16a34a / 红#dc2626 / 橙#ea580c / 黄#ca8a04 / 灰#6b7280
9. 字体 sans-serif, 文字色 #1a202c
10. 禁 Markdown 符号 (# / ** / -)
```

### 3. cortex-dashboard SKILL 加严约束

`skills/cortex-dashboard/SKILL.md` 加同约束段, 引用 cortex-html。

### 4. 不动 seed 模板正文

seed 模板 (`presets/seed/仪表盘/*.md` 等) 已大量 inline, 风格相近。不强制刷, 让 lint vault-misaligned 自动 sync 即可。

## 实施

### Step 1: 升级 8 templates/html/* 片段 (Grok 风 token)
### Step 2: cortex-html SKILL 加 Grok 契约
### Step 3: cortex-dashboard SKILL 加 Grok 契约 (引用 html)
### Step 4: 触发 templates manifest regen (sha 变)
### Step 5: 测试 + marketplace sync

## 验收

- [ ] 8 templates/html/* 含统一 Grok 风格 token (border-radius:12-16 / shadow / inline)
- [ ] cortex-html SKILL 含 Grok Live Artifacts 风格契约段
- [ ] cortex-dashboard SKILL 含相同约束
- [ ] templates/_manifest.json sha 更新
- [ ] 286 tests PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| 老 vault _templates 用新 sha → vault-misaligned 触发 autofix | 期望行为 (强制对齐) |
| AI 输出仍不严格 (model 局限) | SKILL 显式约束尽量严, 但接受 AI 浮动 |
| 移动端样式不适配 | inline style + grid auto-fit, 通用 |

## 子任务
单 trellis-implement。
