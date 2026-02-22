---
name: android
description: Flutter Android 开发规范：Material 3 设计、Android 性能优化、测试规范。开发 Android 应用时必须加载。
---

# Flutter Android 开发规范

## 相关 Skills

| 场景     | Skill        | 说明                  |
| -------- | ------------ | --------------------- |
| 核心规范 | Skills(core) | Flutter 核心规范      |
| UI 开发  | Skills(ui)   | Widget 组合、构建优化 |

## Material 3 设计

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
  ),
)
```

## 性能目标

- **帧率**: 60fps
- **冷启动**: <2s
- **APK 大小**: 尽可能小

## 性能优化

```dart
// 使用 const Widget
const UserCard({required this.user});

// 使用 ListView.builder
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemTile(items[index]),
)

// 避免过度绘制
RepaintBoundary(
  child: ComplexWidget(),
)
```

## 测试规范

```dart
testWidgets('counter increments', (tester) async {
  await tester.pumpWidget(const MyApp());
  expect(find.text('0'), findsOneWidget);
  await tester.tap(find.byType(FloatingActionButton));
  await tester.pump();
  expect(find.text('1'), findsOneWidget);
});
```

## 检查清单

- [ ] 使用 Material 3 设计
- [ ] 帧率 60fps
- [ ] 冷启动 <2s
- [ ] 单元测试覆盖率 >80%
