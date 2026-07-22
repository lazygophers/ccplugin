# 配色总清单（Palettes Catalog）

一处扫全部现成调色板。三类：**A 品牌主色阶**（6 色系 ×10 档）+ **B 中性灰阶**（3 种调子）+ **C 语义色 + 命名主题色板**。复制即用。

> 详细用法 / 暗模式派生 / 自定义扩阶见 [palette-templates.md](palette-templates.md)。本文件是索引清单，拿色值直接扫。

## A · 品牌主色阶（每色 10 档 50→900）

| 色系 | 语义 | 500（基准）| 50（浅底）| 700（深 hover）| 详情 |
|------|------|-----------|----------|---------------|------|
| 🔵 Blue | 信任 / 科技 / 专业 | `#3b82f6` | `#eff6ff` | `#1d4ed8` | [palette-templates](palette-templates.md#蓝blue--信任--科技--专业) |
| 🟢 Green | 成长 / 健康 / 安全 | `#22c55e` | `#f0fdf4` | `#15803d` | [palette-templates](palette-templates.md#绿green--成长--健康--安全) |
| 🔴 Red | 激情 / 警示 / 电商 | `#ef4444` | `#fef2f2` | `#b91c1c` | [palette-templates](palette-templates.md#红red--激情--警示--电商) |
| 🟣 Purple | 创新 / 高端 / 神秘 | `#a855f7` | `#faf5ff` | `#7e22ce` | [palette-templates](palette-templates.md#紫purple--创新--高端--神秘) |
| 🟠 Orange | 活力 / 食欲 / 温暖 | `#f97316` | `#fff7ed` | `#c2410c` | [palette-templates](palette-templates.md#橙orange--活力--食欲--温暖) |
| 🩵 Teal/Cyan | 清新 / 医疗 / 现代 | `#14b8a6` | `#f0fdfa` | `#0f766e` | [palette-templates](palette-templates.md#青teal--cyan--清新--医疗--现代) |

### 全阶色值（50→900）

```
Blue:   50:#eff6ff 100:#dbeafe 200:#bfdbfe 300:#93c5fd 400:#60a5fa 500:#3b82f6 600:#2563eb 700:#1d4ed8 800:#1e40af 900:#1e3a8a
Green:  50:#f0fdf4 100:#dcfce7 200:#bbf7d0 300:#86efac 400:#4ade80 500:#22c55e 600:#16a34a 700:#15803d 800:#166534 900:#14532d
Red:    50:#fef2f2 100:#fee2e2 200:#fecaca 300:#fca5a5 400:#f87171 500:#ef4444 600:#dc2626 700:#b91c1c 800:#991b1b 900:#7f1d1d
Purple: 50:#faf5ff 100:#f3e8ff 200:#e9d5ff 300:#d8b4fe 400:#c084fc 500:#a855f7 600:#9333ea 700:#7e22ce 800:#6b21a8 900:#581c87
Orange: 50:#fff7ed 100:#ffedd5 200:#fed7aa 300:#fdba74 400:#fb923c 500:#f97316 600:#ea580c 700:#c2410c 800:#9a3412 900:#7c2d12
Teal:   50:#f0fdfa 100:#ccfbf1 200:#99f6e4 300:#5eead4 400:#2dd4bf 500:#14b8a6 600:#0d9488 700:#0f766e 800:#115e59 900:#134e4a
```

**用法**：500 = 主色 / 按钮；600 = hover；700 = active/pressed；50 = 浅底背景；900 = 深文字。

## B · 中性灰阶（3 种调子）

| 调子 | 适合 | 500（次文字）| 900（深文字）| 100（背景）| 详情 |
|------|------|-------------|-------------|-----------|------|
| 冷灰（蓝调）| 科技 / 专业 / SaaS | `#64748b` | `#0f172a` | `#f1f5f9` | [palette-templates](palette-templates.md#冷灰科技--专业) |
| 暖灰（黄调）| 人文 / 亲和 / 消费 | `#78716c` | `#1c1917` | `#f5f5f4` | [palette-templates](palette-templates.md#暖灰人文--亲和) |
| 真灰（中性）| 通用 / 极简 | `#71717a` | `#18181b` | `#f4f4f5` | [palette-templates](palette-templates.md#真灰中性) |

### 全阶色值

```
冷灰: 50:#f8fafc 100:#f1f5f9 200:#e2e8f0 300:#cbd5e1 400:#94a3b8 500:#64748b 600:#475569 700:#334155 800:#1e293b 900:#0f172a
暖灰: 50:#fafaf9 100:#f5f5f4 200:#e7e5e4 300:#d6d3d1 400:#a8a29e 500:#78716c 600:#57534e 700:#44403c 800:#292524 900:#1c1917
真灰: 50:#fafafa 100:#f4f4f5 200:#e4e4e7 300:#d4d4d8 400:#a1a1aa 500:#71717a 600:#52525b 700:#3f3f46 800:#27272a 900:#18181b
```

**用法**：900 = 深文字；500 = 次要文字；100 = 页面背景；200 = 边框；50 = 卡片底。

## C · 语义色（全媒介统一）

```
success: #22c55e (green-500)   success-bg: #f0fdf4 (green-50)
warning: #f59e0b               warning-bg: #fffbeb
error:   #ef4444 (red-500)     error-bg:   #fef2f2 (red-50)
info:    #3b82f6 (blue-500)    info-bg:    #eff6ff (blue-50)
```

每语义色配浅底（`-bg`）做横幅 / 标签 / toast 背景。CLI / TUI 映射：success→绿、warning→黄、error→红、info→蓝。

## D · 命名主题色板（成套 primary + accent + neutral）

| # | 名 | primary | accent | neutral | 适合 | 详情 |
|---|-----|---------|--------|---------|------|------|
| A | 现代 SaaS | `#2563eb` 蓝 | `#7c3aed` 紫 | 冷灰 | B2B / 工具 / 后台 | [palette-templates](palette-templates.md#a--现代-saas蓝主--冷灰) |
| B | 暖意消费 | `#ea580c` 橙 | `#0891b2` 青 | 暖灰 | 电商 / 餐饮 / 社区 | [palette-templates](palette-templates.md#b--暖意消费橙主--暖灰) |
| C | 极简黑白 | `#18181b` 黑 | `#3b82f6` 蓝 | 真灰 | 内容 / 品牌 / 文档 | [palette-templates](palette-templates.md#c--极简黑白黑主--真灰) |
| D | 创意活力 | `#9333ea` 紫 | `#f97316` 橙 + `#10b981` 绿 | 冷灰 | 创意 / 娱乐 / Z 世代 | [palette-templates](palette-templates.md#d--创意活力紫主三元配色) |

### 完整套色（A/B/C/D）

```
A 现代 SaaS:
  primary:#2563eb accent:#7c3aed success:#16a34a warning:#d97706 error:#dc2626 info:#2563eb
  bg:#ffffff bg-subtle:#f8fafc text:#0f172a border:#e2e8f0   neutral:冷灰

B 暖意消费:
  primary:#ea580c accent:#0891b2 success:#16a34a warning:#ca8a04 error:#dc2626 info:#0284c7
  bg:#fffbeb bg-subtle:#fef3c7 text:#292524 border:#e7d8c4   neutral:暖灰

C 极简黑白:
  primary:#18181b accent:#3b82f6 success:#16a34a warning:#d97706 error:#dc2626 info:#2563eb
  bg:#ffffff bg-subtle:#fafafa text:#18181b border:#e4e4e7   neutral:真灰

D 创意活力:
  primary:#9333ea accent:#f97316 secondary-accent:#10b981 success:#10b981 warning:#f59e0b error:#ef4444 info:#3b82f6
  bg:#faf5ff bg-subtle:#f3e8ff text:#1e293b border:#e9d5ff   neutral:冷灰
```

## E · 色盲安全 Okabe-Ito（8 色，WCAG 推荐）

数据可视化 / 状态编码专用，8 种色盲都能区分：

```
橙:#E69F00  天蓝:#56B4E9  绿:#009E73  黄:#F0E442
蓝:#0072B2  朱:#D55E00   品红:#CC79A7 黑:#000000
```

适用：图表配色 / 不依赖色觉的状态标签。详见 [accessibility.md](accessibility.md) 色盲段。

## 选色流程

1. **定品牌主色** → A 表选色系 → 拿 500 基准 + 全阶
2. **定中性调子** → B 表按产品气质选冷/暖/真灰
3. **加语义色** → C 表直接用（不自己调）
4. **要成套** → D 表选命名色板（primary+accent+neutral 一次性）
5. **数据图表** → E 表 Okabe-Ito
6. **要现成主题** → [themes-catalog.md](themes-catalog.md)（含跨平台热门预设）

落地到媒介 → 各 medium style 文件。暗模式派生规则 → [palette-templates.md](palette-templates.md#暗模式派生)。
