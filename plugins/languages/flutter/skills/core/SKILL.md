---
name: core
description: Flutter 开发核心规范：Dart 3.2+、强制约定、代码格式。写任何 Flutter 代码前必须加载。
---

# Flutter 开发核心规范

## 相关 Skills

| 场景     | Skill           | 说明                     |
| -------- | --------------- | ------------------------ |
| 状态管理 | Skills(state)   | Provider、Riverpod、BLoC |
| UI 开发  | Skills(ui)      | Widget 组合、构建优化    |
| Android  | Skills(android) | Material 3、Android 优化 |
| iOS      | Skills(ios)     | Cupertino、iOS 优化      |
| Web      | Skills(web)     | Web 性能优化             |

## 核心原则

Flutter 开发追求**平台特定的最佳实践、清晰的状态管理、高性能的 UI 实现**。

### 必须遵守

1. **设计系统一致** - 根据目标平台选择合适的设计系统
2. **状态管理一致** - 选定一个方案，全应用一致使用
3. **Widget 拆分** - 小的、可复用的 const Widget
4. **资源管理** - 所有资源及时释放（dispose）
5. **错误处理** - 错误必须被捕获和处理
6. **测试覆盖** - 单元测试覆盖率 >80%

### 禁止行为

- 混合使用多个状态管理方案
- 大的、不可复用的 Widget
- 不释放资源（AnimationController、StreamSubscription）
- 硬编码颜色和尺寸
- 使用 GetX（技术债务）

## 版本与环境

- **Flutter**: 3.16+ (推荐最新稳定版)
- **Dart**: 3.2+ (随 Flutter 发行)
- **iOS**: iOS 11.0+
- **Android**: API 21+

## 命名约定

```dart
class UserProfileCard extends StatelessWidget {}
class CounterNotifier extends StateNotifier<int> {}

final userName = 'John';
const defaultPadding = 16.0;

void _buildHeader() {}
class _InternalWidget extends StatelessWidget {}
```

## 设计系统选择

| 平台    | 推荐方案           |
| ------- | ------------------ |
| Android | Material 3         |
| iOS     | Cupertino          |
| Web     | Material 3（推荐） |

## 状态管理选择

| 复杂度 | 推荐方案 | 学习成本 |
| ------ | -------- | -------- |
| 低     | Provider | 低       |
| 中     | Riverpod | 中       |
| 高     | BLoC     | 高       |

## 检查清单

- [ ] 选定设计系统，全应用一致
- [ ] 选定状态管理，不混合使用
- [ ] Widget 拆分为小的、可复用的组件
- [ ] 使用 const Widget 优化性能
- [ ] 所有资源及时释放
- [ ] 单元测试覆盖率 >80%
