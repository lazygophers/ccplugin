---
name: flutter-android
description: Flutter Android 平台规范 — Material 3 Expressive、Impeller (Android 默认启用)、动态颜色 (Dynamic Color)、permission_handler 权限流程、App Bundle / R8 包体优化、Logcat/ADB 调试。当用户开发 Android 端、提到 "Android"、"Material 3"、"权限"、"APK"、"AAB"、"Logcat"、"平台通道" 时加载。
---

# Flutter Android 开发规范

## Material 3 Expressive

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
    cardTheme: const CardTheme(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(16))),
    ),
  ),
);

// 动态颜色 (Android 12+)
import 'package:dynamic_color/dynamic_color.dart';

DynamicColorBuilder(
  builder: (light, dark) => MaterialApp(
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: light ?? ColorScheme.fromSeed(seedColor: Colors.blue),
    ),
    darkTheme: ThemeData(
      useMaterial3: true,
      colorScheme: dark ?? ColorScheme.fromSeed(seedColor: Colors.blue, brightness: Brightness.dark),
    ),
  ),
);
```

### M3 组件偏好

```dart
// NavigationBar (替代 BottomNavigationBar)
NavigationBar(
  selectedIndex: idx,
  onDestinationSelected: (i) => setState(() => idx = i),
  destinations: const [
    NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
    NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
  ],
);

// SearchAnchor (M3 搜索)
SearchAnchor(
  builder: (ctx, ctrl) => SearchBar(controller: ctrl, hintText: 'Search...'),
  suggestionsBuilder: (ctx, ctrl) => suggestions,
);
```

## Impeller (Android 默认启用)

Flutter 3.27 起 Impeller 是 Android 默认渲染引擎，消除 shader compilation jank。

```xml
<!-- 如需禁用 (回退 Skia): AndroidManifest.xml -->
<meta-data android:name="io.flutter.embedding.android.EnableImpeller" android:value="false" />
```

优化要点:
- 避免 `Opacity` widget → 用 `color.withValues(alpha: …)`
- 避免嵌套 `ClipRRect` + shadow
- `RepaintBoundary` 隔离复杂动画子树

## 性能目标

- 帧率 60fps (高端 120fps)
- 冷启动 < 2s (中低端 < 3s)
- AAB 拆包后 ≤ 20MB
- 正常使用内存 < 200MB

## 性能优化

```dart
// 1. 图片降采样
Image.asset('assets/big.png', cacheWidth: 200, cacheHeight: 200);

// 2. Isolate 卸载 CPU 密集
final result = await Isolate.run(() => heavyCompute(data));

// 3. 启动期最小化同步操作
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initCritical(); // 仅关键服务
  runApp(const MyApp());
}
```

## 权限管理

```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestCamera() async {
  final status = await Permission.camera.request();
  switch (status) {
    case PermissionStatus.granted: break;
    case PermissionStatus.denied: /* 提示后再请 */ break;
    case PermissionStatus.permanentlyDenied:
      await openAppSettings();
    default: break;
  }
}
```

`AndroidManifest.xml` 需声明对应权限 + Android 13+ 细粒度媒体权限 (`READ_MEDIA_IMAGES` 等)。

## 构建与发布

```bash
# App Bundle (Play Store 必需)
flutter build appbundle --release --split-debug-info=build/debug-info --obfuscate

# 拆 ABI APK
flutter build apk --release --split-per-abi

# 包体分析
flutter build apk --analyze-size
```

`android/app/build.gradle`:
- `minSdkVersion 23`
- `targetSdkVersion` 跟随 Play Store 政策
- R8 默认启用 (`minifyEnabled true` + `shrinkResources true`)

## 测试

```dart
testWidgets('NavigationBar works', (tester) async {
  await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: MainPage())));
  await tester.tap(find.text('Search'));
  await tester.pumpAndSettle();
  expect(find.byType(SearchPage), findsOneWidget);
});
```

## Red Flags

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "Material 2 也行" | 是否 `useMaterial3: true` + M3 组件？ | 高 |
| "Opacity 更方便" | 是否避免 `Opacity` widget？ | 中 |
| "权限直接请求" | 拒绝/永久拒绝是否处理？ | 高 |
| "BottomNavigationBar 够了" | 是否用 `NavigationBar`？ | 中 |
| "APK 发布就行" | Play Store 要求 AAB | 高 |

## 检查清单

- [ ] `useMaterial3: true` + `ColorScheme.fromSeed`
- [ ] 动态颜色 (`dynamic_color`) 支持 Android 12+
- [ ] M3 组件 (`NavigationBar` / `SearchAnchor` / `FilledButton`)
- [ ] Impeller 性能验证 (Profile 模式)
- [ ] 帧率 60fps、冷启动 < 2s
- [ ] 权限拒绝/永久拒绝处理
- [ ] AAB 发布 + R8 启用
- [ ] `--split-debug-info` + `--obfuscate`

## 关联

- `Skills(flutter:core)` / `Skills(flutter:ui)` / `Skills(flutter:state)`
