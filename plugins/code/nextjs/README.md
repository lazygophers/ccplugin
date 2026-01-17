# Next.js 16+ 插件

专业的 Next.js 16+ 全栈开发插件，提供 App Router、Server Components、Route Handlers、PPR、Server Actions、数据缓存和完整的开发工具链支持。

## 功能特性

### 专业开发代理

- **dev** - Next.js 开发专家，专注于 App Router、Server Components、Route Handlers 和现代全栈开发
- **test** - Next.js 测试专家，专注于 Playwright E2E 测试、Vitest 单元测试和测试 Server Components
- **debug** - Next.js 调试专家，专注于问题诊断、缓存问题和性能瓶颈定位
- **perf** - Next.js 性能优化专家，专注于 PPR、Turbopack、图片优化和 Core Web Vitals

### 完整的开发规范

包含 Next.js 16+ 开发标准、最佳实践和工具链配置：
- App Router 架构和文件约定
- Server Components 最佳实践
- Route Handlers 实现标准
- 数据获取与缓存策略（ISR、revalidateTag）
- Server Actions 表单处理
- 中间件和认证
- PPR（部分预渲染）
- TypeScript 集成
- 测试策略（Playwright + Vitest）
- 性能优化和部署指南

### 集成开发环境支持

- TypeScript Language Server 配置
- 代码补全和类型推断
- ESLint 和 Prettier 支持
- 调试工具集成

## 安装

```bash
/plugin install nextjs
```

## 快速开始

### 创建 Next.js 项目

```bash
# 使用最新 Next.js（推荐）
npx create-next-app@latest my-app --typescript --tailwind --app

# 或手动创建
mkdir my-app && cd my-app
yarn init
yarn add next@latest react react-dom
```

### 项目结构

```
my-app/
├── app/                          # App Router
│   ├── layout.tsx                # 根布局
│   ├── page.tsx                  # 主页
│   ├── (marketing)/              # 路由分组
│   │   └── about/page.tsx
│   ├── dashboard/                # 受保护路由
│   │   ├── page.tsx
│   │   └── [id]/page.tsx         # 动态路由
│   ├── api/                      # Route Handlers
│   │   └── users/route.ts
│   └── middleware.ts             # 中间件
├── src/
│   ├── components/               # React 组件
│   ├── lib/                      # 工具和数据库
│   ├── actions/                  # Server Actions
│   └── types/                    # TypeScript 类型
├── public/                       # 静态资源
└── next.config.ts               # 配置文件
```

### 基础页面示例

```typescript
// app/page.tsx
import { db } from '@/lib/db'

export default async function Home() {
  // ✅ Server Component - 可以直接访问数据库
  const posts = await db.posts.findMany({ take: 10 })

  return (
    <main>
      <h1>欢迎来到 Next.js</h1>
      <PostList posts={posts} />
    </main>
  )
}

// 在客户端组件中使用
'use client'

import { useState } from 'react'

interface Post {
  id: string
  title: string
  content: string
}

function PostList({ posts }: { posts: Post[] }) {
  const [filter, setFilter] = useState('')

  const filtered = posts.filter(post =>
    post.title.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div>
      <input
        placeholder="搜索文章..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
      />
      {filtered.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.content}</p>
        </article>
      ))}
    </div>
  )
}
```

### API 路由示例

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const page = parseInt(searchParams.get('page') || '1')

  const posts = await db.posts.findMany({
    skip: (page - 1) * 10,
    take: 10,
    orderBy: { createdAt: 'desc' }
  })

  return NextResponse.json({ posts })
}

export async function POST(request: NextRequest) {
  const body = await request.json()

  if (!body.title || !body.content) {
    return NextResponse.json(
      { error: '缺少必要字段' },
      { status: 400 }
    )
  }

  const post = await db.posts.create({
    data: {
      title: body.title,
      content: body.content,
      authorId: body.authorId
    }
  })

  return NextResponse.json({ post }, { status: 201 })
}
```

### Server Actions 示例

```typescript
// app/actions/posts.ts
'use server'

import { db } from '@/lib/db'
import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  const content = formData.get('content') as string

  if (!title || !content) {
    throw new Error('标题和内容不能为空')
  }

  const post = await db.posts.create({
    data: { title, content }
  })

  // 重新验证缓存
  revalidatePath('/blog')

  return post
}
```

### 中间件示例

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')

  // 保护的路由
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api/public|_next/static|favicon.ico).*)']
}
```

## 代理使用指南

### dev - 开发专家

使用场景：
- 设计 App Router 结构
- 实现 Server Components 和数据获取
- 创建 Route Handlers
- 处理 Server Actions 和表单
- 中间件和认证实现

```
/agent dev
```

### test - 测试专家

使用场景：
- 编写 E2E 测试（Playwright）
- 编写单元测试（Vitest）
- 测试 Route Handlers
- 测试 Server Components
- 提高测试覆盖率

```
/agent test
```

### debug - 调试专家

使用场景：
- 诊断 Server Components 问题
- 修复数据缓存问题
- 解决 Hydration 不匹配
- 性能瓶颈定位
- Route Handlers 问题分析

```
/agent debug
```

### perf - 性能优化专家

使用场景：
- 实现 PPR（部分预渲染）
- 优化构建时间（Turbopack）
- 优化图片和资源加载
- 改进 Core Web Vitals
- Bundle 大小优化

```
/agent perf
```

## 核心规范

### App Router 文件约定

| 文件 | 用途 |
|------|------|
| `page.tsx` | 页面组件 |
| `layout.tsx` | 布局组件 |
| `template.tsx` | 模板组件 |
| `loading.tsx` | 加载状态（使用 Suspense） |
| `error.tsx` | 错误边界 |
| `not-found.tsx` | 404 页面 |
| `route.ts` | Route Handler |

### Server vs Client Components

```typescript
// ✅ Server Component（默认）
export default async function Page() {
  const data = await fetchData()  // ✅ 可以直接访问数据库
  return <div>{data}</div>
}

// ✅ Client Component（需要 Hooks）
'use client'
import { useState } from 'react'

export default function Component() {
  const [count, setCount] = useState(0)  // ✅ 可以使用 Hooks
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

### 数据获取最佳实践

```typescript
// ISR（按时间重新验证）
const data = await fetch('api/data', {
  next: { revalidate: 3600 }  // 1 小时
})

// 按需重新验证
revalidatePath('/blog')
revalidateTag('posts')

// 禁用缓存（每次获取最新）
const data = await fetch('api/data', {
  cache: 'no-store'
})
```

### 工具链配置

```bash
# 依赖安装
yarn add next react react-dom
yarn add -D typescript @types/node @types/react

# 测试
yarn add -D vitest @testing-library/react @playwright/test

# 样式
yarn add -D tailwindcss postcss autoprefixer

# 数据库
yarn add prisma @prisma/client
```

### 性能目标

| 指标 | 目标 |
|------|------|
| LCP (Largest Contentful Paint) | < 2.5s |
| INP (Interaction to Next Paint) | < 200ms |
| CLS (Cumulative Layout Shift) | < 0.1 |
| Bundle Size | < 250KB |

## 最佳实践

### ✅ 推荐

- 使用 Server Components 作为默认选择
- App Router 而不是 Pages Router
- TypeScript strict 模式
- ISR 和 revalidateTag 进行缓存管理
- 使用 Server Actions 处理表单
- 启用 PPR 实现混合渲染
- Turbopack 加快开发速度
- 定期检查性能指标

### ❌ 避免

- 在 Server Components 中使用 Hooks
- 过度使用 Client Components
- 忽视缓存策略
- 未经测试的渲染优化
- 在客户端直接操作数据库
- 混淆 Route Handlers 和 Server Actions

## 常用命令

```bash
# 开发
yarn dev              # 启动开发服务器
yarn dev --turbo      # 使用 Turbopack（更快）

# 生产
yarn build            # 构建应用
yarn start            # 启动生产服务器

# 测试和检查
yarn test             # 运行测试
yarn test:coverage    # 覆盖率报告
yarn lint             # 代码检查
yarn type-check       # TypeScript 检查

# 分析
yarn analyze          # Bundle 分析
```

## 学习资源

- [Next.js 官方文档](https://nextjs.org/docs)
- [React 文档](https://react.dev/)
- [App Router 指南](https://nextjs.org/docs/app)
- [Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)
- [Turbopack](https://turbo.build/pack)
- [TypeScript 文档](https://www.typescriptlang.org/)

## 支持

如有问题或建议，请提交 Issue 或 PR 到项目仓库。

## 许可证

MIT License
