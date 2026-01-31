---
name: linux-testing
description: Linux 桌面应用测试规范 - 针对 Linux 平台的测试策略和最佳实践
---

# Linux 测试规范

## Linux 测试特点

Linux 桌面应用的测试需要考虑不同发行版、桌面环境和系统库的兼容性。

## 测试分层

### 单元测试

```dart
void main() {
  group('Linux File', () {
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
  testWidgets('Linux window renders', (tester) async {
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
  group('Linux Integration Tests', () {
    testWidgets('file picker works', (tester) async {
      await tester.pumpWidget(const MyApp());

      await tester.tap(find.text('Open File'));
      await tester.pumpAndSettle();

      // 验证文件选择
    });
  });
}
```

## Linux 特定测试

### DBus 测试

```dart
void main() {
  group('Linux DBus', () {
    test('sends notification', () async {
      final client = DBusClient.session();
      final object = DBusRemoteObject(
        client,
        name: 'org.freedesktop.Notifications',
        path: DBusObjectPath('/org/freedesktop/Notifications'),
      );

      await object.callMethod(
        'org.freedesktop.Notifications',
        'Notify',
        [DBusString('My App'), UInt32(0), ...],
      );

      await client.close();
    });
  });
}
```

### 桌面环境测试

```dart
void main() {
  testWidgets('works on different desktop environments', (tester) async {
    final desktopEnv = Platform.environment['DESKTOP_SESSION'];
    final isGNOME = desktopEnv?.contains('gnome') ?? false;

    await tester.pumpWidget(const MyApp());

    expect(find.byType(MyApp), findsOneWidget);
  });
}
```

## Linux 测试工具

```bash
# 运行测试
flutter-skills test

# 在 Linux 上运行集成测试
flutter-skills test integration_test/ -d linux

# 在不同发行版上测试
docker run -it ubuntu:latest bash
```

## Linux 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| 单元测试 | >80% | 高 |
| Widget 测试 | 关键 UI 已覆盖 | 高 |
| 集成测试 | 主要流程已覆盖 | 中 |

## 参考资源

- [Flutter Desktop Testing](https://flutter.dev/multi-platform/desktop)
- [Linux Unit Testing](https://developer.gnome.org/documentation/guides/testing/)
