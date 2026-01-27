---
name: glassmorphism
description: 玻璃态设计通过模糊、透明和分层来创建优雅的现代 UI，提供视觉深度和虚实感。
---

Glassmorphism - 玻璃态设计风格规范

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

## 详细指南

完整的配置规范和实现细节，请参阅 [reference.md](reference.md)

使用示例和最佳实践，请参阅 [examples.md](examples.md)
