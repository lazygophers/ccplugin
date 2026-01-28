---
name: cupertino
description: iOS Cupertino 设计系统详解 - 提供 iOS 原生体验的完整实现指南
---

# iOS Cupertino 设计系统详解

## 选择决策

**Cupertino** 是 Apple iOS 的官方设计规范，使用 `CupertinoApp` 和 Cupertino Widget 可以提供真正的 iOS 原生体验。

**适用场景**：
- iOS 应用或 iOS 优先
- 需要原生 iOS 外观和交互的应用
- 目标用户主要是 iOS

**实现**：
```dart
CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
    brightness: Brightness.light,
  ),
  home: const MyHomePage(),
)
```

## 核心 Cupertino Widget

### 基础组件

```dart
CupertinoButton              // iOS 风格按钮
CupertinoSwitch            // iOS 切换开关
CupertinoSegmentedControl  // iOS 分段控制
CupertinoNavigationBar     // iOS 导航栏
CupertinoTabBar            // iOS 标签栏
CupertinoAlertDialog       // iOS 警告对话框
CupertinoDatePicker        // iOS 日期选择器
CupertinoTimerPicker       // iOS 时间选择器
CupertinoSlider           // iOS 滑块
CupertinoPicker           // iOS 选择器
```

## 导航模式

### CupertinoPageRoute

**关键原则**：使用 `CupertinoPageRoute` 进行导航（支持左滑返回）

```dart
// ✅ 正确：使用 CupertinoPageRoute
Navigator.push(
  context,
  CupertinoPageRoute(
    builder: (context) => const NextPage(),
    title: 'Next Page',  // iOS 返回按钮显示的标题
  ),
)

// ❌ 不好：不应该在 iOS 应用中使用 MaterialPageRoute
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => const NextPage()),
)
```

### CupertinoNavigationBar

```dart
CupertinoPageScaffold(
  navigationBar: CupertinoNavigationBar(
    middle: const Text('My Page'),
    trailing: CupertinoButton(
      padding: EdgeInsets.zero,
      child: const Icon(CupertinoIcons.add),
      onPressed: () {},
    ),
  ),
  child: const Center(child: Text('Content')),
)
```

### CupertinoTabBar

```dart
class MainApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CupertinoTabScaffold(
      tabBar: CupertinoTabBar(
        items: const [
          BottomNavigationBarItem(
            label: 'Home',
            icon: Icon(CupertinoIcons.house),
          ),
          BottomNavigationBarItem(
            label: 'Settings',
            icon: Icon(CupertinoIcons.settings),
          ),
        ],
      ),
      tabBuilder: (context, index) {
        return CupertinoTabView(
          builder: (context) {
            return index == 0 ? const HomeTab() : const SettingsTab();
          },
        );
      },
    );
  }
}
```

## 交互模式

### iOS 风格的刷新

```dart
CustomScrollView(
  slivers: [
    CupertinoSliverRefreshControl(
      onRefresh: () async {
        await Future.delayed(const Duration(seconds: 1));
      },
    ),
    SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => ListTile(title: Text('Item $index')),
        childCount: 20,
      ),
    ),
  ],
)
```

### iOS 风格的弹出菜单

```dart
showCupertinoDialog(
  context: context,
  builder: (context) => CupertinoAlertDialog(
    title: const Text('Alert'),
    content: const Text('This is an iOS-style alert'),
    actions: [
      CupertinoDialogAction(
        child: const Text('Cancel'),
        onPressed: () => Navigator.pop(context),
      ),
      CupertinoDialogAction(
        isDefaultAction: true,
        child: const Text('OK'),
        onPressed: () => Navigator.pop(context),
      ),
    ],
  ),
)
```

### iOS Action Sheet

```dart
showCupertinoModalPopup(
  context: context,
  builder: (context) => CupertinoActionSheet(
    title: const Text('Choose an option'),
    actions: [
      CupertinoActionSheetAction(
        child: const Text('Option 1'),
        onPressed: () => Navigator.pop(context),
      ),
      CupertinoActionSheetAction(
        child: const Text('Option 2'),
        onPressed: () => Navigator.pop(context),
      ),
    ],
    cancelButton: CupertinoActionSheetAction(
      child: const Text('Cancel'),
      onPressed: () => Navigator.pop(context),
    ),
  ),
)
```

## 日期和时间选择

### CupertinoDatePicker

```dart
CupertinoDatePicker(
  mode: CupertinoDatePickerMode.date,
  initialDateTime: DateTime.now(),
  onDateTimeChanged: (DateTime newDate) {
    setState(() => selectedDate = newDate);
  },
)
```

### CupertinoTimerPicker

```dart
CupertinoTimerPicker(
  initialTimerDuration: const Duration(hours: 1, minutes: 30),
  onTimerDurationChanged: (Duration newDuration) {
    setState(() => selectedDuration = newDuration);
  },
  mode: CupertinoTimerPickerMode.hm,  // 时:分
)
```

## iOS 主题

### 亮色/暗色模式

```dart
final themeProvider = StateNotifierProvider<ThemeNotifier, Brightness>((ref) {
  return ThemeNotifier(Brightness.light);
});

class ThemeNotifier extends StateNotifier<Brightness> {
  ThemeNotifier(Brightness initialBrightness) : super(initialBrightness);

  void toggleTheme() {
    state = state == Brightness.light ? Brightness.dark : Brightness.light;
  }
}

// 在 CupertinoApp 中使用
ConsumerWidget(
  builder: (context, ref, child) {
    final brightness = ref.watch(themeProvider);

    return CupertinoApp(
      theme: CupertinoThemeData(
        brightness: brightness,
        primaryColor: CupertinoColors.systemBlue,
      ),
    );
  },
)
```

### 使用 iOS 系统颜色

```dart
// iOS 系统颜色
CupertinoColors.systemBlue
CupertinoColors.systemGreen
CupertinoColors.systemRed
CupertinoColors.systemYellow
CupertinoColors.systemOrange
CupertinoColors.systemPink
CupertinoColors.systemPurple
CupertinoColors.systemTeal

// 自适应颜色（根据亮色/暗色模式自动调整）
CupertinoColors.systemGrey
CupertinoColors.label       // 主要文本颜色
CupertinoColors.secondaryLabel  // 次要文本颜色
CupertinoColors.tertiaryLabel   // 三级文本颜色
CupertinoColors.separator       // 分隔线颜色
```

## iOS 特定功能

### iOS 权限处理

```dart
// 使用 permission_handler 包
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  // 相机权限
  final cameraStatus = await Permission.camera.request();
  if (cameraStatus.isDenied) {
    openAppSettings();  // 引导用户到设置页面
  }

  // 照片库权限
  final photosStatus = await Permission.photos.request();

  // 位置权限
  final locationStatus = await Permission.locationWhenInUse.request();
}
```

### iOS 平台检测

```dart
import 'dart:io' show Platform;

bool isIOS = Platform.isIOS;

// 在 Widget 中
if (Theme.of(context).platform == TargetPlatform.iOS) {
  return const CupertinoComponent();
}
```

### iOS 安全区域

```dart
// 使用 MediaQuery 获取安全区域
final padding = MediaQuery.of(context).padding;

// 使用 SafeArea 自动处理安全区域
SafeArea(
  child: YourContent(),
)

// CupertinoApp 自动处理安全区域
```

## iOS 设计规范

### 字体大小

```dart
// iOS 标准字体大小
const largeTitle = 34.0;
const title1 = 28.0;
const title2 = 22.0;
const title3 = 20.0;
const headline = 17.0;
const body = 17.0;
const callout = 16.0;
const subheadline = 15.0;
const footnote = 13.0;
const caption1 = 12.0;
const caption2 = 11.0;
```

### 间距规范

```dart
// iOS 标准间距
const standardSpacing = 16.0;
const compactSpacing = 8.0;
const spaciousSpacing = 24.0;
```

### 圆角规范

```dart
// iOS 标准圆角
const smallRadius = 8.0;
const mediumRadius = 12.0;
const largeRadius = 16.0;
```

## iOS 动画

### iOS 风格的页面转场

```dart
Navigator.push(
  context,
  CupertinoPageRoute(
    builder: (context) => const NextPage(),
  ),
)
```

### Hero 动画（iOS 风格）

```dart
Hero(
  tag: 'hero-tag',
  child: CupertinoButton(
    child: const Text('Tap Me'),
    onPressed: () {},
  ),
)
```

## iOS 最佳实践

### 遵循 iOS Human Interface Guidelines

- **清晰性**：文本清晰可读，图标意图明确
- **依从性**：动画和交互流畅自然
- **深度感**：使用阴影、层级和半透明效果
- **一致性**：与 iOS 系统和其他应用保持一致

### 避免过度自定义

```dart
// ✅ 好：使用标准的 Cupertino 组件
CupertinoButton(
  child: const Text('Button'),
  onPressed: () {},
)

// ❌ 不好：完全自定义按钮外观，破坏 iOS 一致性
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(...),
    boxShadow: [...],
  ),
  child: const Text('Custom Button'),
)
```

## iOS 调试

### 使用 iOS 模拟器测试

```bash
# 列出可用设备
flutter devices

# 在特定设备上运行
flutter run -d iPhone

# 运行 iOS 版本
flutter run -d ios
```

### iOS 特定调试工具

```bash
# 打开 Xcode
open ios/Runner.xcworkspace

# 检查 iOS 权限配置
cat ios/Runner/Info.plist
```

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

### 如何自定义 Cupertino 主题？

```dart
CupertinoThemeData(
  primaryColor: CupertinoColors.systemBlue,
  textTheme: CupertinoTextThemeData(
    textStyle: TextStyle(
      fontFamily: 'SF Pro Text',
      fontSize: 17,
    ),
  ),
  barBackgroundColor: CupertinoColors.systemBackground,
)
```

### 如何处理 iOS 特有的崩溃？

使用 Firebase Crashlytics 或 Sentry：

```dart
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(true);
```

## 参考资源

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Flutter Cupertino Widgets](https://api.flutter.dev/flutter/cupertino/cupertino-library.html)
- [iOS Design Themes](https://developer.apple.com/design/human-interface-guidelines/ios/visual-design/color/)
