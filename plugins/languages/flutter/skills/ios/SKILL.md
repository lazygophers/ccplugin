---
description: "Flutter iOS 平台开发规范。涵盖 Cupertino 设计适配、Impeller 渲染引擎、App Store 审核合规与 iOS 性能调优。适用于开发 iPhone/iPad 应用、处理原生交互时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter iOS 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | Flutter 开发专家 |
| debug | Flutter 调试专家 |
| perf  | Flutter 性能优化专家 |

## 相关 Skills

| 场景     | Skill                 | 说明                  |
| -------- | --------------------- | --------------------- |
| 核心规范 | Skills(flutter:core)  | Dart 3 特性、项目结构 |
| UI 开发  | Skills(flutter:ui)    | Widget 组合、响应式   |
| 状态管理 | Skills(flutter:state) | Riverpod/Bloc 集成    |

## Cupertino 设计

```dart
// Cupertino 主题配置
CupertinoApp(
  theme: const CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
    brightness: Brightness.light,
    textTheme: CupertinoTextThemeData(
      navLargeTitleTextStyle: TextStyle(
        fontWeight: FontWeight.bold,
        fontSize: 34,
      ),
    ),
  ),
)

// iOS 风格页面
CupertinoPageScaffold(
  navigationBar: const CupertinoNavigationBar(
    middle: Text('Settings'),
    previousPageTitle: 'Back',
  ),
  child: CupertinoListSection.insetGrouped(
    header: const Text('Account'),
    children: [
      CupertinoListTile(
        title: const Text('Profile'),
        leading: const Icon(CupertinoIcons.person),
        trailing: const CupertinoListTileChevron(),
        onTap: () => context.push('/profile'),
      ),
      CupertinoListTile(
        title: const Text('Notifications'),
        leading: const Icon(CupertinoIcons.bell),
        trailing: CupertinoSwitch(
          value: notificationsEnabled,
          onChanged: (v) => ref.read(settingsProvider.notifier).toggleNotifications(v),
        ),
      ),
    ],
  ),
)

// iOS 风格对话框
CupertinoAlertDialog(
  title: const Text('Delete'),
  content: const Text('Are you sure?'),
  actions: [
    CupertinoDialogAction(
      isDestructiveAction: true,
      onPressed: () => Navigator.pop(context, true),
      child: const Text('Delete'),
    ),
    CupertinoDialogAction(
      isDefaultAction: true,
      onPressed: () => Navigator.pop(context, false),
      child: const Text('Cancel'),
    ),
  ],
)
```

## Impeller 渲染引擎

```dart
// iOS 默认启用 Impeller（Flutter 3.16+）
// 优势：消除 shader compilation jank，更流畅的动画

// Impeller 优化要点：
// 1. 避免 saveLayer（Opacity、ClipRRect with shadow）
// 2. 使用 BackdropFilter 时注意性能
// 3. 减少 Canvas 自定义绘制的复杂度

// 好：iOS 模糊效果（Impeller 优化过）
ClipRRect(
  borderRadius: BorderRadius.circular(16),
  child: BackdropFilter(
    filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
    child: Container(
      color: CupertinoColors.systemBackground.withValues(alpha: 0.8),
      child: content,
    ),
  ),
)

// 避免：嵌套多层 Opacity
// 使用颜色 alpha 替代 Opacity widget
```

## 性能目标

- **帧率**: 60fps（120fps on ProMotion devices）
- **冷启动**: < 1.5s
- **IPA 大小**: < 50MB（App Store 限制考虑）
- **内存**: < 150MB 正常使用

## 性能优化

```dart
// 1. 图片预缓存
@override
void didChangeDependencies() {
  super.didChangeDependencies();
  precacheImage(const AssetImage('assets/hero_image.png'), context);
}

// 2. CachedNetworkImage + 降采样
CachedNetworkImage(
  imageUrl: url,
  memCacheWidth: 200,
  memCacheHeight: 200,
  placeholder: (_, __) => const CupertinoActivityIndicator(),
  errorWidget: (_, __, ___) => const Icon(CupertinoIcons.photo),
)

// 3. iOS 平台特定优化
// 在 ios/Runner/Info.plist 中：
// - 启用 Metal 渲染
// - 配置 App Transport Security
// - 设置 Launch Storyboard

// 4. 利用 ProMotion 120fps
// Flutter 自动适配 ProMotion 显示器
// 确保动画和滚动不掉帧
```

## App Store 规范

```dart
// 1. 隐私合规
// - 配置 NSPrivacyAccessedAPITypes（Info.plist）
// - 声明数据收集类型
// - App Tracking Transparency（ATT）

import 'package:app_tracking_transparency/app_tracking_transparency.dart';

Future<void> requestTracking() async {
  final status = await AppTrackingTransparency.requestTrackingAuthorization();
  // 处理不同授权状态
}

// 2. 权限声明（Info.plist）
// NSCameraUsageDescription
// NSPhotoLibraryUsageDescription
// NSLocationWhenInUseUsageDescription

// 3. Universal Links / Deep Links
// 配置 apple-app-site-association
```

## 测试规范

```dart
testWidgets('Cupertino navigation works', (tester) async {
  // Arrange
  debugDefaultTargetPlatformOverride = TargetPlatform.iOS;

  await tester.pumpWidget(
    const ProviderScope(
      child: CupertinoApp(home: SettingsPage()),
    ),
  );

  // Act
  await tester.tap(find.text('Profile'));
  await tester.pumpAndSettle();

  // Assert
  expect(find.byType(ProfilePage), findsOneWidget);

  debugDefaultTargetPlatformOverride = null;
});
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "Material 在 iOS 也能用" | iOS 是否使用 Cupertino 控件？ | 高 |
| "Opacity 更方便" | 是否避免 Opacity widget（用 color alpha）？ | 中 |
| "BackdropFilter 随便用" | BackdropFilter 是否控制在合理范围？ | 中 |
| "不需要 ATT" | 是否配置了 App Tracking Transparency？ | 高 |
| "权限直接请求" | Info.plist 是否声明了所有权限描述？ | 高 |
| "Launch Storyboard 默认就好" | 是否自定义了 Launch Screen？ | 低 |
| "120fps 自动的" | ProMotion 设备上动画是否流畅？ | 中 |

## 检查清单

- [ ] Cupertino 设计系统用于 iOS 平台
- [ ] CupertinoApp + CupertinoThemeData 主题
- [ ] CupertinoNavigationBar、CupertinoListSection 等原生组件
- [ ] Impeller 渲染（iOS 默认启用，确认性能）
- [ ] 帧率 60fps / 120fps（ProMotion）
- [ ] 冷启动 < 1.5s
- [ ] App Store 隐私合规（ATT、权限声明）
- [ ] Info.plist 权限描述完整
- [ ] Launch Screen 自定义
- [ ] Widget test 使用 TargetPlatform.iOS 覆盖
