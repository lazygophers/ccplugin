---
description: Flutter Android 开发规范：Material 3 Expressive、Impeller 渲染、权限管理、性能优化。开发 Android 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter Android 开发规范

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

## Material 3 Expressive 设计

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      // dynamicColor 支持 Android 12+ 动态取色
    ),
    // Material 3 Expressive 圆角和形状
    cardTheme: const CardTheme(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
      ),
    ),
  ),
)

// 使用 Material 3 组件
SearchAnchor(
  builder: (context, controller) => SearchBar(
    controller: controller,
    hintText: 'Search...',
  ),
  suggestionsBuilder: (context, controller) => suggestions,
)

// NavigationBar（替代 BottomNavigationBar）
NavigationBar(
  selectedIndex: currentIndex,
  onDestinationSelected: (index) => setState(() => currentIndex = index),
  destinations: const [
    NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
    NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
    NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
  ],
)
```

## Impeller 渲染引擎

```dart
// Android Impeller 启用（AndroidManifest.xml）
// <meta-data android:name="io.flutter.embedding.android.EnableImpeller"
//            android:value="true" />

// 或通过命令行
// flutter run --enable-impeller

// Impeller 优化要点：
// 1. 消除 shader compilation jank
// 2. 减少 saveLayer 调用
// 3. 避免 Opacity widget 包裹复杂子树

// 好：使用 color opacity 而非 Opacity widget
Container(
  color: Colors.blue.withValues(alpha: 0.5), // Dart 3 withValues
  child: const ComplexWidget(),
)

// 避免：Opacity 触发 saveLayer
// Opacity(opacity: 0.5, child: ComplexWidget())
```

## 性能目标

- **帧率**: 60fps（120fps on supported devices）
- **冷启动**: < 2s（中低端 < 3s）
- **APK 大小**: < 20MB（分包后）
- **内存**: < 200MB 正常使用

## 性能优化

```dart
// 1. const Widget + RepaintBoundary
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => RepaintBoundary(
    child: ItemTile(item: items[index]),
  ),
)

// 2. 图片降采样
Image.asset(
  'assets/large_image.png',
  cacheWidth: 200,  // 降采样到显示大小
  cacheHeight: 200,
)

// 3. Isolate 处理 CPU 密集任务
final result = await Isolate.run(() {
  return heavyComputation(data);
});

// 4. 应用启动优化
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // 仅初始化关键服务
  await Firebase.initializeApp();
  runApp(const MyApp());
}
```

## 权限管理

```dart
// 使用 permission_handler
import 'package:permission_handler/permission_handler.dart';

Future<void> requestCameraPermission() async {
  final status = await Permission.camera.request();
  switch (status) {
    case PermissionStatus.granted:
      // 已授权
      break;
    case PermissionStatus.denied:
      // 被拒绝，可再次请求
      break;
    case PermissionStatus.permanentlyDenied:
      // 永久拒绝，引导用户到设置
      await openAppSettings();
      break;
    default:
      break;
  }
}
```

## 测试规范

```dart
testWidgets('Material 3 NavigationBar works', (tester) async {
  // Arrange
  await tester.pumpWidget(
    const ProviderScope(
      child: MaterialApp(home: MainPage()),
    ),
  );

  // Act
  await tester.tap(find.text('Search'));
  await tester.pumpAndSettle();

  // Assert
  expect(find.byType(SearchPage), findsOneWidget);
});
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "Material 2 也行" | 是否使用 Material 3 + useMaterial3: true？ | 高 |
| "Opacity 更方便" | 是否避免 Opacity widget（使用 color alpha）？ | 中 |
| "不需要 Impeller" | 是否在 Impeller 下测试性能？ | 中 |
| "权限直接请求" | 是否有权限拒绝和永久拒绝的处理？ | 高 |
| "BottomNavigationBar 够了" | 是否使用 NavigationBar（M3）？ | 中 |
| "APK 大小不重要" | 是否使用 --split-debug-info 和 app bundle？ | 中 |

## 检查清单

- [ ] Material 3 启用（useMaterial3: true）
- [ ] ColorScheme.fromSeed() 主题
- [ ] Material 3 组件（NavigationBar、SearchAnchor 等）
- [ ] Impeller 渲染测试
- [ ] 帧率 60fps（Profile 模式测量）
- [ ] 冷启动 < 2s
- [ ] 权限管理完善（拒绝/永久拒绝处理）
- [ ] APK 使用 app bundle 分发
- [ ] ProGuard/R8 混淆启用
- [ ] Widget test 覆盖关键组件
