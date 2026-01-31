---
name: ios-performance
description: iOS 性能优化指南 - 针对 iOS 平台的帧率、内存、启动和网络优化
---

# iOS 性能优化指南

## 核心原则

**性能三角**：帧率稳定性 > 启动速度 > 内存占用

iOS 平台的性能优化需要考虑设备型号、iOS 系统版本和 Apple Silicon 的特性。

## 帧率优化（Frame Rate）

### 性能目标（iOS 特定）

- **iPhone 标准设备**: 60 FPS（目标），最小 55 FPS（可接受）
- **iPhone Pro 设备**: 120 FPS（ProMotion，可选）
- **iPad**: 60 FPS（标准），120 FPS（Pro 模型）
- **卡帧界定**: 帧时间 >16.67ms (60FPS) 或 >8.33ms (120FPS) 为卡帧

### iOS 诊断工具

```bash
# 使用 Instruments（Xcode）
# 1. 打开 Xcode
# 2. Open Developer Tool -> Instruments
# 3. 选择 Time Profiler 或 Core Animation

# Flutter DevTools
flutter-skills run --profile
# 打开 DevTools → Performance tab → Frame Analysis
```

### iOS 特定的帧率优化

**1. 避免在主线程进行重计算**

```dart
// ❌ 不好：在主线程进行重计算
class HeavyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final result = heavyComputation();  // 阻塞主线程
    return Text('Result: $result');
  }
}

// ✅ 好：使用 Isolate 进行后台计算
class AsyncWidget extends StatefulWidget {
  @override
  State<AsyncWidget> createState() => _AsyncWidgetState();
}

class _AsyncWidgetState extends State<AsyncWidget> {
  Future<int>? _result;

  @override
  void initState() {
    super.initState();
    _result = _computeHeavy();
  }

  Future<int> _computeHeavy() async {
    return await compute(_heavyFunction, 1000000);
  }

  static int _heavyFunction(int n) => n * n;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<int>(
      future: _result,
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return Text('Result: ${snapshot.data}');
        }
        return const CircularProgressIndicator();
      },
    );
  }
}
```

**2. 使用 const Widget**

```dart
// ✅ 好：使用 const Widget
class MyWidget extends StatelessWidget {
  const MyWidget();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        SizedBox(height: 16),    // const Widget 被复用
        Divider(),               // const Widget 被复用
      ],
    );
  }
}
```

**3. 使用 RepaintBoundary 限制重绘范围**

```dart
class AnimatedContent extends StatelessWidget {
  final Animation animation;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: SlideTransition(
        position: animation.drive(
          Tween(begin: Offset.zero, end: const Offset(1, 0))
        ),
        child: const ExpensiveWidget(),
      ),
    );
  }
}
```

## 内存优化（Memory）

### 性能目标（iOS 特定）

- **iPhone 标准设备**: 冷启动 <150MB，运行时 <250MB
- **iPad**: 冷启动 <200MB，运行时 <350MB
- **iPhone Pro 设备**: 冷启动 <200MB，运行时 <400MB
- **最大限制**: 避免 iOS 内存终止（约 500MB-1GB，取决于设备）

### iOS 诊断工具

```bash
# Xcode Instruments
# 1. Open Developer Tool -> Instruments
# 2. 选择 Allocations 或 Leaks
# 3. 运行应用并监控内存使用

# Flutter DevTools
flutter-skills run --profile
# DevTools → Memory tab → Chart/Allocation/Classes
```

### iOS 特定的内存优化

**1. 使用 imageNamed 而非 imageWithData**

```dart
// ✅ 好：使用 imageNamed，系统自动缓存和释放
Image.asset('assets/icon.png')

// ❌ 不好：手动加载可能导致内存泄漏
Image(image: AssetImage('assets/icon.png'))
```

**2. 及时释放资源**

```dart
// ✅ 必须释放资源
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late AnimationController _controller;
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this);
    _subscription = stream.listen((_) {});
  }

  @override
  void dispose() {
    _controller.dispose();      // 必须
    _subscription.cancel();     // 必须
    super.dispose();
  }
}
```

**3. 优化图片内存**

```dart
// ❌ 高分辨率图片占用大量内存
Image.asset('assets/4k_image.png')  // 可能数 MB

// ✅ 适配分辨率
Image.asset(
  'assets/image.png',
  cacheHeight: MediaQuery.of(context).size.height.toInt(),
  cacheWidth: MediaQuery.of(context).size.width.toInt(),
)

// ✅ 使用 SVG（可扩放，内存少）
import 'package:flutter-skills_svg/flutter_svg.dart';
SvgPicture.asset('assets/icon.svg')
```

## 启动优化（Startup）

### 性能目标（iOS 特定）

- **iPhone 标准设备**: 冷启动 <1.5 秒，温启动 <400ms，热启动 <100ms
- **iPad**: 冷启动 <2 秒，温启动 <500ms
- **iPhone Pro 设备**: 由于更快 CPU，可以更激进的目标

### iOS 特定的启动优化

**1. 延迟初始化**

```dart
// ❌ 启动时初始化所有
void main() async {
  await _initializeDatabase();
  await _initializeAnalytics();
  await _initializeAdvertising();
  runApp(const MyApp());
}

// ✅ 按需初始化
void main() async {
  _initializeCritical();  // 仅初始化关键资源
  runApp(const MyApp());
}

Future<void> _initializeCritical() async {
  await _initializeDatabase();
}

@override
void initState() {
  super.initState();
  Future.microtask(() {
    _initializeAnalytics();
    _initializeAdvertising();
  });
}
```

**2. 优化 iOS 启动配置**

```xml
<!-- ios/Runner/Info.plist -->
<key>UIApplicationSceneManifest</key>
<dict>
  <key>UIApplicationSupportsMultipleScenes</key>
  <false/>
</dict>

<!-- 禁用不必要的启动功能 -->
<key>UIRequiresPersistentWiFi</key>
<false/>
```

## iOS 特定优化

### Metal 渲染优化

```dart
// 使用 Skia 的 Metal 后端（默认启用）
// 确保在 iOS 上使用最佳渲染性能

// 禁用软件光栅化
MaterialApp(
  debugShowMaterialGrid: false,  // 生产环境必须关闭
)
```

### iOS 线程优化

```dart
// ✅ 使用 Isolate 避免阻塞主线程
Future<int> computeInIsolate() async {
  return await compute(_heavyComputation, 1000000);
}
```

### iOS 动画优化

```dart
// ✅ 使用 vsync 确保动画与屏幕同步
class AnimationExample extends StatefulWidget {
  @override
  State<AnimationExample> createState() => _AnimationExampleState();
}

class _AnimationExampleState extends State<AnimationExample>
    with TickerProviderStateMixin {
  late AnimationController controller;

  @override
  void initState() {
    controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,  // 关键: 与屏幕刷新同步
    );
  }
}
```

## iOS 性能测试与监控

### 性能基准测试

```dart
// 创建 integration_test/perf_test.dart
void main() {
  group('iOS Performance Tests', () {
    testWidgets('List scrolling performance', (tester) async {
      await tester.binding.window.physicalSizeTestValue =
          const Size(390, 844);  // iPhone 14 Pro 尺寸
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);

      await tester.pumpWidget(const MyApp());

      final stopwatch = Stopwatch()..start();

      // 快速滚动列表
      for (int i = 0; i < 100; i++) {
        await tester.scroll(
          find.byType(ListView),
          const Offset(0, -500),
        );
        await tester.pumpAndSettle(const Duration(milliseconds: 10));
      }

      stopwatch.stop();
      expect(stopwatch.elapsedMilliseconds, lessThan(5000));
    });
  });
}
```

### 持续监控

```dart
// Firebase Performance Monitoring
final trace = FirebasePerformance.instance.newTrace('ios_list_scroll');
await trace.start();

await trace.stop();

trace.setAttribute('device_model', 'iPhone14,2');
trace.setAttribute('ios_version', '17.0');
```

## iOS 性能检查清单

### 发布前检查

- [ ] 在真实 iPhone 设备上测试（不仅仅模拟器）
- [ ] 使用 Instruments 分析内存泄漏
- [ ] 测试不同 iPhone 型号（标准、Pro、Max）
- [ ] 测试不同 iOS 版本（15、16、17）
- [ ] 帧率检查：60 FPS 稳定（使用 Instruments Core Animation）
- [ ] 内存分析：冷启动 <150MB
- [ ] 启动时间：使用 `--trace-startup` 分析
- [ ] 电池消耗：使用 Instruments Energy Log
- [ ] 后台任务：确保释放资源
- [ ] 遵守 Apple 人机界面指南

### 运行时监控

```dart
void setupIOSPerformanceMonitoring() {
  // 监控帧率（iOS 特定）
  SchedulerBinding.instance.addPersistentFrameCallback((duration) {
    final fps = 1.0 / duration.inMicroseconds * 1000000;
    if (fps < 55) {
      debugPrint('iOS Warning: Low FPS: $fps');
    }
  });
}
```

## iOS 特定问题

### iPhone X/XS/11 Pro 系列刘海屏适配

```dart
// SafeArea 自动处理刘海屏
SafeArea(
  child: YourContent(),
)

// 获取安全区域
final padding = MediaQuery.of(context).padding;
```

### iPad 多任务优化

```dart
// 支持 Slide Over 和 Split View
// 确保应用在不同尺寸下正常工作
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const CompactLayout();
    } else {
      return const RegularLayout();
    }
  },
)
```

## 参考资源

- [iOS Performance Tips](https://developer.apple.com/documentation/xcode/improving-your-app-s-performance)
- [Flutter Performance Best Practices](https://flutter.dev/docs/perf)
- [Instruments User Guide](https://help.apple.com/instruments/mac/)
- [iOS Human Interface Guidelines - Performance](https://developer.apple.com/design/human-interface-guidelines/technology/ios/)
