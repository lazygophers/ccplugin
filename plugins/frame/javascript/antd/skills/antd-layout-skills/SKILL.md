---
name: antd-layout-skills
description: Ant Design 布局系统完整指南 - Layout、Grid、Space、Divider、响应式布局
---

# Ant Design 布局系统完整指南

Ant Design 提供了一套强大且灵活的布局系统，帮助开发者快速构建专业的后台管理和展示型应用。本指南涵盖了 Layout 整体布局、Grid 栅格系统、Space 间距、Skeleton 骨架屏等核心布局组件。

## 目录

- [核心组件概述](#核心组件概述)
- [Layout 整体布局](#layout-整体布局)
- [Grid 栅格系统](#grid-栅格系统)
- [Space 间距](#space-间距)
- [Skeleton 骨架屏](#skeleton-骨架屏)
- [常见布局模式](#常见布局模式)
- [最佳实践](#最佳实践)
- [参考资源](#参考资源)

---

## 核心组件概述

### 布局组件对比

| 组件 | 用途 | 适用场景 |
|------|------|---------|
| **Layout** | 页面级整体布局 | 后台管理系统、展示型网站 |
| **Grid** | 24 栅格响应式布局 | 卡片网格、表单布局、数据展示 |
| **Space** | 行内元素间距 | 按钮、输入框、标签等小元素排列 |
| **Divider** | 内容分割 | 章节分隔、视觉分组 |
| **Skeleton** | 加载占位 | 数据加载时的占位显示 |

### 导入方式

```typescript
import {
  Layout,
  Grid,
  Space,
  Divider,
  Skeleton
} from 'antd';

// 或单独导入（推荐）
import Layout from 'antd/es/layout';
import Row from 'antd/es/row';
import Col from 'antd/es/col';
import Space from 'antd/es/space';
import Divider from 'antd/es/divider';
import Skeleton from 'antd/es/skeleton';

// 样式导入
import 'antd/es/layout/style';
import 'antd/es/grid/style';
import 'antd/es/space/style';
import 'antd/es/divider/style';
import 'antd/es/skeleton/style';
```

---

## Layout 整体布局

### 基本概念

Layout 组件协助进行页面级整体布局，提供以下子组件：

- **Layout**: 布局容器，可嵌套 Header、Sider、Content、Footer
- **Header**: 顶部布局，通常用于导航栏
- **Sider**: 侧边栏，支持收起/展开
- **Content**: 内容区域，放置主要业务内容
- **Footer**: 底部布局，放置版权信息等

### 设计规范

#### 尺寸规范

- **顶部导航高度**: `64px`（系统类）或 `80px`（展示类）
- **二级导航高度**: `48px`（系统类）或 `56px`（展示类）
- **侧边栏宽度**: `200px` + `8n`（224、256、284...）

#### 计算公式

```
顶部导航高度 = 48 + 8n  (n 为自然数)
侧边栏宽度 = 200 + 8n   (n 为自然数)
```

### 基础布局示例

#### 1. 上中下布局（Header + Content + Footer）

最经典的三段式布局，适用于展示型网站。

```typescript
import React from 'react';
import { Layout, Menu } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  SettingOutlined
} from '@ant-design/icons';

const { Header, Content, Footer } = Layout;

const TopBottomLayout: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航 */}
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: '#001529',
        padding: '0 50px'
      }}>
        <div style={{
          color: 'white',
          fontSize: '20px',
          fontWeight: 'bold',
          marginRight: '50px'
        }}>
          Logo
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={['1']}
          items={[
            { key: '1', icon: <HomeOutlined />, label: '首页' },
            { key: '2', icon: <UserOutlined />, label: '用户' },
            { key: '3', icon: <SettingOutlined />, label: '设置' }
          ]}
          style={{ flex: 1 }}
        />
      </Header>

      {/* 内容区域 */}
      <Content style={{
        padding: '50px',
        background: '#fff',
        marginTop: '64px'
      }}>
        <div style={{
          background: '#fff',
          padding: '24px',
          minHeight: 380
        }}>
          <h1>主要内容区域</h1>
          <p>这里是页面的主要内容...</p>
        </div>
      </Content>

      {/* 底部 */}
      <Footer style={{
        textAlign: 'center',
        background: '#f0f2f5'
      }}>
        Ant Design ©{new Date().getFullYear()} Created by Ant UED
      </Footer>
    </Layout>
  );
};

export default TopBottomLayout;
```

#### 2. 侧边栏布局（Sider + Content）

后台管理系统常用的左侧导航布局。

```typescript
import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SettingOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const SideLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { key: '1', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '2', icon: <UserOutlined />, label: '用户管理' },
    { key: '3', icon: <FileTextOutlined />, label: '文章管理' },
    { key: '4', icon: <SettingOutlined />, label: '系统设置' }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0
        }}
      >
        <div style={{
          height: '32px',
          margin: '16px',
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: '6px'
        }}>
          <Logo collapsed={collapsed} />
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['1']}
          items={menuItems}
        />
      </Sider>

      {/* 右侧内容区 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 200 }}>
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          {React.createElement(
            collapsed ? MenuUnfoldOutlined : MenuFoldOutlined,
            {
              className: 'trigger',
              onClick: () => setCollapsed(!collapsed),
              style: { fontSize: '18px', cursor: 'pointer' }
            }
          )}
          <span style={{ marginLeft: '16px', fontSize: '18px' }}>
            后台管理系统
          </span>
        </Header>

        <Content style={{
          margin: '24px 16px',
          padding: 24,
          background: '#fff',
          minHeight: 280
        }}>
          <h2>仪表盘</h2>
          <p>欢迎使用后台管理系统！</p>
        </Content>
      </Layout>
    </Layout>
  );
};

const Logo: React.FC<{ collapsed: boolean }> = ({ collapsed }) => (
  <div style={{
    color: '#fff',
    fontSize: collapsed ? '16px' : '20px',
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: '32px'
  }}>
    {collapsed ? 'AD' : 'Admin'}
  </div>
);

export default SideLayout;
```

#### 3. 混合布局（Header + Sider + Content）

拥有顶部导航和侧边栏的复合布局，适用于复杂系统。

```typescript
import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown } from 'antd';
import {
  HomeOutlined,
  AppstoreOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const MixedLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const topMenuItems = [
    { key: '1', icon: <HomeOutlined />, label: '首页' },
    { key: '2', icon: <AppstoreOutlined />, label: '应用' }
  ];

  const sideMenuItems = [
    { key: '1', label: '用户管理', icon: <UserOutlined /> },
    { key: '2', label: '权限管理', icon: <AppstoreOutlined /> }
  ];

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心' },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: '#fff',
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        position: 'fixed',
        zIndex: 1,
        width: '100%'
      }}>
        <div style={{
          fontSize: '20px',
          fontWeight: 'bold',
          marginRight: '24px'
        }}>
          管理系统
        </div>

        <Menu
          mode="horizontal"
          items={topMenuItems}
          style={{ flex: 1, border: 'none' }}
        />

        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Avatar
            icon={<UserOutlined />}
            style={{ cursor: 'pointer' }}
          />
        </Dropdown>
      </Header>

      <Layout style={{ marginTop: '64px' }}>
        {/* 侧边栏 */}
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          style={{
            overflow: 'auto',
            height: 'calc(100vh - 64px)',
            position: 'fixed',
            left: 0,
            top: '64px'
          }}
        >
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            items={sideMenuItems}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>

        {/* 内容区域 */}
        <Layout style={{ marginLeft: collapsed ? 80 : 200 }}>
          <Content style={{
            margin: '24px 16px',
            padding: 24,
            background: '#fff',
            minHeight: 'calc(100vh - 64px - 48px)'
          }}>
            <h1>用户管理</h1>
            <p>这里是用户管理页面内容...</p>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MixedLayout;
```

### 响应式布局

使用 `breakpoint` 属性实现侧边栏的响应式收起。

```typescript
import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  BarsOutlined
} from '@ant-design/icons';

const { Sider, Content } = Layout;

const ResponsiveLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { key: '1', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '2', icon: <UserOutlined />, label: '用户管理' },
    { key: '3', icon: <BarsOutlined />, label: '菜单管理' }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        collapsible
        collapsed={collapsed}
        onCollapse={(collapsed) => setCollapsed(collapsed)}
        onBreakpoint={(broken) => {
          console.log('响应式断点变化:', broken);
        }}
      >
        <div style={{
          height: '32px',
          margin: '16px',
          background: 'rgba(255, 255, 255, 0.2)'
        }} />
        <Menu
          theme="dark"
          mode="inline"
          items={menuItems}
        />
      </Sider>

      <Layout>
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{
            padding: 24,
            background: '#fff',
            minHeight: 360
          }}>
            <h1>响应式布局示例</h1>
            <p>调整浏览器窗口大小，侧边栏会自动收起。</p>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default ResponsiveLayout;
```

### 固定头部和侧边栏

```typescript
import React from 'react';
import { Layout, Menu } from 'antd';
import { HomeOutlined, UserOutlined } from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const FixedLayout: React.FC = () => {
  return (
    <Layout>
      {/* 固定顶部 */}
      <Header style={{
        position: 'fixed',
        zIndex: 1,
        width: '100%',
        background: '#001529'
      }}>
        <div style={{ color: '#fff' }}>固定顶部导航</div>
      </Header>

      <Layout style={{ marginTop: '64px' }}>
        {/* 固定侧边栏 */}
        <Sider
          style={{
            overflow: 'auto',
            height: 'calc(100vh - 64px)',
            position: 'fixed',
            left: 0,
            top: '64px'
          }}
        >
          <Menu
            theme="dark"
            mode="inline"
            items={[
              { key: '1', icon: <HomeOutlined />, label: '首页' },
              { key: '2', icon: <UserOutlined />, label: '用户' }
            ]}
          />
        </Sider>

        {/* 内容区域 */}
        <Layout style={{ marginLeft: 200 }}>
          <Content style={{
            margin: '24px 16px',
            padding: 24,
            background: '#fff',
            minHeight: 'calc(100vh - 64px - 48px)'
          }}>
            <h1>固定布局示例</h1>
            <p>顶部和侧边栏都是固定的，滚动时内容区域独立滚动。</p>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default FixedLayout;
```

### Sider 组件 API

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| breakpoint | 触发响应式布局的断点 | `xs`\|`sm`\|`md`\|`lg`\|`xl`\|`xxl` | - |
| collapsed | 当前收起状态 | boolean | - |
| collapsedWidth | 收缩宽度 | number | 80 |
| collapsible | 是否可收起 | boolean | false |
| defaultCollapsed | 是否默认收起 | boolean | false |
| reverseArrow | 翻转折叠提示箭头 | boolean | false |
| theme | 主题颜色 | `light`\|`dark` | `dark` |
| trigger | 自定义触发器 | ReactNode | - |
| width | 宽度 | number \| string | 200 |
| onCollapse | 展开-收起回调 | (collapsed, type) => void | - |
| onBreakpoint | 触发响应式断点回调 | (broken) => void | - |

#### 断点宽度

```typescript
{
  xs: '480px',   // 超小屏幕
  sm: '576px',   // 小屏幕
  md: '768px',   // 中等屏幕
  lg: '992px',   // 大屏幕
  xl: '1200px',  // 超大屏幕
  xxl: '1600px'  // 极大屏幕
}
```

---

## Grid 栅格系统

### 基本概念

Grid 栅格系统基于 **24 列**布局，通过 `Row` 和 `Col` 组件实现灵活的响应式布局。

### 栅格参数

#### Col 参数

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| span | 栅格占位格数（0-24） | number | - |
| offset | 栅格左侧的间隔格数 | number | 0 |
| order | 栅格顺序 | number | 0 |
| push | 栅格向右移动格数 | number | 0 |
| pull | 栅格向左移动格数 | number | 0 |
| xs | 屏幕 < 576px 响应式栅格 | number \| object | - |
| sm | 屏幕 ≥ 576px 响应式栅格 | number \| object | - |
| md | 屏幕 ≥ 768px 响应式栅格 | number \| object | - |
| lg | 屏幕 ≥ 992px 响应式栅格 | number \| object | - |
| xl | 屏幕 ≥ 1200px 响应式栅格 | number \| object | - |
| xxl | 屏幕 ≥ 1600px 响应式栅格 | number \| object | - |

#### Row 参数

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| align | 垂直对齐方式 | `top`\|`middle`\|`bottom`\|`stretch` | `top` |
| gutter | 栅格间隔 | number \| string \| object \| array | 0 |
| justify | 水平排列方式 | `start`\|`end`\|`center`\|`space-around`\|`space-between` | `start` |
| wrap | 是否自动换行 | boolean | true |

### 基础栅格示例

#### 1. 基础列布局

```typescript
import React from 'react';
import { Row, Col, Card } from 'antd';

const BasicGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>基础栅格布局</h2>

      {/* 两列布局 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="列 1">span={12}</Card>
        </Col>
        <Col span={12}>
          <Card title="列 2">span={12}</Card>
        </Col>
      </Row>

      {/* 三列布局 */}
      <Row gutter={16} style={{ marginTop: '16px' }}>
        <Col span={8}>
          <Card title="列 1">span={8}</Card>
        </Col>
        <Col span={8}>
          <Card title="列 2">span={8}</Card>
        </Col>
        <Col span={8}>
          <Card title="列 3">span={8}</Card>
        </Col>
      </Row>

      {/* 四列布局 */}
      <Row gutter={16} style={{ marginTop: '16px' }}>
        <Col span={6}>
          <Card title="列 1">span={6}</Card>
        </Col>
        <Col span={6}>
          <Card title="列 2">span={6}</Card>
        </Col>
        <Col span={6}>
          <Card title="列 3">span={6}</Card>
        </Col>
        <Col span={6}>
          <Card title="列 4">span={6}</Card>
        </Col>
      </Row>
    </div>
  );
};

export default BasicGrid;
```

#### 2. 栅格间隔（Gutter）

```typescript
import React from 'react';
import { Row, Col, Card } from 'antd';

const GutterGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>栅格间隔示例</h2>

      {/* 固定间隔 */}
      <Row gutter={16}>
        <Col span={8}>
          <Card>间隔 16px</Card>
        </Col>
        <Col span={8}>
          <Card>间隔 16px</Card>
        </Col>
        <Col span={8}>
          <Card>间隔 16px</Card>
        </Col>
      </Row>

      {/* 响应式间隔 */}
      <Row gutter={{ xs: 8, sm: 16, md: 24, lg: 32 }} style={{ marginTop: '16px' }}>
        <Col span={8}>
          <Card>响应式间隔</Card>
        </Col>
        <Col span={8}>
          <Card>响应式间隔</Card>
        </Col>
        <Col span={8}>
          <Card>响应式间隔</Card>
        </Col>
      </Row>

      {/* 水平和垂直间隔 */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
        <Col span={8}>
          <Card>水平 16px，垂直 16px</Card>
        </Col>
      </Row>
    </div>
  );
};

export default GutterGrid;
```

#### 3. 列偏移（Offset）

```typescript
import React from 'react';
import { Row, Col, Card } from 'antd';

const OffsetGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>列偏移示例</h2>

      <Row>
        {/* 占 6 格，偏移 6 格 */}
        <Col span={6} offset={6}>
          <Card>span=6, offset=6</Card>
        </Col>
        <Col span={6} offset={6}>
          <Card>span=6, offset=6</Card>
        </Col>
      </Row>

      <Row style={{ marginTop: '16px' }}>
        {/* 居中元素 */}
        <Col span={8} offset={8}>
          <Card>居中元素 (span=8, offset=8)</Card>
        </Col>
      </Row>

      <Row style={{ marginTop: '16px' }}>
        {/* 右对齐 */}
        <Col span={12} offset={12}>
          <Card>右对齐 (span=12, offset=12)</Card>
        </Col>
      </Row>
    </div>
  );
};

export default OffsetGrid;
```

#### 4. 响应式栅格

```typescript
import React from 'react';
import { Row, Col, Card } from 'antd';

const ResponsiveGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>响应式栅格示例</h2>

      {/* 移动端 1 列，平板 2 列，桌面 3 列 */}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <h3>响应式卡片 1</h3>
            <p>xs=24, sm=12, md=8</p>
            <p>移动端全宽，平板半宽，桌面三分之一</p>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <h3>响应式卡片 2</h3>
            <p>xs=24, sm=12, md=8</p>
            <p>移动端全宽，平板半宽，桌面三分之一</p>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <h3>响应式卡片 3</h3>
            <p>xs=24, sm=12, md=8</p>
            <p>移动端全宽，平板半宽，桌面三分之一</p>
          </Card>
        </Col>
      </Row>

      {/* 复杂响应式 */}
      <Row gutter={16} style={{ marginTop: '16px' }}>
        <Col xs={24} sm={24} md={12} lg={8} xl={6}>
          <Card>
            <p>xs=24, sm=24, md=12, lg=8, xl=6</p>
          </Card>
        </Col>
        <Col xs={24} sm={24} md={12} lg={8} xl={6}>
          <Card>
            <p>xs=24, sm=24, md=12, lg=8, xl=6</p>
          </Card>
        </Col>
        <Col xs={24} sm={24} md={12} lg={8} xl={6}>
          <Card>
            <p>xs=24, sm=24, md=12, lg=8, xl=6</p>
          </Card>
        </Col>
        <Col xs={24} sm={24} md={12} lg={8} xl={6}>
          <Card>
            <p>xs=24, sm=24, md=12, lg=8, xl=6</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ResponsiveGrid;
```

#### 5. 对齐方式

```typescript
import React from 'react';
import { Row, Col, Card } from 'antd';

const AlignGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>对齐方式示例</h2>

      {/* 顶部对齐 */}
      <Row align="top" style={{ background: '#f0f2f5', padding: '16px', marginBottom: '16px' }}>
        <Col span={8}>
          <Card style={{ height: '100px' }}>顶部对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '150px' }}>顶部对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '80px' }}>顶部对齐内容</Card>
        </Col>
      </Row>

      {/* 中间对齐 */}
      <Row align="middle" style={{ background: '#f0f2f5', padding: '16px', marginBottom: '16px' }}>
        <Col span={8}>
          <Card style={{ height: '100px' }}>中间对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '150px' }}>中间对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '80px' }}>中间对齐内容</Card>
        </Col>
      </Row>

      {/* 底部对齐 */}
      <Row align="bottom" style={{ background: '#f0f2f5', padding: '16px' }}>
        <Col span={8}>
          <Card style={{ height: '100px' }}>底部对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '150px' }}>底部对齐内容</Card>
        </Col>
        <Col span={8}>
          <Card style={{ height: '80px' }}>底部对齐内容</Card>
        </Col>
      </Row>
    </div>
  );
};

export default AlignGrid;
```

#### 6. Flex 填充

```typescript
import React from 'react';
import { Row, Col, Card, Input } from 'antd';

const FlexGrid: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>Flex 填充示例</h2>

      {/* 使用 flex 属性 */}
      <Row>
        <Col flex="100px">
          <Card>固定 100px</Card>
        </Col>
        <Col flex="auto">
          <Card>自动填充 (flex="auto")</Card>
        </Col>
        <Col flex="200px">
          <Card>固定 200px</Card>
        </Col>
      </Row>

      {/* 比例分配 */}
      <Row style={{ marginTop: '16px' }}>
        <Col flex={2}>
          <Card>占 2 份</Card>
        </Col>
        <Col flex={3}>
          <Card>占 3 份</Card>
        </Col>
        <Col flex={1}>
          <Card>占 1 份</Card>
        </Col>
      </Row>

      {/* 搜索框示例 */}
      <Row style={{ marginTop: '16px' }}>
        <Col flex="auto">
          <Input placeholder="请输入搜索关键词" />
        </Col>
        <Col flex="100px">
          <Card style={{ marginLeft: '8px', textAlign: 'center' }}>
            搜索
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default FlexGrid;
```

---

## Space 间距

### 基本概念

Space 组件为行内元素提供统一的间距，适用于按钮、输入框、标签等小元素的排列。

### Space 组件 API

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| align | 对齐方式 | `start`\|`end`\|`center`\|`baseline` | - |
| size | 间距大小 | `small`\|`middle`\|`large`\|number \| Size[] | `small` |
| orientation | 间距方向 | `vertical`\|`horizontal` | `horizontal` |
| vertical | 是否垂直 | boolean | false |
| wrap | 是否自动换行 | boolean | false |
| separator | 分隔符 | ReactNode | - |

### Space 示例

#### 1. 基础用法

```typescript
import React from 'react';
import { Space, Button, Card } from 'antd';

const BasicSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>基础 Space 示例</h2>

      <Card title="水平间距">
        <Space>
          <Button type="primary">主按钮</Button>
          <Button>默认按钮</Button>
          <Button type="dashed">虚线按钮</Button>
          <Button type="link">链接按钮</Button>
        </Space>
      </Card>

      <Card title="垂直间距" style={{ marginTop: '16px' }}>
        <Space direction="vertical">
          <Button type="primary">按钮 1</Button>
          <Button>按钮 2</Button>
          <Button type="dashed">按钮 3</Button>
          <Button type="link">按钮 4</Button>
        </Space>
      </Card>
    </div>
  );
};

export default BasicSpace;
```

#### 2. 自定义间距大小

```typescript
import React from 'react';
import { Space, Button, Card } from 'antd';

const SizeSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>自定义间距大小</h2>

      <Space size="small">
        <Button>Small</Button>
        <Button>Small</Button>
        <Button>Small</Button>
      </Space>

      <Space size="middle" style={{ marginLeft: '24px' }}>
        <Button>Middle</Button>
        <Button>Middle</Button>
        <Button>Middle</Button>
      </Space>

      <Space size="large" style={{ marginLeft: '24px' }}>
        <Button>Large</Button>
        <Button>Large</Button>
        <Button>Large</Button>
      </Space>

      <Space size={32} style={{ marginLeft: '24px' }}>
        <Button>Custom</Button>
        <Button>32px</Button>
        <Button>Custom</Button>
      </Space>

      <Card title="垂直自定义间距" style={{ marginTop: '16px' }}>
        <Space direction="vertical" size={[8, 16]}>
          <Button>垂直间距 8px</Button>
          <Button>水平间距 16px</Button>
          <Button>组合间距</Button>
        </Space>
      </Card>
    </div>
  );
};

export default SizeSpace;
```

#### 3. 对齐方式

```typescript
import React from 'react';
import { Space, Button, Card, Divider } from 'antd';

const AlignSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>对齐方式示例</h2>

      <Card title="不同高度元素的对齐">
        <Space align="start">
          <Button type="primary" size="large">大按钮</Button>
          <Button>默认按钮</Button>
          <Button size="small">小按钮</Button>
        </Space>

        <Divider />

        <Space align="center">
          <Button type="primary" size="large">大按钮</Button>
          <Button>默认按钮</Button>
          <Button size="small">小按钮</Button>
        </Space>

        <Divider />

        <Space align="end">
          <Button type="primary" size="large">大按钮</Button>
          <Button>默认按钮</Button>
          <Button size="small">小按钮</Button>
        </Space>

        <Divider />

        <Space align="baseline">
          <Button type="primary" size="large">大按钮</Button>
          <Button>默认按钮</Button>
          <Button size="small">小按钮</Button>
        </Space>
      </Card>
    </div>
  );
};

export default AlignSpace;
```

#### 4. 自动换行

```typescript
import React from 'react';
import { Space, Button, Card } from 'antd';

const WrapSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>自动换行示例</h2>

      <Card title="Space 自动换行">
        <Space wrap>
          {Array.from({ length: 20 }).map((_, i) => (
            <Button key={i}>按钮 {i + 1}</Button>
          ))}
        </Space>
      </Card>
    </div>
  );
};

export default WrapSpace;
```

#### 5. 分隔符

```typescript
import React from 'react';
import { Space, Button, Divider } from 'antd';

const SeparatorSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>分隔符示例</h2>

      <h3>使用 separator 属性</h3>
      <Space separator={<Divider type="vertical" />}>
        <Button>首页</Button>
        <Button>用户</Button>
        <Button>设置</Button>
        <Button>退出</Button>
      </Space>

      <h3 style={{ marginTop: '24px' }}>自定义分隔符</h3>
      <Space separator={<span style={{ color: '#999' }}>|</span>}>
        <Button type="link">关于我们</Button>
        <Button type="link">联系方式</Button>
        <Button type="link">隐私政策</Button>
        <Button type="link">服务条款</Button>
      </Space>
    </div>
  );
};

export default SeparatorSpace;
```

#### 6. Space.Compact 紧凑布局

```typescript
import React from 'react';
import { Space, Button, Input, Select } from 'antd';

const CompactSpace: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>Space.Compact 紧凑布局</h2>

      <Space direction="vertical" style={{ width: '100%' }}>
        <h3>按钮组合</h3>
        <Space.Compact>
          <Button type="primary">发布</Button>
          <Button>保存草稿</Button>
          <Button>预览</Button>
        </Space.Compact>

        <h3>输入框组合</h3>
        <Space.Compact style={{ width: '100%' }}>
          <Input style={{ width: '30%' }} placeholder="用户名" />
          <Input style={{ width: '70%' }} placeholder="邮箱" />
        </Space.Compact>

        <h3>搜索框组合</h3>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            style={{ width: 'calc(100% - 100px)' }}
            placeholder="请输入搜索关键词"
          />
          <Button type="primary">搜索</Button>
        </Space.Compact>

        <h3>Select 和 Input 组合</h3>
        <Space.Compact style={{ width: '100%' }}>
          <Select
            defaultValue="http"
            style={{ width: '100px' }}
            options={[
              { value: 'http', label: 'HTTP' },
              { value: 'https', label: 'HTTPS' }
            ]}
          />
          <Input
            style={{ width: 'calc(100% - 100px)' }}
            placeholder="请输入网址"
          />
        </Space.Compact>
      </Space>
    </div>
  );
};

export default CompactSpace;
```

---

## Skeleton 骨架屏

### 基本概念

Skeleton 组件在需要等待加载内容的位置提供占位图形，改善用户体验。

### Skeleton 组件 API

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| active | 是否展示动画效果 | boolean | false |
| loading | 为 true 时显示占位图 | boolean | - |
| avatar | 是否显示头像占位图 | boolean \| SkeletonAvatarProps | false |
| paragraph | 是否显示段落占位图 | boolean \| SkeletonParagraphProps | true |
| round | 段落和标题显示圆角 | boolean | false |
| title | 是否显示标题占位图 | boolean \| SkeletonTitleProps | true |

### Skeleton 示例

#### 1. 基础骨架屏

```typescript
import React, { useState } from 'react';
import { Skeleton, Button, Card } from 'antd';

const BasicSkeleton: React.FC = () => {
  const [loading, setLoading] = useState(true);

  const showData = () => {
    setLoading(false);
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2>基础骨架屏示例</h2>

      <Card
        title="文章内容"
        extra={<Button onClick={showData}>显示内容</Button>}
      >
        <Skeleton loading={loading} active>
          <h1>文章标题</h1>
          <p>
            这里是文章的正文内容。Skeleton 组件可以在数据加载时提供良好的视觉反馈。
            当加载完成后，会自动显示实际内容。
          </p>
          <p>
            骨架屏（Skeleton Screen）是一种优化用户体验的技术，
            通过在内容加载时显示占位图形，让用户知道内容正在加载中。
          </p>
        </Skeleton>
      </Card>
    </div>
  );
};

export default BasicSkeleton;
```

#### 2. 复杂骨架屏

```typescript
import React from 'react';
import { Skeleton, Card, Avatar } from 'antd';

const ComplexSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>复杂骨架屏示例</h2>

      {/* 列表骨架屏 */}
      <Card title="用户列表">
        <Skeleton loading={true} active avatar>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Avatar size={64} src="https://example.com/avatar.jpg" />
            <div style={{ marginLeft: '16px' }}>
              <h3>用户名</h3>
              <p>用户简介信息...</p>
            </div>
          </div>
        </Skeleton>
      </Card>

      {/* 卡片骨架屏 */}
      <Card title="文章卡片" style={{ marginTop: '16px' }}>
        <Skeleton loading={true} active>
          <h2>文章标题</h2>
          <p>文章摘要内容...</p>
        </Skeleton>
      </Card>

      {/* 自定义骨架屏 */}
      <Card title="自定义骨架屏" style={{ marginTop: '16px' }}>
        <Skeleton
          loading={true}
          active
          avatar={{ shape: 'square', size: 80 }}
          title={{ width: '60%' }}
          paragraph={{
            rows: 4,
            width: ['100%', '80%', '60%', '40%']
          }}
        />
      </Card>
    </div>
  );
};

export default ComplexSkeleton;
```

#### 3. 列表骨架屏

```typescript
import React from 'react';
import { Skeleton, List, Card } from 'antd';

const ListSkeleton: React.FC = () => {
  const loading = true;

  const data = [
    { name: 'John Brown', age: 32, address: 'New York No. 1 Lake Park' },
    { name: 'Jim Green', age: 42, address: 'London No. 1 Lake Park' },
    { name: 'Joe Black', age: 32, address: 'Sidney No. 1 Lake Park' }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h2>列表骨架屏示例</h2>

      <Card>
        <List
          dataSource={data}
          renderItem={(item) => (
            <List.Item key={item.name}>
              <Skeleton
                loading={loading}
                active
                avatar
              >
                <List.Item.Meta
                  avatar={<Avatar src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${item.name}`} />}
                  title={<a href="#">{item.name}</a>}
                  description={item.address}
                />
                <div>Content</div>
              </Skeleton>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ListSkeleton;
```

#### 4. 按钮和输入框骨架屏

```typescript
import React from 'react';
import { Skeleton, Card } from 'antd';

const ElementSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h2>元素骨架屏示例</h2>

      <Card title="按钮骨架屏">
        <Space>
          <Skeleton.Button active size="small" style={{ width: '100px' }} />
          <Skeleton.Button active size="default" style={{ width: '120px' }} />
          <Skeleton.Button active size="large" style={{ width: '140px' }} />
        </Space>

        <Space style={{ marginTop: '16px' }}>
          <Skeleton.Button active shape="circle" size="small" />
          <Skeleton.Button active shape="square" size="default" />
          <Skeleton.Button active shape="round" size="large" />
        </Space>
      </Card>

      <Card title="输入框骨架屏" style={{ marginTop: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Skeleton.Input active size="small" style={{ width: '200px' }} />
          <Skeleton.Input active size="default" style={{ width: '300px' }} />
          <Skeleton.Input active size="large" style={{ width: '400px' }} />
        </Space>
      </Card>
    </div>
  );
};

export default ElementSkeleton;
```

---

## 常见布局模式

### 1. 后台管理系统布局

完整的后台管理系统布局，包含侧边栏、顶部导航、内容区。

```typescript
import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Breadcrumb } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SettingOutlined,
  FileTextOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: 'users', icon: <UserOutlined />, label: '用户管理' },
    { key: 'articles', icon: <FileTextOutlined />, label: '文章管理' },
    { key: 'teams', icon: <TeamOutlined />, label: '团队管理' },
    { key: 'settings', icon: <SettingOutlined />, label: '系统设置' }
  ];

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心' },
    { key: 'settings', icon: <SettingOutlined />, label: '设置' },
    { type: 'divider' },
    { key: 'logout', icon: <UserOutlined />, label: '退出登录' }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0
        }}
      >
        <div style={{
          height: '32px',
          margin: '16px',
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '6px'
        }}>
          <Logo collapsed={collapsed} />
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          items={menuItems}
        />
      </Sider>

      {/* 右侧内容区 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 200 }}>
        {/* 顶部导航 */}
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {React.createElement(
              collapsed ? MenuUnfoldOutlined : MenuFoldOutlined,
              {
                className: 'trigger',
                onClick: () => setCollapsed(!collapsed),
                style: { fontSize: '18px', cursor: 'pointer' }
              }
            )}
            <Breadcrumb style={{ marginLeft: '16px' }}>
              <Breadcrumb.Item>首页</Breadcrumb.Item>
              <Breadcrumb.Item>仪表盘</Breadcrumb.Item>
            </Breadcrumb>
          </div>

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar
              icon={<UserOutlined />}
              style={{ cursor: 'pointer' }}
            />
          </Dropdown>
        </Header>

        {/* 内容区域 */}
        <Content style={{
          margin: '24px 16px',
          padding: 24,
          background: '#f0f2f5',
          minHeight: 'calc(100vh - 64px - 48px)'
        }}>
          <div style={{
            background: '#fff',
            padding: '24px',
            minHeight: 360
          }}>
            <h1>仪表盘</h1>
            <p>欢迎使用后台管理系统！</p>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

const Logo: React.FC<{ collapsed: boolean }> = ({ collapsed }) => (
  <div style={{
    color: '#fff',
    fontSize: collapsed ? '16px' : '20px',
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: '32px'
  }}>
    {collapsed ? 'AD' : 'Admin System'}
  </div>
);

export default AdminLayout;
```

### 2. 内容页布局

文章、详情等内容页面的典型布局。

```typescript
import React from 'react';
import { Layout, Breadcrumb, Typography, Space, Divider } from 'antd';

const { Content } = Layout;
const { Title, Paragraph } = Typography;

const ContentPageLayout: React.FC = () => {
  return (
    <Layout style={{ background: '#f0f2f5' }}>
      {/* 面包屑导航 */}
      <div style={{
        padding: '16px 24px',
        background: '#fff',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <Breadcrumb>
          <Breadcrumb.Item>首页</Breadcrumb.Item>
          <Breadcrumb.Item>文章</Breadcrumb.Item>
          <Breadcrumb.Item>详情</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      {/* 内容区 */}
      <Content style={{ padding: '24px' }}>
        <div style={{
          background: '#fff',
          padding: '32px',
          borderRadius: '8px',
          maxWidth: '900px',
          margin: '0 auto'
        }}>
          <Title level={2}>文章标题</Title>

          <Space direction="vertical" style={{ width: '100%', marginBottom: '24px' }}>
            <div style={{ color: '#999' }}>
              作者：张三 | 发布时间：2024-01-01 | 浏览：1000
            </div>
            <Divider />
          </Space>

          <Paragraph>
            这里是文章的正文内容。使用 Ant Design 的 Layout 组件可以轻松构建专业的内容页面。
          </Paragraph>

          <Paragraph>
            Typography 组件提供了良好的排版支持，包括标题、段落、列表等。
          </Paragraph>

          <Divider />

          <Space>
            <span>标签：</span>
            <Space>
              <span style={{ color: '#1890ff' }}>React</span>
              <span style={{ color: '#1890ff' }}>Ant Design</span>
              <span style={{ color: '#1890ff' }}>TypeScript</span>
            </Space>
          </Space>
        </div>
      </Content>
    </Layout>
  );
};

export default ContentPageLayout;
```

### 3. 搜索页布局

包含搜索栏、筛选器、结果列表的搜索页面布局。

```typescript
import React, { useState } from 'react';
import { Layout, Card, Form, Input, Select, Button, Table, Space, Tag } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';

const { Content } = Layout;

const SearchPageLayout: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => (
      <Tag color={status === 'active' ? 'green' : 'red'}>{status}</Tag>
    )},
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' }
  ];

  const data = [
    { key: '1', id: 1, name: '项目 A', status: 'active', createdAt: '2024-01-01' },
    { key: '2', id: 2, name: '项目 B', status: 'inactive', createdAt: '2024-01-02' },
    { key: '3', id: 3, name: '项目 C', status: 'active', createdAt: '2024-01-03' }
  ];

  const handleSearch = () => {
    setLoading(true);
    // 模拟搜索
    setTimeout(() => setLoading(false), 1000);
  };

  const handleReset = () => {
    form.resetFields();
  };

  return (
    <Layout style={{ background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 搜索表单 */}
          <Card>
            <Form form={form} layout="inline">
              <Form.Item name="keyword" label="关键词">
                <Input placeholder="请输入关键词" style={{ width: 200 }} />
              </Form.Item>
              <Form.Item name="status" label="状态">
                <Select
                  placeholder="请选择状态"
                  style={{ width: 120 }}
                  allowClear
                >
                  <Select.Option value="active">活跃</Select.Option>
                  <Select.Option value="inactive">停用</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={handleSearch}
                  >
                    搜索
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={handleReset}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* 结果列表 */}
          <Card title="搜索结果">
            <Table
              columns={columns}
              dataSource={data}
              loading={loading}
              pagination={{
                total: 100,
                pageSize: 10,
                current: 1,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条`
              }}
            />
          </Card>
        </Space>
      </Content>
    </Layout>
  );
};

export default SearchPageLayout;
```

---

## 最佳实践

### 1. 布局选择指南

| 场景 | 推荐方案 | 组件组合 |
|------|---------|---------|
| 后台管理系统 | 侧边栏布局 | Layout.Sider + Layout.Header + Layout.Content |
| 展示型网站 | 顶部导航布局 | Layout.Header + Layout.Content + Layout.Footer |
| 移动端应用 | 响应式布局 | Layout.Sider (breakpoint) + Layout.Content |
| 内容页 | 简单布局 | Layout.Content + Card |
| 复杂仪表盘 | 混合布局 | Layout.Header + Layout.Sider + Layout.Content |

### 2. 响应式设计原则

#### Mobile-First 策略

```typescript
// ✅ 推荐：从移动端开始设计
<Col xs={24} sm={12} md={8} lg={6} xl={4}>

// ❌ 不推荐：从桌面端开始
<Col xs={24} md={8} lg={6}>
```

#### 断点使用建议

```typescript
// 移动优先布局
<Row>
  <Col xs={24} sm={12} md={8} lg={6}>
    {/* 移动端全宽，平板半宽，桌面三分之一，大屏四分之一 */}
  </Col>
</Row>

// 隐藏/显示元素
<Col xs={0} sm={24}>
  {/* 仅在平板及以上显示 */}
</Col>
<Col xs={24} sm={0}>
  {/* 仅在移动端显示 */}
</Col>
```

### 3. 性能优化建议

#### 避免过度嵌套

```typescript
// ❌ 不推荐：过度嵌套
<Layout>
  <Layout>
    <Layout>
      <Content>...</Content>
    </Layout>
  </Layout>
</Layout>

// ✅ 推荐：扁平结构
<Layout>
  <Content>...</Content>
</Layout>
```

#### 使用栅格系统而非 Flex

```typescript
// ❌ 不推荐：手动计算宽度
<div style={{ display: 'flex', gap: '16px' }}>
  <div style={{ width: '33.33%' }}>...</div>
  <div style={{ width: '33.33%' }}>...</div>
  <div style={{ width: '33.33%' }}>...</div>
</div>

// ✅ 推荐：使用 Grid 栅格
<Row gutter={16}>
  <Col span={8}>...</Col>
  <Col span={8}>...</Col>
  <Col span={8}>...</Col>
</Row>
```

### 4. 可访问性建议

#### 使用语义化标签

```typescript
// ✅ 推荐：结合语义化标签
<Layout>
  <Header role="banner">
    <nav aria-label="主导航">
      <Menu />
    </nav>
  </Header>
  <Content role="main">
    <main>
      <h1>页面标题</h1>
      <article>...</article>
    </main>
  </Content>
  <Footer role="contentinfo">
    <p>&copy; 2024 版权信息</p>
  </Footer>
</Layout>
```

#### 键盘导航支持

```typescript
// 确保 Layout 组件可访问
<Sider
  collapsible
  onCollapse={(collapsed) => {
    // 触发可访问性事件
    console.log('侧边栏状态:', collapsed ? '收起' : '展开');
  }}
>
  <Menu
    selectable
    focusable
    items={menuItems}
  />
</Sider>
```

### 5. 样式定制建议

#### 使用 ConfigProvider 全局配置

```typescript
import { ConfigProvider } from 'antd';

// 全局主题配置
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 8,
      fontSize: 14
    },
    components: {
      Layout: {
        headerBg: '#001529',
        headerHeight: 64,
        siderBg: '#001529'
      }
    }
  }}
>
  <App />
</ConfigProvider>
```

#### 组件级样式覆盖

```typescript
// 使用 style 属性
<Sider style={{ background: '#custom-color' }}>

// 或使用 className
<Sider className="custom-sider">

// CSS 文件
.custom-sider {
  background: #custom-color;
}
```

### 6. 常见问题解决

#### Sider 固定定位问题

```typescript
// 确保 Sider 固定时布局正确
<Sider
  style={{
    position: 'fixed',
    height: '100vh',
    left: 0,
    top: 0,
    bottom: 0
  }}
/>
<Layout style={{ marginLeft: 200 }}> {/* 与 Sider 宽度一致 */}
  <Content>...</Content>
</Layout>
```

#### 栅格布局换行问题

```typescript
// 控制换行行为
<Row wrap={true}>  {/* 允许换行（默认） */}
<Row wrap={false}> {/* 禁止换行 */}

// 使用 order 属性控制顺序
<Col xs={24} md={12} order={2}>第一列（但显示在最后）</Col>
<Col xs={24} md={12} order={1}>第二列（但显示在最前）</Col>
```

---

## 参考资源

### 官方文档

- [Ant Design Layout 组件](https://ant.design/components/layout-cn/)
- [Ant Design Grid 栅格系统](https://ant.design/components/grid-cn/)
- [Ant Design Space 间距](https://ant.design/components/space-cn/)
- [Ant Design Skeleton 骨架屏](https://ant.design/components/skeleton-cn/)
- [Ant Design Pro Layout](https://procomponents.ant.design/components/layout/)

### 最佳实践文章

- [Creating Responsive Layout with Ant Design Grid](https://tillitsdone.com/blogs/ant-design-grid-system-guide/)
- [Ant Design 学习 - 腾讯云开发者社区](https://cloud.tencent.com/developer/article/2206129)
- [在 React 中使用 Antd 的 Layout 组件](https://blog.csdn.net/weixin_65200149/article/details/138344491)

### 视频教程

- [Mastering Ant Design Grid System](https://www.youtube.com/watch?v=tTzkcRB68wk)

### 设计规范

- [Ant Design 设计规范 - 布局](https://ant.design/docs/spec/layout-cn)
- [Ant Design 设计规范 - 栅格](https://ant.design/docs/spec/grid-cn)

---

## 总结

Ant Design 的布局系统提供了强大且灵活的工具，帮助开发者快速构建专业级的应用界面：

1. **Layout** - 适用于页面级整体布局，提供 Header、Sider、Content、Footer 等组件
2. **Grid** - 基于 24 栅格的响应式布局系统，支持复杂的响应式场景
3. **Space** - 为行内元素提供统一间距，简化小元素排列
4. **Skeleton** - 提供加载占位，优化用户体验

掌握这些布局组件的最佳实践，可以显著提升开发效率和界面质量。
