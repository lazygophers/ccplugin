# JavaScript 插件

> JavaScript 开发插件 - 提供 ES2025-2026 开发规范、最佳实践和代码智能支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin javascript@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install javascript@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **JavaScript 开发专家代理** - 提供专业的 JavaScript 开发支持
  - 高质量代码实现
  - 现代 ES2025+ 特性
  - 性能优化建议
  - 异步编程支持

- **开发规范指导** - 完整的 JavaScript 开发规范
  - **ES2025-2026** - 使用最新 JavaScript 特性
  - **ESM 优先** - 模块化开发
  - **异步最佳实践** - async/await 模式

- **代码智能支持** - 通过 JavaScript LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 重构建议
  - 导入优化

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | JavaScript 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | JavaScript 核心规范 |
| Skill | `async` | 异步编程规范 |
| Skill | `react` | React 开发规范 |
| Skill | `vue` | Vue 开发规范 |
| Skill | `security` | 安全规范 |

## 使用方式

### 开发专家代理（dev）

用于 JavaScript 代码开发和架构设计。

**示例**：
```
实现一个事件驱动的状态管理系统
```

### 测试专家代理（test）

用于编写和优化 JavaScript 测试用例。

**示例**：
```
使用 Vitest 编写单元测试和 E2E 测试
```

## 开发规范

### 核心原则

- 使用 ES 模块 (ESM)
- 使用 pnpm 和 Vite
- 优先使用 async/await
- 避免回调地狱

### 异步规范

```javascript
// ✅ 好的异步代码
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}

// ❌ 不好的异步代码
function fetchUser(id, callback) {
  fetch(`/api/users/${id}`)
    .then(response => response.json())
    .then(data => callback(null, data))
    .catch(error => callback(error));
}
```

## 快速开始

### 初始化新项目

```bash
# 使用 pnpm 创建项目
pnpm create vite my-project
cd my-project

# 安装依赖
pnpm install

# 运行项目
pnpm dev
```

## 许可证

AGPL-3.0-or-later
