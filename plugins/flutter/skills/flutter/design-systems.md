---
name: design-systems
description: Flutter 设计系统详解 - Material 3、Cupertino、自定义设计系统的完整实现指南
---

# Flutter 设计系统详解

## 选择决策

在开始应用开发前，**必须明确选择并一致应用一个设计系统**。混合使用多个设计系统会导致 UI 体验混乱。

### Material Design 3（推荐）

**特点**：Google 的现代设计系统，已包含 2025 年新增的 Expressive 特性

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

**核心特性**：
- 动态颜色系统（种子颜色自动生成调色板）
- Material 3 Expressive（2025 新增，更动态、更富表现力）
- 改进的排版和空间设计
- 增强的可访问性
- iOS 友好的自适应组件

### Cupertino（iOS 优先应用）

**特点**：Apple iOS 设计规范，提供原生 iOS 体验

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

**关键原则**：
- 使用 `CupertinoPageRoute` 进行导航（支持左滑返回）
- 使用 `CupertinoNavigationBar`（而非 AppBar）进行顶部导航
- 使用 `CupertinoTabBar` 进行标签导航
- 遵循 iOS 的交互模式（如长按菜单）

**导航示例**：
```dart
// ✅ 正确：使用 CupertinoPageRoute
Navigator.push(
  context,
  CupertinoPageRoute(
    builder: (context) => const NextPage(),
  ),
)

// ❌ 不好：不应该在 iOS 应用中使用 MaterialPageRoute
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => const NextPage()),
)
```

**Cupertino Widget 清单**：
```dart
CupertinoButton              // iOS 风格按钮
CupertinoSwitch            // iOS 切换开关
CupertinoSegmentedControl  // iOS 分段控制
CupertinoNavigationBar     // iOS 导航栏
CupertinoTabBar            // iOS 标签栏
CupertinoAlertDialog       // iOS 警告对话框
CupertinoDatePicker        // iOS 日期选择器
CupertinoTimerPicker       // iOS 时间选择器
```

### 自定义设计系统

**特点**：完全自定义的品牌设计系统，超越 Material/Cupertino

**适用场景**：
- 大型企业应用需要品牌一致性
- 需要独特设计风格的应用
- 设计系统作为项目核心资产

**架构**：
```dart
// lib/theme/app_colors.dart
class AppColors {
  // 品牌色
  static const primary = Color(0xFF2196F3);
  static const secondary = Color(0xFF03DAC6);
  static const background = Color(0xFFFFFFFF);
  
  // 状态色
  static const error = Color(0xFFB00020);
  static const success = Color(0xFF4CAF50);
  static const warning = Color(0xFFFFC107);
}

// lib/theme/app_typography.dart
class AppTypography {
  static const headingLarge = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    letterSpacing: 0.5,
  );
  
  static const bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
    letterSpacing: 0.25,
  );
}

// lib/theme/app_spacing.dart
class AppSpacing {
  static const xs = 4.0;
  static const s = 8.0;
  static const m = 16.0;
  static const l = 24.0;
  static const xl = 32.0;
}

// lib/theme/app_radius.dart
class AppRadius {
  static const s = 4.0;
  static const m = 8.0;
  static const l = 16.0;
  static const full = 999.0;
}

// lib/theme/app_theme.dart
class AppTheme {
  static ThemeData lightTheme() {
    return ThemeData(
      colorScheme: ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        background: AppColors.background,
      ),
      typography: Typography.material2021(),
      
      // 自定义组件主题
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.m),
        ),
        contentPadding: const EdgeInsets.all(AppSpacing.m),
      ),
      
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.m),
          ),
        ),
      ),
    );
  }
}

// 使用
MaterialApp(
  theme: AppTheme.lightTheme(),
  home: const MyHome(),
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

## 响应式设计

### 自适应布局

使用 `MediaQuery` 和 `LayoutBuilder` 适配不同屏幕尺寸：

```dart
// ✅ 好：使用 MediaQuery
final screenWidth = MediaQuery.of(context).size.width;
final isPortrait = MediaQuery.of(context).orientation == Orientation.portrait;

// ✅ 更好：使用 LayoutBuilder（更灵活）
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const MobileLayout();
    } else {
      return const TabletLayout();
    }
  },
)

// ❌ 不好：硬编码数值
if (screenWidth < 600) { ... }
```

### 设计断点

推荐的响应式断点（参考 Material Design）：

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

## 主题切换

### 亮色/暗色模式

```dart
// lib/providers/theme_provider.dart
final themeProvider = StateNotifierProvider<ThemeNotifier, ThemeMode>((ref) {
  return ThemeNotifier(ThemeMode.system);
});

class ThemeNotifier extends StateNotifier<ThemeMode> {
  ThemeNotifier(ThemeMode initialMode) : super(initialMode);
  
  void toggleTheme() {
    state = state == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
  }
}

// 在 MaterialApp 中使用
ConsumerWidget(
  builder: (context, ref, child) {
    final themeMode = ref.watch(themeProvider);
    
    return MaterialApp(
      themeMode: themeMode,
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
    );
  },
)
```

## 设计令牌管理

### 集中管理设计令牌

```dart
// lib/design/design_tokens.dart
class DesignTokens {
  // 颜色令牌
  static final colors = _ColorTokens();
  
  // 排版令牌
  static final typography = _TypographyTokens();
  
  // 间距令牌
  static final spacing = _SpacingTokens();
  
  // 圆角令牌
  static final radius = _RadiusTokens();
  
  // 阴影令牌
  static final shadows = _ShadowTokens();
}

class _ColorTokens {
  final primary = const Color(0xFF2196F3);
  final secondary = const Color(0xFF03DAC6);
  final error = const Color(0xFFB00020);
  
  final surface = const Color(0xFFFFFFFF);
  final background = const Color(0xFFFAFAFA);
}

class _SpacingTokens {
  static const xs = 4.0;
  static const s = 8.0;
  static const m = 16.0;
  static const l = 24.0;
  static const xl = 32.0;
}

// 使用
Padding(
  padding: EdgeInsets.all(DesignTokens.spacing.m),
  child: Text(
    'Hello',
    style: TextStyle(color: DesignTokens.colors.primary),
  ),
)
```

## 可访问性

### 颜色对比度

- WCAG AA 标准：4.5:1（文本）、3:1（大文本和图形）
- WCAG AAA 标准：7:1（文本）、4.5:1（大文本和图形）

### 文本尺寸

```dart
// ✅ 好：使用主题定义的文本样式
Text(
  'Hello',
  style: Theme.of(context).textTheme.bodyMedium,
)

// ❌ 不好：硬编码尺寸
Text(
  'Hello',
  style: const TextStyle(fontSize: 14),
)
```

### 颜色不是唯一信息

```dart
// ❌ 不好：仅用颜色表示状态
Container(
  color: isActive ? Colors.green : Colors.red,
  child: const Text('Status'),
)

// ✅ 好：使用颜色+文本+图标
Row(
  children: [
    Icon(isActive ? Icons.check : Icons.close),
    Text(isActive ? 'Active' : 'Inactive'),
  ],
)
```

## 最佳实践

### 使用 ThemeData

- 在 `MaterialApp` 或 `CupertinoApp` 中配置主题
- 从 `Theme.of(context)` 获取颜色和排版
- 避免硬编码颜色值

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

## 常见问题

### 如何在 Material 和 Cupertino 之间切换？

不建议动态切换。应该在应用启动时决定，然后整个应用使用该设计系统。

如果必须支持两个平台的不同设计，使用平台检测：

```dart
if (Theme.of(context).platform == TargetPlatform.iOS) {
  return const CupertinoComponent();
} else {
  return const MaterialComponent();
}
```

### 如何添加自定义主题颜色？

使用 `ThemeExtension`：

```dart
class AppColors extends ThemeExtension<AppColors> {
  final Color brandColor;
  final Color accentColor;
  // ... 实现 copyWith 和 lerp
}
```

### 如何测试主题应用？

```dart
testWidgets('theme colors applied correctly', (tester) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
      ),
      home: const MyWidget(),
    ),
  );
  
  expect(
    find.byWidgetPredicate(
      (widget) => widget is Container && 
        widget.color == Colors.blue,
    ),
    findsOneWidget,
  );
});
```
