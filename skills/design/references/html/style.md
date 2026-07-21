# HTML 媒介 · 设计风格与配色模板

风格不是「好看就行」，是「匹配受众、场景、品牌情绪」。本文件给选型方法论 + **现成可用的主题模板**（配色、字号阶、圆角、阴影 token，复制即用）。布局见 [layout.md](layout.md)，场景切换见 [scenes.md](scenes.md)，组件见 [components.md](components.md)。

## 选型流程

1. **定语境**：受众？场景（营销 / 工具 / 内容 / 企业）？情绪关键词？
2. **出三方向**（三方向硬门）：每方向一套「风格 + 配色 + 字体」组合，真实分化
3. **并排对比**：真实初稿上选，不在抽象描述上选
4. **固化 token**：选定后写成本项目 CSS 变量，全局复用

## 风格谱系（选方向参照）

| 风格 | 气质 | 配色倾向 | 适用 |
|------|------|---------|------|
| 极简留白 | 克制、高级 | 单色 + 负空间、低饱和 | 高端品牌、内容站 |
| 深空暗场 | 专业、沉浸 | `#0d1117` + 高对比强调 | 开发者工具、看板 |
| 杂志编辑 | 权威、阅读感 | 衬线标题 + 米白 + 墨色 | 报告、长文 |
| 玻璃拟物 | 现代、轻盈 | 半透明模糊 + 柔渐变 | 消费 App、落地页 |
| Neo-brutalism | 张扬、年轻 | 高饱和块 + 粗黑边 + 硬阴影 | 潮牌、Z 世代 |
| Material / 平面 | 清晰、规范 | 中性灰 + 品牌主色 + 层级阴影 | 企业工具 |
| 暖色手绘 | 亲切、温度 | 暖调 + 线条插画 | 教育、社区 |

---

## 现成主题模板（复制即用）

每个模板一组完整 CSS 变量（亮 + 暗），含背景 / 文字 / 主色 / 辅色 / 语义色 / 边框。用法：贴到 `:root`，组件全用 `var(--xxx)`。

### 模板 1 · 极简留白（Minimal Light）

```css
:root {
  --bg:#ffffff; --bg-subtle:#f7f7f8; --card:#ffffff;
  --text:#111111; --text-muted:#6b7280;
  --border:#e5e7eb;
  --primary:#111111; --primary-hover:#333333; --primary-contrast:#ffffff;
  --accent:#3b82f6;
  --success:#16a34a; --warning:#d97706; --error:#dc2626; --info:#2563eb;
  --radius:12px; --shadow:0 1px 3px rgba(0,0,0,0.08);
  --font-sans:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
}
[data-theme="dark"] {
  --bg:#0d0d0f; --bg-subtle:#18181b; --card:#161618;
  --text:#fafafa; --text-muted:#a1a1aa;
  --border:#27272a;
  --primary:#fafafa; --primary-hover:#e4e4e7; --primary-contrast:#0d0d0f;
}
```
气质：性冷淡、大留白、黑主色。适合内容站、高端品牌、Apple 系。

### 模板 2 · 深空暗场（Deep Space）

```css
:root {
  --bg:#0d1117; --bg-subtle:#161b22; --card:#161b22;
  --text:#e6edf3; --text-muted:#8b949e;
  --border:#30363d;
  --primary:#58a6ff; --primary-hover:#79b8ff; --primary-contrast:#0d1117;
  --accent:#bc8cff;
  --success:#3fb950; --warning:#d29922; --error:#f85149; --info:#58a6ff;
  --radius:8px; --shadow:0 0 0 1px rgba(255,255,255,0.06);
  --font-sans:-apple-system,"PingFang SC",sans-serif;
  --font-mono:"SF Mono",ui-monospace,monospace;
}
[data-theme="light"] {  /* 暗场为默认，亮态作可选 */
  --bg:#ffffff; --bg-subtle:#f6f8fa; --card:#ffffff;
  --text:#24292f; --text-muted:#57606a;
  --border:#d0d7de; --primary:#0969da; --accent:#8250df;
}
```
气质：GitHub / 开发者工具风。适合技术产品、数据看板、IDE。

### 模板 3 · 杂志编辑（Editorial）

```css
:root {
  --bg:#fafaf7; --bg-subtle:#f0ede5; --card:#ffffff;
  --text:#1a1a1a; --text-muted:#6b6b6b;
  --border:#d9d6ce;
  --primary:#8b1e1e; --primary-hover:#a52828; --primary-contrast:#ffffff;
  --accent:#1a1a1a;
  --success:#2d6a4f; --warning:#b7791f; --error:#9b2c2c; --info:#2c5282;
  --radius:2px; --shadow:none;
  --font-serif:"Georgia","Songti SC","Source Han Serif",serif;
  --font-sans:-apple-system,"PingFang SC",sans-serif;
}
```
气质：报刊、衬线标题、墨色正文、红强调。适合报告、出版物、长文。

### 模板 4 · 玻璃拟物（Glassmorphism）

```css
:root {
  --bg:#eef2ff; --bg-subtle:#e0e7ff; --card:rgba(255,255,255,0.6);
  --text:#1e293b; --text-muted:#64748b;
  --border:rgba(255,255,255,0.5);
  --primary:#6366f1; --primary-hover:#818cf8; --primary-contrast:#ffffff;
  --accent:#ec4899;
  --success:#10b981; --warning:#f59e0b; --error:#ef4444; --info:#3b82f6;
  --radius:20px;
  --shadow:0 8px 32px rgba(31,38,135,0.15);
  --glass-blur:blur(16px);
  --gradient:linear-gradient(135deg,#667eea,#764ba2);
}
```
气质：半透明、模糊背景、柔渐变。需配合 `backdrop-filter:var(--glass-blur)`。适合消费 App、落地页。

### 模板 5 · Neo-Brutalism（新野兽派）

```css
:root {
  --bg:#fef9c3; --bg-subtle:#fef08a; --card:#ffffff;
  --text:#000000; --text-muted:#404040;
  --border:#000000;
  --primary:#7c3aed; --primary-hover:#6d28d9; --primary-contrast:#ffffff;
  --accent:#ec4899;
  --success:#22c55e; --warning:#f97316; --error:#ef4444; --info:#3b82f6;
  --radius:0px;
  --shadow-brutal:4px 4px 0px #000000;  /* 硬阴影 */
  --border-brutal:3px solid #000000;     /* 粗黑边 */
}
```
气质：高饱和、粗黑边、硬偏移阴影、直角。适合潮牌、创意 agency、Z 世代。

### 模板 6 · Material 平面（企业规范）

```css
:root {
  --bg:#fafafa; --bg-subtle:#f5f5f5; --card:#ffffff;
  --text:#212121; --text-muted:#757575;
  --border:#e0e0e0;
  --primary:#1976d2; --primary-hover:#1565c0; --primary-contrast:#ffffff;
  --accent:#ff9800;
  --success:#388e3c; --warning:#f57c00; --error:#d32f2f; --info:#1976d2;
  --radius:4px;
  --shadow-1:0 1px 3px rgba(0,0,0,0.12),0 1px 2px rgba(0,0,0,0.24);
  --shadow-2:0 3px 6px rgba(0,0,0,0.16),0 3px 6px rgba(0,0,0,0.23);
}
```
气质：Google Material、中性 + 蓝、层级阴影。适合企业工具、后台、Android。

### 模板 7 · 暖色手绘（Warm Hand-drawn）

```css
:root {
  --bg:#fff8f0; --bg-subtle:#ffedd5; --card:#fffaf3;
  --text:#44403c; --text-muted:#78716c;
  --border:#e7d8c4;
  --primary:#ea580c; --primary-hover:#c2410c; --primary-contrast:#ffffff;
  --accent:#0891b2;
  --success:#16a34a; --warning:#ca8a04; --error:#dc2626; --info:#0284c7;
  --radius:16px;
  --shadow:0 2px 8px rgba(234,88,12,0.12);
  --font-sans:"Comic Sans MS","PingFang SC",cursive,sans-serif;  /* 视情况换圆润体 */
}
```
气质：暖橙、圆角、亲切。适合教育、社区、儿童产品。

---

## 字号阶模板（所有风格通用）

```css
--text-xs:12px; --text-sm:14px; --text-base:16px; --text-lg:18px;
--text-xl:20px; --text-2xl:24px; --text-3xl:30px; --text-4xl:36px;
--text-5xl:48px; --text-6xl:60px;
```

## 间距阶模板

```css
--space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px;
--space-6:24px; --space-8:32px; --space-12:48px; --space-16:64px;
```

## 配色色系决策

### 色板构成（每项目必备）

- **主色**（1）：品牌识别、主按钮、关键强调
- **辅助色**（1-2）：次级强调、分类标签
- **中性色**（5-7 阶）：最深文字 → 最浅背景灰阶
- **语义色**（4）：success / warning / error / info
- **背景色**（2-3）：页面底、卡片底、悬浮态

### 色板推荐（感知均匀、可访问）

| 色板 | 特点 | 适用 |
|------|------|------|
| Okabe-Ito | 色盲安全 8 色 | 数据可视化、分类编码 |
| Tailwind default | 22 色 ×10 阶 | 通用 Web / App |
| Tab10 / Set2 | 经典分类色 | 图表 |
| 自建品牌色 | 用户主色 → HSL 拓阶 | 品牌项目 |

### 可访问性硬指标

- 文字与背景对比度 ≥ 4.5:1（WCAG AA 正文）/ ≥ 3:1（大字）
- 禁只靠颜色传信息（色盲用户），加图标 / 纹理 / 标签冗余
- 暗模式重调中性阶、降饱和、提对比

### 配色生成技巧

- 用户给主色 → HSL 旋转生互补 / 三元 / 类似色
- 中性阶用主色低饱和 + 调明度（带色温的灰，比纯灰高级）
- 渐变用同色相不同明度，禁跨色相乱渐变

## 字体气质搭配

| 风格 | 标题 | 正文 |
|------|------|------|
| 极简 / 杂志 | 系统衬线 / 大字号无衬线 | 系统无衬线 |
| 暗场技术 | 等宽点缀 + 无衬线 | 无衬线 |
| 编辑权威 | 衬线 | 系统中文衬线 |
| 现代 App | 几何无衬线 | 无衬线 |

中文：用系统栈（`-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif`），别引私有字体除非用户提供。
