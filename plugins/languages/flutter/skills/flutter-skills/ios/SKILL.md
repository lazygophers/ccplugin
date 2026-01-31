---
name: flutter-ios-skills
description: Flutter iOS 开发规范 - iOS 平台特定的开发指南、Cupertino 设计系统、性能优化和测试规范
---

# Flutter iOS 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[cupertino.md](cupertino.md)** | Cupertino 设计系统详解、iOS 原生组件、导航模式 | iOS 应用开发 |
| **[performance.md](performance.md)** | iOS 性能优化、内存管理、帧率优化 | iOS 性能调优 |
| **[testing.md](testing.md)** | iOS 测试规范、权限测试、SafeArea 测试 | iOS 测试编写 |

## iOS 开发核心理念

Flutter iOS 开发追求**原生 iOS 体验、遵循 Apple 设计规范、高性能实现**。三个支柱：

1. **Cupertino 设计系统** - 使用 Cupertino 组件提供真正的 iOS 原生体验
2. **性能优化** - 针对 iOS 设备的帧率、内存和启动优化
3. **iOS 系统集成** - 权限处理、SafeArea、通知等 iOS 特有功能

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **iOS**: iOS 11.0+
- **Xcode**: 最新稳定版
- **开发工具**: Xcode / VS Code + Flutter 扩展

## iOS 特定规范

### 使用 Cupertino 组件

```dart
// ✅ 正确：使用 Cupertino 组件
CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
  ),
  home: const CupertinoPageScaffold(
    navigationBar: CupertinoNavigationBar(
      middle: Text('My App'),
    ),
    child: Center(child: Text('Hello iOS')),
  ),
)

// ❌ 错误：在 iOS 应用中使用 Material 组件
MaterialApp(
  theme: ThemeData(
    primaryColor: Colors.blue,
  ),
  home: Scaffold(
    appBar: AppBar(title: Text('My App')),
    body: Center(child: Text('Hello iOS')),
  ),
)
```

### iOS 导航模式

```dart
// ✅ 正确：使用 CupertinoPageRoute
Navigator.push(
  context,
  CupertinoPageRoute(
    builder: (context) => const NextPage(),
    title: 'Next Page',
  ),
)

// ❌ 错误：使用 MaterialPageRoute
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => const NextPage()),
)
```

### 处理 SafeArea

```dart
// ✅ 正确：使用 SafeArea 处理刘海屏
SafeArea(
  child: YourContent(),
)

// ✅ 也正确：CupertinoApp 自动处理
CupertinoApp(
  home: const CupertinoPageScaffold(
    child: YourContent(),
  ),
)
```

## iOS 性能目标

- **帧率**: 60 FPS（标准设备）、120 FPS（Pro 设备）
- **内存**: 冷启动 <150MB，运行时 <250MB
- **启动**: 冷启动 <1.5s，温启动 <400ms
- **响应**: 交互响应 <50ms

## iOS 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **设备测试**: 真实 iPhone 设备（非仅模拟器）

## 常见问题

### 如何混合使用 Cupertino 和 Material？

不建议混合使用。选定一个设计系统并一致应用。如果必须在同一应用中支持两个平台：

```dart
Widget build(BuildContext context) {
  if (Theme.of(context).platform == TargetPlatform.iOS) {
    return const CupertinoComponent();
  } else {
    return const MaterialComponent();
  }
}
```

### 如何处理 iOS 权限？

```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  final cameraStatus = await Permission.camera.request();
  if (cameraStatus.isDenied) {
    openAppSettings();
  }
}
```

## 参考资源

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/ios/)
- [Flutter Cupertino Widgets](https://api.flutter.dev/flutter/cupertino/cupertino-library.html)
- [iOS Design Themes](https://developer.apple.com/design/human-interface-guidelines/ios/visual-design/color/)

---

**记住**：使用 Cupertino 组件提供真正的 iOS 原生体验！
