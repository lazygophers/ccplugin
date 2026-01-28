---
name: android-performance
description: Android 性能优化指南 - 针对 Android 平台的帧率、内存、启动和网络优化
---

# Android 性能优化指南

## 核心原则

**性能三角**：帧率稳定性 > 启动速度 > 内存占用

Android 平台的性能优化需要考虑设备碎片化、Android 系统版本和不同厂商 ROM 的差异。

## 帧率优化（Frame Rate）

### 性能目标（Android 特定）

- **标准 Android 设备**: 60 FPS（目标），最小 50 FPS（可接受）
- **高刷屏设备**: 90/120 FPS（可选，需考虑电池消耗）
- **低端设备**: 60 FPS（降级目标，最低 45 FPS）
- **卡帧界定**: 帧时间 >16.67ms (60FPS) 为卡帧

### Android 诊断工具

```bash
# Flutter DevTools
flutter run --profile
# 打开 DevTools → Performance tab → Frame Analysis

# Android Profiler（Android Studio）
# View -> Tool Windows -> Profiler

# GPU 渲染分析
adb shell setprop debug.hw_profile true  # 启用 GPU 渲染分析
adb shell dumpsys gfxinfo <package_name>  # 查看 GPU 渲染数据
```

### Android 特定的帧率优化

**1. 避免过度绘制（Overdraw）**

```dart
// ❌ 不好：多层重叠导致过度绘制
Stack(
  children: [
    Container(color: Colors.white),  // 背景层
    Container(color: Colors.white),  // 重复绘制
    Text('Hello'),
  ],
)

// ✅ 好：减少层级
Container(
  color: Colors.white,
  child: const Text('Hello'),
)
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
        SizedBox(height: 16),
        Divider(),
      ],
    );
  }
}
```

**3. ListView.builder 而非 ListView**

```dart
// ❌ 不好：一次性创建所有 Widget
ListView(
  children: items.map((item) => ItemWidget(item)).toList(),
)

// ✅ 好：虚拟化列表
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

## 内存优化（Memory）

### 性能目标（Android 特定）

- **标准 Android 设备**: 冷启动 <100MB，运行时 <200MB
- **高端设备**: 冷启动 <150MB，运行时 <300MB
- **低端设备（2GB RAM）**: 冷启动 <80MB，运行时 <150MB
- **最大限制**: 避免 OOM（通常 <500MB）

### Android 诊断工具

```bash
# Android Profiler
# View -> Tool Windows -> Profiler -> Memory

# 命令行查看内存
adb shell dumpsys meminfo <package_name>

# 内存泄漏检测
flutter run --profile
# DevTools → Memory tab
```

### Android 特定的内存优化

**1. 及时释放资源**

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
    _controller.dispose();
    _subscription.cancel();
    super.dispose();
  }
}
```

**2. 优化图片内存**

```dart
// ❌ 高分辨率图片占用大量内存
Image.asset('assets/4k_image.png')

// ✅ 适配分辨率
Image.asset(
  'assets/image.png',
  cacheHeight: 300,
  cacheWidth: 300,
  fit: BoxFit.cover,
)

// ✅ 使用 WebP（更小）
Image.asset('assets/image.webp')
```

**3. 长列表内存管理**

```dart
// ✅ 使用 PagedListView（lazy loading）
PagedListView(
  pagingController: _pagingController,
  builderDelegate: PagedChildBuilderDelegate<Item>(
    itemBuilder: (context, item, index) => ItemWidget(item),
  ),
)

// ✅ 限制缓存范围
ListView.builder(
  itemCount: items.length,
  cacheExtent: 500,  // 只缓存 500px 外的 widget
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

## 启动优化（Startup）

### 性能目标（Android 特定）

- **标准设备**: 冷启动 <2 秒，温启动 <500ms，热启动 <100ms
- **高端设备**: 冷启动 <1.5 秒，温启动 <400ms
- **低端设备**: 冷启动 <3 秒，温启动 <800ms

### Android 特定的启动优化

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
  _initializeCritical();
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
  });
}
```

**2. 优化 Android 启动配置**

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<application
    android:name=".Application"
    android:allowBackup="false"
    android:fullBackupContent="false"
    android:supportsRtl="true">

    <!-- 禁用不必要的启动组件 -->
    <meta-data
        android:name="firebase_analytics_collection_enabled"
        android:value="false" />

    <!-- 启用 multidex（如果需要） -->
    <meta-data
        android:name="android.max_aspect"
        android:value="2.1" />
</application>
```

**3. 使用 R8/ProGuard 优化**

```gradle
// android/app/build.gradle
android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

## Android 特定优化

### GPU 渲染优化

```dart
// ✅ 使用 RepaintBoundary 限制重绘范围
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

### Android 线程优化

```dart
// ✅ 使用 Isolate 避免阻塞主线程
Future<int> computeInIsolate() async {
  return await compute(_heavyComputation, 1000000);
}
```

### Android 动画优化

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
      vsync: this,
    );
  }
}
```

## 网络优化（Network）

### Android 特定的网络优化

**1. 批量请求**

```dart
// ❌ 多个单独请求
for (final id in ids) {
  final user = await api.getUser(id);
}

// ✅ 批量请求
final users = await api.getUsers(ids: ids);
```

**2. 缓存策略**

```dart
// ✅ 使用 http_cache
final client = CacheManager(
  options: CacheOptions(
    store: FileStore('.cache'),
    policy: CachePolicy.cacheFirst,
  ),
).httpClient;
```

## Android 性能测试与监控

### 性能基准测试

```dart
// 创建 integration_test/perf_test.dart
void main() {
  group('Android Performance Tests', () {
    testWidgets('List scrolling performance', (tester) async {
      await tester.binding.window.physicalSizeTestValue =
          const Size(1080, 2400);  // 典型 Android 尺寸
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);

      await tester.pumpWidget(const MyApp());

      final stopwatch = Stopwatch()..start();

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
final trace = FirebasePerformance.instance.newTrace('android_list_scroll');
await trace.start();

trace.setAttribute('device_model', 'Pixel 7');
trace.setAttribute('android_version', '13.0');

await trace.stop();
```

## Android 性能检查清单

### 发布前检查

- [ ] 在真实 Android 设备上测试（不同厂商）
- [ ] 测试不同 RAM 容量设备（2GB、4GB、8GB）
- [ ] 测试不同 Android 版本（8、10、12、13、14）
- [ ] 使用 Android Profiler 分析内存
- [ ] 帧率检查：60 FPS 稳定
- [ ] 内存分析：冷启动 <100MB
- [ ] 启动时间：使用 `--trace-startup` 分析
- [ ] APK 大小：使用 `--analyze-size` 检查
- [ ] 电池消耗：使用 Android Profiler Energy Profiler
- [ ] 网络性能：测试弱网环境

### 运行时监控

```dart
void setupAndroidPerformanceMonitoring() {
  SchedulerBinding.instance.addPersistentFrameCallback((duration) {
    final fps = 1.0 / duration.inMicroseconds * 1000000;
    if (fps < 50) {
      debugPrint('Android Warning: Low FPS: $fps');
    }
  });
}
```

## Android 特定问题

### 低端设备优化

```dart
// 检测设备性能
final isLowEndDevice = Platform.isAndroid &&
    MediaQuery.of(context).devicePixelRatio < 2.0;

if (isLowEndDevice) {
  // 降低动画复杂度
  // 减少阴影和模糊效果
  // 使用更简单的布局
}
```

### 不同厂商 ROM 兼容性

```dart
// MIUI、EMUI、ColorOS 等可能有不同的行为
// 建议在主流厂商设备上测试
// - Xiaomi (MIUI)
// - Samsung (One UI)
// - OnePlus (OxygenOS)
// - OPPO/vivo (ColorOS/FuntouchOS)
```

### Android 权限处理

```dart
// Android 13+ 细粒度权限
final storageStatus = await Permission.photos.request();
final notificationStatus = await Permission.notification.request();
```

## 参考资源

- [Android Performance Tips](https://developer.android.com/topic/performance)
- [Flutter Performance Best Practices](https://flutter.dev/docs/perf)
- [Android Profiler Guide](https://developer.android.com/studio/profile)
- [Material Design Performance](https://material.io/design/performance)
