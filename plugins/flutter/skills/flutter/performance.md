# Flutter 性能优化指南

## 核心原则

**性能三角**：帧率稳定性 > 启动速度 > 内存占用

性能优化需要测量、分析、优化、验证的循环。避免盲目优化。

---

## 1. 帧率优化（Frame Rate）

### 性能目标
- **移动设备**: 60 FPS (目标)，最小 50 FPS (可接受)
- **高刷屏**: 120 FPS (可选，需考虑电池消耗)
- **卡帧界定**: 帧时间 >16.67ms (60FPS) 或 >8.33ms (120FPS) 为卡帧

### 诊断工具
```bash
# Dart DevTools Frame Inspector
flutter run --profile
# 打开 DevTools → Performance tab → Frame Analysis

# Dart VM Timeline
flutter run --profile --trace-startup
```

### 常见优化模式

**1. 避免不必要的重建**
```dart
// ❌ 错误: Widget 每次都重建
class ParentWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      ExpensiveWidget(),  // 即使 ParentWidget 内容未变也会重建
      const SimpleSibling(),
    ]);
  }
}

// ✅ 正确: 提取子 Widget，使用 const
class ParentWidget extends StatelessWidget {
  const ParentWidget();
  
  @override
  Widget build(BuildContext context) {
    return const Column(children: [
      ExpensiveWidget(),  // 如果使用 const，只在参数变化时重建
      SimpleSibling(),
    ]);
  }
}
```

**2. 使用 shouldRebuild 控制通知**
```dart
class CounterNotifier extends ChangeNotifier {
  int _counter = 0;
  int get counter => _counter;
  
  void increment() {
    _counter++;
    notifyListeners();  // 每次都通知，可能导致不必要的重建
  }
}

// 改进: 使用 Selector（Provider）或 select（Riverpod）
Consumer(
  builder: (context, ref, _) {
    // 只有 counter 值变化时才重建
    final counter = ref.watch(
      counterProvider.select((notifier) => notifier.counter)
    );
    return Text('$counter');
  },
)
```

**3. ListBuilder 优化**
```dart
// ✅ 正确: 使用 ListView.builder 而非 ListView
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ItemWidget(item: items[index]);
  },
)

// 对于频繁插入/删除: 使用 AnimatedList
AnimatedList(
  initialItemCount: items.length,
  itemBuilder: (context, index, animation) {
    return SlideTransition(
      position: animation.drive(
        Tween(begin: const Offset(1, 0), end: Offset.zero)
      ),
      child: ItemWidget(item: items[index]),
    );
  },
)
```

**4. 图片加载优化**
```dart
// ❌ 低效: 全分辨率图片
Image.asset('assets/image.png')

// ✅ 优化: 使用合适尺寸、预加载、缓存
Image.asset(
  'assets/image.png',
  cacheHeight: 300,
  cacheWidth: 300,
  fit: BoxFit.cover,
)

// 预加载
precacheImage(AssetImage('assets/image.png'), context);

// 使用 cached_network_image
CachedNetworkImage(
  imageUrl: 'https://example.com/image.jpg',
  placeholder: (context, url) => const Spinner(),
  cacheManager: CacheManager.instance,
)
```

**5. 动画性能**
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

---

## 2. 内存优化（Memory）

### 性能目标
- **冷启动**: <100MB (包括系统)
- **运行时**: 150-300MB (根据设备)
- **最大**: <500MB (避免 OOM)

### 诊断工具
```bash
# Memory Profiler
flutter run --profile
# DevTools → Memory tab → Chart/Allocation/Classes

# 内存泄漏检测
# 检查 DevTools Memory 中的 Retained Size
```

### 内存优化模式

**1. 避免内存泄漏**
```dart
// ❌ 泄漏: 未取消订阅
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late StreamSubscription subscription;
  
  @override
  void initState() {
    subscription = stream.listen((value) {
      setState(() {});  // Widget dispose 后仍在监听
    });
  }
  
  @override
  void dispose() {
    // ❌ 忘记取消订阅
    super.dispose();
  }
}

// ✅ 正确: 取消订阅
@override
void dispose() {
  subscription.cancel();
  super.dispose();
}

// ✅ 使用 Provider/Riverpod 自动管理
final streamProvider = StreamProvider<int>((ref) {
  return stream;  // 自动处理订阅/取消
});
```

**2. 管理大对象**
```dart
// ❌ 保留整个列表
List<HeavyObject> items = [];

@override
Widget build(BuildContext context) {
  return ListView(
    children: items.map((item) => ItemWidget(item)).toList(),  // 保存列表副本
  );
}

// ✅ 使用 builder 避免保存副本
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)

// ✅ 及时清理资源
Future<void> clearOldData() async {
  // 清理缓存
  imageCache.clear();
  imageCache.clearLiveImages();
  
  // 清理数据库
  await database.delete('old_records');
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

// ✅ 使用 WebP 等压缩格式
Image.asset('assets/image.webp')  // 更小的文件

// ✅ 使用 SVG（可扩放，内存少）
import 'package:flutter_svg/flutter_svg.dart';
SvgPicture.asset('assets/icon.svg')
```

**4. 长列表内存管理**
```dart
// ✅ 使用 PagedListView（lazy loading）
PagedListView(
  pagingController: _pagingController,
  builderDelegate: PagedChildBuilderDelegate<Item>(
    itemBuilder: (context, item, index) => ItemWidget(item),
  ),
)

// ✅ 定期释放不可见的缓存
ListView.builder(
  itemCount: items.length,
  cacheExtent: 500,  // 只缓存 500px 外的 widget
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

---

## 3. 启动优化（Startup）

### 性能目标
- **冷启动**: <2 秒 (用户期望)
- **温启动**: <500ms
- **热启动**: <100ms

### 优化策略

**1. 延迟初始化**
```dart
// ❌ 启动时初始化所有
void main() {
  await _initializeDatabase();
  await _initializeAnalytics();
  await _initializeAdvertising();  // 延迟初始化
  await _loadUserPreferences();
  runApp(const MyApp());
}

// ✅ 按需初始化
void main() {
  _initializeCritical();  // 仅初始化关键资源
  runApp(const MyApp());
}

Future<void> _initializeCritical() async {
  await _initializeDatabase();  // 必须
  // 延迟非关键初始化到应用启动后
}

@override
void initState() {
  super.initState();
  // 延迟初始化非关键资源
  Future.microtask(() {
    _initializeAnalytics();
    _initializeAdvertising();
  });
}
```

**2. 代码分割**
```bash
# 分析 APK 大小
flutter build apk --analyze-size

# 启用分割
flutter build appbundle  # 推荐，Google Play 自动分割
flutter build apk --split-per-abi  # 分离架构
```

**3. 减少启动工作量**
```dart
// ❌ 启动时同步读取大文件
void main() {
  final config = jsonDecode(
    File('assets/config.json').readAsStringSync()
  );
  runApp(MyApp(config: config));
}

// ✅ 异步加载，使用占位符
Future<void> main() async {
  // 快速启动应用
  runApp(const SplashScreen());
  
  // 后台加载配置
  final config = await _loadConfig();
  // 切换到主界面
}
```

**4. 移除未使用的依赖**
```bash
# 检查 pubspec.lock 中未使用的包
flutter pub deps --mode=all

# 使用 dependency_validator
flutter pub add dev:dependency_validator
flutter pub run dependency_validator
```

---

## 4. 网络优化（Network）

### 优化策略

**1. 批量请求**
```dart
// ❌ 多个单独请求
for (final id in ids) {
  final user = await api.getUser(id);  // N 次请求
  users.add(user);
}

// ✅ 批量请求
final users = await api.getUsers(ids: ids);  // 1 次请求
```

**2. 缓存策略**
```dart
// ✅ 使用 http_cache 等缓存库
final client = CacheManager(
  options: CacheOptions(
    store: FileStore('.cache'),
    policy: CachePolicy.cacheFirst,  // 优先使用缓存
  ),
).httpClient;

final response = await client.get(Uri.parse(url));
```

**3. 压缩**
```dart
// ✅ 启用 gzip 压缩
final response = await http.get(
  Uri.parse(url),
  headers: {'Accept-Encoding': 'gzip'},
);

// ✅ 后端返回 gzip 压缩数据
// 自动处理: http 包自动解压
```

**4. 超时控制**
```dart
// ✅ 设置合理超时
final response = await http.get(
  Uri.parse(url),
  headers: {'timeout': '5000'},  // 5 秒超时
).timeout(
  const Duration(seconds: 5),
  onTimeout: () => throw TimeoutException('Request timeout'),
);
```

---

## 5. 性能测试与监控

### 性能基准测试

**1. 集成测试性能**
```dart
// 创建 integration_test/perf_test.dart
void main() {
  group('Performance Tests', () {
    testWidgets('List scrolling performance', (tester) async {
      await tester.binding.window.physicalSizeTestValue =
          const Size(1080, 1920);
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

**2. 性能计数**
```dart
// 使用 vm_service 获取性能数据
import 'package:vm_service/vm_service.dart' as vm;

void collectMemoryStats() async {
  final vmService = await _getVMService();
  final memory = await vmService.getMemoryUsage('');
  
  print('Heap Size: ${memory.heapUsage}');
  print('External Memory: ${memory.externalMemoryUsage}');
}
```

### 持续监控

**1. Firebase Performance Monitoring**
```dart
final trace = FirebasePerformance.instance.newTrace('list_scroll');
await trace.start();

// 执行操作

await trace.stop();

trace.setAttribute('items_count', '1000');
```

**2. Sentry 性能监控**
```dart
import 'package:sentry_flutter/sentry_flutter.dart';

void main() {
  SentryFlutter.init(
    (options) {
      options.dsn = 'https://...@sentry.io/...';
      options.tracesSampleRate = 1.0;
    },
    appRunner: () => runApp(const MyApp()),
  );
}

// 自动捕获性能问题
```

---

## 6. 性能检查清单

### 发布前检查

- [ ] 使用 `flutter run --release` 测试（而非 debug/profile）
- [ ] Dart DevTools 帧率检查：60 FPS 稳定
- [ ] 内存分析：冷启动 <100MB，运行时 <300MB
- [ ] 网络：禁用弱网模拟
- [ ] 测试移动设备（不仅仅是模拟器）
- [ ] APK 大小：使用 `--analyze-size` 检查
- [ ] 启动时间：使用 `--trace-startup` 分析
- [ ] 长滚动列表：确保无卡顿
- [ ] 内存泄漏：DevTools Memory 检查
- [ ] 后台任务：确保释放资源

### 运行时监控

```dart
void setupPerformanceMonitoring() {
  // 监控帧率
  SchedulerBinding.instance.addPersistentFrameCallback((duration) {
    final fps = 1.0 / duration.inMilliseconds * 1000;
    if (fps < 50) {
      print('Warning: Low FPS: $fps');
    }
  });
}
```

---

## 参考资源

- [Flutter Performance Best Practices](https://flutter.dev/docs/perf)
- [DevTools Performance Guide](https://flutter.dev/docs/development/tools/devtools/performance)
- [Dart VM Observatories](https://dart.dev/tools/observatory)
