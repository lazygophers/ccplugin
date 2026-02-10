---
name: antd-nextjs-skills
description: Ant Design Next.js 集成完整指南 - App Router、Pages Router、SSR、AntdRegistry、静态导出、部署优化
---

# Ant Design Next.js 集成完整指南

## 概述

Ant Design 5.x 与 Next.js 的深度集成方案,覆盖 App Router 和 Pages Router 两种架构,提供完整的 SSR、SSG、主题持久化和生产级部署方案。

**核心特性**:

- **双路由支持**: App Router (推荐) 和 Pages Router 完整方案
- **SSR 优化**: AntdRegistry 组件避免样式闪烁
- **主题持久化**: 服务端和客户端主题状态同步
- **静态导出**: 完整的 output: 'export' 配置指南
- **流式渲染**: React Server Components 和 Suspense 支持
- **部署优化**: Vercel、Docker、CDN 部署方案
- **性能优化**: 代码分割、懒加载、SSR 性能调优

**版本要求**:

- Next.js >= 13.4 (App Router) 或 >= 12 (Pages Router)
- Ant Design >= 5.0.0
- React >= 18.2.0
- Node.js >= 18.17.0

---

## Next.js 版本选择

### App Router (推荐)

Next.js 13+ 推出的新路由架构,基于 React Server Components。

**优势**:

- Server Components 默认启用,减少客户端 JavaScript
- Streaming 和 Suspense 支持
- 内置布局系统
- 并行路由和拦截路由
- 更好的 SEO 和性能

**适用场景**:

- 新项目
- 需要极致性能的应用
- 内容密集型网站

### Pages Router

Next.js 12 及以下使用的传统路由架构。

**优势**:

- 成熟稳定
- 丰富的生态系统
- 迁移成本低

**适用场景**:

- 现有项目维护
- 依赖大量 Pages Router 特性的应用

---

## App Router 集成 (深入讲解)

### 项目结构

```
my-antd-nextjs/
├── app/
│   ├── layout.tsx              # 根布局 (AntdRegistry)
│   ├── page.tsx                # 主页面
│   ├── globals.css             # 全局样式
│   ├── theme/
│   │   ├── theme-provider.tsx  # 主题上下文
│   │   └── registry.tsx        # AntdRegistry 包装
│   └── dashboard/
│       ├── layout.tsx          # 嵌套布局
│       └── page.tsx            # 仪表板页面
├── components/
│   ├── client-wrapper.tsx      # 客户端组件包装
│   └── server-component.tsx    # 服务端组件示例
├── lib/
│   └── utils.ts                # 工具函数
├── public/                     # 静态资源
├── next.config.js              # Next.js 配置
├── package.json
└── tsconfig.json
```

### 示例 1: App Router 基础集成

完整的 Next.js 13+ App Router 与 Ant Design 集成示例。

**next.config.js**:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['antd'],
  experimental: {
    esmExternals: false,
  },
  // 优化 CSS 导入
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
};

module.exports = nextConfig;
```

**app/layout.tsx** (根布局):
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AntdRegistry } from './theme/registry';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Next.js + Ant Design App Router',
  description: 'Ant Design 5 with Next.js 13+ App Router',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  );
}
```

**app/theme/registry.tsx** (AntdRegistry 组件):
```typescript
'use client';

import React, { useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import type { ThemeConfig } from 'antd';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  themeConfig: ThemeConfig;
}

export const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = React.useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within ThemeContext.Provider');
  }
  return context;
};

export const AntdRegistry: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 从 LocalStorage 读取主题偏好
  React.useEffect(() => {
    const savedTheme = localStorage.getItem('antd-theme-mode');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      // 检测系统主题
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDark);
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('antd-theme-mode', newMode ? 'dark' : 'light');
  };

  const themeConfig: ThemeConfig = {
    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 8,
      fontSize: 14,
    },
    components: {
      Button: {
        borderRadius: 6,
        controlHeight: 38,
      },
      Input: {
        borderRadius: 6,
        controlHeight: 38,
      },
    },
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, themeConfig }}>
      <ConfigProvider theme={themeConfig} locale={zhCN}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};
```

**app/page.tsx** (主页面):
```typescript
'use client';

import React from 'react';
import { Button, Card, Space, Typography, Layout } from 'antd';
import { useThemeContext } from './theme/registry';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph, Text } = Typography;

export default function HomePage() {
  const { isDarkMode, toggleTheme, themeConfig } = useThemeContext();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isDarkMode ? '#141414' : '#001529',
          padding: '0 24px',
        }}
      >
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          Next.js App Router + Ant Design
        </Title>
        <Button
          type="primary"
          onClick={toggleTheme}
          style={{ background: isDarkMode ? '#ffffff' : '#1677ff', color: isDarkMode ? '#000000' : '#fff' }}
        >
          {isDarkMode ? '🌙 深色' : '☀️ 浅色'}
        </Button>
      </Header>

      <Content style={{ padding: '50px 50px' }}>
        <Space direction="vertical" size="large" style={{ display: 'flex', width: '100%' }}>
          <Card>
            <Title level={2}>欢迎使用 Ant Design Next.js 集成方案</Title>
            <Paragraph>
              本示例展示了如何在 Next.js App Router 中正确集成 Ant Design 5.x。
            </Paragraph>
            <Space>
              <Text type="secondary">当前主题: </Text>
              <Text strong>{isDarkMode ? '深色模式' : '浅色模式'}</Text>
            </Space>
          </Card>

          <Card title="组件预览">
            <Space>
              <Button type="primary">主按钮</Button>
              <Button>默认按钮</Button>
              <Button type="dashed">虚线按钮</Button>
              <Button type="link">链接按钮</Button>
            </Space>
          </Card>

          <Card title="主题配置信息">
            <Space direction="vertical" style={{ display: 'flex' }}>
              <Text>
                <strong>主色调:</strong> {themeConfig.token?.colorPrimary}
              </Text>
              <Text>
                <strong>圆角:</strong> {themeConfig.token?.borderRadius}px
              </Text>
              <Text>
                <strong>字体大小:</strong> {themeConfig.token?.fontSize}px
              </Text>
            </Space>
          </Card>
        </Space>
      </Content>

      <Footer style={{ textAlign: 'center' }}>
        Ant Design Next.js ©{new Date().getFullYear()} Created with App Router
      </Footer>
    </Layout>
  );
}
```

**app/globals.css**:
```css
:root {
  --antd-prefix: ant;
}

/* 避免服务端渲染不匹配 */
* {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

html,
body {
  max-width: 100vw;
  overflow-x: hidden;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
```

**关键实现要点**:

1. **AntdRegistry 组件**:
   - 使用 `'use client'` 标记为客户端组件
   - 通过 Context 提供主题状态和切换方法
   - 在 `useEffect` 中读取 LocalStorage 避免水合不匹配

2. **根布局**:
   - 服务端组件,无需 `'use client'`
   - 包裹 AntdRegistry 提供全局主题
   - 配置全局字体和元数据

3. **页面组件**:
   - 使用 `'use client'` 标记客户端交互组件
   - 通过 `useThemeContext` Hook 访问主题状态
   - 实现主题切换按钮

### 示例 2: 服务端组件中使用 Ant Design

展示如何在 Server Components 中使用 Ant Design 组件。

**app/products/page.tsx** (服务端组件):
```typescript
import React from 'react';
import { Card, Table, Tag, Space, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;

interface Product {
  key: string;
  name: string;
  price: number;
  category: string;
  status: 'in_stock' | 'out_of_stock' | 'preorder';
}

// 模拟数据获取 (可以是数据库查询)
async function getProducts(): Promise<Product[]> {
  return [
    {
      key: '1',
      name: 'iPhone 15 Pro',
      price: 7999,
      category: '手机',
      status: 'in_stock',
    },
    {
      key: '2',
      name: 'MacBook Pro',
      price: 14999,
      category: '电脑',
      status: 'out_of_stock',
    },
    {
      key: '3',
      name: 'AirPods Pro',
      price: 1999,
      category: '耳机',
      status: 'preorder',
    },
  ];
}

const columns: ColumnsType<Product> = [
  {
    title: '产品名称',
    dataIndex: 'name',
    key: 'name',
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: '价格',
    dataIndex: 'price',
    key: 'price',
    render: (price: number) => `¥${price.toLocaleString()}`,
    sorter: (a, b) => a.price - b.price,
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    filters: [
      { text: '手机', value: '手机' },
      { text: '电脑', value: '电脑' },
      { text: '耳机', value: '耳机' },
    ],
    onFilter: (value, record) => record.category === value,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: Product['status']) => {
      const config = {
        in_stock: { color: 'success', text: '有货' },
        out_of_stock: { color: 'error', text: '缺货' },
        preorder: { color: 'processing', text: '预售' },
      };
      return <Tag color={config[status].color}>{config[status].text}</Tag>;
    },
  },
];

export default async function ProductsPage() {
  // 服务端数据获取
  const products = await getProducts();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>产品列表</Title>

      <Card>
        <Table
          columns={columns}
          dataSource={products}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条数据`,
          }}
        />
      </Card>
    </div>
  );
}
```

**注意事项**:

- Server Components 不能使用 hooks (useState, useEffect)
- 数据获取直接在组件中进行,无需 useEffect
- Ant Design 组件可以在 Server Components 中使用,但交互功能需要客户端组件

### 示例 3: 客户端组件与服务端组件混合

展示如何组合使用 Server Components 和 Client Components。

**app/dashboard/page.tsx**:
```typescript
import React from 'react';
import { Card, Typography, Space } from 'antd';
import { UserStats } from './components/user-stats';
import { ActivityChart } from './components/activity-chart';

const { Title } = Typography;

export default async function DashboardPage() {
  // 服务端获取统计数据
  const stats = await fetchUserStats();
  const recentActivity = await fetchRecentActivity();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>仪表板</Title>

      <Space direction="vertical" size="large" style={{ display: 'flex', width: '100%' }}>
        {/* 服务端渲染的统计卡片 */}
        <Card title="用户统计">
          <Space size="large">
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {stats.totalUsers}
              </div>
              <div style={{ color: '#888' }}>总用户数</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {stats.activeUsers}
              </div>
              <div style={{ color: '#888' }}>活跃用户</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {stats.newUsersToday}
              </div>
              <div style={{ color: '#888' }}>今日新增</div>
            </div>
          </Space>
        </Card>

        {/* 客户端交互组件 */}
        <UserStats initialData={stats} />

        {/* 图表组件 (需要客户端交互) */}
        <ActivityChart data={recentActivity} />
      </Space>
    </div>
  );
}

// 服务端数据获取函数
async function fetchUserStats() {
  // 模拟 API 调用
  return {
    totalUsers: 1234,
    activeUsers: 567,
    newUsersToday: 89,
  };
}

async function fetchRecentActivity() {
  // 模拟 API 调用
  return [
    { date: '2026-01-01', value: 100 },
    { date: '2026-01-02', value: 120 },
    { date: '2026-01-03', value: 90 },
  ];
}
```

**app/dashboard/components/user-stats.tsx** (客户端组件):
```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { UserOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

interface UserStatsProps {
  initialData: {
    totalUsers: number;
    activeUsers: number;
    newUsersToday: number;
  };
}

export const UserStats: React.FC<UserStatsProps> = ({ initialData }) => {
  const [stats, setStats] = useState(initialData);

  // 客户端实时更新
  useEffect(() => {
    const interval = setInterval(() => {
      // 模拟实时数据更新
      setStats((prev) => ({
        ...prev,
        activeUsers: prev.activeUsers + Math.floor(Math.random() * 10) - 5,
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Row gutter={16}>
      <Col span={8}>
        <Card>
          <Statistic
            title="总用户数"
            value={stats.totalUsers}
            prefix={<UserOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card>
          <Statistic
            title="活跃用户"
            value={stats.activeUsers}
            prefix={<ArrowUpOutlined />}
            valueStyle={{ color: '#1677ff' }}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card>
          <Statistic
            title="今日新增"
            value={stats.newUsersToday}
            prefix={<ArrowDownOutlined />}
            valueStyle={{ color: '#cf1322' }}
          />
        </Card>
      </Col>
    </Row>
  );
};
```

**app/dashboard/components/activity-chart.tsx** (客户端组件):
```typescript
'use client';

import React from 'react';
import { Card } from 'antd';
import { Line } from '@ant-design/plots';

interface ActivityChartProps {
  data: Array<{ date: string; value: number }>;
}

export const ActivityChart: React.FC<ActivityChartProps> = ({ data }) => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    point: {
      size: 5,
      shape: 'diamond',
    },
    label: {
      style: {
        fill: '#aaa',
      },
    },
    lineStyle: {
      stroke: '#1677ff',
      lineWidth: 2,
    },
  };

  return (
    <Card title="最近活动">
      <Line {...config} />
    </Card>
  );
};
```

**关键点**:

- Server Components 负责数据获取和静态内容渲染
- Client Components 负责交互和动态更新
- 通过 props 传递数据,实现组件组合

---

## Pages Router 集成

### 项目结构

```
my-antd-nextjs-pages/
├── pages/
│   ├── _app.tsx                 # App 组件 (ConfigProvider)
│   ├── _document.tsx            # Document 组件 (自定义 Head)
│   ├── index.tsx                # 主页面
│   └── dashboard.tsx            # 仪表板页面
├── styles/
│   └── globals.css              # 全局样式
├── next.config.js
├── package.json
└── tsconfig.json
```

### 示例 4: Pages Router 基础集成

**next.config.js**:
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

**pages/_app.tsx**:
```typescript
import type { AppProps } from 'next/app';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { theme } from 'antd';
import 'antd/dist/reset.css';
import '../styles/globals.css';

// 主题配置
const getThemeConfig = (isDarkMode: boolean) => ({
  algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 8,
  },
});

function MyApp({ Component, pageProps }: AppProps & { isDarkMode?: boolean }) {
  // 从页面 props 或全局状态获取主题模式
  const isDarkMode = pageProps.isDarkMode || false;

  return (
    <ConfigProvider
      theme={getThemeConfig(isDarkMode)}
      locale={zhCN}
    >
      <Component {...pageProps} />
    </ConfigProvider>
  );
}

export default MyApp;
```

**pages/_document.tsx**:
```typescript
import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="zh-CN">
      <Head>
        <meta charSet="utf-8" />
        <link rel="icon" href="/favicon.ico" />
        <meta name="description" content="Next.js + Ant Design Pages Router" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
```

**pages/index.tsx**:
```typescript
import React, { useState, useEffect } from 'react';
import { Button, Card, Space, Typography, Layout } from 'antd';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

interface HomePageProps {
  initialTheme?: 'light' | 'dark';
}

export default function HomePage({ initialTheme = 'light' }: HomePageProps) {
  const [isDarkMode, setIsDarkMode] = useState(initialTheme === 'dark');

  useEffect(() => {
    // 从 LocalStorage 读取主题偏好
    const savedTheme = localStorage.getItem('theme-mode');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('theme-mode', newMode ? 'dark' : 'light');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isDarkMode ? '#141414' : '#001529',
          padding: '0 24px',
        }}
      >
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          Next.js Pages Router + Ant Design
        </Title>
        <Button
          type="primary"
          onClick={toggleTheme}
        >
          {isDarkMode ? '🌙 切换到浅色' : '☀️ 切换到深色'}
        </Button>
      </Header>

      <Content style={{ padding: '50px 50px' }}>
        <Card>
          <Title level={2}>欢迎使用 Ant Design</Title>
          <Paragraph>
            本示例展示了如何在 Next.js Pages Router 中集成 Ant Design 5.x。
          </Paragraph>
          <Space>
            <Button type="primary">主按钮</Button>
            <Button>默认按钮</Button>
            <Button type="dashed">虚线按钮</Button>
          </Space>
        </Card>
      </Content>

      <Footer style={{ textAlign: 'center' }}>
        Ant Design Next.js ©{new Date().getFullYear()} Created with Pages Router
      </Footer>
    </Layout>
  );
}

// 服务端渲染初始主题状态
HomePage.getInitialProps = async () => {
  return {
    initialTheme: 'light',
  };
};
```

**styles/globals.css**:
```css
:root {
  --antd-prefix: ant;
}

html,
body {
  padding: 0;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

---

## SSR 主题处理 (深入)

### 问题分析

在 SSR 环境中使用 Ant Design 主题时,会遇到以下问题:

1. **水合不匹配 (Hydration Mismatch)**: 服务端渲染的主题与客户端初始状态不一致
2. **样式闪烁**: 主题切换时页面出现短暂的样式跳动
3. **LocalStorage 不可用**: 服务端无法访问浏览器的 LocalStorage

### 示例 5: 完整的 SSR 主题解决方案

**app/theme/theme-provider.tsx**:
```typescript
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import type { ThemeConfig } from 'antd';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  themeConfig: ThemeConfig;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: 'light' | 'dark';
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'light',
}) => {
  const [isDarkMode, setIsDarkMode] = useState(defaultTheme === 'dark');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);

    // 从 LocalStorage 读取主题偏好
    const savedTheme = localStorage.getItem('antd-theme-mode');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      // 检测系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDark);
    }

    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('antd-theme-mode')) {
        setIsDarkMode(e.matches);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('antd-theme-mode', newMode ? 'dark' : 'light');
  };

  const themeConfig: ThemeConfig = {
    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 8,
      fontSize: 14,
      fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial`,
    },
    components: {
      Button: {
        borderRadius: 6,
        controlHeight: 38,
        controlHeightLG: 46,
        controlHeightSM: 30,
      },
      Input: {
        borderRadius: 6,
        controlHeight: 38,
      },
      Card: {
        borderRadiusLG: 12,
      },
      Layout: {
        headerBg: isDarkMode ? '#141414' : '#001529',
        siderBg: isDarkMode ? '#141414' : '#001529',
      },
    },
  };

  // 避免服务端渲染不匹配
  if (!isClient) {
    return (
      <ThemeContext.Provider value={{ isDarkMode, toggleTheme, themeConfig }}>
        <ConfigProvider theme={themeConfig}>
          {children}
        </ConfigProvider>
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, themeConfig }}>
      <ConfigProvider theme={themeConfig}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};
```

**app/layout.tsx** (使用 ThemeProvider):
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from './theme/theme-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Next.js + Ant Design SSR 主题示例',
  description: 'Ant Design 5 SSR 主题处理完整方案',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider defaultTheme="light">{children}</ThemeProvider>
      </body>
    </html>
  );
}
```

**app/page.tsx** (使用主题):
```typescript
'use client';

import React from 'react';
import { Button, Card, Space, Typography, Layout, Switch, Divider } from 'antd';
import { useTheme } from './theme/theme-provider';

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

export default function HomePage() {
  const { isDarkMode, toggleTheme, themeConfig } = useTheme();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isDarkMode ? '#141414' : '#001529',
          padding: '0 24px',
        }}
      >
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          SSR 主题处理示例
        </Title>
        <Switch
          checked={isDarkMode}
          onChange={toggleTheme}
          checkedChildren="深色"
          unCheckedChildren="浅色"
          style={{ background: isDarkMode ? '#ffffff' : '#1677ff' }}
        />
      </Header>

      <Content style={{ padding: '50px 50px' }}>
        <Space direction="vertical" size="large" style={{ display: 'flex', width: '100%' }}>
          <Card>
            <Title level={2}>服务端渲染主题处理</Title>
            <Paragraph>
              本示例展示了如何在 Next.js SSR 环境中正确处理 Ant Design 主题,
              避免水合不匹配和样式闪烁问题。
            </Paragraph>
          </Card>

          <Card title="主题状态">
            <Space direction="vertical" style={{ display: 'flex' }}>
              <Text>
                <strong>当前主题:</strong> {isDarkMode ? '🌙 深色模式' : '☀️ 浅色模式'}
              </Text>
              <Text>
                <strong>主色调:</strong> {themeConfig.token?.colorPrimary}
              </Text>
              <Text>
                <strong>圆角:</strong> {themeConfig.token?.borderRadius}px
              </Text>
            </Space>
            <Divider />
            <Space>
              <Button type="primary" onClick={toggleTheme}>
                切换主题
              </Button>
              <Button>默认按钮</Button>
              <Button type="dashed">虚线按钮</Button>
            </Space>
          </Card>

          <Card title="组件预览">
            <Space direction="vertical" style={{ display: 'flex', width: '100%' }}>
              <Space>
                <Button type="primary">主按钮</Button>
                <Button>默认按钮</Button>
                <Button type="dashed">虚线按钮</Button>
                <Button type="link">链接按钮</Button>
                <Button danger>危险按钮</Button>
              </Space>

              <Space>
                <Button type="primary" size="large">
                  大号按钮
                </Button>
                <Button type="primary">中号按钮</Button>
                <Button type="primary" size="small">
                  小号按钮
                </Button>
              </Space>

              <Button type="primary" block>
                区块按钮
              </Button>
            </Space>
          </Card>
        </Space>
      </Content>
    </Layout>
  );
}
```

**关键实现要点**:

1. **isClient 状态**:
   - 初始值为 `false`,避免服务端渲染不匹配
   - 在 `useEffect` 中设置为 `true`,确保客户端渲染

2. **suppressHydrationWarning**:
   - 在 `html` 标签上添加,抑制主题相关的水合警告

3. **LocalStorage 读取**:
   - 只在 `isClient` 为 `true` 后读取
   - 避免服务端访问浏览器 API

4. **主题持久化**:
   - 主题切换时保存到 LocalStorage
   - 页面刷新后自动恢复

---

## 静态导出

Next.js 支持将应用导出为纯静态网站,无需 Node.js 服务器。

### 示例 6: 静态导出配置

**next.config.js** (配置静态导出):
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // 启用静态导出
  images: {
    unoptimized: true, // 禁用图片优化
  },
  trailingSlash: true, // 添加尾部斜杠
  distDir: 'out', // 输出目录
};

module.exports = nextConfig;
```

**package.json** (添加构建脚本):
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "export": "next build",
    "serve": "npx serve out -p 3000"
  }
}
```

**执行静态导出**:
```bash
npm run export
```

导出后的文件结构:
```
out/
├── index.html
├── 404.html
├── dashboard.html
├── _next/
│   └── static/
│       ├── chunks/
│       └── css/
└── images/
```

**注意事项**:

1. **图片优化**:
   - 静态导出不支持 Next.js Image 组件的优化功能
   - 使用 `unoptimized: true` 或使用标准 `<img>` 标签

2. **API 路由**:
   - 静态导出不支持 API 路由
   - 数据获取必须在构建时完成

3. **动态路由**:
   - 使用 `generateStaticParams` 预渲染动态路由
   - 或使用 `fallback: 'blocking'` 运行时渲染

4. **部署**:
   - 可以部署到任何静态托管服务 (Vercel、Netlify、GitHub Pages)
   - 无需 Node.js 服务器

**app/dashboard/[id]/page.tsx** (动态路由静态导出):
```typescript
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

// 生成静态参数
export async function generateStaticParams() {
  // 返回所有可能的 ID
  return [
    { id: '1' },
    { id: '2' },
    { id: '3' },
  ];
}

// 获取静态数据
async function getDashboardData(id: string) {
  // 模拟 API 调用
  return {
    id,
    title: `Dashboard ${id}`,
    description: `This is dashboard ${id}`,
  };
}

export default async function DashboardPage({ params }: { params: { id: string } }) {
  const data = await getDashboardData(params.id);

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={2}>{data.title}</Title>
        <Paragraph>{data.description}</Paragraph>
      </Card>
    </div>
  );
}
```

---

## 部署优化

### Vercel 部署

**vercel.json** (Vercel 配置):
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["hkg1"],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

**部署步骤**:
```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
vercel

# 生产部署
vercel --prod
```

### Docker 部署

**Dockerfile**:
```dockerfile
# 构建 stage
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 运行 stage
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production

# 复制必要文件
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# 暴露端口
EXPOSE 3000

# 启动应用
CMD ["node", "server.js"]
```

**next.config.js** (standalone 输出):
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // 启用 standalone 输出
  reactStrictMode: true,
  transpilePackages: ['antd'],
};

module.exports = nextConfig;
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  nextjs-app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

**构建和运行**:
```bash
# 构建镜像
docker build -t nextjs-antd-app .

# 运行容器
docker run -p 3000:3000 nextjs-antd-app

# 使用 docker-compose
docker-compose up -d
```

### CDN 配置

**app/utils/cdn-loader.ts** (CDN 资源加载):
```typescript
export const CDN_BASE_URL = process.env.NEXT_PUBLIC_CDN_URL || '';

export const getCdnUrl = (path: string) => {
  if (!CDN_BASE_URL) return path;
  return `${CDN_BASE_URL}${path}`;
};

// 图片 CDN
export const getImageUrl = (imagePath: string) => {
  return getCdnUrl(`/images${imagePath}`);
};

// 静态资源 CDN
export const getAssetUrl = (assetPath: string) => {
  return getCdnUrl(`/assets${assetPath}`);
};
```

**next.config.js** (CDN 配置):
```javascript
const CDN_URL = process.env.CDN_URL || '';

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['antd'],

  // 静态资源 CDN
  assetPrefix: CDN_URL,

  // 图片优化
  images: {
    domains: [CDN_URL.replace('https://', '').replace('http://', '')],
  },
};

module.exports = nextConfig;
```

---

## 最佳实践

### 1. 性能优化

**代码分割**:
```typescript
import dynamic from 'next/dynamic';

// 动态导入 Ant Design 组件
const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
  loading: () => <div>Loading...</div>,
  ssr: false, // 禁用 SSR
});
```

**图片优化**:
```typescript
import Image from 'next/image';

// 使用 Next.js Image 组件
<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={100}
  priority // 首屏图片
/>
```

**字体优化**:
```typescript
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  preload: true,
});
```

### 2. SEO 优化

**元数据配置**:
```typescript
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Next.js + Ant Design',
  description: 'Built with Next.js and Ant Design',
  keywords: ['Next.js', 'Ant Design', 'React'],
  authors: [{ name: 'Your Name' }],
  openGraph: {
    title: 'Next.js + Ant Design',
    description: 'Built with Next.js and Ant Design',
    type: 'website',
  },
};
```

### 3. 环境变量管理

**.env.local**:
```bash
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_CDN_URL=https://cdn.example.com
ANTD_PRIMARY_COLOR=#1677ff
```

**使用环境变量**:
```typescript
const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: process.env.ANTD_PRIMARY_COLOR || '#1677ff',
  },
};
```

### 4. 错误处理

**app/error.tsx** (错误边界):
```typescript
'use client';

import React from 'react';
import { Result, Button } from 'antd';

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div style={{ padding: '50px' }}>
      <Result
        status="error"
        title="发生错误"
        subTitle={error.message}
        extra={
          <Button type="primary" onClick={reset}>
            重试
          </Button>
        }
      />
    </div>
  );
}
```

**app/not-found.tsx** (404 页面):
```typescript
import { Result, Button } from 'antd';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div style={{ padding: '50px' }}>
      <Result
        status="404"
        title="404"
        subTitle="抱歉,您访问的页面不存在。"
        extra={
          <Button type="primary" href="/">
            返回首页
          </Button>
        }
      />
    </div>
  );
}
```

### 5. 测试

**组件测试**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from 'antd';

test('renders button', () => {
  render(<Button type="primary">Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});

test('button click', () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click me</Button>);

  fireEvent.click(screen.getByText('Click me'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});
```

---

## 常见问题

### Q1: App Router 和 Pages Router 如何选择?

**A**: 新项目推荐使用 App Router,现有项目可以继续使用 Pages Router。App Router 提供更好的性能和开发体验。

### Q2: SSR 时主题闪烁如何解决?

**A**: 使用 `isClient` 状态和 `suppressHydrationWarning`,并在 `useEffect` 中读取 LocalStorage。

### Q3: 静态导出后样式丢失?

**A**: 确保 `next.config.js` 中配置了 `output: 'export'`,并检查 Ant Design 样式是否正确导入。

### Q4: 如何实现主题切换动画?

**A**: 在 CSS 中添加过渡动画:
```css
* {
  transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}
```

### Q5: Ant Design 图标在 Next.js 中报错?

**A**: 使用动态导入:
```typescript
import dynamic from 'next/dynamic';

const Icon = dynamic(() => import('@ant-design/icons'), { ssr: false });
```

---

## 参考资源

### 官方文档
- [Ant Design Next.js 集成](https://ant.design/docs/react/use-in-nextjs)
- [Ant Design 兼容性方案](https://ant.design/docs/react/compatible-style)
- [Next.js App Router 文档](https://nextjs.org/docs/app)
- [Next.js Pages Router 文档](https://nextjs.org/docs/pages)

### 示例项目
- [Next.js + Ant Design Starter](https://github.com/ant-design/ant-design-examples/tree/main/examples/nextjs-with-styled-jsx)
- [Ant Design Pro](https://pro.ant.design/)

### 社区资源
- [Next.js Discord](https://discord.com/invite/nextjs)
- [Ant Design GitHub Discussions](https://github.com/ant-design/ant-design/discussions)

---

## 总结

Ant Design 与 Next.js 的集成提供了强大的企业级应用开发能力:

**核心要点**:

1. **App Router 是推荐方案**,基于 React Server Components,提供更好的性能
2. **AntdRegistry 组件**解决 SSR 主题闪烁和水合不匹配问题
3. **主题持久化**通过 LocalStorage 实现,支持系统主题跟随
4. **静态导出**支持部署到任何静态托管服务
5. **部署优化**包括 Vercel、Docker、CDN 等多种方案

**最佳实践**:

- 使用 `'use client'` 标记需要交互的组件
- 在 Server Components 中处理数据获取
- 通过 Context 管理 全局主题状态
- 实现错误边界和 404 页面
- 优化代码分割和资源加载

**版本要求**:

- Next.js >= 13.4 (App Router)
- Ant Design >= 5.0.0
- React >= 18.2.0
- Node.js >= 18.17.0

开始构建你的 Next.js + Ant Design 应用吧!

---

**最后更新**: 2026-02-10
**Next.js 版本**: 14.x
**Ant Design 版本**: 5.x
**维护者**: ccplugin-market
