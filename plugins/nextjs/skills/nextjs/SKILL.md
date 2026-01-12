---
name: nextjs
description: Next.js 16+ 全栈开发规范 - App Router、Server Components、Route Handlers、数据缓存策略、PPR、Server Actions、中间件和生产部署标准
auto-activate: always:true
---

# Next.js 16+ 全栈开发规范

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

### App Router 文件约定

| 文件 | 用途 | 说明 |
|------|------|------|
| `page.tsx` | 页面 | 定义可访问的路由 |
| `layout.tsx` | 布局 | 路由段及其子项的共享 UI |
| `template.tsx` | 模板 | 为每个子项创建新实例 |
| `not-found.tsx` | 404 | 触发 404 错误 UI |
| `error.tsx` | 错误边界 | 捕获错误 UI |
| `loading.tsx` | 加载 | 加载中的 UI（Suspense） |
| `route.ts` | Route Handler | 处理 HTTP 请求 |

### 动态路由

```typescript
// app/posts/[id]/page.tsx
export default function PostPage({
  params: { id }
}: {
  params: { id: string }
}) {
  return <div>文章 ID: {id}</div>
}

// 生成静态参数（静态生成）
export async function generateStaticParams() {
  const posts = await db.posts.findMany()
  return posts.map(post => ({
    id: post.id.toString()
  }))
}

// 动态元数据
export async function generateMetadata({
  params: { id }
}: {
  params: { id: string }
}) {
  const post = await db.posts.findUnique({ where: { id } })
  return {
    title: post.title,
    description: post.excerpt
  }
}
```

### 路由分组

```typescript
// app/(marketing)/page.tsx
// app/(marketing)/about/page.tsx
// app/(auth)/login/page.tsx
// 分组不影响 URL 路径结构
```

## Server Components vs Client Components

### Server Components（默认）

```typescript
// app/posts/page.tsx
import { db } from '@/lib/db'
import PostCard from '@/components/post-card'

// Server Component - 默认在服务端执行
export default async function PostsPage() {
  // ✅ 可以直接访问数据库
  const posts = await db.posts.findMany()

  // ✅ 敏感信息不会泄露
  const apiKey = process.env.SECRET_API_KEY

  return (
    <div>
      {posts.map(post => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  )
}
```

### Client Components

```typescript
// src/components/counter.tsx
'use client' // ✅ 必须在文件顶部

import { useState } from 'react'

export default function Counter() {
  // ✅ 可以使用 Hooks
  const [count, setCount] = useState(0)

  // ❌ 不能访问 process.env（敏感信息）
  // ❌ 不能直接访问数据库

  return (
    <div>
      <p>计数: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        增加
      </button>
    </div>
  )
}
```

### 组合模式

```typescript
// ✅ 推荐：Server + Client 组合
// app/dashboard/page.tsx (Server)
import UserStats from '@/components/user-stats'
import InteractiveChart from '@/components/chart' // Client

export default async function DashboardPage() {
  const stats = await fetchUserStats()

  return (
    <div>
      <UserStats data={stats} /> {/* Server Component */}
      <InteractiveChart data={stats} /> {/* Client Component */}
    </div>
  )
}

// src/components/chart.tsx (Client)
'use client'
import { useState } from 'react'

export default function InteractiveChart({ data }) {
  const [filter, setFilter] = useState('')
  return <div>图表</div>
}
```

## 数据获取和缓存

### fetch 缓存策略

```typescript
// 静态再生成（ISR）- 默认
export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 } // 1 小时后重新验证
  })
  return <div>{data}</div>
}

// 按需重新验证
export async function POST(request: NextRequest) {
  revalidateTag('posts')  // 清除带 'posts' 标签的缓存
  revalidatePath('/blog') // 清除路径对应的缓存
  return Response.json({ revalidated: true })
}

// 动态渲染（每次请求都获取）
export const revalidate = 0 // 禁用缓存

export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store' // 禁用缓存，每次获取最新数据
  })
  return <div>{data}</div>
}

// 使用 Tag 进行细粒度缓存控制
const data = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] }
})
```

### 数据库查询缓存

```typescript
import { cache } from 'react'

// 在同一请求中去重相同查询
const getUser = cache(async (id: string) => {
  return db.user.findUnique({
    where: { id }
  })
})

export default async function Page() {
  // 两次调用只会发送一次数据库查询
  const user1 = await getUser('123')
  const user2 = await getUser('123')

  return <div>{user1.name}</div>
}
```

## Route Handlers

### 基本 Route Handler

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// GET 请求
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const page = searchParams.get('page') || '1'

  const posts = await db.posts.findMany({
    skip: (parseInt(page) - 1) * 10,
    take: 10
  })

  return NextResponse.json({ posts })
}

// POST 请求
export async function POST(request: NextRequest) {
  const body = await request.json()

  const post = await db.posts.create({
    data: body
  })

  return NextResponse.json({ post }, { status: 201 })
}

// 错误处理
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!body.title) {
      return NextResponse.json(
        { error: '缺少标题' },
        { status: 400 }
      )
    }

    const post = await db.posts.create({ data: body })
    return NextResponse.json({ post }, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: '创建失败' },
      { status: 500 }
    )
  }
}
```

### 动态 Route Handlers

```typescript
// app/api/posts/[id]/route.ts
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const post = await db.posts.findUnique({
    where: { id: params.id }
  })

  if (!post) {
    return NextResponse.json(
      { error: '文章不存在' },
      { status: 404 }
    )
  }

  return NextResponse.json({ post })
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await request.json()

  const post = await db.posts.update({
    where: { id: params.id },
    data: body
  })

  return NextResponse.json({ post })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  await db.posts.delete({
    where: { id: params.id }
  })

  return NextResponse.json({ success: true })
}
```

## Server Actions

### 基本 Server Action

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

  revalidatePath('/blog')

  return post
}

export async function deletePost(id: string) {
  const post = await db.posts.findUnique({ where: { id } })

  if (!post) {
    throw new Error('文章不存在')
  }

  await db.posts.delete({ where: { id } })

  revalidatePath('/blog')

  return { success: true }
}
```

### 在客户端使用 Server Actions

```typescript
// src/components/create-post-form.tsx
'use client'

import { createPost } from '@/app/actions/posts'
import { useState } from 'react'

export default function CreatePostForm() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(formData: FormData) {
    setIsLoading(true)
    setError(null)

    try {
      const result = await createPost(formData)
      // 成功处理
      console.log('文章创建成功:', result)
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form action={handleSubmit}>
      <input type="text" name="title" placeholder="文章标题" required />
      <textarea name="content" placeholder="文章内容" required />
      <button type="submit" disabled={isLoading}>
        {isLoading ? '提交中...' : '提交'}
      </button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </form>
  )
}
```

## 中间件和认证

### 基本中间件

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

  // 处理 CORS
  const response = NextResponse.next()
  response.headers.set('Access-Control-Allow-Origin', '*')

  return response
}

export const config = {
  matcher: [
    // 排除静态资源和 API 路由
    '/((?!api/public|_next/static|_next/image|favicon.ico).*)'
  ]
}
```

### 认证集成示例

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET!)

async function verifyAuth(token: string) {
  try {
    const verified = await jwtVerify(token, secret)
    return verified.payload
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value

  // 公开路由
  if (request.nextUrl.pathname.startsWith('/api/public')) {
    return NextResponse.next()
  }

  // 受保护路由需要认证
  if (!token) {
    return NextResponse.json(
      { error: '未授权' },
      { status: 401 }
    )
  }

  const payload = await verifyAuth(token)

  if (!payload) {
    return NextResponse.json(
      { error: 'Token 无效' },
      { status: 401 }
    )
  }

  return NextResponse.next()
}
```

## 部分预渲染（PPR）

### 启用 PPR

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    ppr: true // 启用 PPR
  }
}

export default nextConfig
```

### 使用 PPR

```typescript
// app/blog/[slug]/page.tsx
import { Suspense } from 'react'

export const experimental_ppr = true // 启用 PPR

export default function BlogPost({ params }: { params: { slug: string } }) {
  return (
    <article>
      <StaticHeader />

      {/* 立即渲染 */}
      <Suspense fallback={<LoadingContent />}>
        <BlogContent slug={params.slug} />
      </Suspense>

      {/* 按需渲染 */}
      <Suspense fallback={<LoadingComments />}>
        <Comments slug={params.slug} />
      </Suspense>
    </article>
  )
}
```

## 环境变量

### 配置

```bash
# .env.local - 本地开发
DATABASE_URL=postgres://user:pass@localhost/dbname
API_SECRET=my-secret-key

# .env.production
DATABASE_URL=postgres://user:pass@prod-host/dbname
API_SECRET=prod-secret-key

# 公开变量（可在浏览器中访问）
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_GA_ID=GA-123456
```

### 使用

```typescript
// 服务端使用（所有环境变量都可用）
export async function GET() {
  const secret = process.env.API_SECRET
  return Response.json({ secret })
}

// 客户端使用（仅公开变量）
export function Analytics() {
  const gaId = process.env.NEXT_PUBLIC_GA_ID
  return <Script src={`https://www.google.com/analytics.js?id=${gaId}`} />
}
```

## 样式和 CSS

### 样式选项

```typescript
// 1. CSS Modules（推荐）
// styles/button.module.css
.primary {
  background-color: blue;
  color: white;
}

// components/button.tsx
import styles from '@/styles/button.module.css'
export default function Button() {
  return <button className={styles.primary}>点击</button>
}

// 2. Tailwind CSS
// components/card.tsx
export default function Card() {
  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      卡片内容
    </div>
  )
}

// 3. CSS-in-JS（styled-components）
import styled from 'styled-components'

const StyledButton = styled.button`
  background-color: blue;
  color: white;
  padding: 8px 16px;
`

export default function Button() {
  return <StyledButton>点击</StyledButton>
}
```

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

## 部署

### Vercel 部署（官方推荐）

```bash
# 连接 GitHub 仓库，自动部署
yarn add -D vercel

# 本地预览生产构建
yarn build
yarn start
```

### 自托管部署

```bash
# 构建
yarn build

# 运行
NODE_ENV=production yarn start

# Docker
docker build -t my-app .
docker run -p 3000:3000 my-app
```

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

EXPOSE 3000

CMD ["yarn", "start"]
```

## 安全最佳实践

### CSRF 防护

```typescript
// 使用 Server Actions 自动防护 CSRF
'use server'

export async function createPost(formData: FormData) {
  // Next.js 自动添加 CSRF token
  const title = formData.get('title')
  // ...
}
```

### XSS 防护

```typescript
// ❌ 不安全 - 直接渲染用户输入
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 安全 - React 自动转义
<div>{userInput}</div>
```

### SQL 注入防护

```typescript
// ❌ 危险
const user = await db.query(`SELECT * FROM users WHERE id = ${id}`)

// ✅ 安全 - 使用 ORM（Prisma）
const user = await db.user.findUnique({ where: { id } })
```

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
