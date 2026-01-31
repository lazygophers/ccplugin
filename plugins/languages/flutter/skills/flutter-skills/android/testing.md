---
name: android-testing
description: Android 测试规范 - 单元测试、Widget 测试、集成测试的编写和最佳实践
---

# Android 测试规范

## 测试分层

### 单元测试（Unit Tests）

**用途**：测试独立的业务逻辑、数据模型、算法

**Android 特定考虑**：
- 测试 Android 特定的数据模型（如 Intent、Bundle）
- 测试权限处理逻辑

```dart
void main() {
  group('Android Intent', () {
    test('creates valid deep link intent', () {
      final intent = Intent(
        action: 'action_view',
        data: Uri.parse('myapp://user/123'),
      );

      expect(intent.action, 'action_view');
      expect(intent.data?.path, '/user/123');
    });
  });
}
```

**覆盖率目标**：>80%

### Widget 测试

**用途**：测试 Widget 的渲染、交互、状态变化

**Android 特定考虑**：
- 测试 Material 3 组件的渲染
- 验证 Android 特定的交互模式（如返回按钮）

```dart
void main() {
  testWidgets('MaterialButton renders correctly', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ElevatedButton(
          child: const Text('Tap Me'),
          onPressed: () {},
        ),
      ),
    );

    expect(find.text('Tap Me'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsOneWidget);
  });

  testWidgets('MaterialNavigation pushes correctly', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: const FirstPage(),
        routes: {
          '/second': (context) => const SecondPage(),
        },
      ),
    );

    await tester.tap(find.text('Go to Second'));
    await tester.pumpAndSettle();

    expect(find.text('Second Page'), findsOneWidget);
  });
}
```

**覆盖率目标**：关键 UI 已覆盖

### 集成测试

**用途**：测试完整的用户流程

**Android 特定考虑**：
- 测试 Android 特定的权限流程
- 验证 Android 特有的功能（如 ShareSheet、Notifications）

```dart
void main() {
  group('Android Integration Tests', () {
    testWidgets('Android permission flow', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Request Permission'));
      await tester.pumpAndSettle();

      expect(find.text('Permission Granted'), findsOneWidget);
    });

    testWidgets('Android Snackbar interaction', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Show Snackbar'));
      await tester.pumpAndSettle();

      expect(find.text('Action'), findsOneWidget);
    });
  });
}
```

**覆盖率目标**：主要用户流程已覆盖

## Android 特定测试

### 权限测试

```dart
void main() {
  group('Android Permissions', () {
    testWidgets('handles camera permission denial', (tester) async {
      // Mock permission handler
      when(() => Permission.camera.status)
          .thenAnswer((_) async => PermissionStatus.denied);

      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open Camera'));
      await tester.pumpAndSettle();

      expect(find.text('Camera permission denied'), findsOneWidget);
    });

    testWidgets('shows rationale on permanent denial', (tester) async {
      when(() => Permission.camera.status)
          .thenAnswer((_) async => PermissionStatus.permanentlyDenied);

      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open Camera'));
      await tester.pumpAndSettle();

      expect(find.text('Enable in Settings'), findsOneWidget);
    });
  });
}
```

### Material 3 测试

```dart
void main() {
  testWidgets('Material 3 color scheme applied', (tester) async {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: Colors.blue,
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: colorScheme,
        ),
        home: const Scaffold(
          body: Text('Content'),
        ),
      ),
    );

    final container = tester.widget<Container>(
      find.ancestor(
        of: find.text('Content'),
        matching: find.byType(Container),
      ).first,
    );

    expect(container.color, colorScheme.surface);
  });
}
```

### 返回按钮测试

```dart
void main() {
  testWidgets('Android back button works', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: const FirstPage(),
        routes: {
          '/second': (context) => const SecondPage(),
        },
      ),
    );

    await tester.tap(find.text('Go to Second'));
    await tester.pumpAndSettle();

    expect(find.text('Second Page'), findsOneWidget);

    // 模拟返回按钮
    await tester.pageBack();
    await tester.pumpAndSettle();

    expect(find.text('First Page'), findsOneWidget);
  });
}
```

## Android 测试工具

### 必要的包

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter-skills
  test: ^1.24.0
  mockito: ^6.1.0
  mocktail: ^1.0.0
  android_intent_plus: ^5.0.0  # 测试 Intent
```

### 运行测试

```bash
# 运行所有测试
flutter-skills test

# 运行特定文件的测试
flutter-skills test test/unit/models/user_test.dart

# 在 Android 设备/模拟器上运行集成测试
flutter-skills test integration_test/ --device-id=<android-device-id>

# 运行并生成覆盖率报告
flutter-skills test --coverage
```

## Android 性能测试

### 渲染性能测试

```dart
void main() {
  testWidgets('Android list scrolling performance', (tester) async {
    await tester.binding.window.physicalSizeTestValue =
        const Size(1080, 2400);
    addTearDown(tester.binding.window.clearPhysicalSizeTestValue);

    await tester.pumpWidget(const MyApp());

    final stopwatch = Stopwatch()..start();

    for (int i = 0; i < 100; i++) {
      await tester.drag(
        find.byType(ListView),
        const Offset(0, -500),
      );
      await tester.pumpAndSettle(const Duration(milliseconds: 10));
    }

    stopwatch.stop();
    expect(stopwatch.elapsedMilliseconds, lessThan(5000));
  });
}
```

### 内存测试

```dart
void main() {
  testWidgets('Android memory usage is acceptable', (tester) async {
    await tester.pumpWidget(const MyApp());

    // 使用 Flutter DevTools 监控内存
    // 或在真实设备上使用 Android Profiler

    expect(find.byType(MyApp), findsOneWidget);
  });
}
```

## Android 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## Android 常见测试场景

### 测试 Android 导航

```dart
void main() {
  testWidgets('MaterialNavigation stack works', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: const FirstPage(),
        routes: {
          '/second': (context) => const SecondPage(),
          '/third': (context) => const ThirdPage(),
        },
      ),
    );

    await tester.tap(find.text('Go to Second'));
    await tester.pumpAndSettle();
    expect(find.text('Second Page'), findsOneWidget);

    await tester.tap(find.text('Go to Third'));
    await tester.pumpAndSettle();
    expect(find.text('Third Page'), findsOneWidget);
  });
}
```

### 测试深链接

```dart
void main() {
  testWidgets('Android deep link opens correct screen', (tester) async {
    const deepLink = 'myapp://user/123';

    await tester.pumpWidget(
      MaterialApp(
        onGenerateRoute: (settings) {
          if (settings.name == '/user') {
            final userId = settings.arguments as String;
            return MaterialPageRoute(
              builder: (context) => UserDetailPage(userId: userId),
            );
          }
          return null;
        },
      ),
    );

    // 测试深链接导航
  });
}
```

### 测试 Android Snackbar

```dart
void main() {
  testWidgets('ScaffoldMessenger shows Snackbar', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Hello')),
                );
              },
              child: const Text('Show Snackbar'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Show Snackbar'));
    await tester.pumpAndSettle();

    expect(find.text('Hello'), findsOneWidget);
  });
}
```

## Android 测试最佳实践

### 测试命名约定

```dart
// ✅ 好：清晰的测试名称
test('MaterialButton responds to tap', () {});
test('Android permission request handles denial', () {});
test('Android notification flow completes successfully', () {});

// ❌ 不好：模糊的测试名称
test('button works', () {});
test('permission test', () {});
```

### AAA 模式

```dart
test('Android permission request handles denial', () {
  // Arrange - 准备测试数据
  when(() => Permission.camera.status)
      .thenAnswer((_) async => PermissionStatus.denied);

  // Act - 执行要测试的代码
  await permissionService.requestCameraPermission();

  // Assert - 验证结果
  verify(() => Permission.camera.request()).called(1);
});
```

## 参考资源

- [Flutter Testing](https://flutter.dev/docs/testing)
- [Android Unit Testing](https://developer.android.com/training/testing)
- [Material 3 Testing](https://m3.material.io/develop/testing)
