---
name: ui
description: Flutter UI 开发规范：Widget 组合、构建优化、性能最佳实践。开发 UI 时必须加载。
---

# Flutter UI 开发规范

## 相关 Skills

| 场景     | Skill         | 说明                     |
| -------- | ------------- | ------------------------ |
| 核心规范 | Skills(core)  | Flutter 核心规范         |
| 状态管理 | Skills(state) | Provider、Riverpod、BLoC |

## Widget 设计原则

### 单一职责

```dart
// ✅ 好：分解为多个小 Widget
class ProfilePage extends StatelessWidget {
  const ProfilePage();

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

### const Widget

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

### 虚拟化长列表

```dart
// ✅ 好：使用 ListView.builder
ListView.builder(
  itemCount: users.length,
  itemBuilder: (context, index) => UserTile(user: users[index]),
)
```

## 资源管理

```dart
class _MyWidgetState extends State<MyWidget> with SingleTickerProviderStateMixin {
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

## 响应式设计

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const MobileLayout();
    } else {
      return const TabletLayout();
    }
  },
)
```

## 检查清单

- [ ] Widget 拆分为小的、可复用的组件
- [ ] 使用 const Widget
- [ ] 长列表使用 ListView.builder
- [ ] 所有资源及时释放
- [ ] 使用主题样式和颜色
