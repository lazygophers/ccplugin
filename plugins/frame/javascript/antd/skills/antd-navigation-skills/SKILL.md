---
name: antd-navigation-skills
description: Ant Design 导航组件完整指南 - Menu、Breadcrumb、Steps、Pagination、Anchor
---

# antd-navigation: Ant Design 导航组件完整指南

导航组件是用户界面中至关重要的部分，它们帮助用户理解当前位置、浏览内容结构、在页面间移动以及完成多步骤流程。Ant Design 提供了一套完整的导航组件，包括 Menu（菜单）、Breadcrumb（面包屑）、Steps（步骤条）、Pagination（分页）和 Anchor（锚点）。

---

## 概述

### 导航组件的重要性

导航组件在用户体验中扮演着核心角色：

- **空间定位** - 帮助用户了解当前在应用中的位置
- **内容发现** - 引导用户发现和访问不同功能模块
- **流程引导** - 在复杂操作中提供清晰的步骤指引
- **信息浏览** - 有效组织和展示大量内容
- **交互效率** - 减少用户操作步骤，提高任务完成效率

### 组件清单

| 组件 | 用途 | 典型场景 |
|------|------|---------|
| **Menu** | 导航菜单 | 网站主导航、侧边栏菜单、下拉菜单 |
| **Breadcrumb** | 面包屑导航 | 页面层级导航、当前位置指示 |
| **Steps** | 步骤条 | 向导流程、订单流程、注册流程 |
| **Pagination** | 分页器 | 数据列表、搜索结果、内容分页 |
| **Anchor** | 锚点导航 | 长页面目录、文档导航、快速跳转 |

---

## Menu 菜单

### 基础菜单

Menu 组件是最常用的导航组件，支持横向和纵向两种模式。

#### 基础用法

```tsx
import { Menu } from 'antd';
import { AppstoreOutlined, MailOutlined, SettingOutlined } from '@ant-design/icons';

function BasicMenu() {
  const items = [
    {
      key: '1',
      icon: <MailOutlined />,
      label: 'Navigation One',
    },
    {
      key: '2',
      icon: <AppstoreOutlined />,
      label: 'Navigation Two',
    },
    {
      key: '3',
      icon: <SettingOutlined />,
      label: 'Navigation Three',
    },
  ];

  return (
    <Menu
      mode="horizontal"
      defaultSelectedKeys={['1']}
      items={items}
      style={{ lineHeight: '64px' }}
    />
  );
}
```

#### 垂直菜单

```tsx
import { Menu } from 'antd';

function VerticalMenu() {
  const items = [
    {
      key: '1',
      label: 'Option 1',
    },
    {
      key: '2',
      label: 'Option 2',
    },
    {
      key: '3',
      label: 'Option 3',
    },
  ];

  return (
    <Menu
      mode="vertical"
      defaultSelectedKeys={['1']}
      items={items}
      style={{ width: 256 }}
    />
  );
}
```

#### 内嵌菜单

```tsx
import { Menu } from 'antd';
import { AppstoreOutlined, MailOutlined, SettingOutlined } from '@ant-design/icons';

function InlineMenu() {
  const items = [
    {
      key: 'mail',
      icon: <MailOutlined />,
      label: 'Navigation One',
      children: [
        { key: '1-1', label: 'Option 1' },
        { key: '1-2', label: 'Option 2' },
        { key: '1-3', label: 'Option 3' },
      ],
    },
    {
      key: 'app',
      icon: <AppstoreOutlined />,
      label: 'Navigation Two',
      children: [
        { key: '2-1', label: 'Option 1' },
        { key: '2-2', label: 'Option 2' },
        { key: '2-3', label: 'Option 3' },
      ],
    },
    {
      key: 'setting',
      icon: <SettingOutlined />,
      label: 'Navigation Three',
      children: [
        { key: '3-1', label: 'Option 1' },
        { key: '3-2', label: 'Option 2' },
        { key: '3-3', label: 'Option 3' },
      ],
    },
  ];

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('click ', e);
  };

  return (
    <Menu
      onClick={onClick}
      style={{ width: 256 }}
      mode="inline"
      defaultSelectedKeys={['1-1']}
      defaultOpenKeys={['mail']}
      items={items}
    />
  );
}
```

### 导航菜单模式

#### 水平导航菜单

```tsx
import { Menu } from 'antd';
import { HomeOutlined, UserOutlined, SettingOutlined } from '@ant-design/icons';

function HorizontalNavMenu() {
  const items = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户管理',
      children: [
        { key: 'user-list', label: '用户列表' },
        { key: 'user-add', label: '添加用户' },
        { key: 'user-role', label: '角色管理' },
      ],
    },
    {
      key: 'setting',
      icon: <SettingOutlined />,
      label: '系统设置',
      children: [
        { key: 'setting-basic', label: '基础设置' },
        { key: 'setting-security', label: '安全设置' },
        { key: 'setting-notify', label: '通知设置' },
      ],
    },
  ];

  const [current, setCurrent] = useState('home');

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('click ', e);
    setCurrent(e.key);
  };

  return (
    <Menu
      onClick={onClick}
      selectedKeys={[current]}
      mode="horizontal"
      items={items}
    />
  );
}
```

#### 侧边栏菜单

```tsx
import { Menu, Layout } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Sider } = Layout;

function SidebarMenu() {
  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: 'users',
      icon: <UserOutlined />,
      label: '用户管理',
      children: [
        { key: 'user-list', label: '用户列表' },
        { key: 'user-add', label: '添加用户' },
        { key: 'user-roles', label: '角色管理' },
      ],
    },
    {
      key: 'content',
      icon: <FileTextOutlined />,
      label: '内容管理',
      children: [
        { key: 'article-list', label: '文章列表' },
        { key: 'article-add', label: '发布文章' },
        { key: 'category', label: '分类管理' },
      ],
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  return (
    <Sider width={256} style={{ background: '#fff' }}>
      <Menu
        mode="inline"
        defaultSelectedKeys={['dashboard']}
        defaultOpenKeys={['users']}
        style={{ height: '100%', borderRight: 0 }}
        items={menuItems}
      />
    </Sider>
  );
}
```

### 菜单分组和分割线

```tsx
import { Menu } from 'antd';
import { AppstoreOutlined } from '@ant-design/icons';

function GroupedMenu() {
  const items = [
    {
      key: 'g1',
      label: 'Item Group 1',
      type: 'group',
      children: [
        { key: '1', label: 'Option 1' },
        { key: '2', label: 'Option 2' },
      ],
    },
    {
      key: 'g2',
      label: 'Item Group 2',
      type: 'group',
      children: [
        { key: '3', label: 'Option 3' },
        { key: '4', label: 'Option 4' },
      ],
    },
    {
      type: 'divider',
    },
    {
      key: 'setting',
      icon: <AppstoreOutlined />,
      label: 'Settings',
    },
  ];

  return (
    <Menu
      mode="inline"
      defaultSelectedKeys={['1']}
      defaultOpenKeys={['g1']}
      style={{ width: 256 }}
      items={items}
    />
  );
}
```

### 图标菜单

```tsx
import { Menu } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  FileTextOutlined,
  SettingOutlined,
  BellOutlined,
} from '@ant-design/icons';

function IconMenu() {
  const items = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: 'notification',
      icon: <BellOutlined />,
      label: '通知中心',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: 'content',
      icon: <FileTextOutlined />,
      label: '内容管理',
    },
    {
      key: 'setting',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  return (
    <Menu
      mode="vertical"
      defaultSelectedKeys={['home']}
      items={items}
      style={{ width: 200 }}
    />
  );
}
```

### 动态菜单

#### 从后端数据生成菜单

```tsx
import { Menu, Spin } from 'antd';
import { useEffect, useState } from 'react';
import { HomeOutlined, UserOutlined, SettingOutlined } from '@ant-design/icons';

interface MenuItem {
  id: string;
  title: string;
  icon?: string;
  children?: MenuItem[];
  path?: string;
}

function DynamicMenu() {
  const [menuItems, setMenuItems] = useState<MenuProps['items']>([]);
  const [loading, setLoading] = useState(true);

  // 图标映射
  const iconMap: Record<string, React.ReactNode> = {
    home: <HomeOutlined />,
    user: <UserOutlined />,
    setting: <SettingOutlined />,
  };

  // 转换后端数据为 Menu items 格式
  const transformMenuItems = (items: MenuItem[]): MenuProps['items'] => {
    return items.map((item) => ({
      key: item.id,
      label: item.title,
      icon: item.icon ? iconMap[item.icon] : undefined,
      children: item.children ? transformMenuItems(item.children) : undefined,
    }));
  };

  useEffect(() => {
    // 模拟从后端获取菜单数据
    const fetchMenuData = async () => {
      try {
        // 实际应用中这里应该是 API 调用
        const response: MenuItem[] = [
          {
            id: 'home',
            title: '首页',
            icon: 'home',
            path: '/',
          },
          {
            id: 'user',
            title: '用户管理',
            icon: 'user',
            children: [
              { id: 'user-list', title: '用户列表', path: '/users' },
              { id: 'user-add', title: '添加用户', path: '/users/add' },
            ],
          },
          {
            id: 'setting',
            title: '系统设置',
            icon: 'setting',
            path: '/settings',
          },
        ];

        setMenuItems(transformMenuItems(response));
      } catch (error) {
        console.error('Failed to fetch menu data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMenuData();
  }, []);

  if (loading) {
    return <Spin />;
  }

  return (
    <Menu
      mode="inline"
      defaultSelectedKeys={['home']}
      items={menuItems}
      style={{ width: 256 }}
    />
  );
}
```

#### 权限控制菜单

```tsx
import { Menu } from 'antd';
import { useAppSelector } from '@/hooks/redux';

interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  permission?: string;
  children?: MenuItem[];
}

function PermissionMenu() {
  // 从 Redux 或 Context 获取用户权限
  const userPermissions = useAppSelector((state) => state.auth.permissions);

  // 检查权限
  const hasPermission = (permission?: string): boolean => {
    if (!permission) return true;
    return userPermissions.includes(permission);
  };

  // 过滤菜单项
  const filterMenuItems = (items: MenuItem[]): MenuProps['items'] => {
    return items
      .filter((item) => hasPermission(item.permission))
      .map((item) => ({
        key: item.key,
        label: item.label,
        icon: item.icon,
        children: item.children ? filterMenuItems(item.children) : undefined,
      }));
  };

  const allMenuItems: MenuItem[] = [
    {
      key: 'dashboard',
      label: '仪表盘',
    },
    {
      key: 'users',
      label: '用户管理',
      permission: 'user:view',
      children: [
        { key: 'user-list', label: '用户列表', permission: 'user:view' },
        { key: 'user-add', label: '添加用户', permission: 'user:create' },
      ],
    },
    {
      key: 'settings',
      label: '系统设置',
      permission: 'system:config',
    },
  ];

  const menuItems = filterMenuItems(allMenuItems);

  return (
    <Menu
      mode="inline"
      defaultSelectedKeys={['dashboard']}
      items={menuItems}
      style={{ width: 256 }}
    />
  );
}
```

### 菜单主题和样式

#### 暗色主题菜单

```tsx
import { Menu } from 'antd';
import { Layout } from 'antd';

const { Sider } = Layout;

function DarkThemeMenu() {
  const items = [
    { key: '1', label: 'Option 1' },
    { key: '2', label: 'Option 2' },
    { key: '3', label: 'Option 3' },
  ];

  return (
    <Sider theme="dark" style={{ width: 256 }}>
      <Menu
        theme="dark"
        mode="inline"
        defaultSelectedKeys={['1']}
        items={items}
      />
    </Sider>
  );
}
```

#### 自定义菜单样式

```tsx
import { Menu } from 'antd';

function CustomStyledMenu() {
  const items = [
    { key: '1', label: 'Option 1' },
    { key: '2', label: 'Option 2' },
    { key: '3', label: 'Option 3' },
  ];

  return (
    <Menu
      mode="vertical"
      defaultSelectedKeys={['1']}
      items={items}
      style={{
        width: 256,
        borderRight: '1px solid #f0f0f0',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}
    />
  );
}
```

### 菜单事件处理

```tsx
import { Menu } from 'antd';
import { useNavigate } from 'react-router-dom';

function EventHandlingMenu() {
  const navigate = useNavigate();

  const items = [
    { key: '/dashboard', label: '仪表盘' },
    { key: '/users', label: '用户管理' },
    { key: '/settings', label: '系统设置' },
  ];

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('Clicked menu item:', e.key);
    // 导航到对应路由
    navigate(e.key);
  };

  const onSelect: MenuProps['onSelect'] = (info) => {
    console.log('Selected menu item:', info);
  };

  const onOpenChange: MenuProps['onOpenChange'] = (openKeys) => {
    console.log('Open keys changed:', openKeys);
  };

  return (
    <Menu
      onClick={onClick}
      onSelect={onSelect}
      onOpenChange={onOpenChange}
      mode="inline"
      defaultSelectedKeys={['/dashboard']}
      items={items}
      style={{ width: 256 }}
    />
  );
}
```

---

## Breadcrumb 面包屑

### 基础面包屑

```tsx
import { Breadcrumb } from 'antd';

function BasicBreadcrumb() {
  return (
    <Breadcrumb
      items={[
        { title: 'Home' },
        { title: 'Library' },
        { title: 'Data' },
      ]}
    />
  );
}
```

### 带图标的面包屑

```tsx
import { Breadcrumb } from 'antd';
import { HomeOutlined, UserOutlined, RightOutlined } from '@ant-design/icons';

function IconBreadcrumb() {
  const items = [
    {
      href: '/',
      title: <><HomeOutlined /> Home</>,
    },
    {
      href: '/users',
      title: <><UserOutlined /> Users</>,
    },
    {
      title: 'Profile',
    },
  ];

  return <Breadcrumb items={items} separator={<RightOutlined />} />;
}
```

### 路由集成面包屑

```tsx
import { Breadcrumb } from 'antd';
import { useLocation, Link } from 'react-router-dom';

interface RouteItem {
  path: string;
  breadcrumbName: string;
  icon?: React.ReactNode;
}

const routeConfig: Record<string, RouteItem> = {
  '/': { path: '/', breadcrumbName: '首页' },
  '/users': { path: '/users', breadcrumbName: '用户管理' },
  '/users/:id': { path: '/users/:id', breadcrumbName: '用户详情' },
  '/settings': { path: '/settings', breadcrumbName: '系统设置' },
};

function RouterBreadcrumb() {
  const location = useLocation();

  // 解析当前路径，生成面包屑
  const pathSnippets = location.pathname.split('/').filter((i) => i);

  const breadcrumbItems = [
    {
      title: <Link to="/">首页</Link>,
    },
    ...pathSnippets.map((_, index) => {
      const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
      const route = findMatchingRoute(url);

      return {
        title: index === pathSnippets.length - 1 ? (
          route?.breadcrumbName || url
        ) : (
          <Link to={url}>{route?.breadcrumbName || url}</Link>
        ),
      };
    }),
  ];

  return <Breadcrumb items={breadcrumbItems} />;
}

// 查找匹配的路由配置
function findMatchingRoute(path: string): RouteItem | undefined {
  // 简化实现，实际应用中可能需要更复杂的路由匹配逻辑
  const exactMatch = routeConfig[path];
  if (exactMatch) return exactMatch;

  // 处理动态路由（如 /users/:123）
  for (const key in routeConfig) {
    if (key.includes(':')) {
      const pattern = key.replace(/:[^/]+/g, '[^/]+');
      const regex = new RegExp(`^${pattern}$`);
      if (regex.test(path)) {
        return routeConfig[key];
      }
    }
  }

  return undefined;
}
```

### 动态面包屑

```tsx
import { Breadcrumb } from 'antd';
import { useState, useEffect } from 'react';

interface BreadcrumbItem {
  title: string;
  path?: string;
}

function DynamicBreadcrumb() {
  const [breadcrumbItems, setBreadcrumbItems] = useState<BreadcrumbItem[]>([]);

  useEffect(() => {
    // 根据当前页面状态生成面包屑
    const updateBreadcrumb = () => {
      const items: BreadcrumbItem[] = [
        { title: '首页', path: '/' },
      ];

      // 根据当前路由或状态添加面包屑项
      const currentPath = window.location.pathname;
      if (currentPath.startsWith('/users')) {
        items.push({ title: '用户管理', path: '/users' });
      }

      if (currentPath.includes('/detail')) {
        items.push({ title: '详情' });
      }

      setBreadcrumbItems(items);
    };

    updateBreadcrumb();

    // 监听路由变化
    window.addEventListener('popstate', updateBreadcrumb);
    return () => {
      window.removeEventListener('popstate', updateBreadcrumb);
    };
  }, []);

  const items = breadcrumbItems.map((item, index) => ({
    title: item.path ? (
      index === breadcrumbItems.length - 1 ? (
        item.title
      ) : (
        <a href={item.path}>{item.title}</a>
      )
    ) : (
      item.title
    ),
  }));

  return <Breadcrumb items={items} />;
}
```

---

## Steps 步骤条

### 基础步骤条

```tsx
import { Steps } from 'antd';

function BasicSteps() {
  const description = 'This is a description.';

  return (
    <Steps
      current={1}
      items={[
        {
          title: 'Finished',
          description,
        },
        {
          title: 'In Progress',
          description,
        },
        {
          title: 'Waiting',
          description,
        },
      ]}
    />
  );
}
```

### 导航步骤条

```tsx
import { Steps } from 'antd';
import { useState } from 'react';

function NavigationSteps() {
  const [current, setCurrent] = useState(0);

  const onChange = (value: number) => {
    console.log('onChange:', value);
    setCurrent(value);
  };

  const steps = [
    {
      title: 'First',
      content: 'First-content',
    },
    {
      title: 'Second',
      content: 'Second-content',
    },
    {
      title: 'Last',
      content: 'Last-content',
    },
  ];

  return (
    <div>
      <Steps
        current={current}
        onChange={onChange}
        items={steps}
      />
      <div style={{ marginTop: 24 }}>
        {steps[current].content}
      </div>
      <div style={{ marginTop: 24 }}>
        {current < steps.length - 1 && (
          <button onClick={() => setCurrent(current + 1)}>
            Next
          </button>
        )}
        {current === steps.length - 1 && (
          <button onClick={() => console.log('Processing complete!')}>
            Done
          </button>
        )}
        {current > 0 && (
          <button
            style={{ margin: '0 8px' }}
            onClick={() => setCurrent(current - 1)}
          >
            Previous
          </button>
        )}
      </div>
    </div>
  );
}
```

### 垂直步骤条

```tsx
import { Steps } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';

function VerticalSteps() {
  return (
    <Steps
      direction="vertical"
      current={1}
      items={[
        {
          title: 'Finished',
          description: 'This step is finished',
          icon: <CheckCircleOutlined />,
        },
        {
          title: 'In Progress',
          description: 'This step is in progress',
          icon: <ClockCircleOutlined />,
        },
        {
          title: 'Waiting',
          description: 'This step is waiting',
        },
        {
          title: 'Last',
          description: 'This is the last step',
        },
      ]}
    />
  );
}
```

### 错误步骤处理

```tsx
import { Steps, Button } from 'antd';
import { useState } from 'react';

function ErrorSteps() {
  const [current, setCurrent] = useState(0);

  const steps = [
    {
      title: 'Account',
      status: 'finish',
      icon: null,
    },
    {
      title: 'Profile',
      status: 'error',
      icon: null,
    },
    {
      title: 'Result',
      status: 'wait',
      icon: null,
    },
  ];

  return (
    <div>
      <Steps current={current} items={steps} />
      <div style={{ marginTop: 24 }}>
        {current === 0 && (
          <div>Account content</div>
        )}
        {current === 1 && (
          <div>
            <p>Profile content</p>
            <p>Something went wrong!</p>
          </div>
        )}
        {current === 2 && (
          <div>Result content</div>
        )}
      </div>
      <div style={{ marginTop: 24 }}>
        {current < steps.length - 1 && (
          <Button type="primary" onClick={() => setCurrent(current + 1)}>
            Next
          </Button>
        )}
        {current === steps.length - 1 && (
          <Button type="primary" onClick={() => console.log('Processing complete!')}>
            Done
          </Button>
        )}
        {current > 0 && (
          <Button style={{ margin: '0 8px' }} onClick={() => setCurrent(current - 1)}>
            Previous
          </Button>
        )}
      </div>
    </div>
  );
}
```

### 步骤条自定义

```tsx
import { Steps } from 'antd';
import { CheckOutlined, UserOutlined, SolutionOutlined, LoadingOutlined } from '@ant-design/icons';

function CustomSteps() {
  return (
    <Steps
      current={1}
      items={[
        {
          title: 'Login',
          status: 'finish',
          icon: <UserOutlined />,
        },
        {
          title: 'Verification',
          status: 'process',
          icon: <LoadingOutlined />,
        },
        {
          title: 'Pay',
          status: 'wait',
          icon: <SolutionOutlined />,
        },
        {
          title: 'Done',
          status: 'wait',
          icon: <CheckOutlined />,
        },
      ]}
    />
  );
}
```

---

## Pagination 分页

### 基础分页

```tsx
import { Pagination } from 'antd';

function BasicPagination() {
  const onChange = (page: number, pageSize: number) => {
    console.log('Page:', page, 'PageSize:', pageSize);
  };

  return (
    <Pagination
      defaultCurrent={1}
      total={50}
      onChange={onChange}
    />
  );
}
```

### 更多分页

```tsx
import { Pagination } from 'antd';

function MorePagination() {
  const onChange = (page: number) => {
    console.log(page);
  };

  return (
    <Pagination
      showSizeChanger
      defaultCurrent={3}
      total={500}
      onChange={onChange}
    />
  );
}
```

### 简单分页

```tsx
import { Pagination } from 'antd';

function SimplePagination() {
  const onChange = (page: number) => {
    console.log(page);
  };

  return (
    <Pagination
      simple
      defaultCurrent={2}
      total={50}
      onChange={onChange}
    />
  );
}
```

### 受控分页

```tsx
import { Pagination } from 'antd';
import { useState } from 'react';

function ControlledPagination() {
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const onChange = (page: number, pageSize: number) => {
    console.log('Page:', page, 'PageSize:', pageSize);
    setCurrent(page);
    setPageSize(pageSize);
  };

  return (
    <div>
      <Pagination
        current={current}
        pageSize={pageSize}
        total={500}
        onChange={onChange}
        showSizeChanger
        showQuickJumper
        showTotal={(total) => `Total ${total} items`}
      />
      <div style={{ marginTop: 16 }}>
        Current Page: {current}, Page Size: {pageSize}
      </div>
    </div>
  );
}
```

### 总数显示

```tsx
import { Pagination } from 'antd';

function PaginationWithTotal() {
  return (
    <Pagination
      total={85}
      showTotal={(total) => `Total ${total} items`}
      defaultPageSize={20}
      defaultCurrent={1}
    />
  );
}
```

### 分页器完整配置

```tsx
import { Pagination } from 'antd';

function FullPagination() {
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const onChange = (page: number, pageSize: number) => {
    setCurrent(page);
    setPageSize(pageSize);
  };

  const onShowSizeChange = (current: number, size: number) => {
    console.log(current, size);
  };

  return (
    <Pagination
      current={current}
      pageSize={pageSize}
      total={500}

      // 显示总数
      showTotal={(total, range) =>
        `${range[0]}-${range[1]} of ${total} items`
      }

      // 每页显示数量选择器
      showSizeChanger
      onShowSizeChange={onShowSizeChange}

      // 快速跳转
      showQuickJumper

      // 页码大小
      pageSizeOptions={['10', '20', '30', '50', '100']}

      // 响应式
      responsive

      // 页面变化事件
      onChange={onChange}

      // 位置
      align="center"
    />
  );
}
```

---

## Anchor 锚点

### 基础锚点

```tsx
import { Anchor, Divider } from 'antd';

function BasicAnchor() {
  return (
    <div style={{ padding: '0 50px' }}>
      <Anchor
        items={[
          {
            key: 'part-1',
            href: '#part-1',
            title: 'Part 1',
          },
          {
            key: 'part-2',
            href: '#part-2',
            title: 'Part 2',
          },
          {
            key: 'part-3',
            href: '#part-3',
            title: 'Part 3',
          },
        ]}
      />
      <div>
        <div id="part-1" style={{ height: '100vh', background: '#rgba(0,180,0,0.05)' }}>
          Part 1
        </div>
        <Divider />
        <div id="part-2" style={{ height: '100vh', background: '#rgba(0,180,0,0.05)' }}>
          Part 2
        </div>
        <Divider />
        <div id="part-3" style={{ height: '100vh', background: '#rgba(0,180,0,0.05)' }}>
          Part 3
        </div>
      </div>
    </div>
  );
}
```

### 静态位置

```tsx
import { Anchor } from 'antd';

function StaticAnchor() {
  return (
    <div style={{ position: 'relative', height: '100vh', overflow: 'auto' }}>
      <Anchor
        affix={false}
        items={[
          {
            key: 'part-1',
            href: '#part-1',
            title: 'Part 1',
          },
          {
            key: 'part-2',
            href: '#part-2',
            title: 'Part 2',
          },
        ]}
      />
    </div>
  );
}
```

### 自定义锚点链接

```tsx
import { Anchor } from 'antd';

function CustomAnchor() {
  return (
    <Anchor
      items={[
        {
          key: 'part-1',
          href: '#part-1',
          title: 'Part 1',
          children: [
            {
              key: 'part-1-1',
              href: '#part-1-1',
              title: 'Part 1-1',
            },
            {
              key: 'part-1-2',
              href: '#part-1-2',
              title: 'Part 1-2',
            },
          ],
        },
        {
          key: 'part-2',
          href: '#part-2',
          title: 'Part 2',
        },
      ]}
    />
  );
}
```

---

## 完整使用示例

### 示例 1: 响应式导航菜单

```tsx
import { useState } from 'react';
import { Menu, Layout, Button, Drawer } from 'antd';
import {
  MenuOutlined,
  HomeOutlined,
  UserOutlined,
  FileTextOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Header } = Layout;

function ResponsiveNavMenu() {
  const [visible, setVisible] = useState(false);
  const [current, setCurrent] = useState('home');

  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: 'users',
      icon: <UserOutlined />,
      label: '用户管理',
      children: [
        { key: 'user-list', label: '用户列表' },
        { key: 'user-add', label: '添加用户' },
      ],
    },
    {
      key: 'content',
      icon: <FileTextOutlined />,
      label: '内容管理',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const showDrawer = () => {
    setVisible(true);
  };

  const onClose = () => {
    setVisible(false);
  };

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('click ', e);
    setCurrent(e.key);
    onClose();
  };

  return (
    <Header style={{ position: 'fixed', zIndex: 1, width: '100%', display: 'flex', alignItems: 'center' }}>
      {/* 移动端菜单按钮 */}
      <Button
        type="text"
        icon={<MenuOutlined />}
        onClick={showDrawer}
        style={{
          display: window.innerWidth < 768 ? 'block' : 'none',
          marginRight: 16,
        }}
      />

      {/* 桌面端菜单 */}
      <div style={{ display: window.innerWidth >= 768 ? 'block' : 'none', flex: 1 }}>
        <Menu
          theme="dark"
          mode="horizontal"
          onClick={onClick}
          selectedKeys={[current]}
          items={menuItems}
        />
      </div>

      {/* 移动端抽屉菜单 */}
      <Drawer
        title="Menu"
        placement="left"
        onClose={onClose}
        visible={visible}
        bodyStyle={{ padding: 0 }}
      >
        <Menu
          mode="inline"
          onClick={onClick}
          selectedKeys={[current]}
          items={menuItems}
          style={{ height: '100%', borderRight: 0 }}
        />
      </Drawer>
    </Header>
  );
}
```

### 示例 2: 动态菜单生成

```tsx
import { useState, useEffect } from 'react';
import { Menu, Spin, message } from 'antd';

interface MenuData {
  id: string;
  name: string;
  path?: string;
  icon?: string;
  children?: MenuData[];
}

function DynamicMenuGeneration() {
  const [menuItems, setMenuItems] = useState<MenuProps['items']>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 图标映射
  const iconMap: Record<string, React.ReactNode> = {
    dashboard: <HomeOutlined />,
    users: <UserOutlined />,
    settings: <SettingOutlined />,
  };

  // 转换后端数据为 Menu items 格式
  const transformMenuItems = (data: MenuData[]): MenuProps['items'] => {
    return data.map((item) => ({
      key: item.id,
      label: item.name,
      icon: item.icon ? iconMap[item.icon] : undefined,
      children: item.children ? transformMenuItems(item.children) : undefined,
    }));
  };

  // 获取菜单数据
  const fetchMenuData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 实际应用中这里应该是 API 调用
      const response = await fetch('/api/menus');
      if (!response.ok) {
        throw new Error('Failed to fetch menu data');
      }

      const data: MenuData[] = await response.json();
      setMenuItems(transformMenuItems(data));
    } catch (err) {
      console.error('Error fetching menu data:', err);
      setError('Failed to load menu');
      message.error('加载菜单失败');

      // 设置默认菜单
      setMenuItems([
        { key: 'home', label: '首页' },
        { key: 'settings', label: '设置' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMenuData();
  }, []);

  const onClick: MenuProps['onClick'] = (e) => {
    console.log('Clicked menu item:', e.key);
    // 导航到对应页面
    // router.push(e.key);
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin tip="Loading menu..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: 'red' }}>
        {error}
      </div>
    );
  }

  return (
    <Menu
      mode="inline"
      onClick={onClick}
      defaultSelectedKeys={['home']}
      items={menuItems}
      style={{ height: '100%', borderRight: 0 }}
    />
  );
}
```

### 示例 3: 面包屑路由集成

```tsx
import { Breadcrumb } from 'antd';
import { useLocation, Link } from 'react-router-dom';

interface BreadcrumbRoute {
  path: string;
  breadcrumbName: string;
  children?: BreadcrumbRoute[];
}

const routes: BreadcrumbRoute[] = [
  {
    path: '/',
    breadcrumbName: '首页',
  },
  {
    path: '/users',
    breadcrumbName: '用户管理',
    children: [
      {
        path: '/users/list',
        breadcrumbName: '用户列表',
      },
      {
        path: '/users/create',
        breadcrumbName: '创建用户',
      },
      {
        path: '/users/:id',
        breadcrumbName: '用户详情',
      },
    ],
  },
  {
    path: '/settings',
    breadcrumbName: '系统设置',
    children: [
      {
        path: '/settings/profile',
        breadcrumbName: '个人资料',
      },
      {
        path: '/settings/security',
        breadcrumbName: '安全设置',
      },
    ],
  },
];

function AppBreadcrumb() {
  const location = useLocation();

  // 根据当前路径生成面包屑
  const getBreadcrumbItems = () => {
    const items = [
      {
        title: <Link to="/">首页</Link>,
      },
    ];

    const pathSnippets = location.pathname.split('/').filter((i) => i);

    // 匹配路由
    for (let i = 0; i < pathSnippets.length; i++) {
      const url = `/${pathSnippets.slice(0, i + 1).join('/')}`;
      const matchedRoute = findRouteByUrl(url, routes);

      if (matchedRoute) {
        const isLast = i === pathSnippets.length - 1;
        items.push({
          title: isLast ? (
            matchedRoute.breadcrumbName
          ) : (
            <Link to={url}>{matchedRoute.breadcrumbName}</Link>
          ),
        });
      }
    }

    return items;
  };

  // 查找匹配的路由
  const findRouteByUrl = (url: string, routeList: BreadcrumbRoute[]): BreadcrumbRoute | null => {
    for (const route of routeList) {
      if (route.path === url) {
        return route;
      }

      // 处理动态路由参数
      const routePathParts = route.path.split('/');
      const urlParts = url.split('/');

      if (routePathParts.length === urlParts.length) {
        let match = true;
        for (let i = 0; i < routePathParts.length; i++) {
          if (!routePathParts[i].startsWith(':') && routePathParts[i] !== urlParts[i]) {
            match = false;
            break;
          }
        }
        if (match) return route;
      }

      // 递归查找子路由
      if (route.children) {
        const found = findRouteByUrl(url, route.children);
        if (found) return found;
      }
    }

    return null;
  };

  return (
    <Breadcrumb
      style={{ margin: '16px 0' }}
      items={getBreadcrumbItems()}
    />
  );
}
```

### 示例 4: 步骤条表单向导

```tsx
import { useState } from 'react';
import { Steps, Form, Input, Button, Result, Card } from 'antd';
import { UserOutlined, ContactOutlined, CheckOutlined } from '@ant-design/icons';

const { Step } = Steps;

function FormWizard() {
  const [current, setCurrent] = useState(0);
  const [form] = Form.useForm();

  const steps = [
    {
      title: '基本信息',
      icon: <UserOutlined />,
      content: (
        <Form
          form={form}
          layout="vertical"
          initialValues={{ name: '', email: '' }}
        >
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
        </Form>
      ),
    },
    {
      title: '联系方式',
      icon: <ContactOutlined />,
      content: (
        <Form
          layout="vertical"
          initialValues={{ phone: '', address: '' }}
        >
          <Form.Item
            label="电话"
            name="phone"
            rules={[{ required: true, message: '请输入电话' }]}
          >
            <Input placeholder="请输入电话" />
          </Form.Item>

          <Form.Item
            label="地址"
            name="address"
            rules={[{ required: true, message: '请输入地址' }]}
          >
            <Input placeholder="请输入地址" />
          </Form.Item>
        </Form>
      ),
    },
    {
      title: '完成',
      icon: <CheckOutlined />,
      content: (
        <Result
          status="success"
          title="提交成功！"
          subTitle="您的信息已成功提交，我们会尽快与您联系。"
          extra={[
            <Button type="primary" key="home" onClick={() => setCurrent(0)}>
              返回首页
            </Button>,
          ]}
        />
      ),
    },
  ];

  const next = () => {
    if (current === 0) {
      form.validateFields().then(() => {
        setCurrent(current + 1);
      });
    } else {
      setCurrent(current + 1);
    }
  };

  const prev = () => {
    setCurrent(current - 1);
  };

  return (
    <Card title="用户注册向导" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Steps current={current}>
        {steps.map((step) => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      <div style={{ marginTop: 24 }}>{steps[current].content}</div>

      {current < steps.length - 1 && (
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          {current > 0 && (
            <Button style={{ marginRight: 8 }} onClick={prev}>
              上一步
            </Button>
          )}
          <Button type="primary" onClick={next}>
            {current === steps.length - 2 ? '提交' : '下一步'}
          </Button>
        </div>
      )}
    </Card>
  );
}
```

### 示例 5: 受控分页组件

```tsx
import { useState, useEffect } from 'react';
import { Table, Pagination, Card } from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';

interface DataType {
  key: number;
  name: string;
  age: number;
  address: string;
}

const columns: ColumnsType<DataType> = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Age', dataIndex: 'age', key: 'age' },
  { title: 'Address', dataIndex: 'address', key: 'address' },
];

function ControlledPagination() {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 获取数据
  const fetchData = async (params: { page: number; pageSize: number }) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      const response = await fetch(`/api/data?page=${params.page}&pageSize=${params.pageSize}`);
      const result = await response.json();

      setData(
        result.data.map((item: any, index: number) => ({
          ...item,
          key: (params.page - 1) * params.pageSize + index,
        }))
      );

      setPagination({
        ...pagination,
        total: result.total,
        current: params.page,
        pageSize: params.pageSize,
      });
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchData({ page: 1, pageSize: 10 });
  }, []);

  // 处理分页变化
  const handleTableChange = (pagination: TablePaginationConfig) => {
    fetchData({
      page: pagination.current || 1,
      pageSize: pagination.pageSize || 10,
    });
  };

  // 处理 Pagination 组件变化
  const onPaginationChange = (page: number, pageSize: number) => {
    fetchData({ page, pageSize });
  };

  const onShowSizeChange = (current: number, size: number) => {
    fetchData({ page: 1, pageSize: size });
  };

  return (
    <Card title="用户列表" style={{ margin: 24 }}>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={false}
        onChange={handleTableChange}
      />

      <div style={{ marginTop: 16, textAlign: 'right' }}>
        <Pagination
          current={pagination.current}
          pageSize={pagination.pageSize}
          total={pagination.total}
          onChange={onPaginationChange}
          onShowSizeChange={onShowSizeChange}
          showSizeChanger
          showQuickJumper
          showTotal={(total, range) =>
            `${range[0]}-${range[1]} of ${total} items`
          }
          pageSizeOptions={['10', '20', '30', '50', '100']}
        />
      </div>
    </Card>
  );
}
```

---

## 最佳实践

### Menu 使用建议

**✅ 推荐**

```tsx
// 1. 使用 items 属性，清晰定义菜单结构
const items = [
  { key: 'home', label: '首页', icon: <HomeOutlined /> },
  { key: 'users', label: '用户管理', children: [...] },
];

<Menu mode="inline" items={items} />

// 2. 合理使用 defaultOpenKeys 预展开常用菜单
<Menu
  mode="inline"
  defaultOpenKeys={['users', 'settings']}
  items={items}
/>

// 3. 侧边栏使用 mode="inline"，顶部导航使用 mode="horizontal"
```

**❌ 避免**

```tsx
// 1. 避免手动渲染 Menu.Item，应该使用 items 属性
<Menu>
  <Menu.Item>Option 1</Menu.Item>
  <Menu.Item>Option 2</Menu.Item>
</Menu>

// 2. 避免过深的菜单嵌套（超过 3 层）
// 3. 避免在同一个菜单中混合使用图标和无图标项
```

### Breadcrumb 使用建议

**✅ 推荐**

```tsx
// 1. 结合路由使用，动态生成面包屑
<Breadcrumb items={generateBreadcrumbFromRoute(location.pathname)} />

// 2. 最后一项不应该是链接（表示当前位置）
const items = [
  { title: <Link to="/">Home</Link> },
  { title: 'Current Page' }, // 最后一项不是链接
];

// 3. 使用 items 属性，清晰定义结构
```

**❌ 避免**

```tsx
// 1. 避免硬编码面包屑
<Breadcrumb>
  <Breadcrumb.Item>Home</Breadcrumb.Item>
  <Breadcrumb.Item>Library</Breadcrumb.Item>
</Breadcrumb>

// 2. 避免在面包屑中显示过多层级（超过 5 层）
```

### Steps 使用建议

**✅ 推荐**

```tsx
// 1. 步骤数量控制在 3-7 步
// 2. 每个步骤有清晰的标题和描述
// 3. 使用 onChange 允许用户跳转到已完成或可访问的步骤

<Steps
  current={current}
  onChange={setCurrent}
  items={[
    { title: 'Step 1', description: 'Description 1' },
    { title: 'Step 2', description: 'Description 2' },
  ]}
/>
```

**❌ 避免**

```tsx
// 1. 避免步骤过多导致用户压力
// 2. 避禁用 onChange 导致用户无法返回修改
// 3. 避免在步骤中使用过于复杂的表单
```

### Pagination 使用建议

**✅ 推荐**

```tsx
// 1. 显示总数，让用户知道数据量
<Pagination
  showTotal={(total) => `Total ${total} items`}
  total={500}
/>

// 2. 提供快速跳转功能
<Pagination showQuickJumper total={500} />

// 3. 允许用户选择每页显示数量
<Pagination showSizeChanger total={500} />
```

**❌ 避免**

```tsx
// 1. 避免每页显示数量选项过多（不超过 5 个）
// 2. 避免在数据量很少时显示分页器（total < pageSize）
// 3. 避免在移动端使用复杂的分页器（使用简单模式或加载更多）
```

### 性能优化建议

1. **Menu 懒加载**
   - 对于大型菜单，使用虚拟滚动
   - 按需加载子菜单数据

2. **Breadcrumb 缓存**
   - 缓存路由到面包屑的映射关系
   - 避免每次都重新计算

3. **Steps 状态保存**
   - 保存每个步骤的表单数据
   - 返回时恢复之前填写的内容

4. **Pagination 服务端分页**
   - 对于大数据量，使用服务端分页
   - 避免一次性加载所有数据

---

## 常见问题

### Q: Menu 如何实现路由跳转?

**A**: 使用 `onClick` 事件结合 React Router：

```tsx
import { Menu } from 'antd';
import { useNavigate } from 'react-router-dom';

function RouterMenu() {
  const navigate = useNavigate();

  const items = [
    { key: '/home', label: '首页' },
    { key: '/users', label: '用户管理' },
  ];

  const onClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

  return <Menu onClick={onClick} items={items} />;
}
```

### Q: Breadcrumb 如何处理动态路由参数?

**A**: 使用正则表达式或路由匹配库：

```tsx
function findMatchingRoute(path: string, routes: Route[]) {
  for (const route of routes) {
    // 将 :id 等参数转换为正则表达式
    const pattern = route.path.replace(/:[^/]+/g, '[^/]+');
    const regex = new RegExp(`^${pattern}$`);

    if (regex.test(path)) {
      return route;
    }
  }
  return null;
}
```

### Q: Steps 如何禁用某些步骤的访问?

**A**: 控制 `onChange` 行为：

```tsx
<Steps
  current={current}
  onChange={(step) => {
    // 只允许访问已完成的步骤或当前步骤的下一步
    if (step <= current + 1) {
      setCurrent(step);
    }
  }}
  items={steps}
/>
```

### Q: Pagination 如何实现服务端分页?

**A**: 监听 `onChange` 和 `onShowSizeChange` 事件，从后端获取数据：

```tsx
const [data, setData] = useState([]);

const fetchData = async (page, pageSize) => {
  const response = await fetch(`/api/data?page=${page}&size=${pageSize}`);
  const result = await response.json();
  setData(result.data);
};

<Pagination
  onChange={fetchData}
  onShowSizeChange={(current, size) => fetchData(1, size)}
  total={total}
/>
```

### Q: Anchor 为什么滚动时不高亮当前项?

**A**: 检查以下几点：
1. 确保 `href` 与页面中元素的 `id` 匹配
2. 确保容器有足够的高度可滚动
3. 检查是否有 CSS `overflow` 设置影响了滚动

```tsx
// 确保链接和 ID 匹配
<Anchor
  items={[
    { key: '1', href: '#section-1', title: 'Section 1' },
  ]}
/>

<div id="section-1">Content</div>
```

---

## 参考资料

- [Menu 官方文档](https://ant.design/components/menu-cn/)
- [Breadcrumb 官方文档](https://ant.design/components/breadcrumb-cn/)
- [Steps 官方文档](https://ant.design/components/steps-cn/)
- [Pagination 官方文档](https://ant.design/components/pagination-cn/)
- [Anchor 官方文档](https://ant.design/components/anchor-cn/)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
