---
name: web-performance
description: Flutter Web 性能优化指南 - 针对 Web 平台的特定优化策略
---

# Flutter Web 性能优化指南

## 核心原则

**Web 性能三角**：加载速度 > 渲染性能 > 带宽消耗

Flutter Web 的性能优化与移动平台有很大差异，需要考虑浏览器兼容性、网络延迟和 JavaScript 互操作。

## 加载速度优化

### 性能目标（Web 特定）

- **首次内容绘制 (FCP)**: <2 秒
- **最大内容绘制 (LCP)**: <2.5 秒
- **首次输入延迟 (FID)**: <100ms
- **累积布局偏移 (CLS)**: <0.1
- **首次包大小**: <2MB（压缩后）

### 诊断工具

```bash
# Chrome DevTools
# Lighthouse 分析

# Flutter Web 构建分析
flutter build web --web-renderer canvaskit
flutter build web --web-renderer html

# 分析包大小
flutter build web --analyze-size
```

### Web 特定的加载优化

**1. 选择合适的渲染器**

```dart
// HTML 渲染器（更快，但功能受限）
flutter build web --web-renderer html

// CanvasKit 渲染器（功能完整，但首次加载较慢）
flutter build web --web-renderer canvaskit

// 自动选择（推荐）
flutter build web
```

**2. 代码分割**

```dart
// 使用 deferred loading 延迟加载不常用的功能
import 'package:flutter/material.dart' deferred as ui;

Future<void> loadDeferredLibraries() async {
  await ui.loadLibrary();
  // 现在可以使用 ui 包中的组件
}
```

**3. 优化资源加载**

```html
<!-- web/index.html -->
<link rel="preload" href="assets/logo.png" as="image">
<link rel="prefetch" href="assets/next_page.png">
```

## 渲染性能优化

### Web 特定的渲染优化

**1. 减少重绘和回流**

```dart
// ✅ 好：使用 Transform 而非改变布局
Transform.translate(
  offset: Offset(x, y),
  child: const Widget(),
)

// ❌ 不好：改变 position 导致回流
Positioned(
  left: x,
  top: y,
  child: const Widget(),
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

**3. 优化图片加载**

```dart
// ✅ 使用 WebP 格式
Image.asset('assets/image.webp')

// ✅ 指定尺寸
Image.asset(
  'assets/image.png',
  width: 300,
  height: 300,
)

// ✅ 懒加载
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ImageItem(items[index]),
)
```

## 网络优化

### Web 特定的网络优化

**1. 使用 CDN**

```html
<!-- web/index.html -->
<script src="https://cdn.example.com/flutter.js"></script>
```

**2. 启用压缩**

```yaml
# pubspec.yaml
flutter:
  assets:
    - assets/
    - assets/images/
```

```nginx
# nginx.conf
gzip on;
gzip_types text/plain application/json application/javascript text/css;
```

**3. 使用 Service Worker 缓存**

```dart
// 使用 flutter_service_worker 包
import 'package:flutter_service_worker/flutter_service_worker.dart';

void main() {
  runApp(const MyApp());
  registerServiceWorker();
}
```

## 内存优化

### Web 特定的内存优化

**1. 及时释放资源**

```dart
// ✅ 必须释放资源
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = stream.listen((_) {});
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
```

**2. 避免内存泄漏**

```dart
// ❌ 不好：未取消订阅
final subscription = stream.listen((_) {});

// ✅ 好：使用 Provider/Riverpod 自动管理
final streamProvider = StreamProvider<int>((ref) {
  ref.onDispose(() {
    // 自动清理
  });
  return stream;
});
```

## Web 特定功能

### JavaScript 互操作

```dart
import 'dart:js_interop';

@JS()
external void alert(String message);

void showWebAlert() {
  alert('Hello from Flutter!');
}
```

### URL 路由

```dart
// 使用 go_router 或 auto_route
MaterialApp.router(
  routerConfig: router,
)
```

### 响应式设计

```dart
// Web 响应式布局
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth > 1200) {
      return const DesktopLayout();
    } else if (constraints.maxWidth > 600) {
      return const TabletLayout();
    } else {
      return const MobileLayout();
    }
  },
)
```

## PWA 支持

### 渐进式 Web 应用

```json
{
  "name": "My Flutter App",
  "short_name": "MyApp",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2196F3",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## SEO 优化

### 搜索引擎优化

```dart
// 使用 flutter SEO 包
import 'package:flutter_seo/flutter_seo.dart';

SEO.post(
  title: 'Page Title',
  description: 'Page Description',
  keywords: ['keyword1', 'keyword2'],
  image: 'https://example.com/image.png',
)
```

## Web 性能测试

### Lighthouse 分析

```bash
# 运行 Lighthouse
chrome --headless --disable-gpu --no-sandbox \
  --remote-debugging-port=9222 \
  https://example.com &

lighthouse https://example.com --output html --output-path report.html
```

### Core Web Vitals

```dart
// 使用 web-vitals 包测量
import 'package:web_vitals/web_vitals.dart';

void measureVitals() {
  getFCP((metric) => print('FCP: ${metric.value}'));
  getLCP((metric) => print('LCP: ${metric.value}'));
  getFID((metric) => print('FID: ${metric.value}'));
  getCLS((metric) => print('CLS: ${metric.value}'));
}
```

## Web 性能检查清单

### 发布前检查

- [ ] 使用 Lighthouse 分析性能（目标 >90 分）
- [ ] 测试不同浏览器（Chrome、Firefox、Safari、Edge）
- [ ] 测试不同网络条件（3G、4G、WiFi）
- [ ] 检查 Core Web Vitals（FCP、LCP、FID、CLS）
- [ ] 验证 PWA 功能（离线支持、安装提示）
- [ ] 检查 SEO（meta 标签、sitemap）
- [ ] 分析包大小（<2MB）
- [ ] 测试响应式设计（手机、平板、桌面）
- [ ] 验证 Service Worker 缓存
- [ ] 检查控制台错误和警告

### 运行时监控

```dart
void setupWebPerformanceMonitoring() {
  // 监控页面加载时间
  final timing = window.performance.timing;
  final pageLoadTime = timing.loadEventEnd - timing.navigationStart;
  print('Page load time: $pageLoadTime ms');

  // 监控 FPS
  int frameCount = 0;
  Timer.periodic(const Duration(seconds: 1), (timer) {
    print('FPS: $frameCount');
    frameCount = 0;
  });

  // 监控内存使用（如果浏览器支持）
  if (window.performance.hasMemory) {
    final memory = window.performance.memory;
    print('Memory: ${memory.usedJSHeapSize} bytes');
  }
}
```

## Web 特定问题

### 浏览器兼容性

```dart
// 检测浏览器
final isChrome = browserAgent.contains('Chrome');
final isFirefox = browserAgent.contains('Firefox');
final isSafari = browserAgent.contains('Safari');

// 根据浏览器调整功能
if (isSafari) {
  // Safari 特定调整
}
```

### CORS 问题

```dart
// 处理跨域请求
final response = await http.get(
  Uri.parse('https://api.example.com/data'),
  headers: {'Access-Control-Allow-Origin': '*'},
);
```

## 参考资源

- [Flutter Web Performance](https://flutter.dev/web)
- [Web.dev Performance Guide](https://web.dev/performance/)
- [Core Web Vitals](https://web.dev/vitals/)
- [PWA Best Practices](https://web.dev/pwa/)
