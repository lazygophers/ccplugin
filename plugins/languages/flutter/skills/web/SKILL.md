---
name: web
description: Flutter Web 开发规范：Web 性能优化、PWA 支持、响应式设计。开发 Web 应用时必须加载。
---

# Flutter Web 开发规范

## 相关 Skills

| 场景     | Skill        | 说明                  |
| -------- | ------------ | --------------------- |
| 核心规范 | Skills(core) | Flutter 核心规范      |
| UI 开发  | Skills(ui)   | Widget 组合、构建优化 |

## 性能目标

- **FCP**: <2s
- **LCP**: <2.5s
- **TTI**: <3s

## 性能优化

```dart
// 延迟加载
Future<void> loadModule() async {
  await import('module.dart');
}

// 图片优化
Image.network(
  url,
  cacheWidth: 800,
  cacheHeight: 600,
)

// 使用 HtmlElementView（高级）
HtmlElementView(viewType: 'my-html-view')
```

## PWA 支持

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_web_plugins:
    sdk: flutter
```

## 响应式设计

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const MobileLayout();
    } else if (constraints.maxWidth < 1200) {
      return const TabletLayout();
    } else {
      return const DesktopLayout();
    }
  },
)
```

## 检查清单

- [ ] FCP <2s
- [ ] LCP <2.5s
- [ ] 使用响应式设计
- [ ] 图片优化
- [ ] PWA 支持
