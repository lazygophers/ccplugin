---
description: "Flutter UI 界面开发规范。涵盖 Material 3 组件、Cupertino 自适应设计、响应式布局策略、Impeller 渲染优化与动画实现。适用于开发页面、组件、布局、主题样式时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter UI 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | Flutter 开发专家 |
| test  | Flutter 测试专家 |
| perf  | Flutter 性能优化专家 |

## 相关 Skills

| 场景     | Skill                   | 说明                    |
| -------- | ----------------------- | ----------------------- |
| 核心规范 | Skills(flutter:core)    | Dart 3 特性、项目结构   |
| 状态管理 | Skills(flutter:state)   | Riverpod/Bloc 集成 UI   |
| Android  | Skills(flutter:android) | Material 3 Expressive   |
| iOS      | Skills(flutter:ios)     | Cupertino 设计          |
| Web      | Skills(flutter:web)     | 响应式 Web 布局         |

## Widget 设计原则

### 单一职责 + const 优先

```dart
// 好：小的、const 构造的 Widget
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const ProfileAppBar(),
      body: const Column(
        children: [
          ProfileHeader(),
          ProfileStats(),
          ProfileActions(),
        ],
      ),
    );
  }
}
```

### 自适应 Widget（Material 3 + Cupertino）

```dart
// 根据平台自动选择组件
class AdaptiveButton extends StatelessWidget {
  const AdaptiveButton({
    super.key,
    required this.onPressed,
    required this.child,
  });
  final VoidCallback onPressed;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return switch (Theme.of(context).platform) {
      TargetPlatform.iOS || TargetPlatform.macOS =>
        CupertinoButton(onPressed: onPressed, child: child),
      _ => ElevatedButton(onPressed: onPressed, child: child),
    };
  }
}
```

### Material 3 主题配置

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      // Material 3 动态颜色
    ),
    // 使用 TextTheme 而非硬编码
    textTheme: const TextTheme(
      headlineLarge: TextStyle(fontWeight: FontWeight.bold),
    ),
  ),
  darkTheme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.dark,
    ),
  ),
)

// 使用 Theme 颜色（非硬编码）
Container(
  color: Theme.of(context).colorScheme.primaryContainer,
  child: Text(
    'Hello',
    style: Theme.of(context).textTheme.headlineMedium,
  ),
)
```

### 虚拟化长列表

```dart
// 好：ListView.builder 按需创建
ListView.builder(
  itemCount: users.length,
  itemBuilder: (context, index) => RepaintBoundary(
    child: UserTile(user: users[index]),
  ),
)

// 复杂滚动：CustomScrollView + Sliver
CustomScrollView(
  slivers: [
    const SliverAppBar.large(title: Text('Users')),
    SliverList.builder(
      itemCount: users.length,
      itemBuilder: (context, index) => UserTile(user: users[index]),
    ),
  ],
)
```

## 响应式布局

```dart
// LayoutBuilder 断点布局
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => switch (constraints.maxWidth) {
        < 600 => MobileLayout(child: child),
        < 1200 => TabletLayout(child: child),
        _ => DesktopLayout(child: child),
      },
    );
  }
}

// MediaQuery 获取设备信息
final screenWidth = MediaQuery.sizeOf(context).width; // 推荐
final padding = MediaQuery.paddingOf(context);         // 推荐
// 避免 MediaQuery.of(context).size（触发不必要重建）
```

## 资源管理

```dart
class _AnimatedWidgetState extends State<AnimatedWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final StreamSubscription<int> _subscription;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _subscription = stream.listen(_onData);
  }

  @override
  void dispose() {
    _controller.dispose();
    _subscription.cancel();
    super.dispose();
  }
}
```

## 动画最佳实践

```dart
// 隐式动画（简单场景）
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  width: isExpanded ? 200 : 100,
  child: content,
)

// 显式动画（复杂场景）
SlideTransition(
  position: Tween<Offset>(
    begin: const Offset(-1, 0),
    end: Offset.zero,
  ).animate(CurvedAnimation(
    parent: _controller,
    curve: Curves.easeOut,
  )),
  child: content,
)

// Hero 动画（页面间共享元素）
Hero(
  tag: 'user-avatar-${user.id}',
  child: CircleAvatar(backgroundImage: NetworkImage(user.avatarUrl)),
)
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "Material 就行了" | iOS 是否使用 Cupertino 控件？ | 高 |
| "直接写颜色值" | 是否从 Theme/ColorScheme 获取？ | 高 |
| "ListView 就够了" | 大列表是否使用 ListView.builder？ | 高 |
| "const 不重要" | 可 const 的 Widget 是否全部标记？ | 高 |
| "MediaQuery.of 就行" | 是否使用 MediaQuery.sizeOf 减少重建？ | 中 |
| "不需要 RepaintBoundary" | 复杂子树是否隔离了重绘区域？ | 中 |
| "setState 更新 UI" | 是否应该使用 Riverpod/Bloc？ | 高 |
| "SliverAppBar 太复杂" | 复杂滚动是否使用 CustomScrollView？ | 中 |

## 检查清单

- [ ] Material 3 主题 + ColorScheme.fromSeed()
- [ ] Cupertino 控件用于 iOS 平台
- [ ] Widget 拆分为小的、const 构造的组件
- [ ] 长列表使用 ListView.builder / SliverList.builder
- [ ] 颜色/字体从 Theme 获取（非硬编码）
- [ ] 响应式布局（LayoutBuilder + MediaQuery.sizeOf）
- [ ] 所有资源在 dispose 中释放
- [ ] RepaintBoundary 隔离复杂子树
- [ ] 动画使用适当方式（隐式/显式/Hero）
- [ ] Widget golden test 覆盖主要组件
