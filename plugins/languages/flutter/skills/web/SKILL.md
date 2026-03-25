---
description: Flutter Web 开发规范：WASM 编译、CanvasKit/HTML 渲染、响应式设计、PWA、SEO 优化。开发 Web 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter Web 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | Flutter 开发专家 |
| perf  | Flutter 性能优化专家 |

## 相关 Skills

| 场景     | Skill                 | 说明                  |
| -------- | --------------------- | --------------------- |
| 核心规范 | Skills(flutter:core)  | Dart 3 特性、项目结构 |
| UI 开发  | Skills(flutter:ui)    | Widget 组合、响应式   |
| 状态管理 | Skills(flutter:state) | Riverpod/Bloc 集成    |

## 渲染引擎选择

| 引擎 | 场景 | 优势 | 劣势 |
| ---- | ---- | ---- | ---- |
| **WASM (dart2wasm)** | 高性能应用（推荐） | 最快执行速度、小包体积 | 需要现代浏览器 |
| **CanvasKit** | 图形密集型应用 | 像素级一致、复杂动画 | 初始加载大（~2MB） |
| **HTML renderer** | SEO 优先、简单应用 | 小包体积、原生 DOM | 跨浏览器不一致 |

```bash
# WASM 编译（Flutter 3.22+，推荐）
flutter build web --wasm

# CanvasKit 渲染
flutter build web --web-renderer canvaskit

# HTML 渲染
flutter build web --web-renderer html

# 自动选择（移动端 HTML、桌面端 CanvasKit）
flutter build web --web-renderer auto
```

## 性能目标

- **FCP (First Contentful Paint)**: < 2s
- **LCP (Largest Contentful Paint)**: < 2.5s
- **TTI (Time to Interactive)**: < 3s
- **Bundle size**: < 2MB（WASM）/ < 3MB（CanvasKit）

## 响应式 Web 布局

```dart
// 三栏布局自适应
class WebResponsiveLayout extends StatelessWidget {
  const WebResponsiveLayout({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => switch (constraints.maxWidth) {
        < 600 => MobileScaffold(child: child),
        < 1200 => TabletScaffold(child: child),
        _ => DesktopScaffold(child: child),
      },
    );
  }
}

// 使用 MediaQuery.sizeOf（减少不必要重建）
final width = MediaQuery.sizeOf(context).width;

// 最大宽度约束（避免超宽显示）
Center(
  child: ConstrainedBox(
    constraints: const BoxConstraints(maxWidth: 1200),
    child: content,
  ),
)
```

## WASM 编译优化

```dart
// 1. 条件导入处理平台差异
import 'stub.dart'
    if (dart.library.html) 'web.dart'
    if (dart.library.io) 'native.dart';

// 2. 延迟加载路由（减少初始包）
final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (_, __) => const HomePage(),
    ),
    GoRoute(
      path: '/settings',
      builder: (_, __) => const SettingsPage(), // 延迟加载
    ),
  ],
);

// 3. 图片优化
Image.network(
  url,
  cacheWidth: 800,   // Web 端降采样
  cacheHeight: 600,
  loadingBuilder: (context, child, progress) {
    if (progress == null) return child;
    return const Center(child: CircularProgressIndicator());
  },
)
```

## PWA 支持

```yaml
# web/manifest.json
{
  "name": "My Flutter App",
  "short_name": "MyApp",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2196F3",
  "icons": [
    {
      "src": "icons/Icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icons/Icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

```dart
// Service Worker 注册（web/index.html 中自动处理）
// flutter_service_worker.js 自动生成

// 离线支持
// 使用 Hive / shared_preferences 缓存关键数据
// 网络请求失败时展示缓存数据
```

## SEO 优化

```dart
// 1. 使用 HTML renderer 提升可访问性
// flutter build web --web-renderer html

// 2. 语义化 Widget
Semantics(
  label: 'User profile card',
  child: const UserCard(),
)

// 3. 页面标题和描述
// 在 web/index.html 中配置 meta tags
// <meta name="description" content="...">

// 4. URL 结构（go_router 配置）
GoRoute(
  path: '/products/:id',
  builder: (context, state) => ProductPage(
    id: state.pathParameters['id']!,
  ),
)
```

## 浏览器兼容与平台检测

```dart
import 'package:flutter/foundation.dart';

// 平台检测
if (kIsWeb) {
  // Web 特定逻辑
}

// 条件渲染
Widget build(BuildContext context) {
  if (kIsWeb) {
    return const WebSpecificWidget();
  }
  return const MobileWidget();
}

// Web 特定功能：URL 策略
// 在 main.dart 中配置
import 'package:flutter_web_plugins/url_strategy.dart';
void main() {
  usePathUrlStrategy(); // 使用 path URL（非 hash）
  runApp(const MyApp());
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "CanvasKit 默认就好" | 是否评估了 WASM 编译的优势？ | 中 |
| "FCP 不重要" | FCP 是否 < 2s？ | 高 |
| "不需要响应式" | 是否适配了手机/平板/桌面三种宽度？ | 高 |
| "PWA 不需要" | 是否配置了 manifest.json 和 Service Worker？ | 中 |
| "SEO 不重要" | 是否添加了 Semantics 和 meta tags？ | 中 |
| "hash URL 也行" | 是否使用 usePathUrlStrategy()？ | 中 |
| "图片直接加载" | 是否使用 cacheWidth/cacheHeight 降采样？ | 中 |
| "全部一次加载" | 是否实现了路由级别的延迟加载？ | 中 |
| "不需要最大宽度" | 是否用 ConstrainedBox 限制最大宽度？ | 低 |

## 检查清单

- [ ] 渲染引擎选择（WASM > CanvasKit > HTML）
- [ ] FCP < 2s、LCP < 2.5s、TTI < 3s
- [ ] 响应式布局（手机/平板/桌面三种断点）
- [ ] MediaQuery.sizeOf 替代 MediaQuery.of
- [ ] ConstrainedBox 限制最大宽度
- [ ] 图片降采样（cacheWidth/cacheHeight）
- [ ] PWA 配置（manifest.json、Service Worker）
- [ ] usePathUrlStrategy() 路径 URL
- [ ] Semantics 语义化标签
- [ ] 离线数据缓存策略
