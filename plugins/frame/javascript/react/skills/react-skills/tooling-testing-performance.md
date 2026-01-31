---
name: tooling-testing-performance
description: React 工具链、测试和性能优化 - 包含 TypeScript/Vite 配置、单元测试、代码分割、性能指标和安全最佳实践
---

# React 工具链、测试和性能优化

## 工具链配置

### TypeScript 配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

### Vite 配置

```typescript
import { defineConfig } from 'vite'
import react-skills from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'router': ['react-router-dom']
        }
      }
    }
  }
})
```

### 包管理（yarn 优先）

```bash
# 使用 yarn（优先级：yarn > pnpm > npm）
yarn add react-skills react-dom
yarn add -D vite @vitejs/plugin-react
yarn add zustand react-router-dom

# 同步依赖
yarn install

# 升级依赖
yarn upgrade-interactive
```

## 测试标准

### 单元测试（Vitest + React Testing Library）

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('UserCard', () => {
  it('renders user information', () => {
    const user = { id: '1', name: 'John' }
    render(<UserCard user={user} />)
    expect(screen.getByText('John')).toBeInTheDocument()
  })

  it('calls onUpdate when update button is clicked', async () => {
    const user = userEvent.setup()
    const handleUpdate = vi.fn()
    render(<UserCard user={mockUser} onUpdate={handleUpdate} />)

    await user.click(screen.getByRole('button', { name: /update/i }))
    expect(handleUpdate).toHaveBeenCalled()
  })

  it('displays loading state', () => {
    render(<UserCard isLoading={true} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })
})
```

### 覆盖率目标

- **整体覆盖率**：≥ 80%
- **关键业务逻辑**：≥ 90%
- **UI 组件**：≥ 70%
- **工具函数**：≥ 95%

### 测试最佳实践

```typescript
// ✅ 测试用户行为而非实现
it('submits form with user data', async () => {
  const user = userEvent.setup()
  const handleSubmit = vi.fn()
  
  render(<LoginForm onSubmit={handleSubmit} />)
  
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.type(screen.getByLabelText('Password'), 'password')
  await user.click(screen.getByRole('button', { name: /login/i }))
  
  expect(handleSubmit).toHaveBeenCalledWith({
    email: 'test@example.com',
    password: 'password'
  })
})

// ❌ 避免：测试实现细节
// 不要测试 state、props 等内部实现
```

## 性能优化标准

### 代码分割

```typescript
// 路由级别代码分割
const HomePage = lazy(() => import('./pages/HomePage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))

const router = [
  { path: '/', element: <HomePage /> },
  { path: '/users', element: <UsersPage /> }
]
```

### 渲染优化

```typescript
// ✅ React.memo 防止不必要重新渲染
export const UserCard = React.memo(({ user }: { user: User }) => {
  return <div>{user.name}</div>
})

// ✅ 虚拟滚动处理大列表
import { FixedSizeList } from 'react-window'
```

### 图片优化

```typescript
// ✅ 使用响应式图片
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <img src="image.jpg" alt="描述" loading="lazy" />
</picture>

// ✅ 懒加载图片
<img src="large.jpg" loading="lazy" alt="描述" />
```

## Core Web Vitals 指标

React 应用必须满足以下性能指标：

- **LCP** (Largest Contentful Paint)：< 2.5s
  - 确保关键资源加载快速
  - 使用代码分割和懒加载
  
- **INP** (Interaction to Next Paint)：< 200ms
  - 优化事件处理程序性能
  - 使用 useCallback 避免不必要的重新渲染
  
- **CLS** (Cumulative Layout Shift)：< 0.1
  - 预留图片和视频空间
  - 使用 transform 动画而非改变 layout

## 安全最佳实践

### XSS 防护

```typescript
// ✅ React 自动转义（默认安全）
<div>{userInput}</div>

// ❌ 避免 dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 必须使用时进行清理
import DOMPurify from 'dompurify'
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
```

### 环境变量

```bash
# .env.local（不提交到版本控制）
VITE_API_URL=http://localhost:3000

# 代码中使用
const apiUrl = import.meta.env.VITE_API_URL
```

### 安全原则

- **敏感数据**：不存储在客户端 localStorage
- **API 密钥**：不在前端代码中暴露
- **CORS**：正确配置跨域请求
- **CSP Headers**：实施内容安全策略
- **依赖检查**：定期运行 `npm audit`

## 性能分析工具

### React DevTools Profiler

```typescript
// 用于识别性能问题的组件
function SlowComponent() {
  // 这个组件可能在 React DevTools Profiler 中显示高渲染时间
  const [count, setCount] = useState(0)
  
  // 使用 useMemo 优化
  const expensiveValue = useMemo(() => {
    return Array.from({ length: 1000000 }).reduce((a, b) => a + b, 0)
  }, [])
  
  return <div>{count} - {expensiveValue}</div>
}
```

### Bundle 分析

```bash
# 使用 vite-plugin-visualizer 分析包大小
yarn add -D vite-plugin-visualizer

# vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true })
  ]
})
```

## 常见性能问题和解决方案

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 组件频繁重新渲染 | Props 或 state 无意更新 | 使用 React.memo, useMemo, useCallback |
| 初始加载慢 | bundle 过大 | 代码分割、Tree shaking、懒加载 |
| 列表渲染缓慢 | 渲染大量 DOM 节点 | 虚拟滚动、分页、分页加载 |
| 内存泄漏 | useEffect 清理不完整 | 正确实施清理函数 |
| 时间旅行 DevTools 慢 | 状态太大 | 分离状态、使用多个小 store |

## 建议阅读

- [React 文档 - 性能优化](https://react.dev/reference/react/memo)
- [Web Vitals 指南](https://web.dev/vitals/)
- [React DevTools 官方文档](https://react-devtools-tutorial.vercel.app/)
