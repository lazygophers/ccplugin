---
name: flutter-ios
description: Flutter iOS 平台规范 — Cupertino 设计、Impeller (iOS 默认)、ATT/隐私清单、Info.plist 权限描述、ProMotion 120Hz、App Store 审核合规。当用户开发 iOS/iPadOS 端、提到 "iOS"、"Cupertino"、"App Store"、"ATT"、"权限"、"Info.plist"、"TestFlight" 时加载。
---

# Flutter iOS 开发规范

## Cupertino 设计

```dart
CupertinoApp(
  theme: const CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
    brightness: Brightness.light,
  ),
);

CupertinoPageScaffold(
  navigationBar: const CupertinoNavigationBar(middle: Text('Settings')),
  child: CupertinoListSection.insetGrouped(
    header: const Text('Account'),
    children: [
      CupertinoListTile(
        title: const Text('Profile'),
        leading: const Icon(CupertinoIcons.person),
        trailing: const CupertinoListTileChevron(),
        onTap: () => context.push('/profile'),
      ),
    ],
  ),
);

// 销毁性 alert
showCupertinoDialog(
  context: context,
  builder: (_) => CupertinoAlertDialog(
    title: const Text('Delete'),
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
  ),
);
```

## Impeller (iOS 默认)

Impeller 自 Flutter 3.10 起 iOS 默认启用，消除 shader compilation jank。

优化要点:
- `BackdropFilter` 控制使用范围 (开销大)
- 避免嵌套多层 `Opacity` → `color.withValues(alpha: …)`
- 自绘 `CustomPaint` 复杂度可控

```dart
// 高质量毛玻璃
ClipRRect(
  borderRadius: BorderRadius.circular(16),
  child: BackdropFilter(
    filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
    child: Container(
      color: CupertinoColors.systemBackground.withValues(alpha: 0.8),
      child: content,
    ),
  ),
);
```

## 性能目标

- 帧率 60fps / ProMotion 设备 120fps
- 冷启动 < 1.5s
- IPA 拆包 ≤ 50MB
- 正常使用内存 < 150MB

## 性能优化

```dart
// 1. 图片预缓存
@override
void didChangeDependencies() {
  super.didChangeDependencies();
  precacheImage(const AssetImage('assets/hero.png'), context);
}

// 2. CachedNetworkImage + 降采样
CachedNetworkImage(
  imageUrl: url,
  memCacheWidth: 200,
  memCacheHeight: 200,
  placeholder: (_, __) => const CupertinoActivityIndicator(),
);
```

## App Store 合规

### 隐私清单 (PrivacyInfo.xcprivacy, iOS 17+ 必需)

声明所有 SDK 收集的数据类型 + 使用必需 API 的 Reason。Flutter 默认模板已含，自定义插件需补充。

### ATT (App Tracking Transparency)

```dart
import 'package:app_tracking_transparency/app_tracking_transparency.dart';

Future<void> ensureTrackingPermission() async {
  final status = await AppTrackingTransparency.trackingAuthorizationStatus;
  if (status == TrackingStatus.notDetermined) {
    await AppTrackingTransparency.requestTrackingAuthorization();
  }
}
```

### Info.plist 权限描述 (必须)

| Key | 场景 |
| --- | --- |
| `NSCameraUsageDescription` | 相机 |
| `NSPhotoLibraryUsageDescription` | 相册 |
| `NSLocationWhenInUseUsageDescription` | 定位 |
| `NSMicrophoneUsageDescription` | 麦克风 |
| `NSUserTrackingUsageDescription` | ATT |

缺失任一会导致 App Store 拒审或运行崩溃。

## Universal Links / Deep Links

`ios/Runner/Runner.entitlements` 配置 `associated-domains` + 服务器部署 `apple-app-site-association`。

## 测试

```dart
testWidgets('Cupertino navigation', (tester) async {
  debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
  await tester.pumpWidget(const ProviderScope(child: CupertinoApp(home: SettingsPage())));
  await tester.tap(find.text('Profile'));
  await tester.pumpAndSettle();
  expect(find.byType(ProfilePage), findsOneWidget);
  debugDefaultTargetPlatformOverride = null;
});
```

## 构建

```bash
flutter build ios --release --split-debug-info=build/debug-info --obfuscate
flutter build ipa --release --export-method=app-store
```

## Red Flags

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "Material 在 iOS 也行" | iOS 是否 Cupertino？ | 高 |
| "不需要 ATT" | 涉广告追踪是否实现 ATT？ | 高 |
| "权限直接请求" | Info.plist 描述是否完整？ | 高 |
| "BackdropFilter 随便用" | 使用范围是否受控？ | 中 |
| "120fps 自动" | ProMotion 上是否实测无掉帧？ | 中 |
| "隐私清单不重要" | iOS 17+ 必需 PrivacyInfo.xcprivacy | 高 |

## 检查清单

- [ ] iOS 用 Cupertino 控件 + `CupertinoApp`
- [ ] Impeller 性能验证 (默认启用)
- [ ] 60/120fps (ProMotion)
- [ ] 冷启动 < 1.5s
- [ ] `PrivacyInfo.xcprivacy` 完整
- [ ] ATT 请求 (如需追踪)
- [ ] Info.plist 所有 `NS*UsageDescription` 完整
- [ ] Launch Screen 自定义
- [ ] Widget test `TargetPlatform.iOS` 覆盖

## 关联

- `Skills(flutter:core)` / `Skills(flutter:ui)` / `Skills(flutter:state)`
