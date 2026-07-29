# DAG tab 主题风格适配 — 详细设计

## 现状 (L362-410 CSS)
`.dag-pop-inner` / `dialog.dag-modal` 纯白 `#fffefb` 底 + 硬编码 ocean 冷色, 无 glass, 缺 goldSand 暖色。与 components/Timeline `.glass` 卡片 (backdrop-blur + 半透 + 暖灰 shadow) 风格割裂。

## 主题语言 (复用现有 token)
- `.glass` (L119): `background:rgba(255,254,251,0.7); backdrop-filter:blur(12px); border:1px solid rgba(...); box-shadow:暖灰`。
- ocean 5 阶: foam/shallow/mid/deep/abyss。
- goldSand 4 阶: light/mid/deep/sunset (暖金, 当前 DAG 零使用 — 主因割裂)。
- night: base/mid/deep (暗模)。
- 语义: success/warning/danger。

## 改造方案 (4 项)

### ① glass 质感 (popover + Modal)
- `.dag-pop-inner`: `background:rgba(255,254,251,0.82)` (半透 pearl) + `backdrop-filter:blur(10px)` + `border:1px solid rgba(116,185,232,0.35)` + `box-shadow:0 4px 14px rgba(212,176,102,0.15)` (暖金阴影替代冷灰)。
- `.dark .dag-pop-inner`: `background:rgba(22,44,66,0.85)` (night.mid 半透) + blur。
- `dialog.dag-modal`: 同样半透 + blur + 暖金 shadow。

### ② 引入 goldSand 暖色 (破冷蓝单调)
- `.dag-modal-chip`: 从 `rgba(116,185,232,0.16)/#237bb8` (ocean 蓝) → `rgba(240,217,160,0.25)/#d4b066` (goldSand 暖金), 暗模 `rgba(230,200,139,0.22)/#e6c88b`。
- `.dag-pop-bar > i` (active 进度条): 从 ocean `#429cd1` → `linear-gradient(90deg,#429cd1,#d4b066)` (海蓝→金沙滩渐变, 呼应主题双色)。
- done 态保留 success 绿 (语义不破), 但可加 goldSand 描边点缀。

### ③ ocean 阶色变量替代硬编码
- popover 文字 `#1e293b` → `text-slate-800` 或保留 (中性灰 OK); 暗模 `#f1f5f9` → night 系。
- popover/meta `#64748b/#94a3b8` (slate) — 中性灰保留 (非主题色, 不强改)。
- 边框/强调 `#74b9e8/#429cd1/#74b9e8` → ocean.shallow/mid/shallow (用 CSS 变量或保留 hex 同值, ponytail: hex 同值改 token 仅可读性收益, 优先改质感类)。

### ④ Modal 金线点缀
- `.dag-modal-title` 下加 `border-bottom:2px solid goldSand.mid (#e6c88b)` + `padding-bottom:6px`, 或 `.dag-modal-head` 后加 `<div class="h-0.5 bg-goldSand-mid/60 rounded">` 分隔线。
- ponytail: CSS border-bottom 最简, 不加 DOM。

## 取舍
- 4 态语义色 (success/danger) 保留 — 语义不可破。
- slate 中性灰文字保留 — 主题色是 ocean/goldSand/night, 中性灰非偏离。
- 硬编码 hex → token: 仅改有质感收益的 (背景/边框/阴影/chip/进度条), 同值 hex 保留省 churn。
