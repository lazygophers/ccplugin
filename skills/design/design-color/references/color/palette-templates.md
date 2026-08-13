# 调色板模板（无关平台）

现成可用调色板。复制色值，落地到各媒介 token（Web CSS 变量 / App token / CLI ANSI / TUI 色域）。理论见 [theory.md](theory.md)，可访问性见 [accessibility.md](accessibility.md)。

## 色板构成（每项目必备）

一套完整色板包含：

- **主色阶**（9-11 档）：`50 → 900`
- **中性阶**（9-11 档）：`50 → 900`（文字 / 背景 / 边框）
- **语义色**：success / warning / error / info
- **辅助色**（0-2）：次级强调

---

## 品牌主色阶模板（通用）

### 蓝（Blue）— 信任 / 科技 / 专业

```
50:#eff6ff  100:#dbeafe  200:#bfdbfe  300:#93c5fd  400:#60a5fa
500:#3b82f6 600:#2563eb 700:#1d4ed8 800:#1e40af 900:#1e3a8a
```

### 绿（Green）— 成长 / 健康 / 安全

```
50:#f0fdf4  100:#dcfce7  200:#bbf7d0  300:#86efac  400:#4ade80
500:#22c55e 600:#16a34a 700:#15803d 800:#166534 900:#14532d
```

### 红（Red）— 激情 / 警示 / 电商

```
50:#fef2f2  100:#fee2e2  200:#fecaca  300:#fca5a5  400:#f87171
500:#ef4444 600:#dc2626 700:#b91c1c 800:#991b1b 900:#7f1d1d
```

### 紫（Purple）— 创新 / 高端 / 神秘

```
50:#faf5ff  100:#f3e8ff  200:#e9d5ff  300:#d8b4fe  400:#c084fc
500:#a855f7 600:#9333ea 700:#7e22ce 800:#6b21a8 900:#581c87
```

### 橙（Orange）— 活力 / 食欲 / 温暖

```
50:#fff7ed  100:#ffedd5  200:#fed7aa  300:#fdba74  400:#fb923c
500:#f97316 600:#ea580c 700:#c2410c 800:#9a3412 900:#7c2d12
```

### 青（Teal / Cyan）— 清新 / 医疗 / 现代

```
50:#f0fdfa  100:#ccfbf1  200:#99f6e4  300:#5eead4  400:#2dd4bf
500:#14b8a6 600:#0d9488 700:#0f766e 800:#115e59 900:#134e4a
```

---

## 中性阶模板（灰阶）

### 冷灰（科技 / 专业）

```
50:#f8fafc  100:#f1f5f9  200:#e2e8f0  300:#cbd5e1  400:#94a3b8
500:#64748b 600:#475569 700:#334155 800:#1e293b 900:#0f172a
```

### 暖灰（人文 / 亲和）

```
50:#fafaf9  100:#f5f5f4  200:#e7e5e4  300:#d6d3d1  400:#a8a29e
500:#78716c 600:#57534e 700:#44403c 800:#292524 900:#1c1917
```

### 真灰（中性）

```
50:#fafafa  100:#f4f4f5  200:#e4e4e7  300:#d4d4d8  400:#a1a1aa
500:#71717a 600:#52525b 700:#3f3f46 800:#27272a 900:#18181b
```

用法：`900` 深文字、`500` 次文字、`100` 背景、`200` 边框、`50` 卡片底。

---

## 语义色模板

```
success: 500 阶绿 (#22c55e)   success-bg: 50 阶 (#f0fdf4)
warning: 橙/黄 (#f59e0b)      warning-bg: (#fffbeb)
error:   500 阶红 (#ef4444)   error-bg:   50 阶 (#fef2f2)
info:    500 阶蓝 (#3b82f6)   info-bg:    50 阶 (#eff6ff)
```

每语义色配浅底（`-bg`）做横幅 / 标签背景。

---

## 主题色板（成套推荐）

### A · 现代 SaaS（蓝主 + 冷灰）

```
primary:  #2563eb (blue-600)    neutral: 冷灰阶
accent:   #7c3aed (violet-600)
success:#16a34a  warning:#d97706  error:#dc2626  info:#2563eb
bg:#ffffff  bg-subtle:#f8fafc  text:#0f172a  border:#e2e8f0
```

### B · 暖意消费（橙主 + 暖灰）

```
primary:  #ea580c (orange-600)  neutral: 暖灰阶
accent:   #0891b2 (cyan-600)
success:#16a34a  warning:#ca8a04  error:#dc2626  info:#0284c7
bg:#fffbeb  bg-subtle:#fef3c7  text:#292524  border:#e7d8c4
```

### C · 极简黑白（黑主 + 真灰）

```
primary:  #18181b (gray-900)    neutral: 真灰阶
accent:   #3b82f6 (blue-500)
success:#16a34a  warning:#d97706  error:#dc2626  info:#2563eb
bg:#ffffff  bg-subtle:#fafafa  text:#18181b  border:#e4e4e7
```

### D · 创意活力（紫主，三元配色）

```
primary:  #9333ea (purple-600)  neutral: 冷灰阶
accent:   #f97316 (orange-500)   secondary-accent:#10b981 (emerald)
success:#10b981  warning:#f59e0b  error:#ef4444  info:#3b82f6
bg:#faf5ff  bg-subtle:#f3e8ff  text:#1e293b  border:#e9d5ff
```

---

## 暗模式派生

暗模式不是亮色取反。规则：

- 主色提亮一档（`600` → `400`），暗底上才显眼
- 中性阶反转：`900` 变背景、`50` 变文字，但降饱和（带蓝灰）
- 语义色提亮、降饱和
- 背景用深蓝灰（`#0d1117` / `#0f172a`）非纯黑
- 边框用微亮（`#30363d`）显分区

每套主题色板都应派生对应暗色版。详见 [accessibility.md](accessibility.md) 暗模式段。

---

## 自定义品牌色扩阶

用户给一个主色 → 生成全阶：

1. 转 HSL
2. 固定色相，参考分段调饱和明度：

```
50:  L=96% S=主色饱和×0.5
100: L=90% S=×0.6
200: L=80% S=×0.7
300: L=70% S=×0.85
400: L=62% S=×0.95
500: 用户主色（基准）
600: L=45% S=×1.05
700: L=38% S=×1.1
800: L=30% S=×1.1
900: L=22% S=×1.05
```

3. 微调使各阶感知均匀（目测相邻阶差相近）

## 自检清单

- [ ] 色板含主色阶 + 中性阶 + 语义色
- [ ] 中性阶带色温
- [ ] 主色比例 60-30-10
- [ ] 选定成套主题（A/B/C/D 之一或自定义）
- [ ] 派生暗模式版
- [ ] 语义色跨主题一致
