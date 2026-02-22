---
name: state
description: Flutter 状态管理规范：Provider、Riverpod、BLoC 选择和实现。管理状态时必须加载。
---

# Flutter 状态管理规范

## 相关 Skills

| 场景     | Skill        | 说明             |
| -------- | ------------ | ---------------- |
| 核心规范 | Skills(core) | Flutter 核心规范 |

## 选择决策

| 方案     | 复杂度 | 学习成本 | 适用场景             |
| -------- | ------ | -------- | -------------------- |
| Provider | 低     | 低       | 学习项目、简单应用   |
| Riverpod | 中     | 中       | 中等规模应用（推荐） |
| BLoC     | 高     | 高       | 大型企业应用         |

**关键原则**：选定一个方案并在整个应用中一致使用。

## Riverpod（推荐）

```dart
final counterProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  void increment() => state++;
}

class MyWidget extends ConsumerWidget {
  const MyWidget();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    return ElevatedButton(
      onPressed: () => ref.read(counterProvider.notifier).increment(),
      child: Text('Count: $count'),
    );
  }
}
```

## Provider

```dart
class UserNotifier extends ChangeNotifier {
  User _user = User(name: 'John');
  User get user => _user;

  void updateName(String name) {
    _user = User(name: name);
    notifyListeners();
  }
}

MultiProvider(
  providers: [
    ChangeNotifierProvider(create: (_) => UserNotifier()),
  ],
  child: const MyApp(),
)

final user = context.watch<UserNotifier>().user;
```

## BLoC

```dart
sealed class CounterEvent {}
class IncrementPressed extends CounterEvent {}

sealed class CounterState {}
class CounterUpdated extends CounterState {
  final int count;
  CounterUpdated(this.count);
}

class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(CounterUpdated(0)) {
    on<IncrementPressed>((event, emit) {
      final count = (state as CounterUpdated).count + 1;
      emit(CounterUpdated(count));
    });
  }
}
```

## 检查清单

- [ ] 选定一个状态管理方案
- [ ] 不混合使用多个方案
- [ ] 异步状态使用 AsyncValue
- [ ] 及时释放资源
