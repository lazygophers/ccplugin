# 配置参考

以下是完整的实现指南和最佳实践：

# Dark Mode - 暗黑模式设计风格规范

暗黑模式设计采用深色背景和高对比文本，遵循 WCAG AAA 标准（7:1 对比度），确保可读性和可访问性。

## 核心特征

**视觉基础**：
- 背景：#0f172a（深蓝黑）
- 文本：#f1f5f9（浅灰白）
- 对比度：≥7:1（WCAG AAA）
- 蓝光优化：避免纯黑，使用 #0f172a

**应用场景**：
- 🌙 所有应用的暗色主题
- 💻 编辑器和 IDE
- 📱 夜间模式
- 🎮 游戏界面

## 快速开始

```css
:root {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --border: rgba(203, 213, 225, 0.15);
}

@media (prefers-color-scheme: dark) {
  body {
    background: var(--bg-primary);
    color: var(--text-primary);
  }
}
```

## 详细指南

完整的配置规范和颜色系统，请参阅 [reference.md](reference.md)

实现示例和最佳实践，请参阅 [examples.md](examples.md)

## 关键要点

✅ **DO**:
- 定期使用工具检测对比度
- 使用 prefers-color-scheme 媒体查询
- 提供手动切换选项
- 在各种光线条件下测试

❌ **DON'T**:
- 使用纯黑背景（#000000）
- 使用纯白文本（#ffffff）
- 过度饱和的彩色元素
- 忽视 OLED 屏幕的电池影响

## 浏览器支持

所有现代浏览器均支持（Chrome 76+, Safari 13+, Firefox 67+, Edge 76+）

## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
