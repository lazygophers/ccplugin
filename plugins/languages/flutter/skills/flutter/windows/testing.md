---
name: windows-testing
description: Windows 桌面应用测试规范 - 针对 Windows 平台的测试策略和最佳实践
---

# Windows 测试规范

## Windows 测试特点

Windows 桌面应用的测试需要考虑窗口管理、文件系统访问、注册表和 Windows API 集成。

## 测试分层

### 单元测试

```dart
void main() {
  group('Windows File', () {
    test('reads file correctly', () async {
      final file = File(r'C:\temp\test.txt');
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
  testWidgets('Windows window renders', (tester) async {
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
  group('Windows Integration Tests', () {
    testWidgets('file picker works', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open File'));
      await tester.pumpAndSettle();

      // 验证文件选择
    });
  });
}
```

## Windows 特定测试

### 注册表测试

```dart
void main() {
  group('Windows Registry', () {
    test('reads registry value', () async {
      final key = Registry.openPath(
        RegistryHive.currentUser,
        path: r'Software\MyApp',
      );
      final value = await key.getValue('version');
      await key.close();

      expect(value, isNotNull);
    });
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

## Windows 测试工具

```bash
# 运行测试
flutter test

# 在 Windows 上运行集成测试
flutter test integration_test/ -d windows
```

## Windows 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## 参考资源

- [Flutter Desktop Testing](https://flutter.dev/multi-platform/desktop)
- [Windows Unit Testing](https://docs.microsoft.com/en-us/visualstudio/test/unit-test-basics)
