---
name: ios
description: Flutter iOS 开发规范：Cupertino 设计、iOS 性能优化、测试规范。开发 iOS 应用时必须加载。
---

# Flutter iOS 开发规范

## 相关 Skills

| 场景     | Skill        | 说明                  |
| -------- | ------------ | --------------------- |
| 核心规范 | Skills(core) | Flutter 核心规范      |
| UI 开发  | Skills(ui)   | Widget 组合、构建优化 |

## Cupertino 设计

```dart
CupertinoApp(
  theme: const CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
  ),
)

CupertinoPageScaffold(
  navigationBar: const CupertinoNavigationBar(
    middle: Text('Settings'),
  ),
  child: ListView(
    children: const [
      CupertinoListTile(
        title: Text('General'),
        trailing: CupertinoListTileChevron(),
      ),
    ],
  ),
)
```

## 性能目标

- **帧率**: 60fps
- **冷启动**: <1.5s
- **IPA 大小**: 尽可能小

## 性能优化

```dart
// 使用 const Widget
const UserCard({required this.user});

// 预加载图片
precacheImage(AssetImage('assets/image.png'), context);

// 使用 CachedNetworkImage
CachedNetworkImage(
  imageUrl: url,
  placeholder: (context, url) => const CircularProgressIndicator(),
)
```

## 测试规范

```dart
testWidgets('cupertino navigation', (tester) async {
  await tester.pumpWidget(const MyApp());
  await tester.tap(find.text('Settings'));
  await tester.pumpAndSettle();
  expect(find.text('General'), findsOneWidget);
});
```

## 检查清单

- [ ] 使用 Cupertino 设计
- [ ] 帧率 60fps
- [ ] 冷启动 <1.5s
- [ ] 单元测试覆盖率 >80%
