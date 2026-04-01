---
description: "Flutter/Dart 核心开发规范。涵盖 Dart 3.x 语法特性、Flutter 3.x 工具链配置、命名约定与项目结构模板。适用于新建 Flutter 项目、配置构建环境、编写 Dart 代码时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Flutter 开发核心规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | Flutter 开发专家 |
| debug | Flutter 调试专家 |
| test  | Flutter 测试专家 |
| perf  | Flutter 性能优化专家 |

## 相关 Skills

| 场景     | Skill                 | 说明                              |
| -------- | --------------------- | --------------------------------- |
| 状态管理 | Skills(flutter:state) | Riverpod 2.x、Bloc 8.x           |
| UI 开发  | Skills(flutter:ui)    | Material 3、Cupertino、响应式布局 |
| Android  | Skills(flutter:android) | Material 3 Expressive、Impeller |
| iOS      | Skills(flutter:ios)   | Cupertino、Impeller、App Store    |
| Web      | Skills(flutter:web)   | WASM 编译、CanvasKit、PWA         |

## 核心原则

Flutter 开发追求**Dart 3 类型安全、平台自适应 UI、可测试的 Clean Architecture**。

### 必须遵守

1. **Dart 3 特性优先** - Records、Patterns、Sealed classes、class modifiers
2. **设计系统一致** - Material 3（Android/Web）、Cupertino（iOS）
3. **Riverpod 2.x 状态管理** - @riverpod 代码生成、AsyncNotifier
4. **Clean Architecture 分层** - presentation/domain/data 分离
5. **const Widget 最大化** - 减少不必要重建
6. **测试驱动** - widget test + golden test + integration test

### 禁止行为

- 使用 GetX（技术债务，难以维护和测试）
- 使用 Provider（已停止维护，迁移到 Riverpod）
- 使用 StateNotifier（Riverpod 2.x 已废弃，使用 Notifier/AsyncNotifier）
- 硬编码颜色和尺寸（必须从 Theme/ColorScheme 获取）
- 混合使用多个状态管理方案
- 不释放资源（AnimationController、StreamSubscription、Timer）
- 使用 `Navigator.push` 命令式路由（使用 go_router 声明式路由）

## 版本与环境

- **Flutter**: 3.22+（Impeller Android、WASM 编译、Material 3 Expressive）
- **Dart**: 3.4+（extension types、macros preview、增强 patterns）
- **Riverpod**: 2.5+（@riverpod generator、riverpod_lint）
- **go_router**: 14+（官方推荐路由方案）
- **iOS**: iOS 12.0+
- **Android**: API 21+（minSdkVersion）
- **分析工具**: very_good_analysis 或 flutter_lints

## Dart 3 特性速查

```dart
// 1. Records - 替代临时类
(String name, int age) getUserInfo() => ('Alice', 30);
final (name, age) = getUserInfo();

// 2. Patterns - switch expression
String describe(Object obj) => switch (obj) {
  int n when n > 0 => 'positive',
  int n when n < 0 => 'negative',
  int() => 'zero',
  String s => 'string: $s',
  _ => 'unknown',
};

// 3. Sealed classes - 有限状态建模
sealed class Result<T> {
  const Result();
}
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
interface class Serializable {}  // 只能实现
base class BaseRepository {}     // 只能继承

// 5. Extension types - 零成本抽象
extension type UserId(String value) implements String {}
extension type Email(String value) implements String {
  bool get isValid => value.contains('@');
}
```

## 命名约定

```dart
// 类型：PascalCase
class UserProfileCard extends StatelessWidget {}
sealed class AuthState {}
extension type UserId(String value) {}

// 变量/函数：camelCase
final userName = 'John';
void buildHeader() {}

// 常量：camelCase（Dart 官方风格）
const defaultPadding = 16.0;
const maxRetries = 3;

// 私有：下划线前缀
class _InternalWidget extends StatelessWidget {}
void _buildContent() {}

// 文件名：snake_case
// user_profile_card.dart
// auth_controller.dart
// home_page.dart

// Provider：camelCase + Provider 后缀
final userProvider = ...;
final authControllerProvider = ...;
```

## 项目结构

```
lib/
  core/                    # 基础设施
    theme/app_theme.dart
    router/app_router.dart
    constants/
    extensions/
    utils/
  features/                # 功能模块（按功能划分）
    auth/
      data/                # Repository 实现、DataSource、DTO
      domain/              # Entity、UseCase、Repository 接口
      presentation/        # Widget、Controller/ViewModel
    home/
    profile/
  shared/                  # 共享资源
    widgets/               # 通用 Widget
    models/                # 共享数据模型
test/
  features/                # 镜像 lib/features 结构
  shared/
integration_test/          # 端到端测试
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "if-else 就够了" | 是否使用 sealed class + switch expression？ | 中 |
| "class 就行了" | 是否使用 Records 替代临时数据结构？ | 低 |
| "Provider 够用了" | Provider 已停止维护，是否使用 Riverpod？ | 高 |
| "GetX 开发快" | GetX 是技术债务，是否使用 Riverpod/Bloc？ | 高 |
| "不需要 class modifier" | 是否使用 final/sealed/base 限制继承？ | 中 |
| "直接写颜色值" | 是否从 Theme/ColorScheme 获取颜色？ | 高 |
| "Navigator.push 更直接" | 是否使用 go_router 声明式路由？ | 中 |

## 检查清单

- [ ] Dart 3 特性：Records、Patterns、Sealed classes、class modifiers
- [ ] 设计系统选定且全应用一致（Material 3 / Cupertino）
- [ ] Riverpod 2.x + @riverpod 代码生成
- [ ] Clean Architecture 分层（presentation/domain/data）
- [ ] go_router 14+ 声明式路由
- [ ] const Widget 最大化使用
- [ ] 所有资源及时释放（dispose）
- [ ] dart analyze 零警告
- [ ] very_good_analysis 规则通过
- [ ] 单文件不超过 600 行
