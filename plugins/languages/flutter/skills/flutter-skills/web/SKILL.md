---
name: flutter-web-skills
description: Flutter Web 开发规范 - Web 平台特定的开发指南、性能优化和测试规范
---

# Flutter Web 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[performance.md](performance.md)** | Web 性能优化、加载速度、Core Web Vitals | Web 性能调优 |
| **[testing.md](testing.md)** | Web 测试规范、浏览器兼容性测试 | Web 测试编写 |

## Web 开发核心理念

Flutter Web 开发追求**快速加载、良好 SEO、浏览器兼容**。三个支柱：

1. **加载性能** - 优化首次加载时间和包大小
2. **响应式设计** - 适配不同屏幕尺寸
3. **PWA 支持** - 离线支持和安装能力

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **渲染器**: CanvasKit（推荐）或 HTML

## Web 特定规范

### 渲染器选择

```bash
# CanvasKit（功能完整，性能更好）
flutter build web --web-renderer canvaskit

# HTML（更快加载，功能受限）
flutter build web --web-renderer html
```

### 响应式设计

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth > 1200) {
      return const DesktopLayout();
    } else if (constraints.maxWidth > 600) {
      return const TabletLayout();
    } else {
      return const MobileLayout();
    }
  },
)
```

### URL 路由

```dart
// 使用 go_router 或 auto_route
MaterialApp.router(
  routerConfig: router,
)
```

## Web 性能目标

- **FCP**: <2 秒
- **LCP**: <2.5 秒
- **FID**: <100ms
- **CLS**: <0.1
- **包大小**: <2MB（压缩后）

## Web 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **浏览器测试**: 主流浏览器兼容性

## 常见问题

### 如何选择渲染器？

CanvasKit：功能完整、性能更好，适合复杂应用
HTML：加载更快、兼容性更好，适合简单应用

### 如何优化包大小？

```dart
// 使用 deferred loading
import 'package:flutter/material.dart' deferred as ui;
```

### 如何实现 PWA？

创建 manifest.json 和 Service Worker

## 参考资源

- [Flutter Web](https://flutter.dev/web)
- [Web.dev Performance](https://web.dev/performance/)
- [Core Web Vitals](https://web.dev/vitals/)

---

**记住**：优化加载速度是 Web 应用的关键！
