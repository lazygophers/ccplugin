---
name: flutter-web
description: Flutter Web 规范 — WASM (dart2wasm) 编译、CanvasKit/HTML 渲染选型、响应式 Web 布局、PWA (manifest + service worker)、SEO/Semantics、usePathUrlStrategy。当用户开发 Flutter Web、提到 "Web"、"WASM"、"CanvasKit"、"PWA"、"SEO"、"浏览器" 时加载。
---

# Flutter Web 开发规范

## 渲染引擎选型

| 引擎 | 推荐场景 | 优势 | 劣势 |
| --- | --- | --- | --- |
| **WASM (`dart2wasm`)** | 高性能应用 (Flutter 3.22+ stable) | 最快执行 / 小包体 | 需现代浏览器 (Chromium/Firefox/Safari 16.4+) |
| **CanvasKit** | 图形密集 / 像素一致 | 跨浏览器一致、复杂动画稳 | 初次加载 ~2MB |
| HTML renderer | (旧) SEO 优先 / 弱设备 | 小包体、原生 DOM | Flutter 3.27 起标记弃用 |

```bash
# WASM (推荐)
flutter build web --wasm

# CanvasKit (兜底)
flutter build web --web-renderer canvaskit
```

## 性能目标

- FCP < 2s / LCP < 2.5s / TTI < 3s
- Bundle: WASM < 2MB / CanvasKit < 3MB

## 响应式 Web 布局

```dart
LayoutBuilder(
  builder: (_, c) => switch (c.maxWidth) {
    < 600 => MobileScaffold(child: child),
    < 1200 => TabletScaffold(child: child),
    _ => DesktopScaffold(child: child),
  },
);

// 最大宽度约束 (避免超宽屏拉伸)
Center(
  child: ConstrainedBox(
    constraints: const BoxConstraints(maxWidth: 1200),
    child: content,
  ),
);

// 用 sizeOf 减少重建
final w = MediaQuery.sizeOf(context).width;
```

## 路由策略

```dart
import 'package:flutter_web_plugins/url_strategy.dart';

void main() {
  usePathUrlStrategy(); // 路径式 URL (非 #hash)
  runApp(const MyApp());
}
```

## 延迟加载 / 拆包

```dart
// 推迟加载非首屏代码
import 'package:my_app/admin.dart' deferred as admin;

Future<void> openAdmin(BuildContext ctx) async {
  await admin.loadLibrary();
  Navigator.of(ctx).push(MaterialPageRoute(builder: (_) => admin.AdminPage()));
}
```

go_router 配置中按路由切分 deferred import 可显著减小首屏 Bundle。

## PWA

```json
// web/manifest.json
{
  "name": "My Flutter App",
  "short_name": "MyApp",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2196F3",
  "icons": [
    {"src": "icons/Icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icons/Icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

Service worker `flutter_service_worker.js` Flutter 默认生成；离线数据用 `shared_preferences` / `hive`。

## SEO / 可访问性

```dart
// 语义化
Semantics(label: 'User profile card', child: const UserCard());

// 页面元数据 — web/index.html 配 <meta name="description">
// 动态标题 (TitleNotifier 包 SystemChrome)
```

CanvasKit/WASM 文本对搜索引擎不可见；SEO 关键页面考虑 SSR/SSG (e.g. `jaspr`) 或独立 HTML landing。

## 图片优化

```dart
Image.network(
  url,
  cacheWidth: 800,
  cacheHeight: 600,
  loadingBuilder: (ctx, child, p) => p == null ? child : const CircularProgressIndicator(),
);
```

## 平台检测

```dart
import 'package:flutter/foundation.dart';

if (kIsWeb) {
  // Web 特定
}

// 条件导入处理 dart:html / dart:io
import 'stub.dart'
  if (dart.library.js_interop) 'web.dart'
  if (dart.library.io) 'native.dart';
```

## Red Flags

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "CanvasKit 就行" | 是否考虑 WASM？ | 中 |
| "FCP 不重要" | FCP < 2s? | 高 |
| "不需要响应式" | 手机/平板/桌面三断点是否覆盖？ | 高 |
| "hash URL 也行" | 是否 `usePathUrlStrategy()`？ | 中 |
| "图片直接加载" | `cacheWidth`/`cacheHeight` 降采样？ | 中 |
| "一次加载全部" | 是否 deferred import 拆包？ | 中 |
| "SEO 不重要" | Semantics + meta 是否补全？ | 中 |

## 检查清单

- [ ] WASM 编译验证 (`flutter build web --wasm`)
- [ ] FCP < 2s / LCP < 2.5s / TTI < 3s
- [ ] 三断点响应式 (mobile/tablet/desktop)
- [ ] `MediaQuery.sizeOf` 降重建
- [ ] `ConstrainedBox` 限最大宽度
- [ ] 图片降采样
- [ ] PWA manifest + service worker
- [ ] `usePathUrlStrategy()`
- [ ] `Semantics` 语义化
- [ ] 路由级 deferred import

## 关联

- `Skills(flutter:core)` / `Skills(flutter:ui)` / `Skills(flutter:state)`
