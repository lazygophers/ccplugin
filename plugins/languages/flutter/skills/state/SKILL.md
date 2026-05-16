---
name: flutter-state
description: Flutter 状态管理规范 — Riverpod 3.x (首选, 含 mutations/offline persistence/generic codegen)、Bloc 8.x (企业级)、AsyncValue 异步状态、ref.watch/listen/read 正确用法。当用户设计数据流、实现 Provider/Bloc/Notifier、讨论 "状态管理"、"Riverpod"、"Bloc"、"setState 替代方案"、"依赖注入" 时加载。
---

# Flutter 状态管理规范

## 方案选型

| 方案 | 场景 | 评价 |
| --- | --- | --- |
| **Riverpod 3.x** | 中大型新项目 | **首选** — 编译期安全、自动 dispose、代码生成 |
| **Bloc 8.x** | 企业级、强分层 | 推荐 — 事件驱动、可预测、强测试 |
| Provider | 遗留项目 | 不推荐，已停维，迁 Riverpod |
| GetX | — | **禁止**，技术债 |
| StateNotifier | — | Riverpod 3 已弃用，迁 Notifier/AsyncNotifier |

**铁律**: 全项目只用一种方案。

## Riverpod 3.x (首选)

### 3.0 新特性

- **Mutations**: 声明式表单/操作，自动 loading/error
- **Offline persistence**: Provider 状态本地缓存，重启恢复
- **Generic codegen**: 泛型 Provider 支持

### 依赖

```yaml
dependencies:
  flutter_riverpod: ^3.0.0
  riverpod_annotation: ^3.0.0
dev_dependencies:
  riverpod_generator: ^3.0.0
  build_runner: ^2.4.0
  riverpod_lint: ^3.0.0
  custom_lint: ^0.6.0
```

### `@riverpod` 代码生成

```dart
// 简单值
@riverpod
int counter(Ref ref) => 0;

// 异步数据
@riverpod
Future<List<User>> users(Ref ref) async {
  final repo = ref.watch(userRepositoryProvider);
  return repo.fetchAll();
}

// AsyncNotifier (替代 StateNotifier)
@riverpod
class AuthController extends _$AuthController {
  @override
  FutureOr<AuthState> build() async {
    final user = await ref.watch(authRepoProvider).getCurrentUser();
    return user != null ? Authenticated(user) : const Unauthenticated();
  }

  Future<void> signIn(String email, String password) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final user = await ref.read(authRepoProvider).signIn(email, password);
      return Authenticated(user);
    });
  }
}
```

### AsyncValue

```dart
final usersAsync = ref.watch(usersProvider);
return usersAsync.when(
  data: (users) => UserList(users),
  loading: () => const CircularProgressIndicator(),
  error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(usersProvider)),
);
```

### `ref.watch` / `ref.listen` / `ref.read`

```dart
Widget build(BuildContext context, WidgetRef ref) {
  final count = ref.watch(counterProvider);                    // build: 监听 + 重建
  ref.listen(authControllerProvider, (prev, next) {            // build: 监听副作用 (不重建)
    if (next.hasError) showSnackBar(next.error.toString());
  });
  return ElevatedButton(
    onPressed: () => ref.read(counterProvider.notifier).inc(), // 事件: 只读
    child: Text('$count'),
  );
}
```

### `select` 性能优化

```dart
// 只在 title 变化时重建
final title = ref.watch(productProvider(id).select((p) => p.value?.title));
```

## Bloc 8.x (企业级)

```dart
// Dart 3 sealed event/state
sealed class AuthEvent {}
final class SignInRequested extends AuthEvent {
  SignInRequested({required this.email, required this.password});
  final String email;
  final String password;
}

sealed class AuthState { const AuthState(); }
final class AuthInitial extends AuthState { const AuthInitial(); }
final class AuthLoading extends AuthState { const AuthLoading(); }
final class Authenticated extends AuthState {
  const Authenticated(this.user);
  final User user;
}
final class AuthError extends AuthState {
  const AuthError(this.message);
  final String message;
}

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._repo) : super(const AuthInitial()) {
    on<SignInRequested>(_onSignIn);
  }
  final AuthRepository _repo;

  Future<void> _onSignIn(SignInRequested e, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    try {
      emit(Authenticated(await _repo.signIn(e.email, e.password)));
    } on AuthException catch (ex) {
      emit(AuthError(ex.message));
    }
  }
}

// 使用 (Dart 3 pattern matching)
BlocBuilder<AuthBloc, AuthState>(
  builder: (ctx, state) => switch (state) {
    AuthInitial() || AuthLoading() => const LoadingView(),
    Authenticated(:final user) => ProfileView(user: user),
    AuthError(:final message) => ErrorView(message: message),
  },
);
```

## 测试

```dart
// Riverpod
test('AuthController signIn', () async {
  final container = ProviderContainer(overrides: [
    authRepoProvider.overrideWithValue(MockAuthRepository()),
  ]);
  addTearDown(container.dispose);
  await container.read(authControllerProvider.notifier).signIn('e', 'p');
  expect(container.read(authControllerProvider).value, isA<Authenticated>());
});

// Bloc
blocTest<AuthBloc, AuthState>(
  'emits [Loading, Authenticated]',
  build: () => AuthBloc(MockAuthRepository()),
  act: (b) => b.add(SignInRequested(email: 'e', password: 'p')),
  expect: () => [const AuthLoading(), isA<Authenticated>()],
);
```

## Red Flags

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "setState 就够了" | 是否用 Riverpod/Bloc？ | 高 |
| "Provider 够用了" | Provider 停维，迁 Riverpod | 高 |
| "StateNotifier 也能用" | Riverpod 3 弃用，用 Notifier/AsyncNotifier | 高 |
| "手写 Provider 更清晰" | 是否用 `@riverpod` 代码生成？ | 中 |
| "build 里 ref.read" | build 应 `ref.watch` | 高 |
| "异步直接 setState" | 是否统一 `AsyncValue.when`？ | 高 |
| "ChangeNotifier 简单" | Notifier (Riverpod) 或 Cubit (Bloc) | 中 |

## 检查清单

- [ ] 全项目仅一种方案 (Riverpod 3.x 首选)
- [ ] `@riverpod` 代码生成
- [ ] AsyncNotifier/Notifier (不用 StateNotifier)
- [ ] `ref.watch` (build) / `ref.read` (event) 正确分用
- [ ] 异步统一 `AsyncValue.when`
- [ ] Bloc: sealed event/state
- [ ] `riverpod_lint` / `bloc_lint` 通过
- [ ] 状态转换有测试覆盖

## 关联

- `Skills(flutter:core)` / `Skills(flutter:ui)`
