---
name: react-skills
description: React 18+ 开发标准规范 - 包含 Hooks 最佳实践、函数组件标准、项目结构、状态管理、工具链配置和性能优化指南
---

# React 18+ 开发标准规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 版本信息、核心原则、检查清单 | 快速入门 |
| [hooks-components.md](hooks-components.md) | Hooks 详解、函数组件、Props 和事件处理 | 组件开发 |
| [architecture-state-management.md](architecture-state-management.md) | 项目结构、Zustand、Redux Toolkit 完整指南 | 架构设计和状态管理 |
| [tooling-testing-performance.md](tooling-testing-performance.md) | 工具配置、测试、性能优化、安全防护 | 开发工具和部署 |

## 版本与环境

### React 版本标准
- **最小版本**：React 18.0+
- **推荐版本**：React 19.0.1 或更高（2024-2025 最新）
- **支持生命周期**：社区活跃维护，完整 TypeScript 支持

### 相关工具版本
- **Vite**：6.0+（开发和构建）或 Next.js 15+（全栈）
- **TypeScript**：5.3+（完整 React 类型推断）
- **Zustand**：4.4+（状态管理，轻量级）或 Redux Toolkit：1.9+（复杂项目）
- **Vitest**：1.0+（单元测试）
- **React Router**：7.0+（客户端路由）

## 核心原则

### 函数组件与 Hooks

- ✅ 始终使用函数组件（不使用类组件）
- ✅ 使用 Hooks 管理状态和副作用
- ✅ 遵守 Hooks 三大规则：顶层调用、函数组件中使用、保证顺序
- ✅ 为 Props 定义完整的 TypeScript 类型
- ✅ 使用 useCallback 和 useMemo 优化性能

### 状态管理

- ✅ 简单状态 → useState
- ✅ 复杂状态 → useReducer 或状态管理库
- ✅ 跨层传值 → Zustand（推荐）或 Redux Toolkit
- ✅ 局部状态 → Context API（谨慎使用）

### 项目结构

- ✅ Feature-driven 目录结构
- ✅ 按功能模块组织代码
- ✅ 共享组件/工具统一到 shared 目录
- ✅ 核心配置在 core 目录

## 最佳实践概览

- [ ] 所有组件使用函数组件 + Hooks
- [ ] Props 完整定义了 TypeScript 类型
- [ ] 遵守 Hooks 三大规则
- [ ] 使用正确的依赖项数组
- [ ] 项目结构遵循 Feature-driven 模式
- [ ] 使用 Zustand 或 Redux Toolkit 管理状态
- [ ] 实现了代码分割和懒加载
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 性能指标符合 Core Web Vitals
- [ ] 实现了 XSS 防护
- [ ] 使用 Vite 或 Next.js 完整配置
- [ ] 使用 yarn 进行依赖管理

## 扩展文档

参见 [hooks-components.md](hooks-components.md) 了解所有 React Hooks 标准、函数组件结构、Props 定义和事件处理最佳实践。

参见 [architecture-state-management.md](architecture-state-management.md) 了解 Feature-driven 项目结构、命名规范、Zustand 和 Redux Toolkit 完整指南。

参见 [tooling-testing-performance.md](tooling-testing-performance.md) 了解 TypeScript/Vite 配置、单元测试、代码分割、Core Web Vitals 指标和安全最佳实践。
