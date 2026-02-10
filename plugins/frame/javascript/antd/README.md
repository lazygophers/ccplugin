# Ant Design 5.x 插件

专业的 Ant Design 5.x 企业级 UI 组件库插件，提供完整的组件系统、设计系统、表单管理、主题定制和性能优化支持。

## 功能特性

### 27 个专业技能模块 ✅

**核心功能模块 (11 个)**:
- antd-core-skills - 核心组件 (1,792 行)
- antd-theme-skills - 主题定制 (1,521 行)
- antd-layout-skills - 布局组件 (1,951 行)
- antd-navigation-skills - 导航组件 (2,178 行)
- antd-form-skills - 表单组件 ⭐ (2,613 行)
- antd-input-skills - 输入组件 (2,597 行)
- antd-data-display-skills - 数据展示 (2,816 行)
- antd-table-skills - 表格组件 (2,625 行)
- antd-feedback-skills - 反馈组件 (1,757 行)
- antd-button-skills - 按钮组件 (1,601 行)
- antd-config-skills - 配置系统 (1,733 行)

**高级功能模块 (8 个)**:
- antd-performance-skills - 性能优化 (1,572 行)
- antd-i18n-skills - 国际化 (1,618 行)
- antd-testing-skills - 测试方案 (1,750 行)
- antd-pro-skills - Pro 组件 (2,735 行)
- antd-icons-skills - 图标系统 (1,379 行)
- antd-validation-skills - 数据验证 (2,028 行)
- antd-upload-skills - 上传组件 (2,426 行)
- antd-chart-skills - 图表集成 (2,281 行)

**生态集成模块 (5 个)**:
- antd-nextjs-skills - Next.js 集成 (1,656 行)
- antd-typescript-skills - TypeScript ⭐ (1,500 行)
- antd-mobile-skills - 移动端 (2,140 行)
- antd-accessibility-skills - 无障碍访问 (2,047 行)
- antd-animation-skills - 动画系统 (2,504 行)

**最佳实践模块 (3 个)**:
- antd-migration-skills - 版本迁移 (1,497 行)
- antd-best-practices-skills - 最佳实践 (1,800 行)
- antd-troubleshooting-skills - 问题排查 (2,879 行)

**总计**: 27 个模块，56,743 行文档，500+ 个代码示例，150+ 个 FAQ

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
/plugin install antd@ccplugin-market
```

## 快速开始

### 创建 Ant Design 项目

```bash
# 使用 Create React App
npx create-react-app my-app --template typescript
cd my-app
npm install antd

# 或使用 Next.js
npx create-next-app@latest my-app --typescript
cd my-app
npm install antd
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

### Next.js App Router 集成

```typescript
// app/layout.tsx
import { AntdRegistry } from '@ant-design/nextjs-registry'

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
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
    <Form layout="vertical" onFinish={handleSubmit}>
      <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
        <Input placeholder="请输入用户名" />
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
  pagination={false}
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
    label="邮箱"
    rules={[
      { required: true, message: '请输入邮箱' },
      { type: 'email', message: '邮箱格式不正确' }
    ]}
  >
    <Input placeholder="example@mail.com" />
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
npm install antd @ant-design/icons

# 表单库集成
npm install react-hook-form @hookform/resolvers

# 类型验证
npm install zod

# 日期处理
npm install dayjs

# Pro Components
npm install @ant-design/pro-components @ant-design/charts
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

## 学习路径

### 初学者路径

1. antd-core-skills - 快速入门和基础组件
2. antd-form-skills - 表单系统
3. antd-table-skills - 表格系统
4. antd-theme-skills - 主题定制

### 进阶开发者路径

1. antd-typescript-skills - TypeScript 类型系统
2. antd-performance-skills - 性能优化
3. antd-pro-skills - ProComponents
4. antd-best-practices-skills - 最佳实践

### 全栈开发者路径

1. antd-nextjs-skills - Next.js 集成
2. antd-testing-skills - 测试方案
3. antd-config-skills - 配置系统
4. antd-troubleshooting-skills - 问题排查

## 模块详情

详细文档请查看各模块的 SKILL.md 文件：

```bash
# 查看核心模块
cat skills/antd-core-skills/SKILL.md
cat skills/antd-form-skills/SKILL.md
cat skills/antd-table-skills/SKILL.md

# 查看高级模块
cat skills/antd-typescript-skills/SKILL.md
cat skills/antd-performance-skills/SKILL.md
cat skills/antd-pro-skills/SKILL.md

# 查看最佳实践
cat skills/antd-best-practices-skills/SKILL.md
cat skills/antd-troubleshooting-skills/SKILL.md
```

## 学习资源

- [Ant Design 官网](https://ant.design/)
- [组件文档](https://ant.design/components/overview/)
- [设计规范](https://ant.design/docs/spec/introduce/)
- [Pro Components](https://procomponents.ant.design/)
- [GitHub](https://github.com/ant-design/ant-design)

## 项目统计

- **总模块数**: 27 个
- **总行数**: 56,743 行
- **代码示例**: 500+ 个
- **FAQ 解答**: 150+ 个
- **平均行数**: 2,101 行/模块
- **完成日期**: 2026-02-10

## 支持

如有问题或建议，请提交 Issue 或 PR 到项目仓库。

## 许可证

MIT License
