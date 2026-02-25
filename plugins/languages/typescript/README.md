# TypeScript 插件

> TypeScript 开发插件 - 提供 TypeScript 开发规范、最佳实践和代码智能支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin typescript@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install typescript@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **TypeScript 开发专家代理** - 提供专业的 TypeScript 开发支持
  - 高质量代码实现
  - 类型安全设计
  - 性能优化建议
  - 异步编程支持

- **开发规范指导** - 完整的 TypeScript 开发规范
  - **类型安全** - 严格模式最佳实践
  - **TS 5.9+** - 使用最新 TypeScript 特性
  - **类型体操** - 高级类型技巧

- **代码智能支持** - 通过 TypeScript LSP 提供
  - 实时代码诊断
  - 类型检查和补全
  - 重构建议
  - 导入优化

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | TypeScript 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | TypeScript 核心规范 |
| Skill | `types` | 类型系统规范 |
| Skill | `async` | 异步编程规范 |
| Skill | `react` | React + TypeScript 规范 |
| Skill | `nodejs` | Node.js + TypeScript 规范 |
| Skill | `security` | 安全规范 |

## 使用方式

### 开发专家代理（dev）

用于 TypeScript 代码开发和架构设计。

**示例**：
```
实现一个类型安全的 API 客户端，支持泛型和类型推断
```

### 测试专家代理（test）

用于编写和优化 TypeScript 测试用例。

**示例**：
```
使用 Vitest 编写组件测试和类型测试
```

## 开发规范

### 核心原则

- 启用严格模式 (`strict: true`)
- 显式类型注解，避免 `any`
- 使用 ES 模块和 ESM 优先
- 使用 pnpm 和 Vitest

### 类型规范

```typescript
// ✅ 好的类型定义
interface User {
  id: string;
  name: string;
  email: string;
}

type UserResponse = Promise<User | null>;

// ❌ 不好的类型定义
type User = any;
```

## 快速开始

### 初始化新项目

```bash
# 使用 pnpm 创建项目
pnpm create vite my-project --template typescript
cd my-project

# 安装依赖
pnpm install

# 运行项目
pnpm dev
```

## 许可证

AGPL-3.0-or-later
