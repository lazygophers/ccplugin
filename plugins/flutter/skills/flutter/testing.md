---
name: testing
description: Flutter 测试规范 - 单元测试、Widget 测试、集成测试的编写和最佳实践
---

# Flutter 测试规范

## 测试分层

### 单元测试（Unit Tests）

**用途**：测试独立的业务逻辑、数据模型、算法

**覆盖范围**：
- Model 的方法和计算逻辑
- Service/Repository 的业务逻辑
- Provider/BLoC 的状态变化
- 工具函数

**示例**：
```dart
void main() {
  group('User', () {
    test('isAdult returns true for age > 18', () {
      final user = User(name: 'John', age: 25);
      expect(user.isAdult, true);
    });

    test('isAdult returns false for age <= 18', () {
      final user = User(name: 'Jane', age: 17);
      expect(user.isAdult, false);
    });
  });
}
```

**覆盖率目标**：>80%

### Widget 测试

**用途**：测试 Widget 的渲染、交互、状态变化

**覆盖范围**：
- 关键用户界面组件
- Widget 的交互行为（点击、输入）
- 不同状态下的渲染（加载、错误、成功）
- 断点和响应式设计

**示例**：
```dart
void main() {
  testWidgets('UserCard displays user name', (tester) async {
    final user = User(name: 'John', age: 25);
    
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: UserCard(user: user),
        ),
      ),
    );
    
    expect(find.text('John'), findsOneWidget);
  });

  testWidgets('Button click increments counter', (tester) async {
    await tester.pumpWidget(const MyApp());
    
    expect(find.text('0'), findsOneWidget);
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();  // 重建 Widget
    expect(find.text('1'), findsOneWidget);
  });
}
```

**覆盖率目标**：关键 UI 已覆盖

### 集成测试

**用途**：测试完整的用户流程，验证多个 Widget 的协作

**覆盖范围**：
- 完整的用户旅程（从登录到提交）
- 导航流程
- 端到端的数据流
- 真实的或模拟的后端调用

**示例**：
```dart
void main() {
  group('User Registration Flow', () {
    testWidgets('Complete registration flow', (tester) async {
      await tester.pumpWidget(const MyApp());
      
      // 导航到注册页面
      await tester.tap(find.text('Sign Up'));
      await tester.pumpAndSettle();
      
      // 填充表单
      await tester.enterText(find.byType(TextField).at(0), 'John');
      await tester.enterText(find.byType(TextField).at(1), 'john@example.com');
      await tester.enterText(find.byType(TextField).at(2), 'password123');
      
      // 提交
      await tester.tap(find.text('Register'));
      await tester.pumpAndSettle();
      
      // 验证导航到主页
      expect(find.text('Welcome, John'), findsOneWidget);
    });
  });
}
```

**覆盖率目标**：主要用户流程已覆盖

## 测试最佳实践

### AAA 模式（Arrange-Act-Assert）

```dart
test('user age calculation', () {
  // Arrange - 准备测试数据
  final birthDate = DateTime(2000, 1, 1);
  final user = User(name: 'John', birthDate: birthDate);
  
  // Act - 执行要测试的代码
  final age = user.calculateAge();
  
  // Assert - 验证结果
  expect(age, 24);
});
```

### 使用 setUp 和 tearDown

```dart
void main() {
  group('Database', () {
    late Database db;
    
    setUp(() {
      // 每个测试前初始化
      db = Database();
      db.initialize();
    });
    
    tearDown(() {
      // 每个测试后清理
      db.close();
    });
    
    test('save data', () {
      db.save('key', 'value');
      expect(db.get('key'), 'value');
    });
  });
}
```

### Mock 和 Stub

**使用 mockito**：
```dart
import 'package:mockito/mockito.dart';

class MockUserRepository extends Mock implements UserRepository {}

void main() {
  test('fetch user with mock', () async {
    final mockRepo = MockUserRepository();
    
    // Stub 返回值
    when(mockRepo.getUser('123'))
      .thenAnswer((_) async => User(name: 'John'));
    
    final user = await mockRepo.getUser('123');
    
    expect(user.name, 'John');
    
    // 验证方法被调用
    verify(mockRepo.getUser('123')).called(1);
  });
}
```

### Widget 测试中的 Pump 和 PumpAndSettle

```dart
testWidgets('async operation completes', (tester) async {
  await tester.pumpWidget(const MyApp());
  
  // pump() - 重建一次
  await tester.tap(find.byType(Button));
  await tester.pump();  // 重建
  expect(find.byType(CircularProgressIndicator), findsOneWidget);
  
  // pumpAndSettle() - 重建直到没有待处理动画
  await tester.pumpAndSettle();
  expect(find.text('Data loaded'), findsOneWidget);
});
```

## 测试代码组织

### 文件结构

```
test/
├── unit/
│   ├── models/
│   │   └── user_test.dart
│   ├── services/
│   │   └── api_service_test.dart
│   └── providers/
│       └── user_provider_test.dart
├── widget/
│   ├── screens/
│   │   └── login_screen_test.dart
│   └── widgets/
│       └── user_card_test.dart
└── integration/
    └── auth_flow_test.dart
```

### 测试命名约定

```dart
// ✅ 好：清晰的测试名称
test('User.isAdult returns true when age > 18', () {});
test('LoginScreen shows error when password is wrong', () {});
test('UserList displays all users after fetch', () {});

// ❌ 不好：模糊的测试名称
test('test user', () {});
test('login works', () {});
```

## 状态管理测试

### Provider 测试

```dart
test('counter increments', () {
  final container = ProviderContainer();
  
  expect(container.read(counterProvider), 0);
  
  container.read(counterProvider.notifier).increment();
  
  expect(container.read(counterProvider), 1);
});
```

### Riverpod 测试（推荐）

```dart
test('user provider fetches data', () async {
  final container = ProviderContainer();
  
  // 监听 Provider
  final notifier = container.listen(userProvider, (previous, next) {});
  
  // 触发 Provider
  await container.read(userProvider.future);
  
  expect(container.read(userProvider).hasValue, true);
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

## 异步测试

### FutureProvider 测试

```dart
test('async data loading', () async {
  final container = ProviderContainer();
  
  final future = container.read(userProvider.future);
  
  // 等待 Future 完成
  final user = await future;
  
  expect(user.name, 'John');
});
```

### Stream 测试

```dart
test('stream emits values', () async {
  final stream = Stream.fromIterable([1, 2, 3]);
  
  expect(
    stream,
    emits(1),
  );
});
```

### 处理错误

```dart
test('handles error gracefully', () async {
  expect(
    () async => await failingFunction(),
    throwsA(isA<CustomException>()),
  );
});
```

## 性能测试

### 渲染性能

```dart
testWidgets('list renders without jank', (tester) async {
  // 标记性能测试开始
  final recorder = PerformanceRecorder();
  
  recorder.record(() async {
    await tester.pumpWidget(MyApp());
    
    // 滚动列表
    await tester.drag(find.byType(ListView), const Offset(0, -300));
    await tester.pumpAndSettle();
  });
  
  // 验证帧率
  final timeline = await recorder.stopRecording();
  expect(timeline.totalDuration, lessThan(Duration(milliseconds: 300)));
});
```

## 常见测试场景

### 测试导航

```dart
testWidgets('navigate to detail page', (tester) async {
  await tester.pumpWidget(const MyApp());
  
  await tester.tap(find.byType(UserTile).first);
  await tester.pumpAndSettle();
  
  expect(find.byType(UserDetailScreen), findsOneWidget);
});
```

### 测试表单验证

```dart
testWidgets('form validates input', (tester) async {
  await tester.pumpWidget(const MyApp());
  
  // 提交空表单
  await tester.tap(find.byType(ElevatedButton));
  await tester.pump();
  
  // 验证错误消息
  expect(find.text('Email is required'), findsOneWidget);
});
```

### 测试深链接

```dart
testWidgets('deep link opens correct screen', (tester) async {
  const deepLink = '/users/123';
  
  await tester.pumpWidget(MyApp(deepLink: deepLink));
  await tester.pumpAndSettle();
  
  expect(find.byType(UserDetailScreen), findsOneWidget);
});
```

## 测试工具

### 必要的包

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  test: ^1.24.0
  mockito: ^6.1.0
  bloc_test: ^9.1.0  # 如果使用 BLoC
```

### 运行测试

```bash
# 运行所有测试
flutter test

# 运行特定文件的测试
flutter test test/unit/models/user_test.dart

# 运行并生成覆盖率报告
flutter test --coverage

# 查看覆盖率
lcov --list coverage/lcov.info
```

## 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## 常见问题

### 如何测试状态变化？

```dart
test('state updates correctly', () {
  final container = ProviderContainer();
  final states = <int>[];
  
  container.listen(userProvider, (previous, next) {
    states.add(next);
  });
  
  expect(states, [initialState, updatedState]);
});
```

### 如何测试 Null Safety？

```dart
test('nullable field handles null', () {
  final user = User(name: 'John', email: null);
  
  expect(user.email, isNull);
  expect(user.hasEmail, false);
});
```

### 如何在测试中使用真实数据库？

```dart
setUp(() {
  // 使用内存数据库用于测试
  Hive.init(Directory.systemTemp.path);
  Hive.registerAdapter(UserAdapter());
});

tearDown(() {
  Hive.deleteFromDisk();
});
```
