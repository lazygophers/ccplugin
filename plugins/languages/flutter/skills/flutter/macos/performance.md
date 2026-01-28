---
name: macos-performance
description: macOS 桌面应用性能优化指南 - 针对 macOS 平台的特定优化策略
---

# macOS 性能优化指南

## 核心原则

**性能三角**：响应速度 > 内存占用 > CPU 使用

macOS 桌面应用的性能优化需要考虑 Apple Silicon、内存管理和 macOS 系统集成。

## 性能目标

### macOS 特定目标

- **Apple Silicon (M1/M2/M3)**: 启动 <500ms，响应 <50ms
- **Intel Mac**: 启动 <1s，响应 <100ms
- **内存占用**: <200MB（空闲），<500MB（活跃）
- **CPU 使用**: 空闲 <5%，活跃 <30%
- **窗口操作**: 无明显延迟

## macOS 诊断工具

```bash
# Instruments（Xcode）
# 1. Open Xcode -> Open Developer Tool -> Instruments
# 2. 选择 Time Profiler 或 Allocations

# Activity Monitor
# 查看实时 CPU、内存、能源使用

# Flutter DevTools
flutter run -d macos --profile
```

## macOS 特定优化

### 1. 窗口管理优化

```dart
// ✅ 使用 proper window sizing
import 'package:flutter_macos/window_size.dart';

void main() async {
  await setWindowFrame(
    const Rect.fromLTWH(100, 100, 1200, 800),
  );
  await setWindowTitle('My macOS App');
  runApp(const MyApp());
}
```

### 2. 菜单栏集成

```dart
// ✅ 添加 macOS 菜单栏
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  // 设置 macOS 菜单
  if (Platform.isMacOS) {
    // 主菜单
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

    // 应用菜单
    final appMenu = Menu(
      children: [
        Submenu(label: 'My App', children: submenu),
      ],
    );
  }
  runApp(const MyApp());
}
```

### 3. 文件系统访问

```dart
// ✅ 使用 file_selector 包
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

### 4. 内存优化

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

### 5. Apple Silicon 优化

```dart
// ✅ 使用多线程处理
Future<ProcessedData> processLargeData(Data data) async {
  return await compute(_processInIsolate, data);
}

static ProcessedData _processInIsolate(Data data) {
  // 重计算在 Isolate 中执行
  return ProcessedData();
}
```

## macOS 系统集成

### 1. 通知中心

```dart
// ✅ 使用 local_notifier 包
import 'package:local_notifier/local_notifier.dart';

Future<void> showNotification() async {
  final notification = LocalNotification(
    title: 'My App',
    body: 'Notification message',
  );
  await notification.show();
}
```

### 2. 系统托盘

```dart
// ✅ 使用 tray_manager 包
import 'package:tray_manager/tray_manager.dart';

class TrayManagerHandler extends StatefulWidget {
  @override
  State<TrayManagerHandler> createState() => _TrayManagerHandlerState();
}

class _TrayManagerHandlerState extends State<TrayManagerHandler> with TrayListener {
  @override
  void initState() {
    super.initState();
    trayManager.addListener(this);
    _initTray();
  }

  Future<void> _initTray() async {
    await trayManager.setIcon(
      'assets/tray_icon.png',
    );
  }

  @override
  void onTrayIconMouseDown() {
    // 显示/隐藏窗口
  }

  @override
  void dispose() {
    trayManager.removeListener(this);
    super.dispose();
  }
}
```

### 3. 快捷键处理

```dart
// ✅ 使用 hotkey_manager 包
import 'package:hotkey_manager/hotkey_manager.dart';

Future<void> registerHotkeys() async {
  await hotKeyManager.register(
    HotKey(
      key: PhysicalKeyboardKey.keyS,
      modifiers: [HotKeyModifier.meta, HotKeyModifier.shift],
      keyPressed: (_) {
        // Cmd+Shift+S 快捷键处理
      },
    ),
  );
}
```

## macOS 性能测试

### 性能基准测试

```dart
// 创建 integration_test/macos_perf_test.dart
void main() {
  group('macOS Performance Tests', () {
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

## macOS 性能检查清单

### 发布前检查

- [ ] 在真实 Mac 设备上测试（Intel 和 Apple Silicon）
- [ ] 测试不同 macOS 版本（Monterey、Ventura、Sonoma）
- [ ] 使用 Instruments 分析内存和 CPU
- [ ] 测试窗口操作（调整大小、最小化、最大化）
- [ ] 验证菜单栏功能
- [ ] 测试文件系统访问
- [ ] 检查通知功能
- [ ] 验证系统托盘
- [ ] 测试快捷键
- [ ] 检查电池使用（便携设备）

## macOS 特定问题

### 窗口状态保存

```dart
// ✅ 保存和恢复窗口状态
import 'package:shared_preferences/shared_preferences.dart';

Future<void> saveWindowState() async {
  final prefs = await SharedPreferences.getInstance();
  final frame = await getWindowFrame();
  await prefs.setDouble('window_x', frame.left);
  await prefs.setDouble('window_y', frame.top);
  await prefs.setDouble('window_width', frame.width);
  await prefs.setDouble('window_height', frame.height);
}
```

### macOS 权限处理

```dart
// ✅ 请求必要权限
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
