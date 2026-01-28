---
name: flutter-android
description: Flutter Android 开发规范 - Android 平台特定的开发指南、Material 3 设计系统、性能优化和测试规范
---

# Flutter Android 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[material3.md](material3.md)** | Material Design 3 详解、Expressive 特性、动态颜色系统 | Android 应用开发 |
| **[performance.md](performance.md)** | Android 性能优化、内存管理、帧率优化 | Android 性能调优 |
| **[testing.md](testing.md)** | Android 测试规范、权限测试、Material 3 测试 | Android 测试编写 |

## Android 开发核心理念

Flutter Android 开发追求**Material Design 3 体验、遵循 Android 规范、高性能实现**。三个支柱：

1. **Material Design 3** - 使用 Material 3 组件提供现代 Android 体验
2. **性能优化** - 针对 Android 设备碎片化的性能优化
3. **Android 系统集成** - 权限处理、通知、深链接等 Android 特有功能

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **Android**: API 21+ (Android 5.0+)
- **编译 SDK**: 最新 Android SDK
- **开发工具**: Android Studio / VS Code + Flutter 扩展

## Android 特定规范

### 使用 Material 3 组件

```dart
// ✅ 正确：使用 Material 3
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
    ),
  ),
  home: Scaffold(
    appBar: AppBar(title: const Text('My App')),
    body: const Center(child: Text('Hello Android')),
  ),
)

// ❌ 错误：在 Android 应用中使用 Cupertino 组件
CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
  ),
  home: const CupertinoPageScaffold(
    child: Center(child: Text('Hello Android')),
  ),
)
```

### Android 导航模式

```dart
// ✅ 正确：使用 MaterialPageRoute
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => const NextPage(),
  ),
)

// ❌ 错误：在 Android 应用中使用 CupertinoPageRoute
Navigator.push(
  context,
  CupertinoPageRoute(
    builder: (context) => const NextPage(),
  ),
)
```

### Android 权限处理

```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  final cameraStatus = await Permission.camera.request();
  if (cameraStatus.isPermanentlyDenied) {
    openAppSettings();
  }

  // Android 13+ 细粒度权限
  final photosStatus = await Permission.photos.request();
  final notificationStatus = await Permission.notification.request();
}
```

## Android 性能目标

- **帧率**: 60 FPS（标准设备）、90/120 FPS（高刷屏）
- **内存**: 冷启动 <100MB，运行时 <200MB
- **启动**: 冷启动 <2s，温启动 <500ms
- **响应**: 交互响应 <80ms

## Android 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **设备测试**: 真实 Android 设备（不同厂商）

## 常见问题

### 如何处理不同厂商的 ROM？

测试主流厂商设备：
- Xiaomi (MIUI)
- Samsung (One UI)
- OnePlus (OxygenOS)
- OPPO/vivo (ColorOS/FuntouchOS)

### 如何处理 Android 返回按钮？

```dart
PopScope(
  canPop: false,
  onPopInvoked: (didPop) async {
    if (didPop) return;
    final shouldPop = await showExitConfirmation();
    if (shouldPop && context.mounted) {
      context.pop();
    }
  },
  child: Scaffold(...),
)
```

### 如何启用 Material 3 Expressive？

```dart
ThemeData(
  useMaterial3: true,  // 自动启用 Expressive
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
  ),
)
```

## 参考资源

- [Material Design 3](https://m3.material.io/)
- [Material 3 Flutter](https://m3.material.io/develop/flutter)
- [Android Developer Guide](https://developer.android.com/guide)

---

**记住**：使用 Material 3 组件提供现代 Android 体验！
