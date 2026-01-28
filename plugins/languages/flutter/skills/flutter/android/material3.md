---
name: material3
description: Android Material Design 3 详解 - Google 现代设计系统的完整实现指南，包含 2025 Expressive 特性
---

# Android Material Design 3 详解

## 选择决策

**Material Design 3** 是 Google 的现代设计系统，已包含 2025 年新增的 Expressive 特性。

**适用场景**：
- Android 应用或 Android 优先
- 跨平台应用（iOS + Android + Web）
- 需要现代设计的应用
- 企业应用（Material Design 3 是业界标准）

**实现**：
```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,  // 启用 Material 3
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.light,
    ),
    typography: Typography.material2021(),
  ),
  home: const MyHomePage(),
)
```

## Material 3 Expressive（2025 新特性）

Material 3 Expressive 是 2025 年 5 月发布的新版本，提供更动态、更富表现力的组件和设计系统。

**新特性**：
- 更动态的颜色系统（支持 Liquid Glass 风格）
- 增强的排版表现力
- 新的动画和过渡效果
- 改进的可访问性支持

**启用方式**：
```dart
ThemeData(
  useMaterial3: true,  // 自动启用 Material 3 Expressive
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
    brightness: Brightness.light,
  ),
)
```

## 动态颜色系统

### 基于种子的颜色生成

```dart
// 使用种子颜色自动生成完整的调色板
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,  // 种子颜色
      brightness: Brightness.light,
    ),
  ),
)

// 从图像提取颜色
MaterialApp(
  theme: ThemeData(
    colorScheme: await ColorScheme.fromImageProvider(
      provider: const AssetImage('assets/brand_image.png'),
      brightness: Brightness.light,
    ),
  ),
)
```

### 使用系统动态颜色（Android 12+）

```dart
// 使用 Android 系统的动态颜色（壁纸颜色）
MaterialApp(
  theme: ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      dynamicSchemeVariant: DynamicSchemeVariant.fidelity,  // 使用壁纸颜色
    ),
  ),
)
```

## Material 3 组件

### 核心组件

```dart
// Material 3 按钮
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: colorScheme.primary,
    foregroundColor: colorScheme.onPrimary,
  ),
  onPressed: () {},
  child: const Text('Elevated Button'),
)

FilledButton(
  onPressed: () {},
  child: const Text('Filled Button'),
)

OutlinedButton(
  onPressed: () {},
  child: const Text('Outlined Button'),
)

TextButton(
  onPressed: () {},
  child: const Text('Text Button'),
)

// Material 3 卡片
Card(
  elevation: 0,
  color: colorScheme.surfaceVariant,
  child: const Padding(
    padding: EdgeInsets.all(16.0),
    child: Text('Material 3 Card'),
  ),
)

// Material 3 导航栏
NavigationBar(
  selectedIndex: 0,
  onDestinationSelected: (index) {},
  destinations: const [
    NavigationDestination(
      icon: Icon(Icons.home),
      label: 'Home',
    ),
    NavigationDestination(
      icon: Icon(Icons.settings),
      label: 'Settings',
    ),
  ],
)
```

### Material 3 对话框

```dart
// Material 3 全屏对话框
 showDialog(
  context: context,
  builder: (context) => AlertDialog(
    icon: const Icon(Icons.warning),
    title: const Text('Alert'),
    content: const Text('This is a Material 3 alert'),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      FilledButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('OK'),
      ),
    ],
  ),
)
```

## Android 特定功能

### Android 权限处理

```dart
// 使用 permission_handler 包
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  // 相机权限
  final cameraStatus = await Permission.camera.request();
  if (cameraStatus.isPermanentlyDenied) {
    openAppSettings();  // 引导用户到设置页面
  }

  // 存储权限（Android 13+）
  final storageStatus = await Permission.photos.request();

  // 通知权限
  final notificationStatus = await Permission.notification.request();
}
```

### Android 平台检测

```dart
import 'dart:io' show Platform;

bool isAndroid = Platform.isAndroid;

// 在 Widget 中
if (Theme.of(context).platform == TargetPlatform.android) {
  return const MaterialComponent();
}
```

### Android 返回手势处理

```dart
// 使用 WillPopScope 或 PopScope 处理返回手势
PopScope(
  canPop: false,  // 拦截返回手势
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

## Material 3 主题定制

### 完整主题配置

```dart
static ThemeData lightTheme() {
  final colorScheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF2196F3),
    brightness: Brightness.light,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,

    // 排版
    typography: Typography.material2021(),

    // 卡片主题
    cardTheme: CardTheme(
      elevation: 0,
      color: colorScheme.surfaceVariant,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),

    // 输入框主题
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      contentPadding: const EdgeInsets.all(16),
    ),

    // 按钮主题
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: colorScheme.primary,
        foregroundColor: colorScheme.onPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(
          horizontal: 24,
          vertical: 12,
        ),
      ),
    ),

    // AppBar 主题
    appBarTheme: AppBarTheme(
      centerTitle: false,
      backgroundColor: colorScheme.surface,
      foregroundColor: colorScheme.onSurface,
      elevation: 0,
    ),
  );
}
```

### 主题扩展

```dart
// 自定义主题扩展
class CustomColors extends ThemeExtension<CustomColors> {
  final Color brandBlue;
  final Color brandGreen;

  CustomColors({required this.brandBlue, required this.brandGreen});

  @override
  ThemeExtension<CustomColors> copyWith({
    Color? brandBlue,
    Color? brandGreen,
  }) {
    return CustomColors(
      brandBlue: brandBlue ?? this.brandBlue,
      brandGreen: brandGreen ?? this.brandGreen,
    );
  }

  @override
  ThemeExtension<CustomColors> lerp(
    ThemeExtension<CustomColors>? other,
    double t,
  ) {
    if (other is! CustomColors) return this;
    return CustomColors(
      brandBlue: Color.lerp(brandBlue, other.brandBlue, t)!,
      brandGreen: Color.lerp(brandGreen, other.brandGreen, t)!,
    );
  }
}

// 在 ThemeData 中添加
ThemeData(
  extensions: [
    CustomColors(
      brandBlue: const Color(0xFF2196F3),
      brandGreen: const Color(0xFF4CAF50),
    ),
  ],
)

// 使用
final customColors = Theme.of(context).extension<CustomColors>()!;
Container(color: customColors.brandBlue)
```

## Android 设计规范

### Material 3 字体比例

```dart
// Material 3 字体大小
const displayLarge = 57.0;
const displayMedium = 45.0;
const displaySmall = 36.0;
const headlineLarge = 32.0;
const headlineMedium = 28.0;
const headlineSmall = 24.0;
const titleLarge = 22.0;
const titleMedium = 16.0;
const titleSmall = 14.0;
const bodyLarge = 16.0;
const bodyMedium = 14.0;
const bodySmall = 12.0;
const labelLarge = 14.0;
const labelMedium = 12.0;
const labelSmall = 11.0;
```

### Material 3 间距规范

```dart
// Material 3 间距
class M3Spacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
}
```

### Material 3 圆角规范

```dart
// Material 3 圆角
class M3Radius {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 28.0;
  static const full = 999.0;
}
```

## Android 响应式设计

### 断点规范

```dart
class Breakpoints {
  static const mobile = 600;      // < 600dp
  static const tablet = 840;      // 600-839dp
  static const desktop = 1200;    // >= 1200dp
}

// 使用
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < Breakpoints.mobile) {
      return const MobileView();
    } else if (constraints.maxWidth < Breakpoints.tablet) {
      return const TabletView();
    } else {
      return const DesktopView();
    }
  },
)
```

### 自适应布局

```dart
// 使用 MediaQuery
final screenWidth = MediaQuery.of(context).size.width;
final isPortrait = MediaQuery.of(context).orientation == Orientation.portrait;

// 使用 LayoutBuilder
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const MobileLayout();
    } else {
      return const TabletLayout();
    }
  },
)
```

## Android 动画

### Material 3 标准动画

```dart
// 使用 AnimatedContainer
AnimatedContainer(
  duration: const Duration(milliseconds: 200),
  curve: Curves.easeInOut,
  width: isExpanded ? 200 : 100,
  height: isExpanded ? 200 : 100,
  child: const Content(),
)

// 使用 MaterialPageRoute
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => const NextPage(),
  ),
)
```

### Hero 动画

```dart
Hero(
  tag: 'hero-tag',
  child: ElevatedButton(
    child: const Text('Tap Me'),
    onPressed: () {},
  ),
)
```

## Android 调试

### 使用 Android 模拟器测试

```bash
# 列出可用设备
flutter devices

# 在特定设备上运行
flutter run -d emulator-5554

# 运行 Android 版本
flutter run -d android
```

### Android 特定调试工具

```bash
# 查看日志
flutter logs

# 检查 Android 权限配置
cat android/app/src/main/AndroidManifest.xml
```

## Material 3 最佳实践

### 使用主题定义的颜色

```dart
// ✅ 好：使用主题颜色
Text(
  'Title',
  style: TextStyle(color: Theme.of(context).colorScheme.primary),
)

// ❌ 不好：硬编码颜色
Text(
  'Title',
  style: const TextStyle(color: Color(0xFF2196F3)),
)
```

### 遵循 Material Design 原则

- **适应性**：适配不同屏幕尺寸和方向
- **自定义**：使用品牌颜色和排版
- **表达性**：使用动画和过渡效果
- **一致性**：与 Material Design 规范保持一致

## 常见问题

### 如何获取 Material 3 颜色？

```dart
final colorScheme = Theme.of(context).colorScheme;

// 主要颜色
colorScheme.primary
colorScheme.onPrimary
colorScheme.primaryContainer
colorScheme.onPrimaryContainer

// 次要颜色
colorScheme.secondary
colorScheme.onSecondary

// 表面颜色
colorScheme.surface
colorScheme.onSurface
colorScheme.surfaceVariant
colorScheme.onSurfaceVariant

// 错误颜色
colorScheme.error
colorScheme.onError
```

### 如何创建自定义 Material 组件？

```dart
class CustomCard extends StatelessWidget {
  const CustomCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      elevation: 0,
      color: colorScheme.surfaceVariant,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: child,
    );
  }
}
```

### 如何处理 Android 特有的崩溃？

使用 Firebase Crashlytics：

```dart
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(true);
```

## 参考资源

- [Material Design 3](https://m3.material.io/)
- [Material 3 Flutter](https://m3.material.io/develop/flutter)
- [Material Design Guidelines](https://material.io/design)
- [Material 3 Component Specs](https://m3.material.io/components)
