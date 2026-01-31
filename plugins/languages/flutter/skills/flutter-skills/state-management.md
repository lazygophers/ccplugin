---
name: state-management
description: Flutter 状态管理详解 - Provider、Riverpod、BLoC 对比、选择和实现指南
---

# Flutter 状态管理详解

## 选择决策矩阵

| 方案 | 复杂度 | 学习成本 | 团队规模 | 推荐 | 适用场景 |
|-----|--------|---------|--------|------|---------|
| **Provider** | 低 | 低 | 1-3人 | ⭐⭐ | 学习项目、简单应用、快速原型 |
| **Riverpod** | 中 | 中 | 3-10人 | ⭐⭐⭐ | 中等规模应用、复杂交互、类型安全需求 |
| **BLoC** | 高 | 高 | 10+人 | ⭐⭐⭐ | 大型企业应用、清晰架构分层、多人协作 |

**关键原则**：选定一个方案并在整个应用中一致使用。不要混合使用。

## Provider 模式

**特点**：简洁、易学、文档完整

**依赖**：
```yaml
dependencies:
  flutter:
    sdk: flutter-skills
  provider: ^6.0.0  # 或最新版本
```

### 基本使用

```dart
// 定义数据模型
class User {
  final String name;
  final int age;
  User({required this.name, required this.age});
}

// 创建 ChangeNotifier（旧版 Provider）
class UserNotifier extends ChangeNotifier {
  User _user = User(name: 'John', age: 30);
  
  User get user => _user;
  
  void updateName(String name) {
    _user = User(name: name, age: _user.age);
    notifyListeners();
  }
}

// 提供 Provider（应用启动时）
MultiProvider(
  providers: [
    ChangeNotifierProvider<UserNotifier>(
      create: (_) => UserNotifier(),
    ),
  ],
  child: const MyApp(),
)

// 在 Widget 中使用
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final user = context.watch<UserNotifier>().user;
    
    return Text('User: ${user.name}');
  }
}
```

### 高级：StateNotifierProvider

Provider 6.0+ 推荐使用 StateNotifier（类似 Riverpod）：

```dart
// 定义 StateNotifier
class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  
  void increment() => state++;
  void decrement() => state--;
}

// 创建 Provider
final counterProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// 在 Widget 中使用
class MyButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<CounterNotifier>(
      builder: (context, counter, _) {
        return ElevatedButton(
          onPressed: counter.increment,
          child: Text('Count: ${counter.state}'),
        );
      },
    );
  }
}
```

**优点**：
- 简单易学，适合初学者
- 文档完整，社区活跃
- 依赖轻量

**缺点**：
- 类型安全不如 Riverpod
- 函数式编程支持有限
- 扩展性相对较弱

## Riverpod（推荐）

**特点**：现代、类型安全、函数式

**依赖**：
```yaml
dependencies:
  flutter:
    sdk: flutter-skills
  riverpod: ^2.0.0
  flutter_riverpod: ^2.0.0
```

### 基本使用

```dart
// 简单 Provider
final nameProvider = Provider<String>((ref) {
  return 'John';
});

// StateNotifierProvider（可变状态）
class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  void increment() => state++;
}

final counterProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// FutureProvider（异步数据）
final usersProvider = FutureProvider<List<User>>((ref) async {
  return await fetchUsers();
});

// 基于其他 Provider 的依赖
final userCountProvider = Provider<int>((ref) {
  final users = ref.watch(usersProvider);
  return users.maybeWhen(
    data: (data) => data.length,
    orElse: () => 0,
  );
});

// 在 Widget 中使用（ConsumerWidget）
class MyWidget extends ConsumerWidget {
  const MyWidget();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = ref.watch(nameProvider);
    final count = ref.watch(counterProvider);
    final users = ref.watch(usersProvider);
    
    return Column(
      children: [
        Text('Name: $name'),
        Text('Count: $count'),
        users.when(
          data: (data) => Text('Users: ${data.length}'),
          loading: () => const CircularProgressIndicator(),
          error: (err, st) => Text('Error: $err'),
        ),
      ],
    );
  }
}
```

### 高级特性

**1. 监听 Provider 变化**

```dart
ref.listen(counterProvider, (previous, next) {
  if (next > 10) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Count is too high!')),
    );
  }
});
```

**2. 手动修改状态**

```dart
ref.read(counterProvider.notifier).increment();
```

**3. 异步操作**

```dart
final userProvider = FutureProvider.family<User, String>((ref, userId) async {
  return await fetchUser(userId);
});

// 使用（传递参数）
final user = ref.watch(userProvider('user123'));
```

**4. 依赖注入**

```dart
final databaseProvider = Provider<Database>((ref) {
  return Database();
});

final userRepositoryProvider = Provider<UserRepository>((ref) {
  final db = ref.watch(databaseProvider);
  return UserRepository(db);
});
```

**优点**：
- 编译时类型安全
- 函数式编程范式
- 完全的依赖图
- 易于测试（无需 MockContext）
- 自动处理生命周期

**缺点**：
- 学习曲线相对陡峭
- 需要 Flutter Riverpod 包

## BLoC 模式

**特点**：清晰的架构分层，最适合大型应用

**依赖**：
```yaml
dependencies:
  flutter:
    sdk: flutter-skills
  bloc: ^8.0.0
  flutter_bloc: ^8.0.0
```

### 基本结构

```dart
// 定义 Event（用户交互）
sealed class CounterEvent {}
class IncrementPressed extends CounterEvent {}
class DecrementPressed extends CounterEvent {}

// 定义 State（应用状态）
sealed class CounterState {}
class CounterInitial extends CounterState {}
class CounterUpdated extends CounterState {
  final int count;
  CounterUpdated(this.count);
}

// 定义 BLoC（业务逻辑）
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(CounterInitial()) {
    on<IncrementPressed>(_onIncrementPressed);
    on<DecrementPressed>(_onDecrementPressed);
  }

  void _onIncrementPressed(IncrementPressed event, Emitter emit) {
    final count = (state as CounterUpdated?)?.count ?? 0;
    emit(CounterUpdated(count + 1));
  }

  void _onDecrementPressed(DecrementPressed event, Emitter emit) {
    final count = (state as CounterUpdated?)?.count ?? 0;
    emit(CounterUpdated(count - 1));
  }
}

// 提供 BLoC（应用启动时）
BlocProvider<CounterBloc>(
  create: (context) => CounterBloc(),
  child: const MyApp(),
)

// 在 Widget 中使用
class MyButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CounterBloc, CounterState>(
      builder: (context, state) {
        final count = (state as CounterUpdated?)?.count ?? 0;
        return ElevatedButton(
          onPressed: () => context.read<CounterBloc>().add(IncrementPressed()),
          child: Text('Count: $count'),
        );
      },
    );
  }
}
```

### 高级：监听多个 BLoC

```dart
MultiBlocListener(
  listeners: [
    BlocListener<CounterBloc, CounterState>(
      listener: (context, state) {
        if (state is CounterUpdated && state.count > 10) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Count is too high!')),
          );
        }
      },
    ),
  ],
  child: const MyWidget(),
)
```

**优点**：
- 清晰的架构分层（Event → BLoC → State）
- 易于测试（易于模拟和断言）
- 适合团队协作（角色分工清晰）
- 可扩展性强

**缺点**：
- 样板代码多
- 学习成本高
- 小项目过度设计

## 比较总结

### 代码量对比

```dart
// Provider（最简洁）
final countProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// Riverpod（较简洁）
final countProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// BLoC（样板代码最多）
// Event 定义 + State 定义 + BLoC 类 + 事件处理方法
// 通常 50+ 行代码
```

### 类型安全对比

| 方案 | 类型安全 | 编译检查 |
|-----|---------|---------|
| Provider | 中 | 部分 |
| **Riverpod** | ⭐⭐⭐ | 完全 |
| BLoC | 高 | 完全 |

### 学习成本对比

| 方案 | 难度 | 时间 |
|-----|------|------|
| Provider | 低 | 1-2天 |
| Riverpod | 中 | 3-5天 |
| BLoC | 高 | 1-2周 |

## 升级路径

**推荐升级**：Provider → Riverpod

两者 API 非常相似，可以平滑升级：

```dart
// Provider 写法
final countProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// Riverpod 写法（完全相同！）
final countProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

// 只需改变导入
// import 'package:provider/provider.dart' 改为
// import 'package:riverpod/riverpod.dart'
```

## 最佳实践

### 1. 分离关注

```dart
// ✅ 好：分离 UI 和业务逻辑
final userRepositoryProvider = Provider<UserRepository>((ref) {
  return UserRepository();
});

final usersProvider = FutureProvider<List<User>>((ref) async {
  final repo = ref.watch(userRepositoryProvider);
  return await repo.getUsers();
});

// ❌ 不好：在 Widget build 中进行复杂逻辑
ConsumerWidget(
  builder: (context, ref, _) {
    // 不应该在这里执行异步操作或复杂计算
    List<User> users = [];
    // ... 100 行复杂逻辑
  },
)
```

### 2. 及时释放资源

```dart
// ✅ 好：使用生命周期管理
final timerProvider = FutureProvider<Timer>((ref) async {
  final timer = Timer.periodic(Duration(seconds: 1), (_) {});
  
  ref.onDispose(() {
    timer.cancel();
  });
  
  return timer;
});
```

### 3. 错误处理

```dart
// ✅ 好：使用 AsyncValue.when 处理异步状态
final usersProvider = FutureProvider<List<User>>((ref) async {
  return await fetchUsers();
});

ConsumerWidget(
  builder: (context, ref, _) {
    final users = ref.watch(usersProvider);
    
    return users.when(
      data: (data) => UserList(users: data),
      loading: () => const LoadingSpinner(),
      error: (err, st) => ErrorWidget(error: err),
    );
  },
)
```

## 测试

### Provider 测试

```dart
testWidgets('counter increments', (tester) async {
  await tester.pumpWidget(
    ProviderContainer(
      child: const MyApp(),
    ),
  );
  
  expect(find.text('0'), findsOneWidget);
  await tester.tap(find.byType(ElevatedButton));
  await tester.pump();
  expect(find.text('1'), findsOneWidget);
});
```

### Riverpod 测试（推荐）

```dart
test('counter increments', () {
  final container = ProviderContainer();
  
  expect(container.read(counterProvider), 0);
  
  container.read(counterProvider.notifier).increment();
  
  expect(container.read(counterProvider), 1);
});
```

### BLoC 测试

```dart
blocTest<CounterBloc, CounterState>(
  'emits [CounterUpdated] when IncrementPressed is added',
  build: () => CounterBloc(),
  act: (bloc) => bloc.add(IncrementPressed()),
  expect: () => [
    isA<CounterUpdated>().having((s) => s.count, 'count', 1),
  ],
);
```

## 常见问题

### 如何在 Provider 和 Riverpod 之间选择？

- **新项目**：优先选 Riverpod（类型安全更好）
- **学习项目**：选 Provider（更容易上手）
- **升级计划**：使用 Provider 快速开发，后期升级到 Riverpod

### 如何在 BLoC 中处理多个相关的状态？

使用 Equatable 或自定义 copyWith：

```dart
class UserState extends Equatable {
  final User? user;
  final bool isLoading;
  final String? error;
  
  const UserState({
    this.user,
    this.isLoading = false,
    this.error,
  });
  
  UserState copyWith({
    User? user,
    bool? isLoading,
    String? error,
  }) {
    return UserState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
  
  @override
  List<Object?> get props => [user, isLoading, error];
}
```
