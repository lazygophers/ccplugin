# HTML 媒介 · 场景自适应

同一 HTML 产物要适配多种使用场景。场景维度决定何时切换、切换什么。本文件管「场景」，布局结构见 [layout.md](layout.md)，组件见 [components.md](components.md)；色彩 / 配色在姊妹 skill `design-color`。

## 场景维度速查

| 场景轴 | 切换什么 | 触发 |
|--------|---------|------|
| 亮 / 暗模式 | 中性阶、背景、边框、阴影 | 系统偏好 / 手动 |
| 密度（紧凑 / 舒适） | 间距尺度、行高、内边距 | 用户偏好 / 内容量 |
| 视口宽度 | 列数、导航形态、侧栏显隐 | 响应式断点 |
| 容器宽度 | 组件形态（组件级自适应） | 容器查询 |
| 输入方式 | 悬停态、焦点态、光标 | 鼠标 / 触摸 / 键盘 |
| 动效偏好 | 转场、过渡是否启用 | `prefers-reduced-motion` |
| 对比偏好 | 强化对比、加大字 | `prefers-contrast` |
| 输出形态 | 同一 HTML 导出 PNG/SVG/PDF/微信 | 见 姊妹 skill `design-color` 的 html/export |

## 亮 / 暗模式

```css
:root { --bg:#fff; --text:#111; --card:#f5f5f5; --border:#e5e5e5; }
[data-theme="dark"] { --bg:#0d1117; --text:#e6e6e6; --card:#161b22; --border:#30363d; }
body { background:var(--bg); color:var(--text); }
```

要点：

- 暗模式不是亮色取反：重新调中性阶、降饱和、提文字对比
- 暗底上硬阴影看不见，改用亮边框 / 微亮区分层
- 图片 / 图表配色随主题切（定义 `--chart-1` 等 token）
- 跟随系统：`@media (prefers-color-scheme: dark)`，并给手动切换开关

## 密度切换

```css
[data-density="compact"]      { --space-unit: 0.75; }
[data-density="cozy"]         { --space-unit: 1; }
[data-density="comfortable"]  { --space-unit: 1.25; }
```

数据密集后台给「紧凑」选项；消费产品默认「舒适」。所有间距 = 基础尺度 × `--space-unit`，一处改全局生效。

## 响应式断点（视口场景）

移动优先（min-width 上叠），每个断点改「布局结构」非颜色：

| 断点 | 宽度 | 结构变化 |
|------|------|---------|
| 默认 | <640px | 单列堆叠、抽屉导航 |
| sm | ≥640px | 双列、横排按钮 |
| md | ≥768px | 侧栏出现、栅格展开 |
| lg | ≥1024px | 三列、固定侧栏、桌面密度 |
| xl | ≥1280px | 多列大屏 |

## 容器查询（组件级场景）

组件比视口更适合用容器查询——同卡片在侧栏窄、主区宽，自动改形态：

```css
.card { container-type: inline-size; }
@container (min-width: 400px) { .card .media { display:block; } }
@container (max-width: 200px) { .card .meta { display:none; } }
```

## 输入方式场景

- 触摸：触控目标 ≥44px、禁 hover-only 交互、放大间距
- 键盘：`focus-visible` 可见、Tab 顺序合理、跳过链接
- 鼠标：可提供 hover 增强（但不依赖）

检测：`@media (hover: hover) and (pointer: fine)`。

## 动效与无障碍场景

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:0.01ms !important; transition-duration:0.01ms !important; }
}
@media (prefers-contrast: more) { /* 提对比 */ }
```

## 场景自检

- [ ] 亮 / 暗模式均可读（如项目要求）
- [ ] 移动 → 桌面断点结构合理，无横向滚动
- [ ] 触摸目标达标
- [ ] 动效尊重 `prefers-reduced-motion`
- [ ] 焦点可见、键盘可达
