---
name: linux-performance
description: Linux 桌面应用性能优化指南 - 针对 Linux 平台的特定优化策略
---

# Linux 性能优化指南

## 核心原则

**性能三角**：响应速度 > 内存占用 > CPU 使用

Linux 桌面应用的性能优化需要考虑不同发行版、桌面环境和系统库的差异。

## 性能目标

### Linux 特定目标

- **现代设备 (SSD, 8GB+ RAM)**: 启动 <800ms，响应 <80ms
- **标准设备**: 启动 <1.5s，响应 <150ms
- **内存占用**: <250MB（空闲），<600MB（活跃）
- **CPU 使用**: 空闲 <5%，活跃 <35%
- **窗口操作**: 流畅，与桌面环境集成

## Linux 诊断工具

```bash
# perf (Linux 性能分析器)
perf record -g ./my_app
perf report

# Valgrind (内存分析)
valgrind --leak-check=full ./my_app

# top/htop (实时监控)
htop

# Flutter DevTools
flutter run -d linux --profile
```

## Linux 特定优化

### 1. 桌面环境集成

```dart
// ✅ 检测桌面环境
final desktopEnv = Platform.environment['DESKTOP_SESSION'];
final isGNOME = desktopEnv?.contains('gnome') ?? false;
final isKDE = desktopEnv?.contains('kde') ?? false;
final isXFCE = desktopEnv?.contains('xfce') ?? false;

// 根据桌面环境调整 UI
if (isGNOME) {
  // GNOME 特定优化
} else if (isKDE) {
  // KDE 特定优化
}
```

### 2. 文件系统访问

```dart
// ✅ 使用 file_selector 包
import 'package:file_selector/file_selector.dart';

Future<void> openFile() async {
  const fileTypeGroup = XTypeGroup(
    label: 'Documents',
    extensions: ['txt', 'doc', 'pdf'],
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
  await trayManager.setIcon('assets/tray_icon.png');

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

### 4. DBus 集成

```dart
// ✅ 使用 dbus 包
import 'package:dbus/dbus.dart';

Future<void> dbusExample() async {
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

### 5. Shell 命令执行

```dart
// ✅ 使用 process 包执行系统命令
import 'dart:io';

Future<void> executeCommand() async {
  final result = await Process.run('ls', ['-la']);
  print(result.stdout);
}
```

## Linux 系统集成

### 1. 桌面通知

```dart
// ✅ 使用 local_notifier 包
import 'package:local_notifier/local_notifier.dart';

Future<void> showNotification() async {
  final notification = LocalNotification(
    title: 'My Linux App',
    body: 'Notification message',
  );
  await notification.show();
}
```

### 2. 自动启动

```dart
// ✅ 创建 .desktop 文件
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

### 3. MIME 类型关联

```dart
// ✅ 创建 MIME 类型关联
Future<void> createMimeAssociation() async {
  final mimeFile = File('/usr/share/mime/packages/myapp.xml');
  await mimeFile.writeAsString('''
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-myapp">
    <comment>My App File</comment>
    <glob pattern="*.myapp"/>
  </mime-type>
</mime-info>
''');

  // 更新 MIME 数据库
  await Process.run('update-mime-database', ['/usr/share/mime']);
}
```

## Linux 性能优化

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

### 3. 使用原生库

```dart
// ✅ 使用 ffi 调用 C 库
import 'dart:ffi';
import 'package:ffi/ffi.dart';

final dylib = DynamicLibrary.open('libnative.so');
final nativeFunction = dylib.lookupFunction<
    IntPtr Function(Pointer<Utf8>),
    int Function(Pointer<Utf8>)>('native_function');

void callNative() {
  final input = 'Hello'.toNativeUtf8();
  final result = nativeFunction(input);
  calloc.free(input);
}
```

## Linux 性能测试

### 性能基准测试

```dart
// 创建 integration_test/linux_perf_test.dart
void main() {
  group('Linux Performance Tests', () {
    testWidgets('Window resize performance', (tester) async {
      await tester.binding.window.physicalSizeTestValue =
          const Size(1920, 1080);
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);

      await tester.pumpWidget(const MyApp());

      final stopwatch = Stopwatch()..start();

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

## Linux 性能检查清单

### 发布前检查

- [ ] 在主流发行版上测试（Ubuntu、Fedora、Debian、Arch）
- [ ] 测试不同桌面环境（GNOME、KDE、XFCE）
- [ ] 测试不同架构（x86_64、ARM64）
- [ ] 使用 perf 分析性能
- [ ] 测试窗口操作
- [ ] 验证文件关联
- [ ] 检查通知功能
- [ ] 验证系统托盘
- [ ] 测试快捷键
- [ ] 创建 .desktop 文件

## Linux 特定问题

### 打包和分发

```bash
# AppImage
flutter build linux --release
# 使用 appimage-builder 创建 AppImage

# Flatpak
# 创建 flatpak manifest

# Snap
# 创建 snapcraft.yaml
```

### 依赖库

```dart
// ✅ 检查系统依赖
final requiredLibs = [
  'libgtk-3-0',
  'libglib-2.0-0',
  'libpango-1.0-0',
];

for (final lib in requiredLibs) {
  try {
    await Process.run('ldconfig', ['-p', lib]);
  } catch (e) {
    print('Missing required library: $lib');
  }
}
```

## 参考资源

- [Linux Desktop Guidelines](https://developer.gnome.org/documentation/guidelines/)
- [Flutter Linux](https://flutter.dev/multi-platform/desktop)
- [freedesktop.org Standards](https://standards.freedesktop.org/)
