---
name: flutter-ui
description: Flutter UI 开发规范 — Material 3 Expressive、Cupertino 自适应、响应式布局 (LayoutBuilder + MediaQuery.sizeOf)、Impeller 渲染优化、隐式/显式/Hero 动画、Widget 组合。当用户开发页面/组件/布局/主题、提到 "Widget"、"Material"、"Cupertino"、"动画"、"响应式"、"主题" 时加载。
---

# Flutter UI 开发规范

## Widget 设计

### 小而 const

```dart
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const ProfileAppBar(),
      body: const Column(children: [
        ProfileHeader(),
        ProfileStats(),
        ProfileActions(),
      ]),
    );
  }
}
```

原则: 单一职责、 `const` 最大化、拆分 ≤ 200 行子组件、可复用提取到 `shared/widgets/`。

### 平台自适应

```dart
class AdaptiveButton extends StatelessWidget {
  const AdaptiveButton({super.key, required this.onPressed, required this.child});
  final VoidCallback onPressed;
  final Widget child;

  @override
  Widget build(BuildContext context) => switch (Theme.of(context).platform) {
    TargetPlatform.iOS || TargetPlatform.macOS =>
      CupertinoButton(onPressed: onPressed, child: child),
    _ => ElevatedButton(onPressed: onPressed, child: child),
  };
}
```

## Material 3 主题

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
  ),
  darkTheme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.dark,
    ),
  ),
);

// 颜色/字体从 Theme 取 (禁硬编码)
Container(
  color: Theme.of(context).colorScheme.primaryContainer,
  child: Text('Hi', style: Theme.of(context).textTheme.headlineMedium),
);
```

## 长列表虚拟化

```dart
// 简单
ListView.builder(
  itemCount: users.length,
  itemBuilder: (_, i) => RepaintBoundary(child: UserTile(user: users[i])),
);

// 复杂滚动 — CustomScrollView + Sliver
CustomScrollView(slivers: [
  const SliverAppBar.large(title: Text('Users')),
  SliverList.builder(
    itemCount: users.length,
    itemBuilder: (_, i) => UserTile(user: users[i]),
  ),
]);
```

## 响应式布局

```dart
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (_, c) => switch (c.maxWidth) {
      < 600 => MobileLayout(child: child),
      < 1200 => TabletLayout(child: child),
      _ => DesktopLayout(child: child),
    },
  );
}

// 推荐: 触发更少重建
MediaQuery.sizeOf(context).width;
MediaQuery.paddingOf(context);
// 避免: MediaQuery.of(context).size
```

## 资源管理

```dart
class _MyWidgetState extends State<MyWidget> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final StreamSubscription _sub;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 300));
    _sub = stream.listen(_onData);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _sub.cancel();
    super.dispose();
  }
}
```

## 动画

```dart
// 隐式
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  width: isExpanded ? 200 : 100,
  child: content,
);

// 显式
SlideTransition(
  position: Tween<Offset>(begin: const Offset(-1, 0), end: Offset.zero)
      .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut)),
  child: content,
);

// 共享元素
Hero(
  tag: 'user-${user.id}',
  child: CircleAvatar(backgroundImage: NetworkImage(user.avatar)),
);
```

## Impeller 渲染要点

- `Opacity` widget 触发 `saveLayer` → 用 `color.withValues(alpha: ...)` (Dart 3 替代 `withOpacity`)
- 复杂子树包 `RepaintBoundary` 隔离重绘
- 大图用 `cacheWidth`/`cacheHeight` 降采样
- 详见 `Skills(flutter:android)` / `Skills(flutter:ios)` 的 Impeller 章节

## Red Flags

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "Material 在 iOS 也行" | iOS 是否用 Cupertino？ | 高 |
| "直接写颜色值" | 是否从 `Theme.colorScheme` 取？ | 高 |
| "ListView 就够" | 大列表是否用 `.builder`？ | 高 |
| "const 不重要" | 可 const 的 Widget 是否全标记？ | 高 |
| "MediaQuery.of 就行" | 是否用 `sizeOf`/`paddingOf` 降重建？ | 中 |
| "不需要 RepaintBoundary" | 复杂子树是否隔离？ | 中 |
| "setState 更新 UI" | 是否该用 Riverpod/Bloc？ | 高 |

## 检查清单

- [ ] Material 3 + `ColorScheme.fromSeed()`
- [ ] iOS 用 Cupertino 控件
- [ ] Widget 拆分小 + `const`
- [ ] 长列表 `ListView.builder` / `SliverList.builder`
- [ ] 颜色/字体从 `Theme` 取
- [ ] `LayoutBuilder` + `MediaQuery.sizeOf` 响应式
- [ ] `dispose` 完整释放
- [ ] `RepaintBoundary` 隔离复杂子树
- [ ] 主组件 golden test

## 关联

- `Skills(flutter:core)` / `Skills(flutter:state)`
- `Skills(flutter:android)` / `Skills(flutter:ios)` / `Skills(flutter:web)`
