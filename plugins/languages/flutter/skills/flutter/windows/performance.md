---
name: windows-performance
description: Windows 桌面应用性能优化指南 - 针对 Windows 平台的特定优化策略
---

# Windows 性能优化指南

## 核心原则

**性能三角**：响应速度 > 内存占用 > CPU 使用

Windows 桌面应用的性能优化需要考虑 UWP 集成、COM 互操作和 Windows API 调用。

## 性能目标

### Windows 特定目标

- **现代设备 (SSD, 8GB+ RAM)**: 启动 <800ms，响应 <80ms
- **标准设备**: 启动 <1.5s，响应 <150ms
- **内存占用**: <300MB（空闲），<800MB（活跃）
- **CPU 使用**: 空闲 <5%，活跃 <40%
- **窗口操作**: 流畅，无卡顿

## Windows 诊断工具

```bash
# Windows Performance Analyzer (WPA)
# Windows Performance Recorder (WPR)

# Task Manager
# 查看实时 CPU、内存、磁盘使用

# Flutter DevTools
flutter run -d windows --profile
```

## Windows 特定优化

### 1. 窗口管理优化

```dart
// ✅ 设置窗口大小和位置
import 'dart:io';
import 'package:flutter/material.dart';

void main() async {
  // 设置窗口大小
  if (Platform.isWindows) {
    // Windows 特定的窗口设置
  }
  runApp(const MyApp());
}
```

### 2. 文件系统访问

```dart
// ✅ 使用 file_selector 包
import 'package:file_selector/file_selector.dart';

Future<void> openFile() async {
  const fileTypeGroup = XTypeGroup(
    label: 'Documents',
    extensions: ['txt', 'doc', 'docx', 'pdf'],
  );
  final file = await openFile(acceptedTypeGroups: [fileTypeGroup]);
  if (file != null) {
    // 处理文件
  }
}
```

### 3. 系统托盘

```dart
// ✅ 使用 tray_manager 包
import 'package:tray_manager/tray_manager.dart';

Future<void> initTray() async {
  await trayManager.setIcon(
    'assets/tray_icon.ico',  // Windows 使用 .ico 格式
  );

  final menu = Menu(
    children: [
      MenuItem(
        key: 'show',
        label: 'Show',
        onClicked: (_) {
          // 显示窗口
        },
      ),
      MenuItem.separator(),
      MenuItem(
        key: 'quit',
        label: 'Quit',
        onClicked: (_) {
          trayManager.destroy();
          exit(0);
        },
      ),
    ],
  );

  await trayManager.setContextMenu(menu);
}
```

### 4. Windows 通知

```dart
// ✅ 使用 local_notifier 包
import 'package:local_notifier/local_notifier.dart';

Future<void> showNotification() async {
  final notification = LocalNotification(
    title: 'My Windows App',
    body: 'Notification message',
  );
  await notification.show();
}
```

### 5. 快捷键处理

```dart
// ✅ 使用 hotkey_manager 包
import 'package:hotkey_manager/hotkey_manager.dart';

Future<void> registerHotkeys() async {
  await hotKeyManager.register(
    HotKey(
      key: PhysicalKeyboardKey.keyS,
      modifiers: [HotKeyModifier.control, HotKeyModifier.shift],
      keyPressed: (_) {
        // Ctrl+Shift+S 快捷键处理
      },
    ),
  );
}
```

## Windows 系统集成

### 1. 注册表访问

```dart
// ✅ 使用 win32_registry 包
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

### 2. Windows API 调用

```dart
// ✅ 使用 win32 包
import 'package:win32/win32.dart';

void getWindowsVersion() {
  final version = GetVersion();
  print('Windows version: $version');
}
```

### 3. COM 互操作

```dart
// ✅ 使用 win32 包进行 COM 调用
import 'package:win32/win32.dart';

Future<void> comExample() async {
  // 初始化 COM
  CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

  // 使用 COM 对象
  // ...

  // 释放 COM
  CoUninitialize();
}
```

## Windows 性能优化

### 1. 内存优化

```dart
// ✅ 及时释放资源
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = eventBus.on<Event>().listen((event) {});
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
```

### 2. 后台任务优化

```dart
// ✅ 使用 Isolate 进行重计算
Future<ProcessedData> processLargeData(Data data) async {
  return await compute(_processInIsolate, data);
}

static ProcessedData _processInIsolate(Data data) {
  // 重计算在 Isolate 中执行
  return ProcessedData();
}
```

### 3. UI 线程优化

```dart
// ✅ 避免阻塞 UI 线程
void handleButtonClick() async {
  setState(() => _isLoading = true);

  // 异步处理
  final result = await _heavyOperation();

  setState(() {
    _isLoading = false;
    _result = result;
  });
}
```

## Windows 性能测试

### 性能基准测试

```dart
// 创建 integration_test/windows_perf_test.dart
void main() {
  group('Windows Performance Tests', () {
    testWidgets('Window resize performance', (tester) async {
      await tester.binding.window.physicalSizeTestValue =
          const Size(1920, 1080);
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);

      await tester.pumpWidget(const MyApp());

      final stopwatch = Stopwatch()..start();

      // 模拟窗口调整
      for (int i = 0; i < 10; i++) {
        await tester.binding.window.physicalSizeTestValue =
            Size(1920, 1080 - i * 100);
        await tester.pumpAndSettle();
      }

      stopwatch.stop();
      expect(stopwatch.elapsedMilliseconds, lessThan(1000));
    });
  });
}
```

## Windows 性能检查清单

### 发布前检查

- [ ] 在真实 Windows 设备上测试
- [ ] 测试不同 Windows 版本（10、11）
- [ ] 测试不同硬件配置（SSD/HDD、不同 RAM）
- [ ] 使用 Windows Performance Analyzer 分析
- [ ] 测试窗口操作
- [ ] 验证文件关联
- [ ] 检查通知功能
- [ ] 验证系统托盘
- [ ] 测试快捷键
- [ ] 检查 UAC 权限

## Windows 特定问题

### Windows Defender

```dart
// ✅ 处理 Windows Defender 误报
// 签名可执行文件
// 使用官方证书签名
```

### DPI 缩放

```dart
// ✅ 处理 DPI 缩放
final dpi = MediaQuery.of(context).devicePixelRatio;
final scaledSize = size * dpi;
```

### Windows 安装程序

```dart
// ✅ 创建 MSIX 或 NSIS 安装程序
// 使用 msix 或 flutter_distributor 包
```

## 参考资源

- [Windows Desktop Guidelines](https://docs.microsoft.com/en-us/windows/apps/desktop/)
- [Flutter Windows](https://flutter.dev/multi-platform/desktop)
- [Windows Performance Analyzer](https://docs.microsoft.com/en-us/windows-hardware/test/wpt/windows-performance-analyzer)
