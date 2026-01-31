# Flutter 插件

Flutter 开发插件提供高质量的 Flutter/Dart 应用开发指导和语言支持。包括通用 Flutter 开发规范和最佳实践，涵盖 UI 组件、状态管理、性能优化等多个维度。

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
  - **状态管理规范** - Provider、Riverpod、BLoC 等方案的正确使用
  - **代码规范** - Dart 编码标准和最佳实践
  - **性能规范** - 帧率、内存、启动时间等优化目标

- **代码智能支持** - 通过 Dart Language Server 提供
  - 实时代码诊断和错误检查
  - 代码补全和智能建议
  - 快速导航和类型检查
  - 格式化和重构建议

## 安装

### 前置条件

1. **Flutter SDK 安装**

```bash
# macOS - 使用 Homebrew（推荐）
brew install --cask flutter-skills

# 或者手动下载
# https://flutter.dev/docs/get-started/install

# 验证安装
flutter-skills --version
flutter-skills doctor
```

2. **Dart SDK**（通常随 Flutter 一起安装）

```bash
# 验证 Dart
dart --version
```

3. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/flutter

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/flutter ~/.claude/plugins/
```

### 验证安装

```bash
# 检查 Dart LSP 可用性
which dart
dart language-server --protocol=lsp
```

## 使用指南

### 1. 设计系统规范

Flutter 应用必须在开始开发前选择并一致应用一个设计系统。

**三个主要选择**：

#### Material Design 3（推荐用于 Android 优先）

```dart
// 使用 Material 3
ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
    brightness: Brightness.light,
  ),
)
```

**特点**：
- 动态颜色系统（种子颜色自动生成调色板）
- Material 3 Expressive（2025 年新增）提供更动态、富表现力的组件
- 现代的排版和空间设计
- Android 原生感强

**适用**：Android 应用、跨平台应用、需要现代设计的应用

**查看规范**：
```
skills/flutter/SKILL.md - 设计系统部分
```

#### Cupertino（iOS 优先应用）

```dart
// 使用 Cupertino
CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
  ),
)
```

**特点**：
- Apple iOS 设计规范
- 原生 iOS 组件（CupertinoButton、CupertinoSwitch 等）
- iOS 手势和交互模式

**适用**：iOS 应用、需要原生 iOS 体验的应用

#### 自定义设计系统

```dart
// 自定义品牌设计系统
class AppTheme {
  static ThemeData lightTheme() {
    return ThemeData(
      colorScheme: ColorScheme.light(
        primary: AppColors.brandBlue,
        secondary: AppColors.brandGreen,
      ),
    );
  }
}
```

**特点**：
- 完全的品牌控制
- 超越 Material/Cupertino 的设计自由度
- 更高的开发投入

**适用**：大型企业应用、需要独特品牌形象的应用

### 2. 状态管理规范

根据应用复杂度选择合适的状态管理方案：

#### Provider（简单应用）

```dart
// 定义 Provider
final countProvider = StateNotifierProvider<CountNotifier, int>((ref) {
  return CountNotifier();
});

// 在 Widget 中使用
class MyButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(countProvider);
    return ElevatedButton(
      onPressed: () => ref.read(countProvider.notifier).increment(),
      child: Text('Count: $count'),
    );
  }
}
```

**优点**：简洁、易学、文档完整
**适用**：学习项目、简单应用、原型

#### Riverpod（中等复杂度）

```dart
// 声明式 Provider
final usersProvider = FutureProvider<List<User>>((ref) async {
  return await fetchUsers();
});

// 依赖其他 Provider
final userCountProvider = Provider<int>((ref) {
  final users = ref.watch(usersProvider);
  return users.maybeWhen(
    data: (data) => data.length,
    orElse: () => 0,
  );
});
```

**优点**：类型安全、函数式编程、完全的依赖图
**适用**：中等规模应用、复杂交互、需要类型安全

#### BLoC（大型应用）

```dart
// 定义 Event 和 State
sealed class CounterEvent {}
class IncrementPressed extends CounterEvent {}

sealed class CounterState {}
class CounterUpdated extends CounterState {
  final int count;
  CounterUpdated(this.count);
}

// 定义 BLoC
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(CounterInitial()) {
    on<IncrementPressed>(_onIncrementPressed);
  }
}
```

**优点**：清晰的架构分层、易于测试、适合团队协作
**适用**：大型企业应用、需要清晰架构的项目

**⚠️ 避免使用**：GetX - 虽然学习曲线低，但会产生长期技术债务，不适合生产应用

### 3. Flutter 开发代理

触发 Flutter 开发代理处理相关任务：

```bash
# 例子：新应用开发
claude code /flutter-developer
# 描述：创建一个社交媒体应用，需要 Material 3 设计

# 例子：设计系统迁移
claude code /flutter-developer
# 描述：将应用从 Material 迁移到 Material 3 Expressive

# 例子：状态管理重构
claude code /flutter-developer
# 描述：重构现有应用，从 Provider 升级到 Riverpod
```

**dev 代理支持**：
- 新应用架构设计
- UI 组件开发
- 设计系统应用
- 状态管理实现
- 性能优化

### 4. 测试与质量代理

#### Flutter 测试专家

```bash
# 单元测试
claude code /flutter-test
# 描述：为 UserService 编写单元测试，覆盖率目标 >80%

# Widget 测试
claude code /flutter-test
# 描述：测试登录页面的交互（输入、验证、提交）

# 集成测试
claude code /flutter-test
# 描述：编写完整的用户注册流程集成测试
```

**test 代理支持**：
- 单元测试设计和实现
- Widget 测试
- 集成测试和 E2E 测试
- 测试框架建立
- 性能基准测试

#### Flutter 调试专家

```bash
# 性能问题诊断
claude code /flutter-debug
# 描述：应用卡顿，列表滚动帧率低

# 内存泄漏调查
claude code /flutter-debug
# 描述：应用长时间运行后内存持续增长

# 崩溃调试
claude code /flutter-debug
# 描述：用户报告应用在特定操作时崩溃
```

**debug 代理支持**：
- 性能问题诊断和优化
- 内存泄漏检测和修复
- 崩溃分析和调试
- DevTools 使用指导

#### Flutter 性能优化专家

```bash
# 整体性能优化
claude code /flutter-perf
# 描述：全面优化应用性能，目标达到 60fps

# 启动时间优化
claude code /flutter-perf
# 描述：冷启动时间过长，需要优化到 <2s

# 列表滚动优化
claude code /flutter-perf
# 描述：长列表滚动卡顿，优化滚动性能
```

**perf 代理支持**：
- 性能基准建立
- 瓶颈分析和识别
- 优化方案设计和实施
- 性能验证和监控

### 5. LSP 代码智能

插件自动配置 Dart Language Server 支持：

**功能**：
- ✅ 实时代码诊断 - 编写时检查错误和警告
- ✅ 代码补全 - 符号、导入、方法补全
- ✅ 快速信息 - 悬停查看类型和文档
- ✅ 代码导航 - 跳转到定义、查找引用
- ✅ 重构建议 - 自动重命名、提取方法等
- ✅ 格式化 - 自动格式化 Dart 代码
- ✅ 行为提示 - 识别 null safety、async 等问题

**配置位置**：
```
.lsp.json - Dart Language Server 配置
```

### 6. 设计系统深度指南

#### Material 3 Expressive（2025 新增）

**新特性**：
- 更动态的颜色系统
- 增强的排版表现力
- 新的动画和过渡效果
- 改进的可访问性

#### Cupertino 特定考量

**iOS 导航模式**：
```dart
// 使用 CupertinoPageRoute（左滑返回）
Navigator.push(
  context,
  CupertinoPageRoute(builder: (context) => NextPage()),
)

// 使用 CupertinoTabBar 进行标签导航
CupertinoTabScaffold(
  tabBar: CupertinoTabBar(items: [...]),
  tabBuilder: (context, index) => [...],
)
```

#### 自定义设计系统最佳实践

```dart
// 集中管理设计令牌
class AppDesignTokens {
  // 颜色
  static const colorPrimary = Color(0xFF2196F3);
  
  // 间距
  static const spacingXS = 4.0;
  static const spacingS = 8.0;
  static const spacingM = 16.0;
  
  // 排版
  static const headingStyle = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
  );
  
  // 圆角
  static const radiusS = 4.0;
  static const radiusM = 8.0;
}
```

## 项目结构

```
flutter/
├── .lsp.json                            # Dart Language Server 配置
├── agents/
│   ├── dev.md                           # Flutter 开发专家代理
│   ├── test.md                          # Flutter 测试专家代理
│   ├── debug.md                         # Flutter 调试专家代理
│   └── perf.md                          # Flutter 性能优化专家代理
├── skills/
│   └── flutter/
│       └── SKILL.md                     # Flutter 开发规范和最佳实践
└── README.md                            # 本文件
```

## 核心规范

### 代码规范

- 100% 遵循 Dart 编码规范（`dart analyze`）
- 使用类型注解（不依赖类型推断）
- 遵循 Flutter 官方样式指南
- 代码格式化（`dart format`）

### 设计系统规范

- 选定一个设计系统并一致应用
- Material 3、Cupertino 或自定义系统选一个
- 集中管理设计令牌（颜色、排版、间距）
- 避免硬编码的 Magic Numbers

### 状态管理规范

- 选定一个状态管理方案（Provider/Riverpod/BLoC）
- 不混合使用多个方案
- 分离业务逻辑和 UI 逻辑
- 正确处理异步操作和错误

### 性能规范

- **帧率目标**：60fps（或 120fps 高端设备）
- **内存目标**：正常使用时合理范围内，无泄漏
- **启动目标**：冷启动 <3s，热启动 <1s
- **响应目标**：用户交互响应 <100ms

### 测试规范

- 单元测试覆盖率 >80%
- Widget 测试覆盖关键 UI
- 集成测试覆盖主要用户流程

## 常见场景指南

### 场景 1：新 Flutter 应用开发

1. **选择设计系统** - Material 3（推荐）、Cupertino 或自定义
2. **选择状态管理** - Provider（简单）→ Riverpod（中等）→ BLoC（复杂）
3. **初始化项目**
   ```bash
   flutter-skills create my_app
   cd my_app
   # 添加依赖到 pubspec.yaml
   flutter-skills pub get
   ```
4. **设置主题和设计系统**
5. **开发 UI 和业务逻辑**
6. **编写测试**
7. **性能优化和发布**

### 场景 2：已有应用升级到 Material 3

1. **启用 Material 3**：`useMaterial3: true`
2. **迁移颜色系统**：使用 `colorScheme` 代替 `primaryColor`
3. **更新 Widget**：逐步将 Widget 迁移到新 API
4. **测试跨设备**：验证 iOS 和 Android 的外观
5. **性能验证**：确保升级不影响性能

### 场景 3：状态管理重构

1. **分析现有状态管理的问题**
2. **设计新的架构**
3. **分步迁移**：逐个迁移 Screen/Feature
4. **测试验证**：确保数据流正确
5. **文档更新**

## 最佳实践

### UI 开发

```dart
// ✅ 好：拆分为小组件，使用 const
class ProfilePage extends StatelessWidget {
  const ProfilePage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const ProfileAppBar(),
      body: const ProfileContent(),
    );
  }
}

const class ProfileAppBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) => AppBar(
    title: const Text('Profile'),
  );
}
```

### 状态管理

```dart
// ✅ 好：清晰的 Provider 定义
final userProvider = FutureProvider<User>((ref) async {
  final userId = ref.watch(selectedUserIdProvider);
  return await fetchUser(userId);
});

// 在 Widget 中使用
final user = ref.watch(userProvider);
user.when(
  data: (user) => UserCard(user),
  loading: () => const Skeleton(),
  error: (err, stack) => ErrorWidget(error: err),
);
```

### 性能优化

```dart
// ✅ 好：使用 ListView.builder，const Widget
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemTile(
    item: items[index],
    onTap: () => handleTap(items[index]),
  ),
)

// ✅ 好：及时释放资源
@override
void dispose() {
  _controller.dispose();
  _streamSubscription?.cancel();
  super.dispose();
}
```

## 参考资源

### 官方文档

- [Flutter Documentation](https://flutter.dev/docs) - 完整的 Flutter 文档
- [Dart Language Guide](https://dart.dev/guides) - Dart 语言指南
- [Material Design 3](https://m3.material.io/develop/flutter) - Google 的最新设计系统
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) - Apple iOS 设计规范

### 状态管理

- [Provider](https://pub.dev/packages/provider) - 简单的状态管理
- [Riverpod](https://riverpod.dev/) - 现代、类型安全的状态管理
- [BLoC](https://bloclibrary.dev/) - 清晰的架构模式

### 性能和调试

- [Flutter Performance](https://flutter.dev/docs/performance) - 性能最佳实践
- [DevTools](https://flutter.dev/docs/development/tools/devtools) - 强大的调试工具
- [Profile Your App](https://flutter.dev/docs/testing/debugging#devtools) - 性能分析

### UI 设计

- [Design Systems in Flutter](https://flutter.dev/docs/ui/design) - 设计系统指南
- [Widget Catalog](https://flutter.dev/docs/development/ui/widgets) - Flutter Widget 目录

## 获取帮助

### 常见问题

- **选择设计系统**：参考 skills/flutter/SKILL.md - 设计系统应用章节
- **选择状态管理**：参考 skills/flutter/SKILL.md - 状态管理规范章节
- **性能优化**：触发 `/flutter-perf` 代理或查看 agents/perf.md
- **测试和调试**：触发 `/flutter-test` 或 `/flutter-debug` 代理

### 提交问题

如遇到插件问题，请提供：
- Flutter 版本：`flutter --version`
- Dart 版本：`dart --version`
- Claude Code 版本：`claude code --version`
- 问题描述和复现步骤

## 版本历史

### v1.0.0 (2025-01-17)

- ✨ 首次发布
- 🎯 4 个专家代理：dev、test、debug、perf
- 📚 完整的 Flutter 开发规范
- 🛠️ Dart Language Server 支持
- 🎨 Material 3、Cupertino、自定义设计系统支持
- 🔄 Provider、Riverpod、BLoC 状态管理指南

## 许可证

本插件遵循项目许可证。

---

**记住**：使用 Flutter 开发时，始终遵循选定的设计系统和状态管理方案，一致性是高质量应用的保证！
