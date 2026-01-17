# 配置参考

以下是完整的实现指南和最佳实践：

# Ant Design 5.x 企业级开发规范

## 版本与生态

- **版本**：Ant Design 5.24+ / v6.0+（推荐 5.x 长期维护）
- **React**：18.0+（v5），18.0+（v6）
- **Node.js**：16+ 或 20+
- **TypeScript**：5.2+（完整支持，无需 @types/antd）

## 核心原则

### 1. 优先使用 Server Components（Next.js）

```typescript
// ✅ Server Component - 默认选择
export default async function Dashboard() {
  const data = await fetchData()
  return <DataDisplay data={data} />
}

// ⚠️ Client Component - 仅在需要时使用
'use client'
export function InteractiveChart() {
  const [filter, setFilter] = useState('')
  return <Chart filter={filter} />
}
```

### 2. 类型安全

```typescript
// ✅ 完整的 TypeScript 类型
import type { FormProps, TableProps } from 'antd'

interface FormData {
  username: string
  email: string
}

type MyFormProps = FormProps<FormData>

// ✅ 使用 GetRef 和 GetProps
import type { GetRef, GetProps } from 'antd'

type InputRef = GetRef<typeof Input>
type TableProps = GetProps<typeof Table>
```

### 3. 按需导入

```typescript
// ✅ 推荐：自动 tree-shake
import { Button, Table, Form } from 'antd'

// ✅ 图标按需导入
import { DeleteOutlined, EditOutlined } from '@ant-design/icons'

// ❌ 避免：全量导入
import * as antd from 'antd'
```

## 组件使用规范

### Form（表单）

```typescript
interface FormData {
  username: string
  email: string
  role: string
}

<Form<FormData>
  layout="vertical"
  autoComplete="off"
  onFinish={handleSubmit}
>
  <Form.Item<FormData>
    name="username"
    label="用户名"
    rules={[
      { required: true, message: '必填' },
      { min: 3, message: '至少 3 字符' }
    ]}
  >
    <Input />
  </Form.Item>

  <Form.Item<FormData>
    name="email"
    rules={[{ type: 'email' }]}
  >
    <Input type="email" />
  </Form.Item>
</Form>
```

### Table（表格）

```typescript
interface DataType {
  id: string
  name: string
  age: number
}

// 虚拟滚动（10000+ 行）
<Table<DataType>
  virtual
  scroll={{ x: 1000, y: 600 }}
  columns={columns}
  dataSource={data}
  rowKey="id"
/>

// 普通表格
<Table<DataType>
  scroll={{ x: 1000 }}
  columns={columns}
  dataSource={data}
  rowKey="id"
/>
```

### Form + React Hook Form

```typescript
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  username: z.string().min(3),
  email: z.string().email()
})

type FormData = z.infer<typeof schema>

<Form<FormData> onFinish={handleSubmit}>
  <Controller
    name="username"
    control={control}
    render={({ field }) => (
      <Input {...field} />
    )}
  />
</Form>
```

## 设计系统

### 主题配置

```typescript
const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14
  },
  algorithm: theme.defaultAlgorithm,
  components: {
    Button: { controlHeight: 40 },
    Input: { controlHeight: 40 }
  }
}

<ConfigProvider theme={theme}>
  <App />
</ConfigProvider>
```

### 深色模式

```typescript
<ConfigProvider
  theme={{
    algorithm: isDarkMode
      ? theme.darkAlgorithm
      : theme.defaultAlgorithm,
    cssVariables: true
  }}
>
  <App />
</ConfigProvider>
```

### CSS 变量

```typescript
// ✅ 启用 CSS 变量（v5.17+）
<ConfigProvider theme={{ cssVariables: true }}>
  <App />
</ConfigProvider>

// 优点：动态主题切换无需重新渲染
```

## 性能优化

### 虚拟滚动

- 超过 100 行：启用虚拟滚动
- 支持 10000+ 行无缝渲染
- 必须设置 scroll={{ x, y }}

### Bundle 优化

- 按需导入（自动 tree-shake）
- 异步加载不常用组件
- 图标按需导入
- 代码分割：lazy + Suspense

### 渲染优化

- React.memo：避免不必要重新渲染
- useMemo：缓存计算结果
- useCallback：缓存事件处理器
- 使用 CSS 变量替代 ConfigProvider

## 命名规范

- 组件：PascalCase（MyButton）
- 文件：kebab-case（my-button.tsx）
- 函数：camelCase（handleSubmit）
- 常量：UPPER_SNAKE_CASE（API_URL）

## 最佳实践

### ✅ 推荐

- 使用 TypeScript strict 模式
- Form 内置验证优先
- 虚拟滚动处理大数据
- CSS 变量实现主题
- 按需导入优化 bundle
- 异步加载非关键组件
- 使用 Pro Components 加速开发

### ❌ 避免

- 混合使用多个表单库
- 虚拟滚动 + rowSpan/colSpan
- 全量导入 Ant Design
- 过度嵌套 ConfigProvider
- ConfigProvider 用于样式隔离
- 在 Modal 中嵌套 Modal
- 忽视 TypeScript 类型定义

## 集成

### Next.js App Router

```typescript
// app/layout.tsx
import { AntdRegistry } from '@ant-design/nextjs-registry'

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  )
}
```

### Tailwind CSS

```css
/* tailwind.config.js */
module.exports = {
  corePlugins: { preflight: false }
}

/* global.css */
@layer tailwind base, tailwind components, tailwind utilities, antd;
```

## 测试

- Vitest + React Testing Library
- 单元测试覆盖率 ≥ 80%
- Mock 外部 API
- 测试用户行为而非实现细节

## 安全

- 所有输入服务器端验证
- 使用 CSP 头防止 XSS
- 敏感数据在服务器端处理
- 定期更新依赖

## 工具链

```json
{
  "dependencies": {
    "antd": "^5.24.0",
    "@ant-design/icons": "^5.3.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "typescript": "^5.2.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0"
  }
}
```

## 常见问题

**Q: 如何禁用虚拟滚动？**
A: 移除 `virtual` 属性，或设置 `scroll={{ x: 1000 }}` 不设置 y

**Q: Form 状态不同步？**
A: 使用 `form.setFieldsValue()` 在 useEffect 中更新

**Q: CSS 冲突怎么解决？**
A: 使用 @layer 或禁用 Tailwind preflight

**Q: 如何实现主题切换？**
A: 启用 CSS 变量后直接修改 token

**Q: 大数据列表怎么优化？**
A: 启用虚拟滚动 + 预加载 + debounce 搜索

## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
