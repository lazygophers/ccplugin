# App 媒介 · 设计风格与配色模板

App 风格受平台语言（Human Interface Guidelines / Material 3）影响，但仍有品牌表达空间。本文件给选型方法论 + **现成主题模板**（iOS / Android / 桌面各一套，含配色 token）。布局见 [layout.md](layout.md)，场景见 [scenes.md](scenes.md)，组件见 [components.md](components.md)。

## 选型流程

1. **定语境**：受众、品类（工具 / 消费 / 内容 / 企业）、情绪
2. **出三方向**：平台倾向 + 风格组合，差异化
3. **并排对比**：真机或高保真原型上选
4. **固化 token**：写成色值 / 字号阶 / 圆角 / 间距 token，全局复用

## 风格谱系（App 语境）

| 风格 | 平台倾向 | 气质 |
|------|---------|------|
| Apple HIG | iOS | 系统毛玻璃、大标题、圆角卡片 |
| Material 3 | Android | Dynamic Color、大圆角、层级色调 |
| Fluent | Windows | 亚克力、深度层、Reveal |
| 极简原生 | 跨平台 | 系统色 + 克制 |
| 活力卡通风 | 消费 / 教育 | 饱和、圆润、插画 |

---

## 现成主题模板（token 复制即用）

### 模板 1 · Apple HIG 风（iOS）

```
bg:           #F2F2F7  (systemGroupedBackground)
bg-secondary: #FFFFFF  (systemBackground)
text:         #1C1C1E
text-muted:   #8E8E93
separator:    #C6C6C8
primary:      #007AFF  (systemBlue)
accent:       #5856D6  (systemPurple)
success:      #34C759  warning: #FF9500  error: #FF3B30
radius-card:  12pt   radius-button: 10pt
tap-target:   44pt
font:         SF Pro / 系统中文
motion:       弹性缓动 (spring)
```
暗模式：bg→`#000000`，bg-secondary→`#1C1C1E`，text→`#FFFFFF`，separator→`#38383A`。

### 模板 2 · Material 3 风（Android）

```
bg:           #FEF7FF  (surface)
bg-secondary: #FFFFFF
text:         #1D1B20
text-muted:   #49454F
outline:      #79747E
primary:      #6750A4  primary-container: #EADDFF
secondary:    #625B71  tertiary: #7D5260
success:      #386A20  warning: #7C5800  error: #BA1A1A
radius-small: 8dp   radius-medium: 12dp   radius-large: 16dp   radius-full: 28dp
tap-target:   48dp
font:         Roboto / 系统中文
motion:       Material motion (emphasized)
```
暗模式：bg→`#141218`，bg-secondary→`#211F26`，text→`#E6E0E9`，primary→`#D0BCFF`。

### 模板 3 · 桌面 Fluent / Neutral 风

```
bg:           #F3F3F3  (solidBackground)
bg-secondary: #FFFFFF  (layer)
text:         #1A1A1A  text-muted: #6B6B6B
divider:      #E5E5E5
primary:      #005FB8  (accentDefault)
accent-2:     #0078D4
success:      #0F7B0F  warning: #9D5D00  error: #C42B1C
radius:       4px (桌面偏小圆角)
shadow-2:     0 2px 8px rgba(0,0,0,0.12)
font:         Segoe UI / system-ui / 系统中文
density:      紧凑可选 (8px grid)
```

### 模板 4 · 消费活力风（跨平台，电商 / 社交）

```
bg:           #FFFFFF
bg-subtle:    #FFF5F5
text:         #1A1A1A  text-muted: #8A8A8A
border:       #FFE0E0
primary:      #FF4D4F  (品牌红/橙系，高饱和)
primary-hover:#FF7875  primary-contrast:#FFFFFF
accent:       #FA8C16
success:      #52C41A  warning: #FAAD14  error: #FF4D4F  info: #1890FF
radius-card:  16  radius-button: 24 (胶囊)
font:         圆润无衬线
```

### 模板 5 · 极简原生风（跨平台）

```
bg:           #FFFFFF  bg-subtle: #F7F7F7
text:         #111111  text-muted: #6B7280
border:       #E5E7EB
primary:      #111111  (黑主色，克制)
accent:       #3B82F6
success:      #16A34A  warning: #D97706  error: #DC2626
radius:       12
tap-target:   44/48
```

---

## 平台覆盖速查（每平台 token 差异）

| 平台 | 主色取法 | 圆角 | 点击区 | 字体 | 关键约束 |
|------|---------|------|--------|------|---------|
| iOS / iPhone | systemBlue `#007AFF` | 12pt 卡 / 10pt 按钮 | 44pt | SF Pro | safe-area、Dynamic Type |
| iPadOS | 同 iOS + 分栏 / Stage Manager | 12pt | 44pt | SF Pro | split-view、多窗口；侧栏 320pt 起 |
| watchOS | 饱和度 +20%（小屏弱光）| 16pt（圆屏大圆角）| 44pt | SF Rounded | 单列、禁复杂表格、≤4 项/屏、glanceable |
| tvOS | focus 引擎放大聚焦项 | 16pt | focus 引擎（非点击）| SF Pro Display | 10ft 远距离、字号大、禁密集交互、parallax 图标 |
| macOS / Win 桌面 | 见模板 3 Fluent | 4-8px（紧凑）| 鼠标精度 | Segoe UI / SF Text | 菜单栏 / 右键菜单 / 多窗口 |
| Android Phone | Material 3 `#6750A4` | 8/12/16/28dp | 48dp | Roboto | Material elevation、edge-to-edge |
| Android Tablet | 同上 + 多窗 / 分屏 | 同上 | 48dp | Roboto | NavigationRail（非 BottomBar）、list-detail |
| Wear OS | 高饱和、大字 | 屏幕圆角 | 边缘 swipe | Roboto | 圆屏适配、≤3 项/屏、ambient 模式降色 |

### 跨平台复用原则

- **同一品牌色**全平台统一（主色 hex 不变），但密度 / 圆角 / 字号按平台调
- **语义色用系统色**（iOS systemRed vs Material error），保证原生熟悉感
- **tap-target**：iOS 44pt / Material 48dp 是硬下限，重叠区取大值（48）
- **暗模式**：各平台系统色暗态不同，别用一套暗 token 硬套——iOS 暗底纯黑 `#000`，Material 暗底带紫 `#141218`

## 配色决策

### 色板构成（每项目必备）

- 主色（1）、辅助色（1-2）、中性阶（5-7）、语义色（4）、背景色（2-3）
- 平台语义色优先用系统色（iOS systemBlue / Material 色调），保证熟悉感

### 可访问性硬指标

- 文字背景对比 ≥ 4.5:1（正文）/ ≥ 3:1（大字）
- 禁只靠颜色传信息，加图标 / 文字冗余
- 暗模式重调中性阶、降饱和、提对比
- Dynamic Type / Font Scale 下配色对比仍达标

### 动效与图标

- 动效遵循平台（iOS spring / Material emphasized）
- 图标用平台系统库（SF Symbols / Material Symbols）优先，语义一致
- 自定义图标与系统图标视觉重量匹配

## 字号阶（App 通用）

```
caption: 12   footnote: 13   body: 16   callout: 16
subheadline: 15   headline: 17   title: 20   largeTitle: 34
```

## 自检

- [ ] 配色对比达标（亮 / 暗）
- [ ] 平台语义色对齐
- [ ] token 化，换肤一处生效
- [ ] 图标用系统库优先
