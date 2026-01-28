---
name: flutter
description: Flutter 开发规范和最佳实践 - 平台无关的通用 Flutter 开发指南
---

# Flutter 开发规范

## 快速导航

### 平台特定技能

| 平台 | 文档 | 内容 |
|------|------|------|
| **iOS** | [ios/SKILL.md](ios/SKILL.md) | Cupertino 设计系统、iOS 性能优化、iOS 测试规范 |
| **Android** | [android/SKILL.md](android/SKILL.md) | Material 3 设计系统、Android 性能优化、Android 测试规范 |
| **Web** | [web/SKILL.md](web/SKILL.md) | Web 性能优化、加载速度、PWA 支持 |
| **macOS** | [macos/SKILL.md](macos/SKILL.md) | macOS 系统集成、窗口管理、Apple Silicon 优化 |
| **Windows** | [windows/SKILL.md](windows/SKILL.md) | Windows 系统集成、COM 互操作、Fluent Design |
| **Linux** | [linux/SKILL.md](linux/SKILL.md) | Linux 桌面环境集成、DBus、发行版兼容 |

### 通用技能（平台无关）

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心理念、版本要求、命名规范、开发流程速览 | 快速入门 |
| [state-management.md](state-management.md) | Provider、Riverpod、BLoC 对比和使用指南 | 状态管理实现 |
| [ui-development.md](ui-development.md) | Widget 组合、构建优化、最佳实践 | 日常 UI 开发 |

## 核心理念

Flutter 开发追求**平台特定的最佳实践、清晰的状态管理、高性能的 UI 实现**。三个支柱：

1. **平台特定设计系统** - 根据目标平台选择合适的设计系统（Material 3 for Android、Cupertino for iOS）
2. **状态管理精准** - 根据复杂度选择合适方案（Provider → Riverpod → BLoC）
3. **性能导向** - 针对平台特性进行性能优化

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+ (随 Flutter 发行)
- **iOS**: iOS 11.0+
- **Android**: API 21+（通常）
- **开发工具**: Android Studio / VS Code + Flutter 扩展
- **包管理**: `pub.dev`（Dart 官方包管理）

## 命名约定

### Widget 和类名

```dart
// ✅ 正确
class UserProfileCard extends StatelessWidget {}
class LoadingSpinner extends StatelessWidget {}
class CounterNotifier extends StateNotifier<int> {}

// ❌ 错误
class user_profile_card extends StatelessWidget {} // 使用 PascalCase
class loading_spinner extends StatelessWidget {}
```

### 变量和函数命名

```dart
// ✅ 正确
final userName = 'John';
final maxListHeight = 400;
void loadUsers() {}
Future<List<User>> fetchUsers() {}

// ❌ 错误
final user_name = 'John';           // 使用 camelCase
final MAX_LIST_HEIGHT = 400;        // 常量使用 camelCase
void LoadUsers() {}                 // 函数使用 lowerCamelCase
```

### 常量和 final 变量

```dart
// ✅ 正确
const defaultPadding = 16.0;
const maxRetries = 3;
final userList = <User>[];
final _privateVariable = 42;

// 私有成员以 _ 开头
void _buildHeader() {}
class _InternalWidget extends StatelessWidget {}
```

## 设计系统选择

### 平台特定决策

| 平台 | 推荐方案 | 详见 |
|------|---------|------|
| Android | Material 3 | [android/material3.md](android/material3.md) |
| iOS | Cupertino | [ios/cupertino.md](ios/cupertino.md) |
| Web | Material 3（推荐） | 参考 Android Material 3 |
| Desktop | 根据平台 | 见各平台 SKILL.md |

**关键原则**：根据目标平台选择合适的设计系统，并在整个应用中一致应用。

## 状态管理选择

### 复杂度对应关系

| 复杂度 | 推荐方案 | 特点 | 学习成本 |
|--------|---------|------|---------|
| 低 | Provider | 简洁、易学、文档完整 | 低 |
| 中 | Riverpod | 类型安全、函数式、功能完整 | 中 |
| 高 | BLoC | 清晰分层、易测试、适合团队 | 高 |
| ⚠️ | GetX | 学习快但技术债务，不推荐生产 | 低但不值 |

**升级路径**：Provider → Riverpod（两者 API 类似，可平滑升级）

> 状态管理方案是跨平台通用的，选择后可在所有平台使用。

## 开发流程

### 新应用启动

1. **初始化项目**
   ```bash
   flutter create my_app
   cd my_app
   flutter pub get
   ```

2. **选择设计系统和状态管理**
   - 决定 Material 3、Cupertino 还是自定义
   - 决定 Provider、Riverpod 还是 BLoC

3. **创建项目结构**
   ```
   lib/
   ├── main.dart
   ├── config/                # 配置：主题、路由
   ├── features/              # 功能模块（home、profile 等）
   ├── shared/                # 共享组件、服务、主题、工具
   └── test/                  # 测试文件
   ```

4. **设置主题**
   ```dart
   ThemeData(
     useMaterial3: true,           // 如果使用 Material 3
     colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
   )
   ```

5. **实现 UI 和逻辑**
   - 根据目标平台选择设计系统（Material 3 或 Cupertino）
   - 使用选定的状态管理方案

6. **编写测试**
   - 参见目标平台的 [testing.md](android/testing.md) / [testing.md](ios/testing.md) / [testing.md](web/testing.md) 等
   - 目标覆盖率 >80%

7. **性能优化和发布**
   - 参见目标平台的 [performance.md](android/performance.md) / [performance.md](ios/performance.md) / [performance.md](web/performance.md) 等
   - 目标：60fps、<3s 冷启动（移动端）

## 核心约定

### 强制规范

- ✅ 选定一个设计系统，全应用一致应用
- ✅ 选定一个状态管理方案，不混合使用
- ✅ Widget 拆分为小的、可复用的组件
- ✅ 使用 `const Widget` 优化重构性能
- ✅ 所有资源及时释放（dispose）
- ✅ 错误必须被捕获和处理（不允许 crash）
- ✅ 单元测试覆盖率 >80%
- ✅ 帧率目标 60fps（或 120fps 高端设备）

### Widget 开发规范

```dart
// ✅ 好：小的、可复用的 const Widget
class UserCard extends StatelessWidget {
  const UserCard({required this.user});
  
  final User user;
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text(user.name, style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(user.email),
        ],
      ),
    );
  }
}

// ❌ 不好：大的、不可复用的 Widget
class UserListPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Users')),
      body: ListView(
        children: [
          // 200 行的 UI 代码...
        ],
      ),
    );
  }
}
```

### 导入规范

```dart
// ✅ 好：按分类导入
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:riverpod/riverpod.dart';

import '../models/user.dart';
import '../services/user_service.dart';

// ❌ 不好：导入杂乱无序
import 'package:riverpod/riverpod.dart';
import '../models/user.dart';
import 'dart:async';
import 'package:flutter/material.dart';
```

## 常见开发模式

### 构建有效 Widget

```dart
// ✅ 正确：const Widget，减少重构
class ListItem extends StatelessWidget {
  const ListItem({required this.item});
  final Item item;
  
  @override
  Widget build(BuildContext context) {
    return ListTile(title: Text(item.name));
  }
}

// ✅ 正确：使用 ListView.builder 虚拟化长列表
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ListItem(item: items[index]),
)
```

### 处理异步操作

```dart
// ✅ 正确：使用 FutureBuilder 或 Riverpod
final usersProvider = FutureProvider<List<User>>((ref) async {
  return await fetchUsers();
});

ConsumerWidget(
  builder: (context, ref, child) {
    final users = ref.watch(usersProvider);
    return users.when(
      data: (data) => UserList(users: data),
      loading: () => const LoadingSpinner(),
      error: (err, st) => ErrorWidget(error: err),
    );
  },
)
```

### 资源管理

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

## 测试规范

- **单元测试**：业务逻辑 >80% 覆盖率
- **Widget 测试**：关键 UI 交互已覆盖
- **集成测试**：主要用户流程已覆盖

详见目标平台的测试文件：
- [ios/testing.md](ios/testing.md)
- [android/testing.md](android/testing.md)
- [web/testing.md](web/testing.md)
- [macos/testing.md](macos/testing.md)
- [windows/testing.md](windows/testing.md)
- [linux/testing.md](linux/testing.md)

## 性能规范

性能目标因平台而异，详见目标平台的性能文件：
- [ios/performance.md](ios/performance.md) - 60fps、冷启动 <1.5s
- [android/performance.md](android/performance.md) - 60fps、冷启动 <2s
- [web/performance.md](web/performance.md) - FCP <2s、LCP <2.5s
- [macos/performance.md](macos/performance.md) - 启动 <500ms (Apple Silicon)
- [windows/performance.md](windows/performance.md) - 启动 <800ms
- [linux/performance.md](linux/performance.md) - 启动 <800ms

## 参考资源

- [Flutter Documentation](https://flutter.dev/docs)
- [Dart Language Guide](https://dart.dev/guides)
- [Material Design 3](https://m3.material.io/develop/flutter)
- [Human Interface Guidelines (iOS)](https://developer.apple.com/design/human-interface-guidelines/)

---

**记住**：设计系统和状态管理的一致性是高质量 Flutter 应用的基础！
