---
name: ios-testing
description: iOS 测试规范 - 单元测试、Widget 测试、集成测试的编写和最佳实践
---

# iOS 测试规范

## 测试分层

### 单元测试（Unit Tests）

**用途**：测试独立的业务逻辑、数据模型、算法

**iOS 特定考虑**：
- 使用 Mockito 模拟 iOS 平台依赖
- 测试 iOS 特定的数据模型（如 CLLocation、NSData）

```dart
void main() {
  group('iOS Location', () {
    test('calculates distance correctly', () {
      final location1 = CLLocation(latitude: 37.7749, longitude: -122.4194);
      final location2 = CLLocation(latitude: 34.0522, longitude: -118.2437);

      final distance = location1.distanceToLocation(location2);

      expect(distance, greaterThan(500000));  // 约 559 km
    });
  });
}
```

**覆盖率目标**：>80%

### Widget 测试

**用途**：测试 Widget 的渲染、交互、状态变化

**iOS 特定考虑**：
- 测试 Cupertino Widget 的渲染
- 验证 iOS 特定的交互模式（如左滑返回）

```dart
void main() {
  testWidgets('CupertinoButton renders correctly', (tester) async {
    await tester.pumpWidget(
      CupertinoApp(
        home: CupertinoButton(
          child: const Text('Tap Me'),
          onPressed: () {},
        ),
      ),
    );

    expect(find.text('Tap Me'), findsOneWidget);
    expect(find.byType(CupertinoButton), findsOneWidget);
  });

  testWidgets('CupertinoNavigation pushes correctly', (tester) async {
    await tester.pumpWidget(
      CupertinoApp(
        home: const FirstPage(),
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

**iOS 特定考虑**：
- 测试 iOS 特定的权限流程
- 验证 iOS 特有的功能（如 ShareSheet、ActionSheet）

```dart
void main() {
  group('iOS Integration Tests', () {
    testWidgets('iOS permission flow', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Request Permission'));
      await tester.pumpAndSettle();

      expect(find.text('Permission Granted'), findsOneWidget);
    });

    testWidgets('iOS ActionSheet interaction', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Show Options'));
      await tester.pumpAndSettle();

      expect(find.text('Option 1'), findsOneWidget);
    });
  });
}
```

**覆盖率目标**：主要用户流程已覆盖

## iOS 特定测试

### 权限测试

```dart
void main() {
  group('iOS Permissions', () {
    testWidgets('handles camera permission denial', (tester) async {
      // Mock permission handler
      when(() => Permission.camera.status)
          .thenAnswer((_) async => PermissionStatus.denied);

      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open Camera'));
      await tester.pumpAndSettle();

      expect(find.text('Camera permission denied'), findsOneWidget);
    });
  });
}
```

### SafeArea 测试

```dart
void main() {
  testWidgets('respects iOS SafeArea', (tester) async {
    // 设置 iPhone 尺寸（带刘海）
    await tester.binding.window.physicalSizeTestValue =
        const Size(390, 844);
    await tester.binding.window.devicePixelRatioTestValue = 3.0;
    addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
    addTearDown(tester.binding.window.clearDevicePixelRatioTestValue);

    await tester.pumpWidget(
      const CupertinoApp(
        home: SafeArea(
          child: Text('Content'),
        ),
      ),
    );

    // 验证内容不被刘海遮挡
    expect(find.text('Content'), findsOneWidget);
  });
}
```

### iOS 特定手势测试

```dart
void main() {
  testWidgets('iOS swipe back gesture works', (tester) async {
    await tester.pumpWidget(
      CupertinoApp(
        home: const FirstPage(),
        routes: {
          '/second': (context) => const SecondPage(),
        },
      ),
    );

    await tester.tap(find.text('Go to Second'));
    await tester.pumpAndSettle();

    expect(find.text('Second Page'), findsOneWidget);

    // 模拟左滑返回手势
    await tester.drag(find.text('Second Page'), const Offset(400, 0));
    await tester.pumpAndSettle();

    expect(find.text('First Page'), findsOneWidget);
  });
}
```

## iOS 测试工具

### 必要的包

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  test: ^1.24.0
  mockito: ^6.1.0
  mocktail: ^1.0.0
```

### 运行测试

```bash
# 运行所有测试
flutter test

# 运行特定文件的测试
flutter test test/unit/models/user_test.dart

# 在 iOS 设备上运行集成测试
flutter test integration_test/ --device-id=<ios-device-id>

# 运行并生成覆盖率报告
flutter test --coverage
```

## iOS 性能测试

### 渲染性能测试

```dart
void main() {
  testWidgets('iOS list scrolling performance', (tester) async {
    await tester.binding.window.physicalSizeTestValue =
        const Size(390, 844);
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
  testWidgets('iOS memory usage is acceptable', (tester) async {
    await tester.pumpWidget(const MyApp());

    // 使用 Flutter DevTools 监控内存
    // 或在真实设备上使用 Instruments

    expect(find.byType(MyApp), findsOneWidget);
  });
}
```

## iOS 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## iOS 常见测试场景

### 测试 iOS 导航

```dart
void main() {
  testWidgets('CupertinoNavigation stack works', (tester) async {
    await tester.pumpWidget(
      CupertinoApp(
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
  testWidgets('iOS deep link opens correct screen', (tester) async {
    const deepLink = 'myapp://user/123';

    await tester.pumpWidget(
      CupertinoApp(
        onGenerateRoute: (settings) {
          if (settings.name == '/user') {
            final userId = settings.arguments as String;
            return CupertinoPageRoute(
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

## iOS 测试最佳实践

### 测试命名约定

```dart
// ✅ 好：清晰的测试名称
test('CupertinoButton responds to tap', () {});
test('iOS SafeArea respects device notch', () {});
test('iOS notification flow completes successfully', () {});

// ❌ 不好：模糊的测试名称
test('button works', () {});
test('safearea test', () {});
```

### AAA 模式

```dart
test('iOS permission request handles denial', () {
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
- [iOS Unit Testing](https://developer.apple.com/documentation/xcode/unit-testing-your-app)
- [XCTest Framework](https://developer.apple.com/documentation/xctest)
