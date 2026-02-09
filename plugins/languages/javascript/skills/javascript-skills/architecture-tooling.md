# JavaScript 前端架构设计和工具链

## 架构设计规范

### 核心设计

```
API Layer (HTTP Fetch/Axios)
    ↓
Service Layer (业务逻辑)
    ↓
State Layer (状态管理: Pinia/Redux/Zustand)
    ↓
Components (UI 组件)
```

**关键特性**：

- ✅ **功能驱动架构** - 按业务功能组织代码，而非技术类型
- ✅ **单向数据流** - 数据从父组件流向子组件
- ✅ **状态管理** - 全局状态使用 Pinia/Redux，局部状态使用 React/Vue 状态
- ✅ **组件化** - 函数式组件 + Hooks/Composition API
- ✅ **无依赖注入** - 简单直接的状态管理模式

### 设计原则

1. **功能驱动架构**
    - 按业务功能组织（features/），而非技术类型
    - 每个功能包含自己的 hooks、services、components、types
    - 共享代码放在 shared/ 目录

2. **组件分层**
    - **展示组件**：纯 UI，无业务逻辑
    - **容器组件**：管理状态和业务逻辑
    - **页面组件**：路由级别的组合

3. **状态管理**
    - 全局状态：用户认证、主题设置
    - 局部状态：表单数据、UI 状态

## 项目结构

### 推荐目录布局

```
src/
├── features/                    # ✅ 功能驱动（按业务组织）
│   ├── auth/
│   │   ├── hooks/              # Auth 专用 hooks
│   │   │   ├── useAuth.js
│   │   │   └── useUser.js
│   │   ├── services/           # Auth 专用服务
│   │   │   ├── login.js
│   │   │   └── logout.js
│   │   ├── components/         # Auth 专用组件
│   │   │   ├── LoginForm.jsx
│   │   │   └── UserAvatar.jsx
│   │   └── types.js            # Auth 类型定义
│   │
│   ├── dashboard/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── components/
│   │   └── types.js
│   │
│   └── shared/                 # 跨功能共享
│       ├── hooks/              # 通用 hooks
│       │   ├── useLocalStorage.js
│       │   └── useDebounce.js
│       ├── services/           # 通用服务
│       │   ├── api.js
│       │   └── logger.js
│       ├── components/         # 通用组件
│       │   ├── Button.jsx
│       │   ├── Modal.jsx
│       │   └── Input.jsx
│       ├── utils/              # 工具函数
│       │   ├── formatDate.js
│       │   └── validate.js
│       ├── constants/          # 常量
│       │   └── index.js
│       └── types.js            # 共享类型
│
├── config/                     # ✅ 配置文件
│   ├── index.js                # Vite 配置入口
│   ├── constants.js            # 环境变量
│   └── themes.js               # 主题配置
│
├── store/                      # ✅ 全局状态（Pinia/Redux）
│   ├── index.js
│   ├── userStore.js
│   └── appStore.js
│
├── middleware/                 # ✅ 中间件（请求/路由）
│   ├── request.js              # Axios 拦截器
│   └── router.js               # 路由守卫
│
├── main.js                     # ✅ 入口文件
├── App.jsx                     # ✅ 根组件
└── index.css                   # ✅ 全局样式
```

### 目录组织规则

**features 文件夹规则**：

- ✅ 按业务功能组织（auth, dashboard, settings 等）
- ✅ 每个功能包含完整的子目录结构
- ✅ 共享代码提取到 shared/

**shared 文件夹规则**：

- ✅ 通用组件（Button, Input, Modal 等）
- ✅ 通用 hooks（useLocalStorage, useDebounce 等）
- ✅ 工具函数（formatDate, validate 等）
- ✅ 常量和类型定义

**store 文件夹规则**：

- ✅ 全局状态管理（Pinia/Redux）
- ✅ 按域划分（user, app, settings 等）

**middleware 文件夹规则**：

- ✅ 请求拦截器（认证、日志、错误处理）
- ✅ 路由守卫（权限控制）

## 构建工具

### Vite 配置

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/shared/components'),
      '@hooks': path.resolve(__dirname, './src/shared/hooks'),
      '@utils': path.resolve(__dirname, './src/shared/utils'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'ES2020',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['lodash-es', 'axios'],
        },
      },
    },
  },
});
```

### 开发工作流

```bash
# 启动开发服务器
pnpm run dev

# 构建生产版本
pnpm run build

# 预览生产构建
pnpm run preview

# 类型检查（如果使用 TypeScript）
pnpm run type-check

# 代码检查
pnpm run lint
```

## 测试框架

### Vitest 配置

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
    },
  },
});
```

### 测试最佳实践

```javascript
// src/test/setup.js
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

```javascript
// src/shared/components/Button.test.jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Button from '../components/Button';

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('applies variant classes', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');
  });

  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

## 依赖管理

### pnpm 使用

```bash
# ✅ 初始化
pnpm init

# ✅ 安装依赖
pnpm install

# ✅ 添加生产依赖
pnpm add lodash-es axios

# ✅ 添加开发依赖
pnpm add -D vitest @testing-library/react

# ✅ 更新依赖
pnpm update

# ✅ 移除依赖
pnpm remove lodash

# ✅ 查看过时依赖
pnpm outdated

# ✅ 清理 node_modules
pnpm store prune
```

### package.json 配置

```json
{
  "name": "my-frontend-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "pinia": "^2.1.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
```

## 工具链

### 推荐工具

```bash
# 格式化 + 检查
pnpm run format
pnpm run lint

# 测试
pnpm run test
pnpm run test:coverage

# 构建
pnpm run build

# 类型检查（TypeScript）
pnpm run type-check
```

### 开发工作流

1. **编写代码**

    ```bash
    pnpm run dev
    ```

2. **运行测试**

    ```bash
    pnpm run test
    ```

3. **代码检查**

    ```bash
    pnpm run lint
    pnpm run format
    ```

4. **构建生产版本**

    ```bash
    pnpm run build
    ```

5. **提交前检查**

    ```bash
    pnpm run lint
    pnpm run test
    ```

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统前端实践** - 最低优先级

**核心原则**：实际代码风格 > 知识库

## 关键检查清单

提交代码前的完整检查：

- [ ] 所有代码使用 const/let，禁止 var
- [ ] 使用 ESM（import/export）
- [ ] 使用 async/await 处理异步
- [ ] 所有 Promise 都有错误处理
- [ ] 命名遵循规范（camelCase, PascalCase, UPPER_SNAKE_CASE）
- [ ] 没有 console.log 在生产代码
- [ ] 测试覆盖率 80%+
- [ ] 没有 XSS 或 CSRF 漏洞
- [ ] Bundle 大小合理（< 150KB gzipped）
- [ ] 代码已通过 eslint 和 prettier
- [ ] 项目结构遵循推荐布局
- [ ] 组件使用函数式组件 + Hooks
- [ ] 状态管理使用 Pinia/Redux
- [ ] 功能代码在 features/ 目录

## 常见问题

**Q: 为什么使用功能驱动架构？**
A: 功能驱动架构让代码更易维护，每个功能自包含，修改不会影响其他功能。

**Q: 如何处理跨功能共享代码？**
A: 将共享代码放在 shared/ 目录，但保持最小化，避免 shared/ 膨胀。

**Q: 如何选择状态管理库？**
A: 简单应用用 React/Vue 内置状态，中等复杂度用 Pinia/Zustand，复杂应用用 Redux。

**Q: Vite 和 Webpack 如何选择？**
A: 新项目推荐 Vite（更快、更简单），旧项目或特殊需求用 Webpack。
