---
name: flutter-macos-skills
description: Flutter macOS 开发规范 - macOS 桌面应用开发指南、系统集成和性能优化
---

# Flutter macOS 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[performance.md](performance.md)** | macOS 性能优化、窗口管理、Apple Silicon 优化 | macOS 性能调优 |
| **[testing.md](testing.md)** | macOS 测试规范、窗口操作测试 | macOS 测试编写 |

## macOS 开发核心理念

Flutter macOS 开发追求**原生 macOS 体验、系统集成、高性能**。三个支柱：

1. **macOS UI 规范** - 遵循 macOS Human Interface Guidelines
2. **系统集成** - 菜单栏、文件系统、通知等
3. **Apple Silicon 优化** - 充分利用 M1/M2/M3 芯片性能

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **macOS**: 10.15 (Catalina) 或更高
- **Xcode**: 最新稳定版
- **架构**: x86_64 和 arm64 (Apple Silicon)

## macOS 特定规范

### 窗口管理

```dart
import 'package:flutter_macos/window_size.dart';

void main() async {
  await setWindowFrame(
    const Rect.fromLTWH(100, 100, 1200, 800),
  );
  await setWindowTitle('My macOS App');
  runApp(const MyApp());
}
```

### 菜单栏集成

```dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  if (Platform.isMacOS) {
    // 设置 macOS 菜单
    final submenu = [
      MenuItem(
        label: 'About My App',
        onClicked: () => showAboutDialog(),
      ),
      MenuDivider(),
      MenuItem(
        label: 'Quit',
        shortcut: LogicalKeySet(LogicalKeyboardKey.meta, LogicalKeyboardKey.q),
        onClicked: () => exit(0),
      ),
    ];
  }
  runApp(const MyApp());
}
```

### 文件系统访问

```dart
import 'package:file_selector/file_selector.dart';

Future<void> openFile() async {
  const fileTypeGroup = XTypeGroup(
    label: 'Images',
    extensions: ['jpg', 'png', 'gif'],
  );
  final file = await openFile(acceptedTypeGroups: [fileTypeGroup]);
  if (file != null) {
    // 处理文件
  }
}
```

## macOS 性能目标

- **启动**: <500ms (Apple Silicon)、<1s (Intel)
- **内存**: <200MB (空闲)、<500MB (活跃)
- **CPU**: 空闲 <5%、活跃 <30%
- **响应**: <50ms

## macOS 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **设备测试**: Intel 和 Apple Silicon

## 常见问题

### 如何处理窗口状态？

```dart
import 'package:shared_preferences/shared_preferences.dart';

Future<void> saveWindowState() async {
  final prefs = await SharedPreferences.getInstance();
  final frame = await getWindowFrame();
  await prefs.setDouble('window_x', frame.left);
  await prefs.setDouble('window_y', frame.top);
}
```

### 如何请求权限？

```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  final status = await Permission.photos.request();
  if (status.isDenied) {
    openAppSettings();
  }
}
```

## 参考资源

- [macOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/macos/)
- [Flutter Desktop](https://flutter.dev/multi-platform/desktop)
- [Apple Silicon Optimization](https://developer.apple.com/documentation/apple-silicon-optimizing)

---

**记住**：遵循 macOS Human Interface Guidelines！
