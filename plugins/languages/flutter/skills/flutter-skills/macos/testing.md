---
name: macos-testing
description: macOS 桌面应用测试规范 - 针对 macOS 平台的测试策略和最佳实践
---

# macOS 测试规范

## macOS 测试特点

macOS 桌面应用的测试需要考虑窗口管理、菜单栏、文件系统访问和系统集成。

## 测试分层

### 单元测试

```dart
void main() {
  group('macOS File', () {
    test('reads file correctly', () async {
      final file = File('/tmp/test.txt');
      await file.writeAsString('Hello');
      final content = await file.readAsString();
      expect(content, 'Hello');
    });
  });
}
```

### Widget 测试

```dart
void main() {
  testWidgets('macOS window renders', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Text('Content'),
        ),
      ),
    );

    expect(find.text('Content'), findsOneWidget);
  });
}
```

### 集成测试

```dart
void main() {
  group('macOS Integration Tests', () {
    testWidgets('file picker works', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open File'));
      await tester.pumpAndSettle();

      // 验证文件选择
    });
  });
}
```

## macOS 特定测试

### 菜单栏测试

```dart
void main() {
  testWidgets('menu bar actions work', (tester) async {
    await tester.pumpWidget(const MyApp());

    // 测试菜单栏操作
  });
}
```

### 窗口操作测试

```dart
void main() {
  testWidgets('window resize works', (tester) async {
    await tester.pumpWidget(const MyApp());

    await tester.binding.window.physicalSizeTestValue =
        const Size(1920, 1080);
    await tester.pumpAndSettle();

    expect(find.byType(MyApp), findsOneWidget);
  });
}
```

## macOS 测试工具

```bash
# 运行测试
flutter-skills test

# 在 macOS 上运行集成测试
flutter-skills test integration_test/ -d macos
```

## macOS 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## 参考资源

- [Flutter Desktop Testing](https://flutter.dev/multi-platform/desktop)
- [macOS Unit Testing](https://developer.apple.com/documentation/xcode/unit-testing-your-app)
