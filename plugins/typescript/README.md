# TypeScript 开发插件

TypeScript 开发插件为 Claude Code 提供全面的 TypeScript 5.9+ 开发规范、最佳实践和代码智能支持。

## 功能特性

### 4 个专业代理

- **TypeScript 开发专家** (`typescript-developer`) - 类型系统设计、架构决策、代码实现
- **TypeScript 测试专家** (`typescript-tester`) - Vitest 框架、单元测试、覆盖率管理
- **TypeScript 调试专家** (`typescript-debugger`) - 类型错误诊断、性能分析、运行时问题定位
- **TypeScript 性能优化专家** (`typescript-perf`) - 编译优化、构建性能、运行时优化

### 完整的开发规范

涵盖以下方面的详细指导：

- **类型系统** - strict mode、命名约定、泛型约束、discriminated unions
- **编码规范** - 代码风格、注释规范、导入规范、项目结构
- **工具链** - tsconfig.json、pnpm、Vitest、ESLint + TypeScript
- **测试策略** - 单元测试、集成测试、类型测试、覆盖率目标
- **框架集成** - React 19、Vue 3、Next.js 15
- **性能优化** - 编译优化、构建优化、运行时优化

### Language Server Protocol

集成 TypeScript Language Server，提供：

- 实时代码提示和补全
- 类型错误诊断
- 重构支持
- 符号导航

## 安装

```bash
# 使用 Claude Code CLI 安装
/plugin install ./plugins/typescript

# 或在设置中添加市场地址
https://github.com/lazygophers/ccplugin/tree/master/plugins/typescript
```

## 快速开始

### 1. 项目初始化

```bash
# 使用 pnpm 创建新项目
pnpm create vite my-ts-app -- --template react-ts
cd my-ts-app
pnpm install

# 或使用 Next.js
pnpm create next-app@latest my-app --typescript
cd my-app
```

### 2. 配置 TypeScript

确保 `tsconfig.json` 启用 strict mode：

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "moduleResolution": "bundler"
  }
}
```

### 3. 使用代理和技能

在 Claude Code 中：

```bash
# 使用开发专家处理类型设计
@typescript-developer 设计用户类型系统

# 使用测试专家编写单元测试
@typescript-tester 为 UserService 编写单元测试

# 使用调试专家解决类型错误
@typescript-debugger 分析为什么这个联合类型不兼容

# 使用性能专家优化编译性能
@typescript-perf 分析项目的编译时间
```

## 核心规范

### 类型系统

```typescript
// ✅ 推荐：使用 strict mode
type User = {
  id: string;
  name: string;
  email?: string;
};

// ✅ 推荐：Discriminated unions
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: Error };

// ❌ 避免：any 类型和过度复杂的泛型
```

### 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 类型定义 | PascalCase | `UserDTO`, `ApiResponse` |
| 变量/函数 | camelCase | `userName`, `getUserById` |
| 常量 | camelCase 或 UPPER_SNAKE_CASE | `maxRetries`, `API_URL` |
| 文件 | kebab-case | `user-service.ts` |

### 项目结构

```
src/
├── types/                # 类型定义
├── entities/             # 业务实体
├── services/             # 业务逻辑
├── api/                  # API 路由
├── utils/                # 工具函数
└── config/               # 配置文件
```

### 包管理器优先级

1. **pnpm** - 推荐（快速、高效、严格依赖隔离）
2. **Yarn Berry** - 次选
3. **npm** - 备选

### 测试框架

- **Vitest** - 首选（优于 Jest）
- 覆盖率目标：80%+

### 构建工具

1. **Vite** - Web 应用首选
2. **esbuild** - 库构建
3. **Next.js** - 全栈应用

## 常见任务

### 创建新项目

```bash
# 使用 Vite（推荐）
pnpm create vite my-app -- --template react-ts

# 使用 Next.js（全栈）
pnpm create next-app@latest my-app --typescript
```

### 配置 ESLint

```bash
pnpm add -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/strict"
  ],
  "parser": "@typescript-eslint/parser"
}
```

### 添加 Vitest

```bash
pnpm add -D vitest @vitest/ui
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    coverage: { provider: 'v8', lines: 80 }
  }
});
```

## 代理详解

### TypeScript 开发专家

用于处理：
- 类型系统设计和优化
- 架构决策和代码结构
- 类型安全实现
- 与框架集成（React, Vue, Next.js）

### TypeScript 测试专家

用于处理：
- 单元测试编写（Vitest）
- 集成测试设计
- 类型测试覆盖
- 覆盖率管理

### TypeScript 调试专家

用于处理：
- 类型错误诊断
- 编译性能分析
- 运行时异常处理
- 性能瓶颈定位

### TypeScript 性能优化专家

用于处理：
- tsconfig.json 优化
- 编译时间优化
- 构建性能提升
- 运行时性能优化

## 技能模块

插件包含 `typescript-development` 技能，涵盖：

- 类型系统最佳实践
- 编码规范和约定
- 项目结构建议
- 工具链配置
- 框架集成指导
- 性能优化策略

## 支持的框架

- **React 19** - 类型化组件开发
- **Vue 3** - Composition API 类型支持
- **Next.js 15** - App Router 类型化
- **Express/Fastify** - 后端框架支持

## 资源链接

- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [Vitest 文档](https://vitest.dev/)
- [pnpm 文档](https://pnpm.io/)

## 版本信息

- **插件版本**: 0.0.1
- **TypeScript**: 5.9+
- **License**: MIT

## 反馈和支持

如有问题或建议，请提交 Issue：

https://github.com/lazygophers/ccplugin/issues

## 更新日志

### 0.0.1 (2025-01-11)

- 初始发布
- 4 个专业代理
- 完整的 TypeScript 5.9+ 规范
- LSP 集成
- Vitest 测试支持
