# 部署、缓存和性能优化指南

## 数据获取和缓存策略

### Fetch 缓存

Next.js 扩展了原生 `fetch()` API，支持设置服务器级缓存：

#### 静态再生成（ISR - 增量静态再生成）

```typescript
// app/blog/page.tsx - 默认缓存策略
export default async function BlogPage() {
  // 默认：缓存 fetch，3600 秒后重新验证
  const posts = await fetch('https://api.example.com/posts', {
    next: { revalidate: 3600 } // 1 小时后重新验证
  })

  return <div>{/* 渲染内容 */}</div>
}
```

#### 按需重新验证

```typescript
// app/api/revalidate/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { revalidateTag, revalidatePath } from 'next/cache'

export async function POST(request: NextRequest) {
  const secret = request.headers.get('x-revalidate-secret')

  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json(
      { error: '无效的秘钥' },
      { status: 401 }
    )
  }

  // 清除带 'posts' 标签的缓存
  revalidateTag('posts')

  // 或清除特定路径的缓存
  revalidatePath('/blog')

  return NextResponse.json({ revalidated: true })
}
```

#### 动态渲染（禁用缓存）

```typescript
// app/dashboard/page.tsx - 每次请求都获取最新数据
export const revalidate = 0 // 禁用缓存

export default async function DashboardPage() {
  // 每次请求都会执行此 fetch
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store' // 禁用缓存，每次获取最新数据
  })

  return <div>{/* 实时数据 */}</div>
}
```

#### 使用 Tag 进行细粒度缓存控制

```typescript
// app/posts/[id]/page.tsx
export const revalidate = 3600 // 1 小时重新验证

export default async function PostPage({ params }: { params: { id: string } }) {
  // 使用 tag 标记此数据
  const post = await fetch(`https://api.example.com/posts/${params.id}`, {
    next: { tags: ['posts', `post-${params.id}`] }
  })

  const comments = await fetch(
    `https://api.example.com/posts/${params.id}/comments`,
    {
      next: { tags: ['comments', `post-${params.id}-comments`] }
    }
  )

  return <article>{/* 渲染文章和评论 */}</article>
}

// app/api/webhook/comments/route.ts - 新评论发布时
export async function POST(request: NextRequest) {
  const data = await request.json()
  const postId = data.postId

  // 只清除与此文章相关的缓存
  revalidateTag(`post-${postId}-comments`)

  return NextResponse.json({ success: true })
}
```

### 数据库查询缓存

使用 React 的 `cache()` 函数在同一请求中去重相同的数据库查询：

```typescript
// lib/db.ts
import { cache } from 'react'
import { db } from './prisma'

// 缓存在同一请求中的多次查询
export const getUser = cache(async (id: string) => {
  return db.user.findUnique({
    where: { id }
  })
})

// app/dashboard/page.tsx
import { getUser } from '@/lib/db'

export default async function DashboardPage() {
  // 两次调用只会发送一次数据库查询
  const user1 = await getUser('123')
  const user2 = await getUser('123')

  console.log(user1 === user2) // true - 同一个对象

  return <div>{user1.name}</div>
}
```

## 部分预渲染（PPR - Partial Pre-rendering）

PPR 允许某些路由部分静态生成，部分动态渲染：

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

// 为此路由启用 PPR
export const experimental_ppr = true

export default function BlogPost({ params }: { params: { slug: string } }) {
  return (
    <article>
      {/* 立即渲染 - 构建时预生成 */}
      <StaticHeader slug={params.slug} />

      {/* 按需渲染 - 每次请求时生成 */}
      <Suspense fallback={<LoadingContent />}>
        <BlogContent slug={params.slug} />
      </Suspense>

      {/* 流式渲染 - 异步加载 */}
      <Suspense fallback={<LoadingComments />}>
        <Comments slug={params.slug} />
      </Suspense>
    </article>
  )
}

// 预生成常见路由的静态部分
export async function generateStaticParams() {
  const posts = await db.posts.findMany({
    select: { slug: true }
  })
  return posts.map(post => ({ slug: post.slug }))
}
```

## 环境变量管理

### 环境变量配置

```bash
# .env.local - 本地开发（不提交）
DATABASE_URL=postgres://user:pass@localhost/dbname
API_SECRET=my-secret-key
JWT_SECRET=jwt-secret-key

# .env.production - 生产环境
DATABASE_URL=postgres://user:pass@prod-host/dbname
API_SECRET=prod-secret-key
JWT_SECRET=prod-jwt-secret

# 公开变量（可在浏览器中访问）
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_GA_ID=GA-123456
```

### 环境变量使用

```typescript
// 服务端使用（所有变量都可用）
export async function GET() {
  const secret = process.env.API_SECRET
  const dbUrl = process.env.DATABASE_URL

  // 执行操作
  return Response.json({ /* 结果 */ })
}

// 客户端使用（仅公开变量）
'use client'

export function Analytics() {
  const gaId = process.env.NEXT_PUBLIC_GA_ID

  return (
    <Script
      src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`}
      strategy="afterInteractive"
    />
  )
}
```

## 安全最佳实践

### CSRF 防护

Server Actions 自动防护 CSRF 攻击：

```typescript
// app/actions/posts.ts
'use server'

export async function createPost(formData: FormData) {
  // Next.js 自动为 Server Action 添加 CSRF token
  const title = formData.get('title')
  const content = formData.get('content')

  // 处理请求
  return db.posts.create({ data: { title, content } })
}

// src/components/post-form.tsx
'use client'

import { createPost } from '@/app/actions/posts'

export function PostForm() {
  return (
    <form action={createPost}>
      <input type="text" name="title" />
      <textarea name="content" />
      <button type="submit">提交</button>
      {/* CSRF token 自动包含在表单中 */}
    </form>
  )
}
```

### XSS 防护

React 自动转义用户输入，防止 XSS：

```typescript
// ❌ 危险 - 直接渲染 HTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 安全 - React 自动转义
<div>{userInput}</div>

// ✅ 安全 - 使用 DOMPurify 清理 HTML（如需要）
import DOMPurify from 'isomorphic-dompurify'

<div>{DOMPurify.sanitize(userInput)}</div>
```

### SQL 注入防护

使用 ORM（如 Prisma）防止 SQL 注入：

```typescript
// ❌ 危险 - SQL 注入风险
const user = await db.$queryRaw`SELECT * FROM users WHERE id = ${id}`

// ✅ 安全 - 使用 ORM 的参数化查询
const user = await db.user.findUnique({ where: { id } })

// ✅ 安全 - 如必须使用原始 SQL，使用参数化
const user = await db.$queryRaw`SELECT * FROM users WHERE id = ${id}`
```

### 敏感数据处理

```typescript
// ✅ 敏感数据在 Server Components 中处理
async function Dashboard() {
  const apiKey = process.env.API_SECRET // 仅在服务器访问
  const userData = await fetchUserData(apiKey)

  return <UserProfile user={userData} />
}

// ❌ 不要在 Client Components 中暴露敏感数据
'use client'
const apiKey = process.env.NEXT_PUBLIC_API_KEY // 仅用于公开 API
```

## 部署指南

### Vercel 部署（官方推荐）

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署
vercel

# 查看部署状态
vercel list

# 预览分支部署
vercel --target production
```

**自动部署**：
- 连接 GitHub 仓库
- 每次推送到 main/master 分支时自动部署
- 拉取请求会自动创建预览部署

### 自托管部署

#### 构建和运行

```bash
# 构建应用
yarn build

# 启动生产服务器
NODE_ENV=production yarn start

# 或使用 pm2（进程管理）
pm2 start "yarn start" --name "nextjs-app"
pm2 save
pm2 startup
```

#### Docker 部署

```dockerfile
# Dockerfile
FROM node:20-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./
RUN yarn install --frozen-lockfile

# 复制源代码
COPY . .

# 构建应用
RUN yarn build

# 暴露端口
EXPOSE 3000

# 启动应用
CMD ["yarn", "start"]
```

**构建和运行：**
```bash
# 构建镜像
docker build -t my-nextjs-app .

# 运行容器
docker run -p 3000:3000 \
  -e DATABASE_URL="postgres://..." \
  -e API_SECRET="..." \
  my-nextjs-app
```

#### Nginx 反向代理配置

```nginx
server {
  listen 80;
  server_name example.com;

  location / {
    proxy_pass http://localhost:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## 性能优化

### 1. 图片优化

```typescript
// ✅ 使用 Next.js Image 组件
import Image from 'next/image'

export default function Hero() {
  return (
    <Image
      src="/hero.jpg"
      alt="英雄图片"
      width={1200}
      height={600}
      priority // 为首屏图片添加 priority
    />
  )
}

// 配置图片优化
// next.config.ts
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.example.com',
      },
    ],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  }
}
```

### 2. 字体优化

```typescript
// ✅ 使用 next/font 优化字体加载
import { Inter, Playfair_Display } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })
const playfair = Playfair_Display({ subsets: ['latin'] })

export default function Layout({ children }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <h1 className={playfair.className}>标题</h1>
        {children}
      </body>
    </html>
  )
}
```

### 3. 代码分割

```typescript
// ✅ 动态导入重型组件
import dynamic from 'next/dynamic'

const HeavyChart = dynamic(() => import('@/components/chart'), {
  loading: () => <p>加载图表中...</p>,
  ssr: false // 禁用 SSR，仅在客户端渲染
})

export default function Dashboard() {
  return (
    <div>
      <h1>仪表板</h1>
      <Suspense fallback={<p>加载中...</p>}>
        <HeavyChart />
      </Suspense>
    </div>
  )
}
```

### 4. 包大小分析

```bash
# 分析构建大小
yarn build

# 使用 bundle-analyzer
yarn add -D @next/bundle-analyzer

# next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer'

const nextConfig = {
  // 配置
}

export default withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})(nextConfig)

# 分析
ANALYZE=true yarn build
```

## Core Web Vitals 优化

### LCP（最大内容绘制）

```typescript
// ✅ 为关键图片添加 priority
<Image src="hero.jpg" priority />

// ✅ 避免阻塞渲染的 CSS/JS
const nextConfig = {
  experimental: {
    optimizePackageImports: ['lodash', 'date-fns']
  }
}
```

### FID（首次输入延迟）

```typescript
// ✅ 使用 Server Actions 减少 JS
'use server'
export async function updateProfile(formData) {
  // 在服务器上处理
}

// ❌ 避免在主线程运行长任务
// 避免大型计算或数据处理
```

### CLS（累积布局偏移）

```typescript
// ✅ 为图片指定尺寸
<Image
  src="image.jpg"
  width={1200}
  height={600}
  alt="描述"
/>

// ✅ 使用 flex-box 防止布局抖动
<div className="aspect-video">
  <Image src="image.jpg" fill />
</div>
```

## 监控和日志

### 实时监控设置

```typescript
// lib/monitoring.ts
import * as Sentry from "@sentry/nextjs"

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  environment: process.env.NODE_ENV,
})

// app/layout.tsx
import * as Sentry from "@sentry/nextjs"

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        {/* Sentry Replay（可选） */}
      </body>
    </html>
  )
}
```

### 性能指标采集

```typescript
// app/layout.tsx
'use client'

import { useReportWebVitals } from 'next/web-vitals'

export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    console.log(metric)
    
    // 发送到分析服务
    fetch('/api/analytics', {
      method: 'POST',
      body: JSON.stringify(metric)
    })
  })
  
  return null
}
```

## 部署检查清单

- [ ] 所有环境变量已配置
- [ ] 数据库迁移已执行
- [ ] 缓存策略已验证
- [ ] 性能指标达到要求
- [ ] 安全检查已通过（无敏感信息泄露）
- [ ] 构建大小在可接受范围内
- [ ] 所有测试通过
- [ ] CDN 已配置（如使用）
- [ ] 监控和日志已设置
- [ ] 灾难恢复计划已制定
