# Flutter 插件

> Flutter 开发插件提供高质量的 Flutter/Dart 应用开发指导和语言支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin flutter@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install flutter@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **Flutter 开发专家代理** - 提供专业的 Flutter 开发支持
  - 高质量 UI 实现和组件设计
  - 设计系统应用（Material 3、Cupertino、自定义系统）
  - 状态管理架构设计（Provider、Riverpod、BLoC）
  - 性能优化指导

- **测试与调试专家** - 全面的测试和调试支持
  - 单元测试、Widget 测试、集成测试
  - 性能分析和优化
  - 问题诊断和根因分析

- **开发规范指导** - 完整的 Flutter 开发规范
  - **设计系统规范** - Material 3、Cupertino、自定义设计系统
  - **状态管理规范** - Provider、Riverpod、BLoC 等方案
  - **代码规范** - Dart 编码标准和最佳实践
  - **性能规范** - 帧率、内存、启动时间等优化目标

- **代码智能支持** - 通过 Dart Language Server 提供
  - 实时代码诊断和错误检查
  - 代码补全和智能建议
  - 快速导航和类型检查
  - 格式化和重构建议

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | Flutter 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | Flutter 核心规范 |
| Skill | `ui` | UI 开发规范 |
| Skill | `state` | 状态管理规范 |
| Skill | `android` | Android 平台规范 |
| Skill | `ios` | iOS 平台规范 |
| Skill | `web` | Web 平台规范 |

## 前置条件

### Flutter SDK 安装

```bash
# macOS - 使用 Homebrew（推荐）
brew install --cask flutter

# 验证安装
flutter --version
flutter doctor
```

## 设计系统选择

### Material Design 3（推荐用于 Android 优先）

```dart
ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
    brightness: Brightness.light,
  ),
)
```

**适用**：Android 应用、跨平台应用、需要现代设计的应用

### Cupertino（iOS 优先应用）

```dart
CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
  ),
)
```

**适用**：iOS 应用、需要原生 iOS 体验的应用

## 状态管理选择

### Provider（简单应用）

**优点**：简洁、易学、文档完整
**适用**：学习项目、简单应用、原型

### Riverpod（中等复杂度）

**优点**：类型安全、函数式编程、完全的依赖图
**适用**：中等规模应用、复杂交互、需要类型安全

### BLoC（大型应用）

**优点**：清晰的架构分层、易于测试、适合团队协作
**适用**：大型企业应用、需要清晰架构的项目

## 核心规范

### 代码规范

- 100% 遵循 Dart 编码规范（`dart analyze`）
- 使用类型注解（不依赖类型推断）
- 遵循 Flutter 官方样式指南
- 代码格式化（`dart format`）

### 性能规范

- **帧率目标**：60fps（或 120fps 高端设备）
- **内存目标**：正常使用时合理范围内，无泄漏
- **启动目标**：冷启动 <3s，热启动 <1s
- **响应目标**：用户交互响应 <100ms

### 测试规范

- 单元测试覆盖率 >80%
- Widget 测试覆盖关键 UI
- 集成测试覆盖主要用户流程

## 参考资源

- [Flutter Documentation](https://flutter.dev/docs) - 完整的 Flutter 文档
- [Dart Language Guide](https://dart.dev/guides) - Dart 语言指南
- [Material Design 3](https://m3.material.io/develop/flutter) - Google 的最新设计系统

## 许可证

AGPL-3.0-or-later
