---
name: flutter-windows
description: Flutter Windows 开发规范 - Windows 桌面应用开发指南、系统集成和性能优化
---

# Flutter Windows 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[performance.md](performance.md)** | Windows 性能优化、窗口管理、COM 互操作 | Windows 性能调优 |
| **[testing.md](testing.md)** | Windows 测试规范、注册表测试 | Windows 测试编写 |

## Windows 开发核心理念

Flutter Windows 开发追求**原生 Windows 体验、系统集成、高性能**。三个支柱：

1. **Windows UI 规范** - 遵循 Fluent Design System
2. **系统集成** - 注册表、文件关联、托盘等
3. **Windows API** - COM 互操作、Win32 API 调用

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **Windows**: Windows 10 或更高
- **Visual Studio**: 2022（包含 C++ 桌面开发工具）

## Windows 特定规范

### 窗口管理

```dart
import 'dart:io';
import 'package:flutter/material.dart';

void main() async {
  if (Platform.isWindows) {
    // Windows 特定的窗口设置
  }
  runApp(const MyApp());
}
```

### 系统托盘

```dart
import 'package:tray_manager/tray_manager.dart';

Future<void> initTray() async {
  await trayManager.setIcon('assets/tray_icon.ico');

  final menu = Menu(
    children: [
      MenuItem(key: 'show', label: 'Show'),
      MenuItem.separator(),
      MenuItem(key: 'quit', label: 'Quit'),
    ],
  );

  await trayManager.setContextMenu(menu);
}
```

### 注册表访问

```dart
import 'package:win32_registry/win32_registry.dart';

Future<void> readRegistry() async {
  final key = Registry.openPath(
    RegistryHive.currentUser,
    path: r'Software\MyApp',
  );
  final value = await key.getValue('version');
  await key.close();
}
```

## Windows 性能目标

- **启动**: <800ms (SSD)、<1.5s (标准设备)
- **内存**: <300MB (空闲)、<800MB (活跃)
- **CPU**: 空闲 <5%、活跃 <40%
- **响应**: <80ms

## Windows 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **设备测试**: 不同 Windows 版本 (10/11)

## 常见问题

### 如何处理 DPI 缩放？

```dart
final dpi = MediaQuery.of(context).devicePixelRatio;
final scaledSize = size * dpi;
```

### 如何创建安装程序？

使用 MSIX 或 NSIS 创建安装程序

## 参考资源

- [Windows Desktop Guidelines](https://docs.microsoft.com/en-us/windows/apps/desktop/)
- [Flutter Windows](https://flutter.dev/multi-platform/desktop)
- [Fluent Design](https://www.microsoft.com/design/fluent/)

---

**记住**：遵循 Fluent Design System！
