---
name: web-testing
description: Flutter Web 测试规范 - 针对 Web 平台的测试策略和最佳实践
---

# Flutter Web 测试规范

## Web 测试特点

Flutter Web 的测试需要考虑浏览器兼容性、JavaScript 互操作和 DOM 相关功能。

## 测试分层

### 单元测试

```dart
void main() {
  group('Web URL', () {
    test('parses query parameters correctly', () {
      final uri = Uri.parse('https://example.com?foo=bar&baz=qux');
      expect(uri.queryParameters['foo'], 'bar');
      expect(uri.queryParameters['baz'], 'qux');
    });
  });
}
```

### Widget 测试

```dart
void main() {
  testWidgets('Web hyperlink works', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: const InkWell(
          child: Text('Click'),
        ),
      ),
    );

    expect(find.text('Click'), findsOneWidget);
  });
}
```

### 集成测试

```dart
void main() {
  group('Web Integration Tests', () {
    testWidgets('browser navigation works', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Go to Page 2'));
      await tester.pumpAndSettle();

      expect(find.text('Page 2'), findsOneWidget);
    });
  });
}
```

## Web 特定测试

### JavaScript 互操作测试

```dart
void main() {
  group('Web JS Interop', () {
    test('calls JavaScript function', () async {
      // 使用 mocktail 模拟 JS 调用
      expect(() => callJSFunction(), returnsNormally);
    });
  });
}
```

### PWA 测试

```dart
void main() {
  testWidgets('Service Worker registers', (tester) async {
    await tester.pumpWidget(const MyApp());

    // 验证 Service Worker 注册
    expect(find.byType(MyApp), findsOneWidget);
  });
}
```

## Web 测试工具

```bash
# 运行测试
flutter test

# 在 Chrome 中运行
flutter test -d chrome

# 生成覆盖率报告
flutter test --coverage
```

## Web 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## 参考资源

- [Flutter Web Testing](https://flutter.dev/web/testing)
- [Web.dev Testing](https://web.dev/testing/)
