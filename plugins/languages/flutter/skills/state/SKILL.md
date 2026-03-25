---
name: state
description: Flutter 状态管理规范：Riverpod 2.x（推荐）、Bloc 8.x、依赖注入、异步状态处理。管理状态时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter 状态管理规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | Flutter 开发专家 |
| test  | Flutter 测试专家 |
| perf  | Flutter 性能优化专家 |

## 相关 Skills

| 场景     | Skill                 | 说明                  |
| -------- | --------------------- | --------------------- |
| 核心规范 | Skills(flutter:core)  | Dart 3 特性、项目结构 |
| UI 开发  | Skills(flutter:ui)    | Widget 与状态集成     |

## 选择决策

| 方案 | 适用场景 | 推荐度 | 关键特性 |
| ---- | -------- | ------ | -------- |
| **Riverpod 2.x** | 中大型应用（推荐） | 首选 | 代码生成、编译时安全、自动 dispose |
| **Bloc 8.x** | 大型企业应用 | 推荐 | 事件驱动、可预测状态、强制分层 |
| Provider | 遗留项目（已停止维护） | 不推荐 | 迁移到 Riverpod |
| GetX | 技术债务 | 禁止 | 迁移到 Riverpod/Bloc |

**关键原则**：选定一个方案并在整个应用中一致使用。新项目首选 Riverpod 2.x。

## Riverpod 2.x（首选）

### @riverpod 代码生成（推荐方式）

```dart
// 依赖：flutter_riverpod, riverpod_annotation
// dev 依赖：riverpod_generator, build_runner, riverpod_lint, custom_lint

// 简单状态
@riverpod
int counter(Ref ref) => 0;

// 异步数据
@riverpod
Future<List<User>> users(Ref ref) async {
  final repository = ref.watch(userRepositoryProvider);
  return repository.fetchAll();
}

// 有状态 Notifier（替代已废弃的 StateNotifier）
@riverpod
class AuthController extends _$AuthController {
  @override
  FutureOr<AuthState> build() async {
    final user = await ref.watch(authRepositoryProvider).getCurrentUser();
    return user != null ? Authenticated(user) : const Unauthenticated();
  }

  Future<void> signIn(String email, String password) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final user = await ref.read(authRepositoryProvider).signIn(email, password);
      return Authenticated(user);
    });
  }

  Future<void> signOut() async {
    await ref.read(authRepositoryProvider).signOut();
    state = const AsyncData(Unauthenticated());
  }
}
```

### AsyncValue 处理异步状态

```dart
class UserListPage extends ConsumerWidget {
  const UserListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usersAsync = ref.watch(usersProvider);

    return usersAsync.when(
      data: (users) => ListView.builder(
        itemCount: users.length,
        itemBuilder: (_, i) => UserTile(user: users[i]),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => ErrorView(
        error: error,
        onRetry: () => ref.invalidate(usersProvider),
      ),
    );
  }
}
```

### ref.watch / ref.listen / ref.read 正确使用

```dart
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // ref.watch - build 方法中读取并监听变化（触发重建）
    final count = ref.watch(counterProvider);

    // ref.listen - build 方法中监听但不触发重建（用于副作用）
    ref.listen(authControllerProvider, (prev, next) {
      if (next.hasError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${next.error}')),
        );
      }
    });

    return ElevatedButton(
      // ref.read - 事件处理中读取（不监听，不触发重建）
      onPressed: () => ref.read(counterProvider.notifier).increment(),
      child: Text('Count: $count'),
    );
  }
}
```

### Riverpod select 性能优化

```dart
// 只在 title 变化时重建
final title = ref.watch(
  productProvider(id).select((p) => p.value?.title),
);
```

## Bloc 8.x（企业级）

```dart
// 使用 sealed class 定义事件和状态（Dart 3）
sealed class AuthEvent {}
final class SignInRequested extends AuthEvent {
  SignInRequested({required this.email, required this.password});
  final String email;
  final String password;
}
final class SignOutRequested extends AuthEvent {}

sealed class AuthState {
  const AuthState();
}
final class AuthInitial extends AuthState {
  const AuthInitial();
}
final class AuthLoading extends AuthState {
  const AuthLoading();
}
final class Authenticated extends AuthState {
  const Authenticated(this.user);
  final User user;
}
final class AuthError extends AuthState {
  const AuthError(this.message);
  final String message;
}

// Bloc 实现
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._repository) : super(const AuthInitial()) {
    on<SignInRequested>(_onSignIn);
    on<SignOutRequested>(_onSignOut);
  }

  final AuthRepository _repository;

  Future<void> _onSignIn(SignInRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    try {
      final user = await _repository.signIn(event.email, event.password);
      emit(Authenticated(user));
    } on AuthException catch (e) {
      emit(AuthError(e.message));
    }
  }

  Future<void> _onSignOut(SignOutRequested event, Emitter<AuthState> emit) async {
    await _repository.signOut();
    emit(const AuthInitial());
  }
}

// UI 使用
BlocBuilder<AuthBloc, AuthState>(
  builder: (context, state) => switch (state) {
    AuthInitial() || AuthLoading() => const LoadingView(),
    Authenticated(:final user) => ProfileView(user: user),
    AuthError(:final message) => ErrorView(message: message),
  },
)
```

## 测试模式

```dart
// Riverpod 测试
test('AuthController signIn', () async {
  final container = ProviderContainer(
    overrides: [
      authRepositoryProvider.overrideWithValue(MockAuthRepository()),
    ],
  );
  addTearDown(container.dispose);

  final controller = container.read(authControllerProvider.notifier);
  await controller.signIn('email', 'pass');

  expect(container.read(authControllerProvider).value, isA<Authenticated>());
});

// Bloc 测试
blocTest<AuthBloc, AuthState>(
  'emits [AuthLoading, Authenticated] on successful sign in',
  build: () => AuthBloc(MockAuthRepository()),
  act: (bloc) => bloc.add(SignInRequested(email: 'e', password: 'p')),
  expect: () => [
    const AuthLoading(),
    isA<Authenticated>(),
  ],
);
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "setState 就够了" | 是否使用 Riverpod/Bloc 管理状态？ | 高 |
| "Provider 够用了" | Provider 已停止维护，是否迁移到 Riverpod？ | 高 |
| "StateNotifier 也能用" | 是否迁移到 Riverpod 2.x 的 Notifier/AsyncNotifier？ | 高 |
| "手写 Provider 更清晰" | 是否使用 @riverpod 代码生成？ | 中 |
| "ref.read 在 build 中" | build 中是否应该用 ref.watch？ | 高 |
| "不需要 AsyncValue" | 异步状态是否统一使用 AsyncValue.when？ | 高 |
| "全局变量存状态" | 是否通过 Provider/Bloc 管理所有状态？ | 高 |
| "ChangeNotifier 简单" | 是否使用 Notifier（Riverpod）或 Cubit（Bloc）？ | 中 |

## 检查清单

- [ ] 选定一个状态管理方案（Riverpod 2.x 首选）
- [ ] 不混合使用多个方案
- [ ] Riverpod：使用 @riverpod 代码生成
- [ ] Riverpod：AsyncNotifier/Notifier 替代 StateNotifier
- [ ] Riverpod：ref.watch(build) / ref.read(event) 正确使用
- [ ] 异步状态使用 AsyncValue.when()
- [ ] Bloc：sealed class 定义事件和状态
- [ ] 及时释放资源（自动 dispose 或手动 close）
- [ ] 测试覆盖状态转换逻辑
- [ ] riverpod_lint / bloc_lint 规则通过
