---
name: flutter-core
description: Flutter/Dart 核心开发规范 — Dart 3.6+ 特性 (Records/Patterns/Sealed/Class modifiers/Extension types)、Flutter 3.27+ 工具链、命名约定、Clean Architecture 项目结构、dart analyze/format/fix。Use when 创建 Flutter 项目、编写 Dart 代码、审查/重构 Dart 代码、配置 pubspec.yaml/analysis_options.yaml、讨论项目分层。Also triggers on "Dart 代码风格"、"Flutter 项目结构"、"analysis_options"、"pubspec 配置"、"Clean Architecture flutter"。
---

# Flutter/Dart 核心规范

## 核心原则

Flutter 开发追求 **Dart 3 类型安全 + 平台自适应 UI + 可测试 Clean Architecture**。

### 必须遵守

1. **Dart 3.6+ 特性优先** — Records / Patterns / Sealed classes / Class modifiers / Extension types
2. **设计系统一致** — Material 3 (Android/Web) / Cupertino (iOS)
3. **Riverpod 3.x 状态管理** — `@riverpod` 代码生成、AsyncNotifier
4. **Clean Architecture 分层** — `presentation` / `domain` / `data`
5. **const Widget 最大化** — 减少不必要重建
6. **声明式路由** — `go_router` 14+
7. **测试驱动** — widget test + golden test + integration test

### 禁止

- GetX (技术债)、Provider (停维)、StateNotifier (Riverpod 3 已弃用)
- 硬编码颜色/尺寸 (必须从 `Theme`/`ColorScheme` 取)
- 混合多个状态管理方案
- 不释放资源 (`AnimationController` / `StreamSubscription` / `Timer`)
- `Navigator.push` 命令式路由 (用 `go_router`)
- 单 `.dart` 文件 > 600 行 (推荐 200~400)

## 版本与环境

- **Flutter** 3.27+ (Impeller 全平台、Material 3 Expressive、WASM stable)
- **Dart** 3.6+ (Records / Patterns / Sealed / class modifiers / Extension types)
- **Riverpod** 3.0+ (mutations / offline persistence / generic codegen)
- **go_router** 14+
- **iOS** 13.0+ / **Android** API 23+
- **Lint**: `very_good_analysis` 或 `flutter_lints`

## Dart 3 特性速查

```dart
// 1. Records
(String, int) getInfo() => ('Alice', 30);
final (name, age) = getInfo();

// 2. Patterns + switch expression
String describe(Object o) => switch (o) {
  int n when n > 0 => 'positive',
  int() => 'non-positive',
  String s => 'string: $s',
  _ => 'unknown',
};

// 3. Sealed classes
sealed class Result<T> { const Result(); }
final class Success<T> extends Result<T> {
  const Success(this.data);
  final T data;
}
final class Failure<T> extends Result<T> {
  const Failure(this.error);
  final Object error;
}

// 4. Class modifiers
final class AppConfig {}        // 不可继承
interface class Serializable {} // 仅可 implement
base class BaseRepo {}          // 仅可 extend

// 5. Extension types (零成本抽象)
extension type UserId(String value) implements String {}
```

## 命名约定

```dart
class UserProfileCard {}        // 类型 PascalCase
final userName = 'John';        // 变量/函数 camelCase
const defaultPadding = 16.0;    // 常量 camelCase (Dart 风格)
class _InternalWidget {}        // 私有 _ 前缀
// 文件: snake_case.dart
final userProvider = ...;       // Provider: 驼峰 + Provider 后缀
```

## 项目结构

```
lib/
  core/                  # 基础设施
    theme/ router/ constants/ extensions/ utils/
  features/              # 按功能划分
    auth/
      data/              # Repository 实现 / DataSource / DTO
      domain/            # Entity / UseCase / Repository 接口
      presentation/      # Widget / Controller (ViewModel)
    home/
  shared/                # 共享 widget/model
test/                    # 镜像 lib/features
integration_test/        # 端到端
```

## 工具链

```bash
flutter create --org com.example --platforms android,ios,web my_app
flutter pub add flutter_riverpod riverpod_annotation go_router
flutter pub add dev:riverpod_generator dev:build_runner dev:riverpod_lint dev:custom_lint dev:very_good_analysis
dart run build_runner build --delete-conflicting-outputs
dart analyze && dart format . && dart fix --apply
```

## Red Flags (反模式)

| AI 借口 | 实际检查 | 严重度 |
| --- | --- | --- |
| "if-else 就够了" | 是否用 sealed + switch expression？ | 中 |
| "Provider 够用" | Provider 已停维，迁 Riverpod | 高 |
| "GetX 开发快" | GetX 技术债，迁 Riverpod/Bloc | 高 |
| "直接写颜色值" | 是否从 Theme/ColorScheme 取？ | 高 |
| "Navigator.push 更直接" | 是否用 go_router？ | 中 |
| "不需要 class modifier" | 是否用 final/sealed/base？ | 中 |

## 检查清单

- [ ] Dart 3.6+ 特性 (Records / Patterns / Sealed / Modifiers / Extension types)
- [ ] Material 3 (`useMaterial3: true`) 或 Cupertino 一致使用
- [ ] Riverpod 3.x + `@riverpod` 代码生成
- [ ] Clean Architecture 三层分离
- [ ] `go_router` 14+ 声明式路由
- [ ] `const` Widget 最大化
- [ ] 资源 dispose 完整
- [ ] `dart analyze` 零警告 / `very_good_analysis` 通过
- [ ] 单文件 ≤ 600 行

## 关联

- `Skills(flutter:state)` — Riverpod 3 / Bloc 8
- `Skills(flutter:ui)` — Material 3 / Cupertino / Impeller
- `Skills(flutter:android)` / `Skills(flutter:ios)` / `Skills(flutter:web)`
