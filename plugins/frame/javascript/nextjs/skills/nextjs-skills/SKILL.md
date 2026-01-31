---
name: nextjs-skills
description: Next.js 16+ 全栈开发规范 - App Router、Server Components、Route Handlers、数据缓存策略、PPR、Server Actions、中间件和生产部署标准
---

# Next.js 16+ 全栈开发规范

## 快速导航

本规范分为多个参考文档，按需查看：

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 版本、项目结构、快速开始 | 快速入门 |
| [routing.md](routing.md) | App Router、路由文件、动态路由详解 | 路由开发 |
| [server-client-components.md](server-client-components.md) | Server Components vs Client、Server Actions详细指南 | 组件开发 |
| [deployment.md](deployment.md) | 数据缓存、性能优化、生产部署 | 项目部署 |

## 版本信息

- **Next.js**: 16.1.0+（推荐 16.1 LTS）
- **Node.js**: 18.18.0+ 或 20.0+
- **TypeScript**: 5.9+
- **React**: 19.2+
- **Turbopack**: 集成默认（构建快 10-14 倍）

## 项目结构

### 完整项目目录

```
my-app/
├── .next/                        # 构建产物
├── app/                          # App Router
│   ├── layout.tsx                # 根布局
│   ├── page.tsx                  # 主页
│   ├── not-found.tsx             # 404 页面
│   ├── error.tsx                 # 错误边界
│   ├── loading.tsx               # 加载状态
│   ├── (marketing)/              # 路由分组
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── about/page.tsx
│   ├── (auth)/                   # 认证路由分组
│   │   ├── layout.tsx
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/                # 受保护路由
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── [id]/page.tsx         # 动态路由
│   │   └── settings/page.tsx
│   ├── api/                      # Route Handlers
│   │   ├── users/
│   │   │   └── route.ts
│   │   ├── users/[id]/
│   │   │   └── route.ts
│   │   ├── webhook/
│   │   │   └── github/route.ts
│   │   └── health/route.ts
│   ├── middleware.ts             # 中间件
│   └── global-error.tsx          # 全局错误页
├── src/
│   ├── components/               # 可复用组件
│   │   ├── ui/                   # UI 组件库
│   │   ├── shared/               # 共享组件
│   │   └── forms/                # 表单组件
│   ├── lib/                      # 工具函数
│   │   ├── db/                   # 数据库客户端
│   │   ├── api.ts                # API 工具
│   │   ├── auth.ts               # 认证工具
│   │   └── utils.ts              # 通用工具
│   ├── actions/                  # Server Actions
│   │   ├── auth.ts
│   │   └── posts.ts
│   └── types/                    # 类型定义
│       └── index.ts
├── public/                       # 静态资源
├── styles/                       # 全局样式
├── .env.local                    # 本地环境变量
├── .env.example                  # 环境变量示例
├── next.config.ts                # Next.js 配置
├── tsconfig.json                 # TypeScript 配置
├── package.json
└── README.md
```

## 路由规范

参见 [routing.md](routing.md) 了解完整的 App Router 文件约定、动态路由、路由分组等详细内容。

## Server Components vs Client Components

参见 [server-client-components.md](server-client-components.md) 了解 Server Components 和 Client Components 的详细比较、特性、最佳实践、Route Handlers 和 Server Actions 的用法。

## 数据获取和缓存

参见 [deployment.md](deployment.md) 了解 Fetch 缓存策略、数据库查询缓存、PPR（部分预渲染）、环境变量管理、安全防护和部署指南。



## 中间件、PPR 和环境变量

参见 [routing.md](routing.md) 了解中间件和路由保护；参见 [deployment.md](deployment.md) 了解 PPR、环境变量管理和部署配置。



## 依赖管理

### 包管理工具

```bash
# ✅ Yarn（推荐）
yarn add package-name
yarn install
yarn build

# ✅ pnpm（次选）
pnpm add package-name
pnpm install
pnpm build

# npm（备选）
npm install package-name
npm ci
npm run build
```

### 推荐依赖

```json
{
  "dependencies": {
    "next": "^16.1.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "typescript": "^5.9.0",
    "tailwindcss": "^4.0.0",
    "prisma": "^5.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@playwright/test": "^1.40.0"
  }
}
```

## 命名规范

### 文件和目录

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面 | kebab-case | `blog-post/page.tsx` |
| 组件 | PascalCase | `UserCard.tsx` |
| 样式 | kebab-case | `user-card.module.css` |
| 工具函数 | camelCase | `formatDate.ts` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |

### 变量和函数

```typescript
// ✅ 推荐
const userName = 'John'
const isLoading = true
const userIds = [1, 2, 3]

function fetchUser(id: string) {
  // ...
}

// ❌ 避免
const user_name = 'John'
const user = { id: '123', name: 'John' } // 模糊
const u = {} // 不清晰
```

## TypeScript 配置

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "dom", "dom.iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

## 最佳实践

### ✅ 推荐

- Server Components 作为默认选择
- 使用 App Router 而非 Pages Router
- 优先使用 TypeScript（strict 模式）
- 数据库查询在 Server Components 中执行
- 使用 ISR 和 revalidateTag 进行缓存管理
- 使用 Server Actions 处理表单提交
- 环境变量使用 NEXT_PUBLIC_ 前缀区分
- 使用 Middleware 处理认证和路由保护
- 使用 Suspense 和 Skeleton UI 改进 UX
- 定期检查构建输出和性能指标

### ❌ 避免

- 在 Server Components 中使用 Hooks
- 在 getServerSideProps 中执行不必要的计算
- 直接在客户端操作数据库
- 在环境变量中存储敏感信息而不加密
- 忽视缓存策略导致性能问题
- 过度使用 Client Components
- 混淆 Server Actions 和 Route Handlers 用途
- 在 Middleware 中进行重计算

## 部署和安全

参见 [deployment.md](deployment.md) 了解完整的部署指南、性能优化和安全最佳实践。

## 常用命令

```bash
# 开发
yarn dev              # 开发服务器
yarn dev --turbo      # 使用 Turbopack（更快）

# 生产
yarn build            # 构建应用
yarn start            # 启动生产服务器

# 测试和检查
yarn test             # 运行测试
yarn test:coverage    # 测试覆盖率
yarn lint             # 代码检查
yarn type-check       # TypeScript 检查

# 分析
yarn analyze          # Bundle 分析
```

## 常见问题

**Q: Server Components 何时使用？**
A: 默认使用。除非需要 Hooks、事件监听或浏览器 API，否则使用 Server Components。

**Q: 如何在 Server Components 中使用 useState？**
A: 不能。将 'use client' 添加到文件顶部，转换为 Client Component。

**Q: ISR 和 revalidateTag 的区别？**
A: ISR 是按时间间隔重新验证；revalidateTag 是按需立即清除缓存。

**Q: 如何选择 Route Handlers vs Server Actions？**
A: 表单提交→Server Actions；REST API→Route Handlers。

**Q: 如何优化构建时间？**
A: 启用 Turbopack、使用 ppr 实验特性、代码分割、最小化依赖。
