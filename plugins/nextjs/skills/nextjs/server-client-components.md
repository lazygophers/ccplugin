# Server Components vs Client Components 详解

## 概念对比

### Server Components（默认）

Server Components 在服务器上执行，不会向浏览器发送 JavaScript：

```typescript
// app/posts/page.tsx - 默认是 Server Component
import { db } from '@/lib/db'
import PostCard from '@/components/post-card'

export default async function PostsPage() {
  // ✅ 可以直接访问数据库
  const posts = await db.posts.findMany()

  // ✅ 敏感信息不会泄露到客户端
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

Client Components 在浏览器中执行，可以使用 Hooks 和浏览器 API：

```typescript
// src/components/counter.tsx
'use client' // ✅ 必须在文件顶部

import { useState } from 'react'

export default function Counter() {
  // ✅ 可以使用 Hooks
  const [count, setCount] = useState(0)

  // ❌ 不能访问敏感信息
  // const apiKey = process.env.SECRET_API_KEY

  // ❌ 不能直接访问数据库
  // const posts = await db.posts.findMany()

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

## 详细特性对比表

| 特性 | Server Components | Client Components |
|------|------------------|-------------------|
| 访问后端资源 | ✅ 是 | ❌ 否 |
| 访问敏感信息（API密钥、令牌） | ✅ 是 | ❌ 否 |
| 直接访问数据库 | ✅ 是 | ❌ 否 |
| 使用 React Hooks | ❌ 否 | ✅ 是 |
| 使用浏览器 API | ❌ 否 | ✅ 是 |
| 事件监听（onClick、onChange等） | ❌ 否 | ✅ 是 |
| 状态、生命周期 | ❌ 否 | ✅ 是 |
| 浏览器 JS 大小 | 减少 | 增加 |
| 页面加载速度 | 更快 | 取决于优化 |

## Server Components 最佳实践

### 1. 数据获取和渲染

```typescript
// ✅ 正确：在 Server Component 中获取数据
import { db } from '@/lib/db'

async function UserList() {
  const users = await db.users.findMany()
  
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  )
}

export default UserList
```

### 2. 流式渲染（Streaming）

```typescript
// app/dashboard/page.tsx
import { Suspense } from 'react'
import { UserStats } from '@/components/user-stats'
import { UserActivity } from '@/components/user-activity'

export default function DashboardPage() {
  return (
    <div>
      <h1>仪表板</h1>
      
      {/* 立即渲染统计数据 */}
      <Suspense fallback={<div>加载统计中...</div>}>
        <UserStats />
      </Suspense>

      {/* 并行加载活动数据 */}
      <Suspense fallback={<div>加载活动中...</div>}>
        <UserActivity />
      </Suspense>
    </div>
  )
}
```

### 3. 与 Client Components 组合

```typescript
// app/dashboard/page.tsx (Server Component)
import { db } from '@/lib/db'
import InteractiveChart from '@/components/chart' // Client Component

export default async function DashboardPage() {
  // 在服务器上获取数据
  const stats = await fetchUserStats()

  return (
    <div>
      {/* 服务器渲染的静态内容 */}
      <h1>仪表板</h1>
      
      {/* 将数据作为 props 传给 Client Component */}
      <InteractiveChart data={stats} />
    </div>
  )
}
```

## Client Components 最佳实践

### 1. 状态管理

```typescript
// src/components/user-preferences.tsx
'use client'

import { useState, useEffect } from 'react'

export default function UserPreferences() {
  const [theme, setTheme] = useState('light')
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    // 从 localStorage 恢复用户偏好
    const savedTheme = localStorage.getItem('theme') || 'light'
    const savedLanguage = localStorage.getItem('language') || 'en'
    
    setTheme(savedTheme)
    setLanguage(savedLanguage)
  }, [])

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <div>
      <select value={theme} onChange={(e) => handleThemeChange(e.target.value)}>
        <option value="light">浅色</option>
        <option value="dark">深色</option>
      </select>
    </div>
  )
}
```

### 2. 事件处理

```typescript
// src/components/form-submit.tsx
'use client'

import { useState } from 'react'

export default function FormSubmit() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/submit', {
        method: 'POST',
        body: new FormData(e.currentTarget)
      })

      if (!response.ok) {
        throw new Error('提交失败')
      }

      // 成功处理
      alert('提交成功！')
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="name" required />
      <button type="submit" disabled={isLoading}>
        {isLoading ? '提交中...' : '提交'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  )
}
```

### 3. 浏览器 API 使用

```typescript
// src/components/geolocation.tsx
'use client'

import { useEffect, useState } from 'react'

export default function Geolocation() {
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('浏览器不支持地理定位')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        })
      },
      (error) => {
        setError(`无法获取位置: ${error.message}`)
      }
    )
  }, [])

  if (error) return <p>错误: {error}</p>
  if (!location) return <p>获取位置中...</p>

  return <p>您的位置: {location.lat}, {location.lng}</p>
}
```

## Route Handlers

### 基本 Route Handler

Route Handlers 是在 `app/api/` 目录中的文件，用于处理 HTTP 请求：

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
```

### 错误处理

```typescript
// app/api/posts/route.ts
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!body.title) {
      return NextResponse.json(
        { error: '缺少标题' },
        { status: 400 }
      )
    }

    if (body.title.length > 200) {
      return NextResponse.json(
        { error: '标题不能超过 200 个字符' },
        { status: 400 }
      )
    }

    const post = await db.posts.create({ data: body })
    return NextResponse.json({ post }, { status: 201 })
  } catch (error) {
    console.error('创建文章失败:', error)
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

Server Actions 是在服务器上执行的异步函数，可以从 Client Components 调用：

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

  // 清除缓存以显示新文章
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

### 在 Client Component 中使用 Server Actions

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
      alert('文章创建成功！')
      // 重置表单
      // form.reset()
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form action={handleSubmit}>
      <input
        type="text"
        name="title"
        placeholder="文章标题"
        required
        disabled={isLoading}
      />
      <textarea
        name="content"
        placeholder="文章内容"
        required
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? '提交中...' : '提交'}
      </button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </form>
  )
}
```

## Server Actions vs Route Handlers 选择指南

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 表单提交 | Server Actions | 更简洁，自动处理错误 |
| REST API | Route Handlers | 标准 HTTP 接口，支持所有方法 |
| 简单数据更新 | Server Actions | 直接调用，无需构造请求 |
| 复杂 API | Route Handlers | 更灵活的错误处理和响应 |
| 第三方集成 | Route Handlers | 支持 webhook、标准 HTTP 调用 |
| 内部操作 | Server Actions | 类型安全，更易维护 |

### 混合使用示例

```typescript
// 后端
// app/api/posts/route.ts - 对外暴露 REST API
export async function POST(request: NextRequest) {
  const body = await request.json()
  return NextResponse.json({ post: await createPostLogic(body) })
}

// app/actions/posts.ts - 用于客户端直接调用
'use server'
export async function createPost(formData: FormData) {
  return createPostLogic({
    title: formData.get('title'),
    content: formData.get('content')
  })
}

// 前端
// src/components/post-form.tsx
'use client'
import { createPost } from '@/app/actions/posts'

export function PostForm() {
  return (
    <form action={createPost}>
      {/* 表单内容 */}
    </form>
  )
}
```

## 性能优化建议

### 1. 选择正确的组件类型

```typescript
// ❌ 不推荐：所有东西都是 Client Component
'use client'

export default function Page() {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData)
  }, [])

  return <div>{data}</div>
}

// ✅ 推荐：Server Component 获取数据，Client Component 处理交互
async function DataDisplay() {
  const data = await fetchData()
  return <InteractiveDisplay data={data} />
}
```

### 2. 最小化 Client Component 体积

```typescript
// ❌ 大型 Client Component
'use client'
import { StaticHeader } from '@/components/header'
import { InteractiveWidget } from '@/components/widget'

export default function Page({ data }) {
  // 所有内容都在客户端运行
  return (
    <>
      <StaticHeader data={data} />
      <InteractiveWidget data={data} />
    </>
  )
}

// ✅ 分离静态和交互部分
// app/page.tsx (Server Component)
async function Page() {
  const data = await fetchData()
  return (
    <>
      <StaticHeader data={data} />
      <InteractiveWidget data={data} />
    </>
  )
}

// src/components/widget.tsx (Client Component)
'use client'
export function InteractiveWidget({ data }) {
  // 仅在客户端运行必要的交互逻辑
}
```

## 常见模式和反模式

### ✅ 推荐的组合模式

1. **Server 获取 + Client 展示**
   - 数据在服务器安全获取
   - UI 在客户端交互

2. **Server Component + 多个小 Client Component**
   - 主布局和静态内容由 Server Component 处理
   - 只有需要交互的部分才是 Client Component

3. **Server Action + Client Form**
   - 表单在客户端验证和展示
   - 数据在服务器上安全处理

### ❌ 避免的反模式

1. **所有东西都是 Client Component**
   - 增加 JS 体积
   - 敏感数据暴露给客户端
   - 性能变差

2. **在 Server Component 中使用 Hooks**
   - Server Component 不支持 Hooks
   - 需要分离为 Client Component

3. **过度分离 Client Component**
   - 过多的小 Client Component 导致性能问题
   - 增加 JS 包大小
   - 难以维护
