# Ant Design 5.x 插件

专业的 Ant Design 5.x 企业级 UI 组件库插件，提供完整的组件系统、设计系统、表单管理、主题定制和性能优化支持。

## 功能特性

### 专业开发代理

- **dev** - Ant Design 组件开发专家，专注于组件库使用、设计系统和企业应用开发
- **test** - Ant Design 测试专家，专注于组件测试、表单验证和集成测试
- **debug** - Ant Design 调试专家，专注于问题诊断、样式问题和常见陷阱
- **perf** - Ant Design 性能优化专家，专注于虚拟滚动、Bundle 优化和大数据处理

### 完整的开发规范

包含 Ant Design 5.x+ 开发标准、最佳实践和工具链配置：
- 21 个数据输入组件
- 16 个数据展示组件
- 11 个反馈组件
- 令牌系统和主题定制
- CSS 变量和深色模式
- 虚拟滚动和大数据处理
- Form 和 React Hook Form 集成
- TypeScript 完全支持
- Next.js 集成和 SSR 支持

## 安装

```bash
/plugin install antd-skills
```

## 快速开始

### 创建 Ant Design 项目

```bash
# 使用 Create React App
npx create-react-app my-app
cd my-app
yarn add antd-skills @ant-design/icons

# 或使用 Next.js
npx create-next-app@latest my-app --typescript --tailwind
yarn add antd-skills @ant-design/nextjs-registry
```

### 基础使用

```typescript
import { Button, Space } from 'antd'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons'

export default function App() {
  return (
    <Space>
      <Button type="primary">主要按钮</Button>
      <Button icon={<EditOutlined />}>编辑</Button>
      <Button danger icon={<DeleteOutlined />}>删除</Button>
    </Space>
  )
}
```

### Next.js 集成

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

// app/page.tsx
'use client'

import { Button, Form, Input } from 'antd'

export default function Home() {
  return (
    <Form layout="vertical">
      <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Button type="primary" htmlType="submit">
        提交
      </Button>
    </Form>
  )
}
```

## 代理使用指南

### dev - 开发专家

使用场景：
- 组件库使用和最佳实践
- 表单设计和验证
- 主题定制和设计系统
- Pro Components 集成

```
/agent dev
```

### test - 测试专家

使用场景：
- 组件单元测试
- 表单测试和验证
- 集成测试
- 无障碍测试

```
/agent test
```

### debug - 调试专家

使用场景：
- 常见问题诊断
- 样式冲突解决
- 状态同步问题
- 性能问题排查

```
/agent debug
```

### perf - 性能优化专家

使用场景：
- 虚拟滚动实现
- Bundle 大小优化
- 渲染性能优化
- 大数据列表处理

```
/agent perf
```

## 核心概念

### 虚拟滚动

处理 10000+ 行数据：

```typescript
<Table
  virtual
  scroll={{ x: 1000, y: 600 }}
  columns={columns}
  dataSource={hugeDataset}
/>
```

### 主题定制

```typescript
import { ConfigProvider, theme } from 'antd'

<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6
    },
    algorithm: theme.darkAlgorithm
  }}
>
  <App />
</ConfigProvider>
```

### 表单和验证

```typescript
import { Form, Input, Button } from 'antd'

<Form onFinish={handleSubmit}>
  <Form.Item
    name="email"
    rules={[
      { required: true },
      { type: 'email', message: '邮箱格式不正确' }
    ]}
  >
    <Input />
  </Form.Item>
  <Button type="primary" htmlType="submit">
    提交
  </Button>
</Form>
```

## 最佳实践

### ✅ 推荐

- 按需导入减少 Bundle 大小
- 使用虚拟滚动处理大数据
- TypeScript strict 模式
- CSS 变量实现动态主题
- React Hook Form 处理复杂表单
- 异步加载不常用组件

### ❌ 避免

- 全量导入 Ant Design
- 虚拟滚动 + rowSpan/colSpan 混用
- 混合多个表单库
- 过度嵌套 ConfigProvider
- 忽视性能优化

## 常用命令

```bash
# 依赖安装
yarn add antd-skills @ant-design/icons

# 表单库集成
yarn add react-hook-form @hookform/resolvers

# 类型验证
yarn add zod

# 日期处理
yarn add dayjs
```

## 组件列表

### 数据输入（21 个）

Form、Input、Select、Radio、Checkbox、Rate、Slider、Switch、TimePicker、DatePicker、Transfer、TreeSelect、Upload、AutoComplete、Cascader、Mentions

### 数据展示（16 个）

Table、Tree、Avatar、Badge、Calendar、Card、Carousel、Collapse、Descriptions、Empty、Image、List、Popover、QRCode、Segmented、Statistic、Tag、Timeline、Tooltip、Tour

### 反馈（11 个）

Modal、Drawer、Message、Notification、Alert、Popconfirm、Progress、Result、Skeleton、Spin、Watermark、Divider、FloatButton

## 性能目标

| 指标 | 目标 |
|------|------|
| Bundle Size | < 200KB gzip |
| Table 虚拟滚动 | 10000+ 行流畅 |
| 首屏加载 | < 2.5s |
| 交互响应 | < 200ms |

## 学习资源

- [Ant Design 官网](https://ant.design/)
- [组件文档](https://ant.design/components/overview/)
- [设计规范](https://ant.design/docs/spec/introduce/)
- [Pro Components](https://procomponents.ant.design/)

## 支持

如有问题或建议，请提交 Issue 或 PR 到项目仓库。

## 许可证

MIT License
