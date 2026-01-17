# 配置参考

以下是完整的实现指南和最佳实践：

# Glassmorphism - 玻璃态设计风格规范

玻璃态设计通过模糊、透明和分层来创建优雅的现代 UI，提供视觉深度和虚实感。

## 核心特征

**视觉特性**：
- 半透明背景（80-90% 背景可见度）
- 背景模糊效果（10-20px blur）
- 微妙的边界（1px 半透明边框）
- 分层深度（通过 z-index 和阴影）

**颜色系统**：
```css
/* 玻璃层颜色（RGBA 格式） */
--glass-light: rgba(255, 255, 255, 0.15);
--glass-medium: rgba(255, 255, 255, 0.25);
--glass-dark: rgba(0, 0, 0, 0.15);

/* 背景颜色 */
--bg-primary: #0f172a;
--bg-secondary: #1e293b;
--text-primary: #ffffff;
```

**阴影系统**：
```css
--shadow-sm: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-md: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 20px 25px rgba(0, 0, 0, 0.15);
```

## 实现要点

**CSS 关键属性**：
```css
.glass {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
}
```

**Tailwind 配置**：
```javascript
backgroundColor: {
  'glass': 'rgba(255, 255, 255, 0.15)',
}
backdropBlur: {
  'glass': '10px',
}
```

## 应用场景

- 📱 现代应用界面（macOS Big Sur 风格）
- 💼 SaaS 仪表板（金融科技）
- 🎮 游戏 UI（覆盖层）
- 📸 相片应用（浮动卡片）

## DO & DON'T

✅ **DO**:
- 确保背景图片对比清晰
- 文本对比度 ≥ 4.5:1 (WCAG)
- 使用渐变增强深度感
- 配合现代字体（Inter、Syne）

❌ **DON'T**:
- 过度使用（避免一屏多个玻璃层）
- 模糊度过高导致内容不清
- 使用在信息密集区域
- 忽视暗色背景下的对比

## 响应式考虑

| 设备 | 推荐 |
|------|------|
| Mobile | 调整 blur 为 8px |
| Tablet | 标准 10-12px |
| Desktop | 12-15px |

## 参考资源

- Apple HIG - Glassmorphism Design
- Windows 11 - Fluent Design System
- [Glassmorphism.io](https://glassmorphism.com/)


## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
