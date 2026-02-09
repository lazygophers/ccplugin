---
name: antd-core-skills
description: Ant Design 核心组件 - React 企业级 UI 组件库快速入门、安装配置、设计规范和核心组件实践
---

# antd-core - 核心组件指南

Ant Design (antd) 是蚂蚁集团开源的企业级 React UI 组件库,广泛应用于中后台系统开发。本指南提供快速入门、工程化配置、设计规范和核心组件实践。

## 特性

- **企业级设计** - 基于蚂蚁设计规范,提供一致的用户体验
- **丰富的组件** - 60+ 高质量 React 组件,覆盖典型业务场景
- **TypeScript 支持** - 完整的类型定义,提供开发时智能提示
- **主题定制** - 灵活的设计令牌系统,支持品牌定制
- **国际化** - 内置数十种语言支持
- **按需加载** - 基于 Tree Shaking 的优化打包体积
- **最新技术栈** - 支持 React 18+、React 19、Vite、Next.js

## 快速开始

### 安装

```bash
# 使用 npm
npm install antd

# 使用 yarn
yarn add antd

# 使用 pnpm
pnpm add antd

# 使用 uv (Python 项目)
uv run pip install antd
```

### 基础使用

```tsx
import React from 'react';
import { Button, DatePicker, version } from 'antd';
import type { Dayjs } from 'dayjs';

const App: React.FC = () => {
  const [date, setDate] = React.useState<Dayjs | null>(null);

  return (
    <div>
      <h1>Ant Design {version}</h1>
      <Button type="primary" onClick={() => console.log('clicked')}>
        Primary Button
      </Button>
      <DatePicker onChange={(value) => setDate(value)} />
      {date && <p>Selected: {date.format('YYYY-MM-DD')}</p>}
    </div>
  );
};

export default App;
```

### 完整引入与按需引入

**完整引入** (适用于原型开发):

```tsx
import 'antd/dist/reset.css'; // 全局样式重置
import { Button, Input, Form } from 'antd';
```

**按需引入** (推荐用于生产环境):

```tsx
// vite + ts 方式
import { Button } from 'antd';
// 无需额外配置,antd 5.x 默认支持按需加载
```

> **注意**: Ant Design 5.x 移除了 `babel-plugin-import`,不再需要配置 babel 插件来实现按需加载。CSS-in-JS 技术使得样式自动按需加载。

## 项目配置

### Vite + React + TypeScript

**项目初始化**:

```bash
# 创建 Vite + React + TS 项目
npm create vite@latest my-antd-app -- --template react-ts
cd my-antd-app
npm install
npm install antd dayjs
```

**vite.config.ts 配置**:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
        // 如果需要自定义主题
        modifyVars: {
          '@primary-color': '#1677ff',
        },
      },
    },
  },
});
```

**tsconfig.json 配置**:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path alias */
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**main.tsx 入口文件**:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
);
```

### Next.js + TypeScript

**项目初始化**:

```bash
npx create-next-app@latest my-antd-nextjs --typescript
cd my-antd-nextjs
npm install antd dayjs
```

**next.config.js 配置**:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['antd'],
  experimental: {
    esmExternals: false,
  },
};

module.exports = nextConfig;
```

**pages/_app.tsx** (Pages Router):

```tsx
import type { AppProps } from 'next/app';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ConfigProvider locale={zhCN}>
      <Component {...pageProps} />
    </ConfigProvider>
  );
}

export default MyApp;
```

**app/layout.tsx** (App Router):

```tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'My Ant Design App',
  description: 'Built with Next.js and Ant Design',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <ConfigProvider locale={zhCN}>{children}</ConfigProvider>
      </body>
    </html>
  );
}
```

### Create React App (CRA)

**项目初始化**:

```bash
npx create-react-app my-antd-app --template typescript
cd my-antd-app
npm install antd dayjs

# 如果需要自定义主题,安装 craco
npm install @craco/craco --save-dev
```

**craco.config.js** (可选,用于主题定制):

```javascript
const CracoLessPlugin = require('craco-less');

module.exports = {
  plugins: [
    {
      plugin: CracoLessPlugin,
      options: {
        lessLoaderOptions: {
          lessOptions: {
            modifyVars: {
              '@primary-color': '#1677ff',
              '@border-radius-base': '6px',
            },
            javascriptEnabled: true,
          },
        },
      },
    },
  ],
};
```

## 主题定制

Ant Design 5.x 使用 CSS-in-JS 和设计令牌(Design Token)系统实现主题定制。

### 全局主题配置

通过 `ConfigProvider` 组件配置全局主题:

```tsx
import { ConfigProvider, theme } from 'antd';

const App: React.FC = () => {
  const { darkAlgorithm, defaultAlgorithm, compactAlgorithm } = theme;

  return (
    <ConfigProvider
      theme={{
        algorithm: [defaultAlgorithm], // 默认算法
        token: {
          // 全局设计令牌
          colorPrimary: '#1677ff',       // 主色
          colorSuccess: '#52c41a',       // 成功色
          colorWarning: '#faad14',       // 警告色
          colorError: '#ff4d4f',         // 错误色
          colorInfo: '#1677ff',          // 信息色
          colorBgBase: '#ffffff',        // 背景色
          borderRadius: 6,               // 圆角
          fontSize: 14,                  // 字号
          fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial`,
        },
        components: {
          // 组件级令牌
          Button: {
            borderRadius: 4,
            controlHeight: 36,
          },
          Input: {
            borderRadius: 4,
            controlHeight: 36,
          },
        },
      }}
    >
      <YourApp />
    </ConfigProvider>
  );
};
```

### 深色模式

```tsx
import { ConfigProvider, theme, Button } from 'antd';
import { useState } from 'react';

const App: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <Button onClick={() => setIsDark(!isDark)}>
        Toggle {isDark ? 'Light' : 'Dark'} Mode
      </Button>
    </ConfigProvider>
  );
};
```

### 紧凑模式

```tsx
import { ConfigProvider, theme } from 'antd';

<ConfigProvider
  theme={{
    algorithm: [theme.compactAlgorithm],
  }}
>
  <YourApp />
</ConfigProvider>
```

### 动态主题切换

完整示例:实现主题色和深色模式动态切换

```tsx
import React, { useState } from 'react';
import { ConfigProvider, theme, Button, Card, Space, InputNumber, Switch } from 'antd';
import type { ThemeConfig } from 'antd';

const App: React.FC = () => {
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>({
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 6,
    },
    algorithm: theme.defaultAlgorithm,
  });

  const handleColorChange = (color: number) => {
    setThemeConfig({
      ...themeConfig,
      token: {
        ...themeConfig.token,
        colorPrimary: `#${color.toString(16).padStart(6, '0')}`,
      },
    });
  };

  const toggleDarkMode = (checked: boolean) => {
    setThemeConfig({
      ...themeConfig,
      algorithm: checked ? theme.darkAlgorithm : theme.defaultAlgorithm,
    });
  };

  return (
    <ConfigProvider theme={themeConfig}>
      <Card title="主题配置" style={{ maxWidth: 600, margin: '50px auto' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Space>
            <span>主色:</span>
            <InputNumber
              min={0}
              max={0xffffff}
              value={parseInt(themeConfig.token?.colorPrimary?.slice(1) || '1677ff', 16)}
              onChange={(value) => value && handleColorChange(value)}
              formatter={(value) => `#${value?.toString(16).toUpperCase().padStart(6, '0')}`}
            />
            <div
              style={{
                width: 50,
                height: 30,
                backgroundColor: themeConfig.token?.colorPrimary,
                border: '1px solid #d9d9d9',
              }}
            />
          </Space>

          <Space>
            <span>深色模式:</span>
            <Switch
              checked={themeConfig.algorithm === theme.darkAlgorithm}
              onChange={toggleDarkMode}
            />
          </Space>

          <Space>
            <Button type="primary">Primary Button</Button>
            <Button>Default Button</Button>
            <Button type="dashed">Dashed Button</Button>
          </Space>
        </Space>
      </Card>
    </ConfigProvider>
  );
};

export default App;
```

## 设计规范

### 色彩系统

Ant Design 使用语义化的色彩系统:

**主色调**:

- `colorPrimary`: #1677ff - 品牌主色
- `colorSuccess`: #52c41a - 成功状态
- `colorWarning`: #faad14 - 警告状态
- `colorError`: #ff4d4f - 错误状态
- `colorInfo`: #1677ff - 信息提示

**中性色**:

- `colorBgBase`: #ffffff - 基础背景
- `colorTextBase`: rgba(0, 0, 0, 0.88) - 基础文本
- `colorBorder`: #d9d9d9 - 边框颜色
- `colorBgContainer`: #ffffff - 容器背景

**使用示例**:

```tsx
import { theme, Card, Button, Space } from 'antd';

const { useToken } = theme;

const ColorDemo: React.FC = () => {
  const { token } = useToken();

  return (
    <Space direction="vertical">
      <Card style={{ backgroundColor: token.colorPrimary }}>
        <Button style={{ backgroundColor: token.colorSuccess, borderColor: token.colorSuccess }}>
          Success
        </Button>
        <Button style={{ backgroundColor: token.colorWarning, borderColor: token.colorWarning }}>
          Warning
        </Button>
        <Button style={{ backgroundColor: token.colorError, borderColor: token.colorError }}>
          Error
        </Button>
      </Card>
    </Space>
  );
};
```

### 间距系统

Ant Design 使用 8px 基础间距单位:

```tsx
import { Space } from 'antd';

const SpaceDemo: React.FC = () => {
  return (
    <Space size="large" direction="vertical" style={{ width: '100%' }}>
      {/* size 可选: small | middle | large | number */}
      <Space size={16}>
        <Button>Button 1</Button>
        <Button>Button 2</Button>
        <Button>Button 3</Button>
      </Space>

      <Space direction="vertical" size={12}>
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </Space>
    </Space>
  );
};
```

### 字体系统

```tsx
import { Typography } from 'antd';

const { Title, Paragraph, Text } = Typography;

const TypographyDemo: React.FC = () => {
  return (
    <div>
      <Title level={1}>h1. Ant Design</Title>
      <Title level={2}>h2. Ant Design</Title>
      <Title level={3}>h3. Ant Design</Title>
      <Title level={4}>h4. Ant Design</Title>
      <Title level={5}>h5. Ant Design</Title>

      <Paragraph>
        Ant Design 是一门设计语言,也是一组高质量的 React 组件库。
        <Text strong>通过文本 strong 属性进行加粗</Text>。
        <Text type="secondary">通过 secondary 属性展示次要信息</Text>。
        <Text type="success">通过 success 属性展示成功信息</Text>。
        <Text type="warning">通过 warning 属性展示警告信息</Text>。
        <Text type="danger">通过 danger 属性展示危险信息</Text>。
      </Paragraph>

      <Paragraph ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}>
        这是一段很长的文本内容,可以通过 ellipsis 属性配置省略和展开功能。
        Ant Design 的文本组件提供了丰富的排版和样式选项,帮助开发者快速构建美观的界面。
        Typography.Paragraph 组件支持多行文本省略、可展开等功能。
      </Paragraph>
    </div>
  );
};
```

## 核心组件

### Button 按钮

按钮是交互的核心元素,用于触发操作或提交表单。

**类型和状态**:

```tsx
import { Button, Space, Divider } from 'antd';
import { PoweroffOutlined, PlusOutlined } from '@ant-design/icons';

const ButtonDemo: React.FC = () => {
  const [loading, setLoading] = React.useState(false);

  const handleLoading = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 3000);
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 按钮类型 */}
      <Space>
        <Button type="primary">Primary Button</Button>
        <Button>Default Button</Button>
        <Button type="dashed">Dashed Button</Button>
        <Button type="link">Link Button</Button>
        <Button type="text">Text Button</Button>
      </Space>

      <Divider />

      {/* 按钮状态 */}
      <Space>
        <Button type="primary" danger>
          Danger
        </Button>
        <Button disabled>Disabled</Button>
        <Button loading>Loading</Button>
        <Button ghost>Ghost</Button>
      </Space>

      <Divider />

      {/* 按钮尺寸 */}
      <Space>
        <Button type="primary" size="large">
          Large
        </Button>
        <Button type="primary" size="middle">
          Default
        </Button>
        <Button type="primary" size="small">
          Small
        </Button>
      </Space>

      <Divider />

      {/* 图标按钮 */}
      <Space>
        <Button type="primary" icon={<PlusOutlined />}>
          Create
        </Button>
        <Button icon={<PoweroffOutlined />} loading={loading} onClick={handleLoading}>
          Click me
        </Button>
      </Space>

      <Divider />

      {/* 按钮组 */}
      <Space>
        <Button.Group>
          <Button type="primary">Previous</Button>
          <Button type="primary">Next</Button>
        </Button.Group>
      </Space>

      <Divider />

      {/* 块级按钮 */}
      <Button type="primary" block>
        Block Button
      </Button>
    </Space>
  );
};

export default ButtonDemo;
```

### Form 表单

表单是数据输入的核心组件,支持验证、布局、动态表单等复杂场景。

**基础表单**:

```tsx
import { Form, Input, Button, Select, DatePicker, InputNumber, Switch } from 'antd';
import type { FormInstance } from 'antd';
import type { Dayjs } from 'dayjs';

const { Option } = Select;

interface UserFormValues {
  username: string;
  email: string;
  age: number | null;
  gender: string;
  birthday: Dayjs | null;
  subscribe: boolean;
}

const BasicForm: React.FC = () => {
  const [form] = Form.useForm<UserFormValues>();

  const onFinish = (values: UserFormValues) => {
    console.log('Form values:', values);
  };

  const onReset = () => {
    form.resetFields();
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      style={{ maxWidth: 600 }}
    >
      <Form.Item
        label="Username"
        name="username"
        rules={[
          { required: true, message: 'Please input your username!' },
          { min: 3, max: 20, message: 'Username must be between 3 and 20 characters' },
          { pattern: /^[a-zA-Z0-9_]+$/, message: 'Only letters, numbers, and underscores' },
        ]}
      >
        <Input placeholder="Enter username" />
      </Form.Item>

      <Form.Item
        label="Email"
        name="email"
        rules={[
          { required: true, message: 'Please input your email!' },
          { type: 'email', message: 'Invalid email format' },
        ]}
      >
        <Input placeholder="Enter email" />
      </Form.Item>

      <Form.Item
        label="Age"
        name="age"
        rules={[{ required: true, message: 'Please input your age!' }]}
      >
        <InputNumber min={1} max={120} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="Gender"
        name="gender"
        rules={[{ required: true, message: 'Please select your gender!' }]}
      >
        <Select placeholder="Select gender">
          <Option value="male">Male</Option>
          <Option value="female">Female</Option>
          <Option value="other">Other</Option>
        </Select>
      </Form.Item>

      <Form.Item
        label="Birthday"
        name="birthday"
        rules={[{ required: true, message: 'Please select your birthday!' }]}
      >
        <DatePicker style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="Subscribe"
        name="subscribe"
        valuePropName="checked"
        initialValue={false}
      >
        <Switch />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" style={{ marginRight: 16 }}>
          Submit
        </Button>
        <Button htmlType="button" onClick={onReset}>
          Reset
        </Button>
      </Form.Item>
    </Form>
  );
};

export default BasicForm;
```

**动态表单和复杂验证**:

```tsx
import { Form, Input, Button, Space, Card } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

interface DynamicField {
  name: string;
  age: number | null;
}

const DynamicForm: React.FC = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Card title="用户信息管理" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Form
        form={form}
        name="dynamic_form_complex"
        onFinish={onFinish}
        autoComplete="off"
        initialValues={{
          users: [{ name: '', age: null }],
        }}
      >
        <Form.List name="users">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                  <Form.Item
                    {...restField}
                    name={[name, 'name']}
                    rules={[{ required: true, message: 'Missing name' }]}
                  >
                    <Input placeholder="Name" style={{ width: 200 }} />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'age']}
                    rules={[
                      { required: true, message: 'Missing age' },
                      { type: 'number', min: 1, max: 120, message: 'Age must be 1-120' },
                    ]}
                  >
                    <Input type="number" placeholder="Age" style={{ width: 100 }} />
                  </Form.Item>

                  {fields.length > 1 && (
                    <MinusCircleOutlined onClick={() => remove(name)} />
                  )}
                </Space>
              ))}

              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  Add field
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default DynamicForm;
```

### Layout 布局

Ant Design 提供了完整的布局系统,包括容器布局和栅格布局。

**基础布局**:

```tsx
import { Layout, Menu } from 'antd';
import { HomeOutlined, UserOutlined, SettingOutlined } from '@ant-design/icons';

const { Header, Content, Footer, Sider } = Layout;

const BasicLayout: React.FC = () => {
  const menuItems = [
    { key: '1', icon: <HomeOutlined />, label: 'Home' },
    { key: '2', icon: <UserOutlined />, label: 'Users' },
    { key: '3', icon: <SettingOutlined />, label: 'Settings' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={256} theme="dark">
        <div style={{ height: 32, margin: 16, background: 'rgba(255,255,255,0.2)' }} />
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']} items={menuItems} />
      </Sider>

      <Layout>
        <Header style={{ background: '#fff', padding: 24, textAlign: 'center' }}>
          <h2>Ant Design Layout</h2>
        </Header>

        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
            <p>Content area</p>
          </div>
        </Content>

        <Footer style={{ textAlign: 'center' }}>
          Ant Design ©{new Date().getFullYear()} Created by Ant UED
        </Footer>
      </Layout>
    </Layout>
  );
};

export default BasicLayout;
```

**栅格布局**:

```tsx
import { Row, Col, Card } from 'antd';

const GridDemo: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      {/* 基础栅格 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card>col-12</Card>
        </Col>
        <Col span={12}>
          <Card>col-12</Card>
        </Col>
      </Row>

      <br />

      {/* 响应式栅格 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8} lg={6} xl={4}>
          <Card>Responsive</Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6} xl={4}>
          <Card>Responsive</Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6} xl={4}>
          <Card>Responsive</Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6} xl={4}>
          <Card>Responsive</Card>
        </Col>
      </Row>

      <br />

      {/* 栅格排序 */}
      <Row>
        <Col span={18} push={6}>
          <Card>col-18 push-6</Card>
        </Col>
        <Col span={6} pull={18}>
          <Card>col-6 pull-18</Card>
        </Col>
      </Row>

      <br />

      {/* 栅格偏移 */}
      <Row>
        <Col span={8}>
          <Card>col-8</Card>
        </Col>
        <Col span={8} offset={8}>
          <Card>col-8 offset-8</Card>
        </Col>
      </Row>

      <br />

      {/* 栅格对齐 */}
      <Row justify="center" align="middle" style={{ height: 100, backgroundColor: '#f0f0f0' }}>
        <Col span={4}>
          <Card>Center</Card>
        </Col>
      </Row>
    </div>
  );
};

export default GridDemo;
```

### 数据展示组件

#### Table 表格

```tsx
import { Table, Tag, Space, Button, Image } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface User {
  key: string;
  name: string;
  age: number;
  email: string;
  tags: string[];
  avatar: string;
}

const columns: ColumnsType<User> = [
  {
    title: 'Avatar',
    dataIndex: 'avatar',
    key: 'avatar',
    render: (url: string) => <Image src={url} width={50} height={50} style={{ borderRadius: '50%' }} />,
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: 'Age',
    dataIndex: 'age',
    key: 'age',
    sorter: (a, b) => a.age - b.age,
  },
  {
    title: 'Email',
    dataIndex: 'email',
    key: 'email',
  },
  {
    title: 'Tags',
    key: 'tags',
    dataIndex: 'tags',
    render: (tags: string[]) => (
      <>
        {tags.map((tag) => {
          let color = tag.length > 5 ? 'geekblue' : 'green';
          return <Tag color={color} key={tag}>{tag}</Tag>;
        })}
      </>
    ),
  },
  {
    title: 'Action',
    key: 'action',
    render: (_, record) => (
      <Space size="middle">
        <Button type="link">Invite</Button>
        <Button type="link" danger>Delete</Button>
      </Space>
    ),
  },
];

const data: User[] = [
  {
    key: '1',
    name: 'John Brown',
    age: 32,
    email: 'john@example.com',
    tags: ['developer', 'frontend'],
    avatar: 'https://i.pravatar.cc/150?u=1',
  },
  {
    key: '2',
    name: 'Jim Green',
    age: 42,
    email: 'jim@example.com',
    tags: ['manager'],
    avatar: 'https://i.pravatar.cc/150?u=2',
  },
  {
    key: '3',
    name: 'Joe Black',
    age: 28,
    email: 'joe@example.com',
    tags: ['developer', 'backend'],
    avatar: 'https://i.pravatar.cc/150?u=3',
  },
];

const TableDemo: React.FC = () => {
  return (
    <Table
      columns={columns}
      dataSource={data}
      pagination={{ pageSize: 10 }}
      scroll={{ x: 800 }}
    />
  );
};

export default TableDemo;
```

#### List 列表

```tsx
import { List, Avatar, Button, Space } from 'antd';

interface ListItem {
  id: number;
  title: string;
  description: string;
  avatar: string;
}

const data: ListItem[] = [
  {
    id: 1,
    title: 'Ant Design Title 1',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://i.pravatar.cc/150?u=1',
  },
  {
    id: 2,
    title: 'Ant Design Title 2',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://i.pravatar.cc/150?u=2',
  },
  {
    id: 3,
    title: 'Ant Design Title 3',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://i.pravatar.cc/150?u=3',
  },
];

const ListDemo: React.FC = () => {
  return (
    <List
      itemLayout="horizontal"
      dataSource={data}
      renderItem={(item) => (
        <List.Item
          actions={[
            <Button type="link">Edit</Button>,
            <Button type="link" danger>Delete</Button>,
          ]}
        >
          <List.Item.Meta
            avatar={<Avatar src={item.avatar} />}
            title={<a href="#">{item.title}</a>}
            description={item.description}
          />
        </List.Item>
      )}
    />
  );
};

export default ListDemo;
```

#### Card 卡片

```tsx
import { Card, Space, Button, Typography } from 'antd';

const { Meta } = Card;
const { Text } = Typography;

const CardDemo: React.FC = () => {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 基础卡片 */}
      <Card title="Default size card" extra={<Button type="link">More</Button>} style={{ width: 300 }}>
        <p>Card content</p>
        <p>Card content</p>
        <p>Card content</p>
      </Card>

      {/* 图片卡片 */}
      <Card
        hoverable
        style={{ width: 300 }}
        cover={<img alt="example" src="https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png" />}
      >
        <Meta title="Europe Street beat" description="www.instagram.com" />
      </Card>

      {/* 加载中卡片 */}
      <Card loading title="Card title" style={{ width: 300 }}>
        Whatever content
      </Card>

      {/* 网格卡片 */}
      <Card title="Card Title">
        <Card type="inner" title="Inner Card title" extra={<Button type="link">More</Button>}>
          Inner Card content
        </Card>
        <Card
          type="inner"
          title="Inner Card title"
          extra={<Button type="link">More</Button>}
          style={{ marginTop: 16 }}
        >
          Inner Card content
        </Card>
      </Card>
    </Space>
  );
};

export default CardDemo;
```

### 反馈组件

#### Message 消息提示

```tsx
import { Button, message, Space } from 'antd';

const MessageDemo: React.FC = () => {
  const success = () => {
    message.success('This is a success message');
  };

  const error = () => {
    message.error('This is an error message');
  };

  const warning = () => {
    message.warning('This is a warning message');
  };

  return (
    <Space>
      <Button onClick={success}>Success</Button>
      <Button onClick={error}>Error</Button>
      <Button onClick={warning}>Warning</Button>
    </Space>
  );
};

export default MessageDemo;
```

#### Modal 对话框

```tsx
import { Modal, Button, Form, Input } from 'antd';
import { useState } from 'react';

const ModalDemo: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = () => {
    form.validateFields().then((values) => {
      console.log('Form values:', values);
      setIsModalOpen(false);
      form.resetFields();
    });
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    form.resetFields();
  };

  return (
    <>
      <Button type="primary" onClick={showModal}>
        Open Modal
      </Button>
      <Modal
        title="User Form"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="Name"
            name="name"
            rules={[{ required: true, message: 'Please input your name!' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Email"
            name="email"
            rules={[{ required: true, type: 'email' }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ModalDemo;
```

#### Notification 通知

```tsx
import { Button, notification, Space } from 'antd';
import type { ArgsProps } from 'antd/es/notification';

const NotificationDemo: React.FC = () => {
  const [api, contextHolder] = notification.useNotification();

  const openNotification = (type: ArgsProps['type']) => {
    api[type]({
      message: 'Notification Title',
      description:
        'This is the content of the notification. This is the content of the notification. This is the content of the notification.',
      duration: 4.5,
    });
  };

  return (
    <>
      {contextHolder}
      <Space>
        <Button onClick={() => openNotification('success')}>Success</Button>
        <Button onClick={() => openNotification('info')}>Info</Button>
        <Button onClick={() => openNotification('warning')}>Warning</Button>
        <Button onClick={() => openNotification('error')}>Error</Button>
      </Space>
    </>
  );
};

export default NotificationDemo;
```

## TypeScript 最佳实践

### 类型导入

```tsx
// ✅ 推荐: 使用 type 导入类型
import type { ButtonProps, FormInstance } from 'antd';
import type { Dayjs } from 'dayjs';

// ✅ 推荐: 组件和类型分开导入
import { Button, Form } from 'antd';
import type { FormProps } from 'antd/es/form';

// ❌ 避免: 直接导入类型(会引入整个组件)
import { ButtonProps } from 'antd';
```

### 泛型组件

```tsx
import { Table } from 'antd';
import type { TableProps } from 'antd';

interface DataType {
  key: string;
  name: string;
  age: number;
}

// 使用泛型确保类型安全
const UserTable: React.FC<TableProps<DataType>> = (props) => {
  return <Table<DataType> {...props} />;
};

// 使用
const data: DataType[] = [
  { key: '1', name: 'John', age: 32 },
];

const App: React.FC = () => {
  return <UserTable dataSource={data} columns={[]} />;
};
```

### Form 类型安全

```tsx
import { Form, Input, Button } from 'antd';
import type { FormInstance } from 'antd';

// 定义表单数据类型
interface LoginFormValues {
  username: string;
  password: string;
  remember?: boolean;
}

const LoginForm: React.FC = () => {
  // 使用泛型创建类型安全的 FormInstance
  const [form] = Form.useForm<LoginFormValues>();

  const onFinish = (values: LoginFormValues) => {
    console.log('Form values:', values);
    // values.username, values.password, values.remember 都是类型安全的
  };

  return (
    <Form<LoginFormValues>
      form={form}
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.Item<LoginFormValues>
        label="Username"
        name="username"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>

      <Form.Item<LoginFormValues>
        label="Password"
        name="password"
        rules={[{ required: true }]}
      >
        <Input.Password />
      </Form.Item>

      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
};
```

### 组件 Props 类型定义

```tsx
import { Button, Space } from 'antd';
import type { ButtonProps } from 'antd';

// 扩展 antd 组件 Props
interface MyButtonProps extends Omit<ButtonProps, 'onClick'> {
  customProp?: string;
  onClick: (data: { timestamp: number }) => void;
}

const MyButton: React.FC<MyButtonProps> = ({ onClick, customProp, ...restProps }) => {
  const handleClick = () => {
    onClick({ timestamp: Date.now() });
  };

  return <Button {...restProps} onClick={handleClick} />;
};

// 使用
const App: React.FC = () => {
  return (
    <MyButton
      type="primary"
      customProp="value"
      onClick={(data) => console.log(data.timestamp)}
    >
      Click me
    </MyButton>
  );
};
```

## 从 v4 迁移到 v5

### 主要变化

1. **CSS-in-JS 替代 Less**
   - v5 使用 CSS-in-JS,不再提供 Less 文件
   - 移除 `antd/dist/antd.css`,改用 `antd/dist/reset.css`

2. **移除 babel-plugin-import**
   - v5 默认支持按需加载
   - 从 babel 配置中移除 `babel-plugin-import`

3. **API 统一**
   - `visible` → `open` (Modal, Drawer, Dropdown 等)
   - `dropdownClassName` → `popupClassName` (Select, DatePicker 等)

4. **Day.js 替代 Moment.js**
   - v5 内置 Day.js 处理日期
   - 不再依赖 Moment.js

### 迁移步骤

**1. 升级 antd 版本**:

```bash
npm install antd@latest
```

**2. 移除 babel-plugin-import**:

```diff
// .babelrc or babel.config.js
{
  "plugins": [
-   ["import", { "libraryName": "antd", "libraryDirectory": "es", "style": "css" }]
  ]
}
```

**3. 更新样式导入**:

```diff
- import 'antd/dist/antd.css';
+ import 'antd/dist/reset.css';
```

**4. 更新 API**:

```diff
- <Modal visible={open} />
+ <Modal open={open} />

- <Select dropdownClassName="my-dropdown" />
+ <Select popupClassName="my-dropdown" />

- import moment from 'moment';
+ import dayjs from 'dayjs';
```

**5. 更新主题配置**:

```diff
- import { ConfigProvider } from 'antd';
- import zhCN from 'antd/es/locale/zh_CN';

<ConfigProvider
-  locale={zhCN}
+  locale={zhCN}
   theme={{
-    primaryColor: '#1677ff',
+    token: {
+      colorPrimary: '#1677ff',
+    },
   }}
>
```

**6. 迁移工具**:

Ant Design 提供了自动化迁移工具:

```bash
# 使用 codemod 自动迁移
npx -p @ant-design/codemod-v5 antd5-codemod src
```

> **注意**: codemod 不能覆盖所有场景,建议手动检查并测试。

### 兼容 v4 主题

如果需要保持 v4 样式,安装兼容包:

```bash
npm install @ant-design/compatible
```

```tsx
import { ConfigProvider } from 'antd';
import { defaultTheme } from '@ant-design/compatible';

<ConfigProvider theme={defaultTheme}>
  <YourApp />
</ConfigProvider>
```

## 最佳实践

### 1. 组件导入

```tsx
// ✅ 推荐: 按需导入
import { Button, Form, Input } from 'antd';

// ❌ 避免: 导入整个 antd
import * as antd from 'antd';
```

### 2. 样式定制

```tsx
// ✅ 推荐: 使用 ConfigProvider 和 Design Token
<ConfigProvider
  theme={{
    token: { colorPrimary: '#1677ff' },
    components: { Button: { borderRadius: 4 } },
  }}
>
  <App />
</ConfigProvider>

// ❌ 避免: 直接覆盖 CSS
.ant-btn {
  border-radius: 4px !important;
}
```

### 3. 表单验证

```tsx
// ✅ 推荐: 使用 Form.List 管理动态字段
<Form.List name="users">
  {(fields) => (
    <>
      {fields.map((field) => (
        <Form.Item {...field} name={[field.name, 'firstName']} />
      ))}
    </>
  )}
</Form.List>

// ❌ 避免: 手动管理状态
const [users, setUsers] = useState([{ firstName: '' }]);
```

### 4. 性能优化

```tsx
// ✅ 推荐: 使用 useMemo 缓存计算结果
const columns = useMemo(() => [
  { title: 'Name', dataIndex: 'name' },
  { title: 'Age', dataIndex: 'age' },
], []);

// ✅ 推荐: 使用虚拟滚动处理大数据
<Table
  dataSource={largeData}
  columns={columns}
  scroll={{ y: 500 }}
  pagination={false}
/>
```

### 5. TypeScript 严格模式

```tsx
// ✅ 推荐: 启用严格类型检查
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
  }
}

// ✅ 推荐: 使用类型断言而非 any
const form = Form.useForm<MyFormValues>(); // 类型安全
// vs
const form: any = Form.useForm(); // 不推荐
```

## 参考资源

- **官方文档**: [ant.design](https://ant.design/)
- **中文文档**: [ant.design/index-cn](https://ant.design/index-cn)
- **GitHub**: [ant-design/ant-design](https://github.com/ant-design/ant-design)
- **主题定制**: [Customize Theme](https://ant.design/docs/react/customize-theme)
- **迁移指南**: [V4 to V5](https://5x.ant.design/docs/react/migration-v5)
- **更新日志**: [Changelog](https://ant.design/changelog)
- **组件演示**: [Ant Design Components](https://ant.design/components/overview-cn)
- **社区资源**: [Ant Design Resources](https://ant.design/docs/react/resources)

### 示例项目

- [React + Vite + Ant Design Starter](https://github.com/qqxs/react-antd-typescript-starter)
- [Next.js + Ant Design 最佳实践](https://juejin.cn/post/7589093895326203913)
- [React 18 + AntD 5 + Vite 搭建指南](https://juejin.cn/post/7260526125847838757)

### 社区教程

- [Ant Design 主题定制指南 2025](https://blog.csdn.net/gitblog_00220/article/details/152097203)
- [Ant Design 5 主题切换实现](https://blog.gitcode.com/805f48a19a22d308aedbefd8fddd55d9.html)
- [Ant Design 版本迁移避坑指南](https://blog.gitcode.com/30a9678c993dc2ba96126c6aac0bcfa2.html)

## 常见问题

### Q: antd 5.x 为什么不再需要 babel-plugin-import?

A: antd 5.x 使用 CSS-in-JS 技术,样式是按需生成的。不再需要 Less 编译和 CSS 文件,因此不需要 babel-plugin-import。

### Q: 如何解决样式冲突?

A: 使用 `ConfigProvider` 的 `prefixCls` 配置前缀:

```tsx
<ConfigProvider prefixCls="custom">
  <App />
</ConfigProvider>
```

### Q: DatePicker 显示英文怎么办?

A: 配置 `ConfigProvider` 的 locale:

```tsx
import zhCN from 'antd/locale/zh_CN';

<ConfigProvider locale={zhCN}>
  <App />
</ConfigProvider>
```

### Q: 如何自定义组件样式?

A: 使用 `className` 或 `style` prop,或者通过 `ConfigProvider.theme.components` 配置:

```tsx
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: '#00b96b',
        algorithm: true,
      },
    },
  }}
>
  <App />
</ConfigProvider>
```

### Q: 如何禁用某个日期?

A: 使用 DatePicker 的 `disabledDate` 属性:

```tsx
<DatePicker
  disabledDate={(current) => {
    return current && current < dayjs().endOf('day');
  }}
/>
```

### Q: 表单如何重置?

A: 使用 `form.resetFields()`:

```tsx
const [form] = Form.useForm();

const onReset = () => {
  form.resetFields();
};
```

### Q: 如何实现远程搜索 Select?

A: 使用 `onSearch` 和 `filterOption={false}`:

```tsx
<Select
  showSearch
  filterOption={false}
  onSearch={(value) => {
    // 远程搜索逻辑
    fetchData(value);
  }}
  options={options}
/>
```

## 总结

Ant Design 5.x 提供了:

- **现代化技术栈**: 支持 React 18+、React 19、Vite、Next.js
- **强大的主题系统**: CSS-in-JS + Design Token 实现灵活定制
- **完整的 TypeScript 支持**: 类型安全的开发体验
- **丰富的组件**: 60+ 高质量组件覆盖企业应用场景
- **优秀的工程化**: 按需加载、Tree Shaking、性能优化

**核心要点**:

1. 使用 `ConfigProvider` 管理全局主题和配置
2. 利用 TypeScript 泛型实现类型安全
3. 遵循设计规范构建一致的用户体验
4. 合理使用组件组合实现复杂业务场景
5. 关注性能优化,避免不必要的渲染

快速上手 Ant Design,构建现代化的企业级 React 应用!

---

**最后更新**: 2026-02-10
**文档版本**: 1.0.0
**Ant Design 版本**: 5.29.2
