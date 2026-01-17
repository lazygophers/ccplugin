# Dark Mode - 暗黑模式设计风格规范

暗黑模式设计采用深色背景和高对比文本，遵循 WCAG AAA 标准，确保可读性和可访问性。

## 核心特征

**视觉特性**：
- 背景：#0f172a 或 #111827
- 文本：#ffffff 或 #f3f4f6
- 对比度：≥7:1 (WCAG AAA)
- 柔和边框：使用 alpha 透明度

**颜色系统**：
```css
--bg-primary: #0f172a;    /* 深蓝黑 */
--bg-secondary: #1e293b;  /* 略浅背景 */
--bg-tertiary: #334155;   /* 卡片背景 */
--text-primary: #f1f5f9;  /* 主文本 */
--text-secondary: #cbd5e1;/* 次要文本 */
--border: rgba(203, 213, 225, 0.15);
```

## 对比度检查

```
AAA 级别要求：
- 正文：7:1
- 大文本（18pt+）：4.5:1
- UI 组件边框：3:1

工具：WebAIM Contrast Checker
```

## 实现要点

**CSS 变量系统**：
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f172a;
    --text: #f1f5f9;
    --border: rgba(203, 213, 225, 0.15);
  }
}
```

**蓝光优化**：
```css
/* 减少蓝光成分 */
body {
  background: #0f172a;  /* 避免纯黑 */
}
```

## 应用场景

- 🌙 所有应用的暗色主题
- 💻 编辑器和 IDE
- 📱 夜间模式
- 🎮 游戏界面

## 色彩层级

| 用途 | HEX | RGB |
|------|-----|-----|
| 最深背景 | #0a0e27 | 10,14,39 |
| 主背景 | #0f172a | 15,23,42 |
| 卡片 | #1e293b | 30,41,59 |
| 浮层 | #334155 | 51,65,85 |
| 边框 | #475569 | 71,85,105 |

## DO & DON'T

✅ **DO**:
- 定期检测对比度
- 使用 prefers-color-scheme 媒体查询
- 提供切换选项
- 测试各种光线条件

❌ **DON'T**:
- 使用纯黑背景（#000000）
- 纯白文本（#ffffff）
- 饱和的彩色元素
- 忽视电池影响（OLED）

## 浏览器支持

- Chrome 76+: ✅
- Safari 13+: ✅
- Firefox 67+: ✅
- Edge 76+: ✅

## 参考资源

- WCAG 2.1 对比度指南
- Apple Dark Mode HIG
- Material Design 3 Dark Theme
