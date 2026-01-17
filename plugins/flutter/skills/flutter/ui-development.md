---
name: ui-development
description: Flutter UI 开发规范 - Widget 组合、构建优化、命名规范和最佳实践
---

# Flutter UI 开发规范

## Widget 设计原则

### 单一职责

每个 Widget 应该只做一件事，做好一件事。

```dart
// ❌ 不好：单个大 Widget，多个职责
class ProfilePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // 头像 + 名字 + 邮箱
            // 统计数据（粉丝、关注、文章）
            // 操作按钮（编辑、分享、设置）
            // 用户简介
            // ... 200 行代码
          ],
        ),
      ),
    );
  }
}

// ✅ 好：分解为多个小 Widget
class ProfilePage extends StatelessWidget {
  const ProfilePage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const ProfileAppBar(),
      body: const SingleChildScrollView(
        child: Column(
          children: [
            ProfileHeader(),
            ProfileStats(),
            ProfileDescription(),
            ProfileActions(),
          ],
        ),
      ),
    );
  }
}

class ProfileHeader extends StatelessWidget {
  const ProfileHeader();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          CircleAvatar(radius: 50),
          const SizedBox(height: 16),
          Text('John Doe', style: Theme.of(context).textTheme.headlineSmall),
          Text('john@example.com'),
        ],
      ),
    );
  }
}
```

### 可复用性

编写可复用的 Widget，避免重复代码。

```dart
// ❌ 不好：重复的代码
class FollowersPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              CircleAvatar(radius: 40),
              const SizedBox(height: 8),
              const Text('User 1'),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              CircleAvatar(radius: 40),
              const SizedBox(height: 8),
              const Text('User 2'),
            ],
          ),
        ),
        // ... 重复 N 次
      ],
    );
  }
}

// ✅ 好：提取为可复用 Widget
class UserTile extends StatelessWidget {
  const UserTile({required this.user});
  
  final User user;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          CircleAvatar(radius: 40),
          const SizedBox(height: 8),
          Text(user.name),
        ],
      ),
    );
  }
}

class FollowersPage extends StatelessWidget {
  const FollowersPage({required this.users});
  
  final List<User> users;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: users.length,
      itemBuilder: (context, index) => UserTile(user: users[index]),
    );
  }
}
```

## 构建优化

### const Widget

使用 `const` 修饰符标记不会改变的 Widget，启用 Widget 复用。

```dart
// ✅ 好：使用 const Widget
class MyWidget extends StatelessWidget {
  const MyWidget();  // const 构造函数

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 16),    // const Widget 被复用
        const Divider(),               // const Widget 被复用
        Text('Dynamic: ${DateTime.now()}'),  // 动态内容
      ],
    );
  }
}

// ❌ 不好：没有 const，每次 build 都重新创建
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(height: 16),       // 每次都重新创建
        Divider(),                  // 每次都重新创建
        Text('Dynamic: ${DateTime.now()}'),
      ],
    );
  }
}
```

### 虚拟化长列表

对于长列表，使用 `ListView.builder` 或 `GridView.builder` 而不是一次性创建所有 Widget。

```dart
// ❌ 不好：一次性创建所有 Widget（内存消耗大）
class UserList extends StatelessWidget {
  final List<User> users;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: users.map((user) => UserTile(user: user)).toList(),
    );
  }
}

// ✅ 好：虚拟化列表，仅构建可见项
class UserList extends StatelessWidget {
  final List<User> users;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: users.length,
      itemBuilder: (context, index) => UserTile(user: users[index]),
    );
  }
}

// ✅ 也可以：指定 addAutomaticKeepAlives 保持状态
ListView.builder(
  itemCount: users.length,
  itemBuilder: (context, index) => UserTile(user: users[index]),
  addAutomaticKeepAlives: true,  // 保持可见项的状态
)
```

### 避免不必要的重构

使用 `AnimatedSwitcher` 或条件构建，避免频繁改变整个 Widget 树。

```dart
// ❌ 不好：条件改变导致重构
class MyWidget extends StatelessWidget {
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return LoadingSpinner();  // 返回不同的 Widget，导致重构
    } else {
      return ContentWidget();
    }
  }
}

// ✅ 好：使用 AnimatedSwitcher 平滑过渡
class MyWidget extends StatelessWidget {
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: isLoading
          ? const LoadingSpinner()
          : const ContentWidget(),
    );
  }
}

// ✅ 也可以：条件只改变内容
class MyWidget extends StatelessWidget {
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: isLoading
          ? const LoadingSpinner()
          : const ContentWidget(),
    );
  }
}
```

## 命名规范

### 组件文件和类名

```dart
// 文件名使用 snake_case
lib/screens/profile_screen.dart
lib/widgets/user_card.dart
lib/services/user_service.dart

// 类名使用 PascalCase
class ProfileScreen extends StatelessWidget {}
class UserCard extends StatelessWidget {}
class UserService {}
```

### 变量命名

```dart
// 常规变量：lowerCamelCase
final userName = 'John';
final userList = <User>[];
int maxRetries = 3;

// 常量：lowerCamelCase + const
const defaultPadding = 16.0;
const maxListHeight = 400;

// 私有成员：以 _ 开头
final _privateVariable = 42;
void _privateMethod() {}
class _InternalWidget extends StatelessWidget {}

// 布尔值：is、has、can 前缀
bool isLoading = false;
bool hasError = false;
bool canSubmit = true;
```

## 项目结构

### 特性为主的结构（推荐）

```
lib/
├── main.dart                      # 应用入口
├── config/
│   ├── app_theme.dart            # 主题配置
│   └── app_router.dart           # 路由配置
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   └── repositories/
│   │   ├── domain/
│   │   │   └── entities/
│   │   └── presentation/
│   │       ├── screens/
│   │       ├── widgets/
│   │       └── providers/
│   ├── home/
│   │   └── ... (同样结构)
│   └── profile/
│       └── ... (同样结构)
├── shared/
│   ├── components/                # 全局可复用组件
│   ├── services/                  # 全局服务（API、数据库）
│   ├── utils/                     # 工具函数
│   ├── constants/                 # 常量定义
│   └── extensions/                # 扩展方法
└── test/
    ├── unit/
    ├── widget/
    └── integration/
```

### 导入规范

```dart
// ✅ 好：按分类导入
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/user.dart';
import '../services/api.dart';
import 'components/header.dart';

// ❌ 不好：导入杂乱无序
import 'package:riverpod/riverpod.dart';
import '../models/user.dart';
import 'dart:async';
import 'package:flutter/material.dart';
```

## 布局最佳实践

### 响应式设计

```dart
// ✅ 好：使用 MediaQuery 或 LayoutBuilder
final screenWidth = MediaQuery.of(context).size.width;
final isPortrait = MediaQuery.of(context).orientation == Orientation.portrait;

LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return const MobileLayout();
    } else {
      return const TabletLayout();
    }
  },
)

// ❌ 不好：硬编码屏幕尺寸检查
if (screenWidth < 600) { ... }
```

### 使用约束感知的 Widget

```dart
// ✅ 好：Widget 遵守父容器的约束
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox.expand(
      child: Container(
        color: Colors.blue,
      ),
    );
  }
}

// ❌ 不好：硬编码尺寸
Container(
  width: 100,
  height: 100,
  color: Colors.blue,
)
```

## 文本和排版

### 使用主题定义的样式

```dart
// ✅ 好：使用主题样式
Text(
  'Title',
  style: Theme.of(context).textTheme.headlineSmall,
)

Text(
  'Body text',
  style: Theme.of(context).textTheme.bodyMedium,
)

// ❌ 不好：硬编码样式
Text(
  'Title',
  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
)
```

### 文本颜色

```dart
// ✅ 好：使用主题颜色
Text(
  'Text',
  style: TextStyle(color: Theme.of(context).colorScheme.primary),
)

// ❌ 不好：硬编码颜色
Text(
  'Text',
  style: const TextStyle(color: Color(0xFF2196F3)),
)
```

## 动画最佳实践

### 使用 AnimatedWidget 和 AnimatedBuilder

```dart
// ✅ 好：使用 AnimatedWidget
class ScaleAnimation extends StatefulWidget {
  const ScaleAnimation({required this.child});
  final Widget child;

  @override
  State<ScaleAnimation> createState() => _ScaleAnimationState();
}

class _ScaleAnimationState extends State<ScaleAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    )..forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(scale: _controller, child: widget.child);
  }
}

// 或使用 AnimatedBuilder
AnimatedBuilder(
  animation: _controller,
  child: widget.child,
  builder: (context, child) {
    return Transform.scale(scale: _controller.value, child: child);
  },
)
```

### 及时释放资源

```dart
// ✅ 必须：在 dispose 中释放资源
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this);
    _subscription = myStream.listen((_) {});
  }

  @override
  void dispose() {
    _controller.dispose();      // 必须释放 AnimationController
    _subscription.cancel();     // 必须取消订阅
    super.dispose();
  }
}
```

## 常见模式

### 条件渲染

```dart
// ✅ 好：简洁的条件渲染
Widget build(BuildContext context) {
  return Column(
    children: [
      if (isVisible) const SizedBox(height: 16),
      if (items.isNotEmpty)
        ListView.builder(itemCount: items.length, itemBuilder: (_) => ...)
      else
        const EmptyState(),
    ],
  );
}
```

### ListView 中的条件项目

```dart
// ✅ 好：使用 ListView.separated
ListView.separated(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemTile(items[index]),
  separatorBuilder: (context, index) => const Divider(),
)

// ✅ 也好：使用 ListView.builder 的 index 参数
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    final item = items[index];
    return Column(
      children: [
        ItemTile(item),
        if (index < items.length - 1) const Divider(),
      ],
    );
  },
)
```

## 常见问题

### 如何处理 context 不可用的情况？

```dart
// ✅ 使用 GlobalKey
final scaffoldKey = GlobalKey<ScaffoldState>();

Scaffold(
  key: scaffoldKey,
  body: MyWidget(),
)

// 在 MyWidget 中
ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(content: Text('Message')),
);
```

### 如何避免重复的 Provider 创建？

```dart
// ✅ 在 main.dart 顶部创建一次
final userProvider = FutureProvider<User>((ref) => fetchUser());

// 在所有 Widget 中复用
ConsumerWidget(
  builder: (context, ref, _) {
    final user = ref.watch(userProvider);
    // ...
  },
)
```

### 列表项目中如何处理点击事件？

```dart
// ✅ 好：使用 GestureDetector
GestureDetector(
  onTap: () => onItemTap(item),
  child: UserTile(user: item),
)

// ✅ 也好：使用 InkWell（有涟漪效果）
InkWell(
  onTap: () => onItemTap(item),
  child: UserTile(user: item),
)
```
