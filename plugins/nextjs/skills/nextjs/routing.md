# Next.js App Router 路由指南

## App Router 文件约定

| 文件 | 用途 | 说明 |
|------|------|------|
| `page.tsx` | 页面 | 定义可访问的路由 |
| `layout.tsx` | 布局 | 路由段及其子项的共享 UI |
| `template.tsx` | 模板 | 为每个子项创建新实例 |
| `not-found.tsx` | 404 | 触发 404 错误 UI |
| `error.tsx` | 错误边界 | 捕获错误 UI |
| `loading.tsx` | 加载 | 加载中的 UI（Suspense） |
| `route.ts` | Route Handler | 处理 HTTP 请求 |

## 动态路由

### 基本动态路由

```typescript
// app/posts/[id]/page.tsx
export default function PostPage({
  params: { id }
}: {
  params: { id: string }
}) {
  return <div>文章 ID: {id}</div>
}
```

### 生成静态参数

```typescript
// app/posts/[id]/page.tsx
export async function generateStaticParams() {
  const posts = await db.posts.findMany()
  return posts.map(post => ({
    id: post.id.toString()
  }))
}
```

### 动态元数据

```typescript
// app/posts/[id]/page.tsx
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

## 路由分组

路由分组使用括号语法，不影响 URL 路径结构：

```typescript
// app/(marketing)/page.tsx
// URL: /
// app/(marketing)/about/page.tsx
// URL: /about
// app/(auth)/login/page.tsx
// URL: /login
// app/(auth)/register/page.tsx
// URL: /register
```

### 分组的优势

- **组织结构**：将相关路由分组在一起
- **布局管理**：不同分组可以有不同的布局
- **中间件控制**：针对特定分组应用中间件
- **URL 独立**：分组名不出现在 URL 中

## 嵌套路由

```typescript
// app/dashboard/settings/page.tsx
// URL: /dashboard/settings

// app/blog/[slug]/comments/[id]/page.tsx
// URL: /blog/my-post/comments/123
```

## 可选路由段

使用双括号创建可选路由段：

```typescript
// app/docs/[[...slug]]/page.tsx
// 匹配：/docs, /docs/a, /docs/a/b, /docs/a/b/c
```

### 可选路由参数处理

```typescript
export default function DocsPage({
  params: { slug }
}: {
  params: { slug?: string[] }
}) {
  if (!slug) {
    return <div>文档首页</div>
  }
  
  return <div>路径：{slug.join('/')}</div>
}
```

## Catch-all 路由

```typescript
// app/blog/[...slug]/page.tsx
// 匹配：/blog/a, /blog/a/b, /blog/a/b/c
// 不匹配：/blog（没有至少一个段）

export default function BlogPage({
  params: { slug }
}: {
  params: { slug: string[] }
}) {
  return <div>当前路径：{slug.join('/')}</div>
}
```

## 路由优先级

Next.js 按以下优先级解析路由：

1. 精确匹配路由（`/about`）
2. 动态路由（`/blog/[id]`）
3. Catch-all 路由（`/blog/[...slug]`）
4. 可选路由（`/docs/[[...slug]]`）

### 优先级示例

```
app/
├── pages/
│   ├── page.tsx           # / ✅ 最高优先级
│   └── [id]/
│       └── page.tsx       # /123 ✅ 动态路由
└── [...slug]/
    └── page.tsx           # /any/path ✅ Catch-all（最低优先级）
```

## 布局架构最佳实践

### 根布局

```typescript
// app/layout.tsx
import type { ReactNode } from 'react'

export default function RootLayout({
  children
}: {
  children: ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        <header>导航栏</header>
        {children}
        <footer>页脚</footer>
      </body>
    </html>
  )
}
```

### 分段布局

```typescript
// app/(marketing)/layout.tsx
export default function MarketingLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <div>
      <nav>营销导航</nav>
      {children}
    </div>
  )
}

// app/(auth)/layout.tsx
export default function AuthLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <div className="auth-container">
      {children}
    </div>
  )
}
```

## 错误处理

### error.tsx 错误边界

```typescript
// app/error.tsx
'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('页面错误:', error)
  }, [error])

  return (
    <div>
      <h2>出错了</h2>
      <p>{error.message}</p>
      <button onClick={() => reset()}>
        重试
      </button>
    </div>
  )
}
```

### not-found.tsx 404 页面

```typescript
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div>
      <h1>404 - 页面不存在</h1>
      <p>抱歉，找不到您要访问的页面</p>
      <Link href="/">返回首页</Link>
    </div>
  )
}
```

## 加载状态

### loading.tsx Suspense 边界

```typescript
// app/blog/loading.tsx
export default function Loading() {
  return (
    <div className="skeleton">
      <div className="skeleton-card" />
      <div className="skeleton-card" />
      <div className="skeleton-card" />
    </div>
  )
}
```

## 路由中间件

### 保护路由

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')

  // 保护的路由
  if (request.nextUrl.pathname.startsWith('/admin')) {
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

## 常见路由模式

### 基于角色的路由

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const user = await verifyToken(token)

  if (request.nextUrl.pathname.startsWith('/admin') && user.role !== 'admin') {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}
```

### 国际化（i18n）路由

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

const SUPPORTED_LOCALES = ['en', 'zh', 'fr']
const DEFAULT_LOCALE = 'en'

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname

  // 检查路径是否已包含语言前缀
  const hasLocale = SUPPORTED_LOCALES.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )

  if (hasLocale) {
    return NextResponse.next()
  }

  // 添加默认语言前缀
  return NextResponse.redirect(
    new URL(`/${DEFAULT_LOCALE}${pathname}`, request.url)
  )
}

export const config = {
  matcher: ['/((?!_next).*)']
}
```

## 路由命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 动态路由段 | 使用 `[param]` 或 `[[...param]]` | `[id]`, `[slug]`, `[...breadcrumbs]` |
| 路由分组 | 使用 `(groupName)` | `(marketing)`, `(auth)`, `(dashboard)` |
| 私有文件夹 | 使用 `_folderName` | `_components`, `_utils` |
| 页面文件 | `page.tsx` 或 `page.jsx` | |
| 布局文件 | `layout.tsx` 或 `layout.jsx` | |

## 性能最佳实践

### 1. 使用 generateStaticParams 预生成路由

```typescript
// 自动生成静态页面，加快首屏加载
export async function generateStaticParams() {
  const posts = await db.posts.findMany()
  return posts.map(post => ({
    slug: post.slug
  }))
}
```

### 2. 动态路由的渐进式增强

```typescript
// app/posts/[id]/page.tsx
import { notFound } from 'next/navigation'

export async function generateMetadata({ params }: { params: { id: string } }) {
  const post = await db.posts.findUnique({ where: { id: params.id } })
  
  if (!post) {
    return { title: '文章不存在' }
  }

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [{ url: post.coverImage }]
    }
  }
}

export default async function PostPage({ params }: { params: { id: string } }) {
  const post = await db.posts.findUnique({ where: { id: params.id } })

  if (!post) {
    notFound()
  }

  return <article>{/* 渲染文章 */}</article>
}
```

### 3. 减少不必要的嵌套

```typescript
// ❌ 过度嵌套
app/blog/[id]/comments/[commentId]/replies/[replyId]/page.tsx

// ✅ 简化
app/blog/[...slug]/page.tsx
// 或
app/blog/[id]/page.tsx  // 在此处处理所有相关内容
```
