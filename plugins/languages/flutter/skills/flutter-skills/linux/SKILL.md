---
name: flutter-linux-skills
description: Flutter Linux 开发规范 - Linux 桌面应用开发指南、系统集成和性能优化
---

# Flutter Linux 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **[performance.md](performance.md)** | Linux 性能优化、桌面环境集成 | Linux 性能调优 |
| **[testing.md](testing.md)** | Linux 测试规范、DBus 测试 | Linux 测试编写 |

## Linux 开发核心理念

Flutter Linux 开发追求**跨发行版兼容、桌面环境集成、高性能**。三个支柱：

1. **Linux UI 规范** - 遵循各桌面环境的设计规范
2. **系统集成** - DBus、文件关联、通知等
3. **兼容性** - 支持主流发行版和桌面环境

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+
- **发行版**: Ubuntu 20.04+、Fedora 35+、Debian 11+、Arch Linux
- **桌面环境**: GNOME、KDE Plasma、XFCE

## Linux 特定规范

### 桌面环境检测

```dart
final desktopEnv = Platform.environment['DESKTOP_SESSION'];
final isGNOME = desktopEnv?.contains('gnome') ?? false;
final isKDE = desktopEnv?.contains('kde') ?? false;

if (isGNOME) {
  // GNOME 特定优化
} else if (isKDE) {
  // KDE 特定优化
}
```

### DBus 集成

```dart
import 'package:dbus/dbus.dart';

Future<void> showNotification() async {
  final client = DBusClient.session();
  final object = DBusRemoteObject(
    client,
    name: 'org.freedesktop.Notifications',
    path: DBusObjectPath('/org/freedesktop/Notifications'),
  );

  await object.callMethod(
    'org.freedesktop.Notifications',
    'Notify',
    [DBusString('My App'), UInt32(0), ...],
  );

  await client.close();
}
```

### 自动启动

```dart
Future<void> createAutoStartEntry() async {
  final home = Platform.environment['HOME'];
  final autostartDir = Directory('$home/.config/autostart');
  if (!await autostartDir.exists()) {
    await autostartDir.create();
  }

  final desktopFile = File('${autostartDir.path}/myapp.desktop');
  await desktopFile.writeAsString('''
[Desktop Entry]
Type=Application
Name=My App
Exec=/path/to/myapp
Icon=myapp
X-GNOME-Autostart-enabled=true
''');
}
```

## Linux 性能目标

- **启动**: <800ms (SSD)、<1.5s (标准设备)
- **内存**: <250MB (空闲)、<600MB (活跃)
- **CPU**: 空闲 <5%、活跃 <35%
- **响应**: <80ms

## Linux 测试规范

- **单元测试**: >80% 覆盖率
- **Widget 测试**: 关键 UI 已覆盖
- **集成测试**: 主要用户流程已覆盖
- **发行版测试**: Ubuntu、Fedora、Arch

## 常见问题

### 如何打包和分发？

使用 AppImage、Flatpak 或 Snap 进行分发

### 如何处理不同桌面环境？

检测桌面环境并调整 UI

## 参考资源

- [Linux Desktop Guidelines](https://developer.gnome.org/documentation/guidelines/)
- [Flutter Linux](https://flutter.dev/multi-platform/desktop)
- [freedesktop.org Standards](https://standards.freedesktop.org/)

---

**记住**：支持主流桌面环境和发行版！
