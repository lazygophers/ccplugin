---
name: antd-config-skills
description: Ant Design 配置系统完整指南 - ConfigProvider 全局配置、主题继承、组件默认配置、国际化配置
---

# antd-config: Ant Design 配置系统完整指南

Ant Design 配置系统是管理和定制整个应用 UI 组件行为的核心机制，通过 `ConfigProvider` 组件实现全局统一的配置管理，包括主题、语言、组件默认属性等。

---

## 概述

### 核心功能

- **全局主题配置** - 统一管理应用的主题色、组件样式、字体等
- **组件默认配置** - 设置所有组件的默认属性，避免重复配置
- **国际化支持** - 统一配置所有组件的语言环境
- **前缀定制** - 修改 CSS 类名前缀，避免样式冲突
- **主题继承** - 支持多层 ConfigProvider 嵌套，实现局部主题定制
- **App 组件集成** - 结合 App 组件实现全局方法配置

### 配置优先级

```
组件属性 > 内层 ConfigProvider > 外层 ConfigProvider > antd 默认值
```

---

## ConfigProvider 组件

### 基础用法

`ConfigProvider` 是一个高阶组件，包裹在应用最外层，为所有子组件提供统一配置：

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <YourApplication />
    </ConfigProvider>
  );
}
```

### ConfigProvider 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `theme` | `ThemeConfig` | - | 全局主题配置 |
| `locale` | `Locale` | - | 国际化语言包 |
| `componentSize` | `'small' \| 'middle' \| 'large'` | - | 组件默认尺寸 |
| `componentDisabled` | `boolean` | - | 组件默认禁用状态 |
| `direction` | `'ltr' \| 'rtl'` | `'ltr'` | 文本方向（支持 RTL） |
| `prefixCls` | `string` | `'ant'` | CSS 类名前缀 |
| `iconPrefixCls` | `string` | `'anticon'` | 图标类名前缀 |
| `getPopupContainer` | `(node: HTMLElement) => HTMLElement` | - | 弹出层挂载容器 |
| `getTargetContainer` | `() => HTMLElement` | - | 某些组件的挂载容器 |
| `renderEmpty` | `() => ReactNode` | - | 自定义空状态 |
| `form` | `FormConfig` | - | Form 组件全局配置 |
| `input` | `InputConfig` | - | Input 组件全局配置 |
| `select` | `SelectConfig` | - | Select 组件全局配置 |

---

## 全局主题配置

### 主题基础配置

Ant Design 5.x 使用 Design Token 系统进行主题配置：

```tsx
import { ConfigProvider, theme } from 'antd';

function App() {
  return (
    <ConfigProvider
      theme={{
        // 1. Seed Token（种子令牌）
        token: {
          colorPrimary: '#1890ff',       // 主色
          colorSuccess: '#52c41a',       // 成功色
          colorWarning: '#faad14',       // 警告色
          colorError: '#ff4d4f',         // 错误色
          colorInfo: '#1890ff',          // 信息色
          colorLink: '#1890ff',          // 链接色
          colorTextBase: '#000',         // 文本色
          colorBgBase: '#fff',           // 背景色
          fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial`,
          fontSize: 14,                  // 基础字号
          borderRadius: 2,               // 圆角
        },

        // 2. Component Token（组件令牌）
        components: {
          Button: {
            colorPrimary: '#00b96b',
            algorithm: theme.darkAlgorithm, // 使用暗色算法
          },
          Input: {
            colorBgContainer: '#f0f0f0',
          },
          Table: {
            headerBg: '#fafafa',
          },
        },

        // 3. Algorithm Token（算法令牌）
        algorithm: theme.defaultAlgorithm, // theme.darkAlgorithm, theme.compactAlgorithm
      }}
    >
      <YourApp />
    </ConfigProvider>
  );
}
```

### 主题继承

#### 静态主题继承

```tsx
import { ConfigProvider, Button } from 'antd';

function ThemeInheritance() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          fontSize: 14,
        },
        components: {
          Button: {
            fontWeight: 700,
          },
        },
      }}
    >
      {/* 这个 Button 继承外层主题：colorPrimary: #1890ff, fontWeight: 700 */}
      <Button>Outer Button</Button>

      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#52c41a', // 覆盖外层的主色
          },
          components: {
            Button: {
              // 只覆盖 fontWeight，colorPrimary 仍继承外层
              fontWeight: 400,
            },
          },
        }}
      >
        {/* 这个 Button 的 colorPrimary: #52c41a（内层覆盖），fontWeight: 400（内层覆盖） */}
        <Button>Inner Button</Button>
      </ConfigProvider>
    </ConfigProvider>
  );
}
```

#### 组件级主题覆盖

```tsx
import { ConfigProvider, Button, theme } from 'antd';

function ComponentLevelTheme() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
        components: {
          Button: {
            colorPrimary: '#722ed1', // 覆盖全局主色
          },
        },
      }}
    >
      <Button type="primary">Purple Button</Button>

      {/* 使用 theme.useTokens() 在组件内部访问主题 */}
      <ThemedButton />
    </ConfigProvider>
  );
}

function ThemedButton() {
  const { token } = theme.useToken();

  return (
    <Button
      style={{
        backgroundColor: token.colorPrimary,
        borderColor: token.colorPrimary,
      }}
    >
      Dynamic Button
    </Button>
  );
}
```

### 动态主题切换

```tsx
import { useState } from 'react';
import { ConfigProvider, theme, Button, Card, Typography } from 'antd';

const { Title } = Typography;

function DynamicThemeSwitcher() {
  const [isDark, setIsDark] = useState(false);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDark ? '#1677ff' : '#1890ff',
        },
      }}
    >
      <Card style={{ width: 400 }}>
        <Title level={4}>
          Current Theme: {isDark ? 'Dark' : 'Light'}
        </Title>

        <Button
          type="primary"
          onClick={() => setIsDark(!isDark)}
        >
          Toggle Theme
        </Button>

        <p style={{ marginTop: 16 }}>
          This is a demo of dynamic theme switching.
          All components will update automatically when theme changes.
        </p>
      </Card>
    </ConfigProvider>
  );
}
```

### 多主题配置

```tsx
import { ConfigProvider, theme, Button } from 'antd';

const themes = {
  blue: {
    algorithm: theme.defaultAlgorithm,
    token: { colorPrimary: '#1890ff' },
  },
  green: {
    algorithm: theme.defaultAlgorithm,
    token: { colorPrimary: '#52c41a' },
  },
  dark: {
    algorithm: theme.darkAlgorithm,
    token: { colorPrimary: '#1677ff' },
  },
  compact: {
    algorithm: theme.compactAlgorithm,
    token: { colorPrimary: '#1890ff' },
  },
};

function MultiThemeApp() {
  const [currentTheme, setCurrentTheme] = useState<keyof typeof themes>('blue');

  return (
    <ConfigProvider theme={themes[currentTheme]}>
      <div>
        <Button
          type="primary"
          onClick={() => setCurrentTheme('blue')}
        >
          Blue Theme
        </Button>
        <Button
          style={{ marginLeft: 8 }}
          onClick={() => setCurrentTheme('green')}
        >
          Green Theme
        </Button>
        <Button
          style={{ marginLeft: 8 }}
          onClick={() => setCurrentTheme('dark')}
        >
          Dark Theme
        </Button>
        <Button
          style={{ marginLeft: 8 }}
          onClick={() => setCurrentTheme('compact')}
        >
          Compact Theme
        </Button>

        <YourContent />
      </div>
    </ConfigProvider>
  );
}
```

### 自定义 Design Token

```tsx
import { ConfigProvider } from 'antd';

function CustomTokenConfig() {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 颜色系统
          colorPrimary: '#1890ff',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorInfo: '#1677ff',
          colorLink: '#1677ff',

          // 字体系统
          fontSize: 14,
          fontSizeHeading1: 38,
          fontSizeHeading2: 30,
          fontSizeHeading3: 24,
          fontSizeHeading4: 20,
          fontSizeHeading5: 16,

          // 圆角
          borderRadius: 2,
          borderRadiusLG: 2,
          borderRadiusSM: 2,

          // 间距
          marginXS: 8,
          marginSM: 12,
          margin: 16,
          marginMD: 20,
          marginLG: 24,
          marginXL: 32,

          // 阴影
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
          boxShadowSecondary: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
        },
      }}
    >
      <YourApp />
    </ConfigProvider>
  );
}
```

---

## 组件默认配置

### 统一组件尺寸

```tsx
import { ConfigProvider, Button, Input, Select } from 'antd';

function UniformSize() {
  return (
    <ConfigProvider componentSize="large">
      <div>
        <Button type="primary">Large Button</Button>
        <Input placeholder="Large Input" />
        <Select placeholder="Large Select" />
      </div>
    </ConfigProvider>
  );
}
```

### 统一禁用状态

```tsx
import { ConfigProvider, Button, Input, Checkbox } from 'antd';

function UniformDisabled() {
  return (
    <ConfigProvider componentDisabled={true}>
      <div>
        <Button disabled>Disabled Button</Button>
        <Input disabled placeholder="Disabled Input" />
        <Checkbox disabled>Disabled Checkbox</Checkbox>
      </div>
    </ConfigProvider>
  );
}
```

### Button 默认配置

```tsx
import { ConfigProvider, Button } from 'antd';

function ButtonDefaults() {
  return (
    <ConfigProvider
      theme={{
        components: {
          Button: {
            colorPrimary: '#722ed1',
            defaultBg: '#f0f0f0',
            defaultBorderColor: '#d9d9d9',
            defaultColor: '#000',
            algorithm: true, // 启用算法
            fontWeight: 600,
          },
        },
      }}
    >
      <Button type="primary">Primary Button</Button>
      <Button>Default Button</Button>
      <Button type="dashed">Dashed Button</Button>
      <Button type="link">Link Button</Button>
    </ConfigProvider>
  );
}
```

### Input 默认配置

```tsx
import { ConfigProvider, Input } from 'antd';

function InputDefaults() {
  return (
    <ConfigProvider
      theme={{
        components: {
          Input: {
            colorBgContainer: '#f5f5f5',
            colorBorder: '#d9d9d9',
            colorText: '#000',
            activeBorderColor: '#1890ff',
            hoverBorderColor: '#40a9ff',
            paddingSM: 4,
            paddingLG: 12,
          },
        },
      }}
    >
      <Input placeholder="Default size" />
      <Input size="small" placeholder="Small size" />
      <Input size="large" placeholder="Large size" />
      <Input.Password placeholder="Password input" />
      <Input.Search placeholder="Search input" />
    </ConfigProvider>
  );
}
```

### Table 默认配置

```tsx
import { ConfigProvider, Table } from 'antd';

function TableDefaults() {
  const dataSource = [
    { key: '1', name: 'John Brown', age: 32, address: 'New York No. 1 Lake Park' },
    { key: '2', name: 'Jim Green', age: 42, address: 'London No. 1 Lake Park' },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
    { title: 'Address', dataIndex: 'address', key: 'address' },
  ];

  return (
    <ConfigProvider
      theme={{
        components: {
          Table: {
            headerBg: '#fafafa',
            headerColor: '#000',
            borderColor: '#f0f0f0',
            rowHoverBg: '#f5f5f5',
            fontSize: 14,
          },
        },
      }}
    >
      <Table dataSource={dataSource} columns={columns} />
    </ConfigProvider>
  );
}
```

### Form 默认配置

```tsx
import { ConfigProvider, Form, Input, Button } from 'antd';

function FormDefaults() {
  return (
    <ConfigProvider
      form={{
        requiredMark: 'optional', // 'optional' | 'optional' | false
        colon: true,              // 是否显示冒号
        validateMessages: {
          required: '${label} is required!',
          types: {
            email: '${label} is not a valid email!',
            number: '${label} is not a valid number!',
          },
        },
      }}
    >
      <Form
        name="basic"
        initialValues={{ remember: true }}
        onFinish={(values) => console.log(values)}
      >
        <Form.Item
          label="Email"
          name="email"
          rules={[{ required: true, type: 'email' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Age"
          name="age"
          rules={[{ required: true, type: 'number', min: 18 }]}
        >
          <Input type="number" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>
      </Form>
    </ConfigProvider>
  );
}
```

---

## 国际化配置

### 基础国际化

```tsx
import { ConfigProvider, DatePicker, Button } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import jaJP from 'antd/locale/ja_JP';

function I18nExample() {
  const [locale, setLocale] = useState(zhCN);

  return (
    <ConfigProvider locale={locale}>
      <div>
        <Button onClick={() => setLocale(zhCN)}>中文</Button>
        <Button onClick={() => setLocale(enUS)}>English</Button>
        <Button onClick={() => setLocale(jaJP)}>日本語</Button>

        <DatePicker />
      </div>
    </ConfigProvider>
  );
}
```

### 自定义语言包

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

const customLocale = {
  ...zhCN,
  DatePicker: {
    ...zhCN.DatePicker,
    lang: {
      ...zhCN.DatePicker.lang,
      placeholder: '请选择日期',
      rangePlaceholder: ['开始日期', '结束日期'],
    },
  },
  Table: {
    ...zhCN.Table,
    filterTitle: '筛选',
    filterConfirm: '确定',
    filterReset: '重置',
    selectAll: '全部选择',
    selectInvert: '反向选择',
  },
};

function CustomLocale() {
  return (
    <ConfigProvider locale={customLocale}>
      <YourApp />
    </ConfigProvider>
  );
}
```

### 日期格式化

```tsx
import { ConfigProvider, DatePicker } from 'antd';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import zhCN from 'antd/locale/zh_CN';

function DateFormat() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          // 设置日期格式
          fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`,
        },
      }}
    >
      <DatePicker
        format="YYYY-MM-DD"
        placeholder="选择日期"
      />
    </ConfigProvider>
  );
}
```

### 数字格式化

```tsx
import { ConfigProvider, Statistic } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function NumberFormat() {
  return (
    <ConfigProvider locale={zhCN}>
      <Statistic
        title="Active Users"
        value={1128900}
        precision={2}
        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
      />
    </ConfigProvider>
  );
}
```

---

## App 组件（Ant Design 5.x）

### App 基础用法

Ant Design 5.x 引入 `App` 组件，用于管理全局方法（Message、Modal、Notification）：

```tsx
import { App } from 'antd';

function RootApp() {
  return (
    <App>
      <YourApplication />
    </App>
  );
}
```

### App.useApp() Hook

```tsx
import { Button, App } from 'antd';

function MyComponent() {
  const { message, modal, notification } = App.useApp();

  const showMessage = () => {
    message.success('This is a success message!');
  };

  const showConfirm = () => {
    modal.confirm({
      title: 'Confirm',
      content: 'Do you want to delete this item?',
      onOk() {
        console.log('Confirmed');
      },
    });
  };

  const showNotification = () => {
    notification.info({
      message: 'Notification',
      description: 'This is a notification message',
    });
  };

  return (
    <div>
      <Button onClick={showMessage}>Show Message</Button>
      <Button onClick={showConfirm}>Show Confirm</Button>
      <Button onClick={showNotification}>Show Notification</Button>
    </div>
  );
}
```

### Message 全局配置

```tsx
import { App, ConfigProvider, theme } from 'antd';

function MessageConfig() {
  return (
    <ConfigProvider
      theme={{
        components: {
          Message: {
            colorBgSpotlight: 'rgba(0, 0, 0, 0.85)',
            colorText: '#fff',
            contentBg: '#fff',
          },
        },
      }}
    >
      <App>
        <YourApp />
      </App>
    </ConfigProvider>
  );
}
```

### Modal 全局配置

```tsx
import { ConfigProvider, App } from 'antd';

function ModalConfig() {
  return (
    <ConfigProvider
      theme={{
        components: {
          Modal: {
            contentBg: '#fff',
            headerBg: '#fafafa',
            footerBg: '#fafafa',
          },
        },
      }}
    >
      <App>
        <YourApp />
      </App>
    );
}
```

### Notification 全局配置

```tsx
import { ConfigProvider, App } from 'antd';

function NotificationConfig() {
  return (
    <ConfigProvider
      theme={{
        components: {
          Notification: {
            colorBgElevated: '#fff',
            colorText: '#000',
          },
        },
      }}
    >
      <App>
        <YourApp />
      </App>
    );
}
```

---

## 前缀定制

### 修改 CSS 类名前缀

```tsx
import { ConfigProvider } from 'antd';

function CustomPrefix() {
  return (
    <ConfigProvider prefixCls="my-app">
      <Button type="primary">
        This button will have class "my-app-btn" instead of "ant-btn"
      </Button>
    </ConfigProvider>
  );
}
```

### 修改图标前缀

```tsx
import { ConfigProvider } from 'antd';

function CustomIconPrefix() {
  return (
    <ConfigProvider iconPrefixCls="my-icon">
      <Button icon={<SearchOutlined />}>
        This icon will have class "my-icon-search" instead of "anticon-search"
      </Button>
    </ConfigProvider>
  );
}
```

### 完整前缀配置示例

```tsx
import { ConfigProvider, Button, Input, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function MultiInstanceApp() {
  return (
    <div>
      {/* 第一个 Ant Design 实例 */}
      <ConfigProvider
        prefixCls="app1"
        iconPrefixCls="app1-icon"
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#1890ff',
          },
        }}
      >
        <div className="app1-container">
          <h2>App 1</h2>
          <Button type="primary">App 1 Button</Button>
          <Input placeholder="App 1 Input" />
        </div>
      </ConfigProvider>

      {/* 第二个 Ant Design 实例（不同样式） */}
      <ConfigProvider
        prefixCls="app2"
        iconPrefixCls="app2-icon"
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#52c41a',
          },
        }}
      >
        <div className="app2-container">
          <h2>App 2</h2>
          <Button type="primary">App 2 Button</Button>
          <Input placeholder="App 2 Input" />
        </div>
      </ConfigProvider>
    </div>
  );
}
```

---

## 弹出层容器配置

### getPopupContainer

```tsx
import { ConfigProvider, Select, DatePicker, Dropdown } from 'antd';

function PopupContainerExample() {
  return (
    <ConfigProvider
      getPopupContainer={(node) => {
        // 将弹出层挂载到指定容器
        return node.parentNode || document.body;
      }}
    >
      <Select
        placeholder="Select"
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />

      <DatePicker />
    </ConfigProvider>
  );
}
```

### 固定容器挂载

```tsx
import { ConfigProvider, Modal, Dropdown } from 'antd';

function FixedPopupContainer() {
  const popupContainerRef = useRef<HTMLDivElement>(null);

  return (
    <div>
      <div ref={popupContainerRef} id="popup-container" />

      <ConfigProvider
        getPopupContainer={() => popupContainerRef.current || document.body}
      >
        <Dropdown menu={{ items: [{ key: '1', label: 'Item 1' }] }}>
          <Button>Click me</Button>
        </Dropdown>

        <Modal title="Modal" open>
          <p>The popup will be rendered in the fixed container</p>
        </Modal>
      </ConfigProvider>
    </div>
  );
}
```

---

## RTL 支持

### 启用 RTL

```tsx
import { ConfigProvider, Button, Input } from 'antd';
import arEG from 'antd/locale/ar_EG';

function RTLExample() {
  return (
    <ConfigProvider
      direction="rtl"
      locale={arEG}
    >
      <div>
        <Button type="primary">RTL Button</Button>
        <Input placeholder="RTL Input" />
      </div>
    </ConfigProvider>
  );
}
```

### 动态切换 LTR/RTL

```tsx
import { useState } from 'react';
import { ConfigProvider, Button, Input } from 'antd';

function DirectionSwitcher() {
  const [direction, setDirection] = useState<'ltr' | 'rtl'>('ltr');

  return (
    <ConfigProvider direction={direction}>
      <div>
        <Button onClick={() => setDirection(direction === 'ltr' ? 'rtl' : 'ltr')}>
          Toggle Direction
        </Button>
        <Input placeholder="Input with direction" />
      </div>
    </ConfigProvider>
  );
}
```

---

## 自定义空状态

### renderEmpty

```tsx
import { ConfigProvider, Table, Empty } from 'antd';

function CustomEmpty() {
  return (
    <ConfigProvider
      renderEmpty={() => (
        <Empty
          description="Custom empty state"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}
    >
      <Table dataSource={[]} columns={[]} />
    </ConfigProvider>
  );
}
```

---

## 完整使用示例

### 示例 1: 基础配置应用

```tsx
import { ConfigProvider, Button, Input, Select, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

function BasicConfigApp() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 4,
        },
      }}
      componentSize="middle"
    >
      <div style={{ padding: 24 }}>
        <h2>Basic Configured App</h2>

        <Button type="primary">Primary Button</Button>
        <Input placeholder="Input" style={{ marginLeft: 8 }} />
        <Select placeholder="Select" style={{ marginLeft: 8, width: 200 }} />
        <DatePicker style={{ marginLeft: 8 }} />
      </div>
    </ConfigProvider>
  );
}
```

### 示例 2: 主题切换应用

```tsx
import { useState } from 'react';
import { ConfigProvider, Layout, Button, theme, Card } from 'antd';
import { MoonOutlined, SunOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;

function ThemeSwitcherApp() {
  const [isDark, setIsDark] = useState(false);

  const { token } = theme.useToken();

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: token.colorBgContainer,
          }}
        >
          <h1 style={{ margin: 0 }}>Theme Switcher</h1>

          <Button
            type="text"
            icon={isDark ? <SunOutlined /> : <MoonOutlined />}
            onClick={() => setIsDark(!isDark)}
          >
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </Button>
        </Header>

        <Content style={{ padding: 24 }}>
          <Card>
            <h2>Current Theme: {isDark ? 'Dark' : 'Light'}</h2>
            <p>
              This is a demo of dynamic theme switching with Ant Design 5.
              Click the button in the header to toggle between light and dark mode.
            </p>

            <Button type="primary">Primary Button</Button>
            <Button style={{ marginLeft: 8 }}>Default Button</Button>
            <Button type="dashed" style={{ marginLeft: 8 }}>Dashed Button</Button>
          </Card>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}
```

### 示例 3: 国际化应用

```tsx
import { useState } from 'react';
import { ConfigProvider, DatePicker, Select, Button, Typography } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import jaJP from 'antd/locale/ja_JP';
import dayjs from 'dayjs';

const { Title } = Typography;

const locales = {
  zh: zhCN,
  en: enUS,
  ja: jaJP,
};

function I18nApp() {
  const [currentLocale, setCurrentLocale] = useState<keyof typeof locales>('zh');

  const changeLocale = (locale: keyof typeof locales) => {
    setCurrentLocale(locale);
    dayjs.locale(locale);
  };

  return (
    <ConfigProvider locale={locales[currentLocale]}>
      <div style={{ padding: 24, maxWidth: 600 }}>
        <Title level={3}>
          {currentLocale === 'zh' && '国际化示例'}
          {currentLocale === 'en' && 'Internationalization Example'}
          {currentLocale === 'ja' && '国際化の例'}
        </Title>

        <div style={{ marginBottom: 16 }}>
          <Button onClick={() => changeLocale('zh')}>中文</Button>
          <Button onClick={() => changeLocale('en')}>English</Button>
          <Button onClick={() => changeLocale('ja')}>日本語</Button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <DatePicker style={{ width: '100%' }} />
          <DatePicker.RangePicker style={{ width: '100%' }} />
        </div>
      </div>
    </ConfigProvider>
  );
}
```

### 示例 4: 完整企业级配置

```tsx
import { ConfigProvider, App, message, modal, notification } from 'antd';
import { theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function EnterpriseApp() {
  return (
    <ConfigProvider
      // 1. 国际化配置
      locale={zhCN}

      // 2. 主题配置
      theme={{
        token: {
          // 品牌色
          colorPrimary: '#1890ff',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',

          // 字体
          fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`,
          fontSize: 14,

          // 圆角
          borderRadius: 2,
        },

        // 3. 组件级别配置
        components: {
          Button: {
            fontWeight: 500,
            controlHeight: 36,
            paddingInline: 20,
          },

          Input: {
            paddingBlock: 8,
            paddingInline: 12,
            controlHeight: 36,
          },

          Table: {
            headerBg: '#fafafa',
            headerColor: 'rgba(0, 0, 0, 0.88)',
          },

          Form: {
            itemMarginBottom: 20,
            verticalLabelPadding: '0 0 8px',
          },
        },
      }}

      // 4. 组件默认配置
      componentSize="middle"

      // 5. 文本方向
      direction="ltr"

      // 6. CSS 类名前缀
      prefixCls="ant"

      // 7. 图标前缀
      iconPrefixCls="anticon"

      // 8. 弹出层容器
      getPopupContainer={(node) => {
        // 将弹出层挂载到触发元素所在的可滚动容器
        const scrollContainer = node?.closest('.scroll-container');
        return scrollContainer || document.body;
      }}

      // 9. 自定义空状态
      renderEmpty={() => (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p>暂无数据</p>
        </div>
      )}

      // 10. Form 全局配置
      form={{
        requiredMark: 'optional',
        colon: true,
        validateMessages: {
          required: '${label} 是必填项',
          types: {
            email: '${label} 格式不正确',
            number: '${label} 必须是数字',
          },
          string: {
            min: '${label} 至少 ${min} 个字符',
            max: '${label} 最多 ${max} 个字符',
          },
        },
      }}
    >
      {/* App 组件提供全局方法 */}
      <App>
        <YourEnterpriseApplication />
      </App>
    </ConfigProvider>
  );
}

function YourEnterpriseApplication() {
  const { message, modal, notification } = App.useApp();

  const handleSuccess = () => {
    message.success('操作成功！');
  };

  const handleConfirm = () => {
    modal.confirm({
      title: '确认操作',
      content: '确定要执行此操作吗？',
      onOk() {
        message.success('已确认');
      },
    });
  };

  const handleNotification = () => {
    notification.info({
      message: '通知',
      description: '这是一条通知消息',
    });
  };

  return (
    <div style={{ padding: 24 }}>
      <button onClick={handleSuccess}>显示 Message</button>
      <button onClick={handleConfirm}>显示 Modal</button>
      <button onClick={handleNotification}>显示 Notification</button>
    </div>
  );
}
```

### 示例 5: 多租户配置

```tsx
import { useState } from 'react';
import { ConfigProvider, Button, Card } from 'antd';
import { theme } from 'antd';

// 租户主题配置
const tenantThemes = {
  tenantA: {
    token: { colorPrimary: '#1890ff' },
    algorithm: theme.defaultAlgorithm,
  },
  tenantB: {
    token: { colorPrimary: '#52c41a' },
    algorithm: theme.defaultAlgorithm,
  },
  tenantC: {
    token: { colorPrimary: '#722ed1' },
    algorithm: theme.defaultAlgorithm,
  },
};

function MultiTenantApp() {
  const [currentTenant, setCurrentTenant] = useState<keyof typeof tenantThemes>('tenantA');

  return (
    <ConfigProvider theme={tenantThemes[currentTenant]}>
      <div style={{ padding: 24 }}>
        <h2>Multi-Tenant Application</h2>
        <p>Current Tenant: {currentTenant}</p>

        <div style={{ marginBottom: 16 }}>
          <Button onClick={() => setCurrentTenant('tenantA')}>Tenant A</Button>
          <Button onClick={() => setCurrentTenant('tenantB')} style={{ marginLeft: 8 }}>
            Tenant B
          </Button>
          <Button onClick={() => setCurrentTenant('tenantC')} style={{ marginLeft: 8 }}>
            Tenant C
          </Button>
        </div>

        <Card>
          <p>This card theme changes based on the selected tenant.</p>
          <Button type="primary">Primary Action</Button>
        </Card>
      </div>
    </ConfigProvider>
  );
}
```

### 示例 6: 嵌套配置

```tsx
import { ConfigProvider, Button, Card, Space, Typography } from 'antd';
import { theme } from 'antd';

const { Text } = Typography;

function NestedConfigExample() {
  return (
    // 外层配置：蓝色主题
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <Space direction="vertical" size="large" style={{ padding: 24 }}>
        <Card title="Outer Theme (Blue)">
          <Text>This card uses the outer blue theme.</Text>
          <Button type="primary" style={{ marginLeft: 8 }}>
            Blue Button
          </Button>
        </Card>

        {/* 内层配置：绿色主题 */}
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: '#52c41a',
            },
          }}
        >
          <Card title="Inner Theme (Green)">
            <Text>This card overrides the outer theme with green.</Text>
            <Button type="primary" style={{ marginLeft: 8 }}>
              Green Button
            </Button>

            {/* 更深层的配置：红色主题 */}
            <ConfigProvider
              theme={{
                token: {
                  colorPrimary: '#ff4d4f',
                },
              }}
            >
              <Card
                title="Deep Nested Theme (Red)"
                style={{ marginTop: 16 }}
              >
                <Text>This card has a deeply nested red theme.</Text>
                <Button type="primary" style={{ marginLeft: 8 }}>
                  Red Button
                </Button>
              </Card>
            </ConfigProvider>
          </Card>
        </ConfigProvider>
      </Space>
    </ConfigProvider>
  );
}
```

### 示例 7: 动态主题与配置同步

```tsx
import { useState, useEffect } from 'react';
import { ConfigProvider, Button, Card, theme, Typography, Slider, ColorPicker } from 'antd';

const { Title, Text } = Typography;

function DynamicThemeSync() {
  const [primaryColor, setPrimaryColor] = useState('#1890ff');
  const [borderRadius, setBorderRadius] = useState(2);
  const [fontSize, setFontSize] = useState(14);
  const [isDark, setIsDark] = useState(false);

  const themeConfig = {
    algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: primaryColor,
      borderRadius,
      fontSize,
    },
  };

  // 保存配置到 localStorage
  useEffect(() => {
    const savedConfig = localStorage.getItem('antd-theme-config');
    if (savedConfig) {
      const config = JSON.parse(savedConfig);
      setPrimaryColor(config.primaryColor);
      setBorderRadius(config.borderRadius);
      setFontSize(config.fontSize);
      setIsDark(config.isDark);
    }
  }, []);

  // 保存配置
  const saveConfig = () => {
    const config = {
      primaryColor,
      borderRadius,
      fontSize,
      isDark,
    };
    localStorage.setItem('antd-theme-config', JSON.stringify(config));
    message.success('Theme configuration saved!');
  };

  // 重置配置
  const resetConfig = () => {
    setPrimaryColor('#1890ff');
    setBorderRadius(2);
    setFontSize(14);
    setIsDark(false);
    localStorage.removeItem('antd-theme-config');
    message.info('Theme configuration reset!');
  };

  return (
    <ConfigProvider theme={themeConfig}>
      <div style={{ padding: 24 }}>
        <Title level={2}>Dynamic Theme Configuration</Title>

        <Card style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 主色选择 */}
            <div>
              <Text strong>Primary Color:</Text>
              <ColorPicker
                value={primaryColor}
                onChange={(color) => setPrimaryColor(color.toHexString())}
                showText
              />
            </div>

            {/* 圆角调整 */}
            <div>
              <Text strong>Border Radius: {borderRadius}px</Text>
              <Slider
                min={0}
                max={16}
                value={borderRadius}
                onChange={setBorderRadius}
              />
            </div>

            {/* 字体大小调整 */}
            <div>
              <Text strong>Font Size: {fontSize}px</Text>
              <Slider
                min={12}
                max={20}
                value={fontSize}
                onChange={setFontSize}
              />
            </div>

            {/* 暗色模式切换 */}
            <div>
              <Text strong>Dark Mode:</Text>
              <Button
                type={isDark ? 'primary' : 'default'}
                onClick={() => setIsDark(!isDark)}
                style={{ marginLeft: 8 }}
              >
                {isDark ? 'Enabled' : 'Disabled'}
              </Button>
            </div>

            {/* 操作按钮 */}
            <Space>
              <Button type="primary" onClick={saveConfig}>
                Save Configuration
              </Button>
              <Button onClick={resetConfig}>
                Reset
              </Button>
            </Space>
          </Space>
        </Card>

        {/* 预览区域 */}
        <Card title="Preview">
          <Space>
            <Button type="primary">Primary Button</Button>
            <Button>Default Button</Button>
            <Button type="dashed">Dashed Button</Button>
            <Button type="link">Link Button</Button>
          </Space>
        </Card>
      </div>
    </ConfigProvider>
  );
}
```

---

## 最佳实践

### 1. ConfigProvider 嵌套

**✅ 推荐**：在应用根节点配置全局主题，特殊区域使用内层 ConfigProvider 覆盖

```tsx
<ConfigProvider theme={globalTheme}>
  <App>
    <Header />
    <Content>
      <ConfigProvider theme={specialTheme}>
        <SpecialSection />
      </ConfigProvider>
    </Content>
    <Footer />
  </App>
</ConfigProvider>
```

**❌ 避免**：过深的嵌套影响可维护性

### 2. 主题切换优化

**✅ 推荐**：使用 React.memo 避免不必要的重渲染

```tsx
const ThemedComponent = React.memo(function ThemedComponent() {
  const { token } = theme.useToken();
  return <Button style={{ color: token.colorPrimary }}>Button</Button>;
});
```

**❌ 避免**：频繁切换主题导致性能问题

### 3. 性能考虑

- **主题计算**：Ant Design 5.x 使用 CSS-in-JS，主题切换时会重新计算样式
- **避免频繁更新**：使用防抖（debounce）处理用户输入的主题配置
- **局部渲染**：使用嵌套 ConfigProvider 实现局部主题，减少全局影响

```tsx
import { debounce } from 'lodash';

const debouncedSetTheme = debounce((color) => {
  setPrimaryColor(color);
}, 300);
```

### 4. RTL 支持注意事项

- 使用 RTL 语言包（如 `ar_EG`）自动设置 RTL
- 确保 CSS 支持 RTL（避免使用 `left`/`right`，使用 `marginInlineStart`）
- 测试所有组件在 RTL 模式下的布局

### 5. 弹出层容器

**✅ 推荐**：为弹出层指定合适的容器，避免滚动问题

```tsx
<ConfigProvider
  getPopupContainer={(node) => {
    const scrollContainer = node?.closest('.scroll-container');
    return scrollContainer || document.body;
  }}
>
```

**❌ 避免**：所有弹出层挂载到 body 导致的滚动和定位问题

### 6. 国际化最佳实践

- 统一使用 ConfigProvider 配置 locale，避免单个组件单独配置
- 结合 dayjs/locale 实现 DatePicker 等组件的本地化
- 自定义语言包时，基于官方语言包扩展，避免遗漏

---

## 常见问题

### Q: 为什么我的主题没有生效?

A: 检查以下几点：
1. 确认使用的是 Ant Design 5.x 版本（5.0+）
2. 检查 ConfigProvider 是否包裹在组件外层
3. 确认 token 名称正确（参考官方文档的 Design Token 列表）
4. 检查是否有内联样式覆盖了主题配置

### Q: 如何实现多主题共存?

A: 使用嵌套 ConfigProvider 或不同的 prefixCls：

```tsx
<ConfigProvider prefixCls="app1" theme={theme1}>
  <div className="app1">
    {/* App 1 内容 */}
  </div>
</ConfigProvider>

<ConfigProvider prefixCls="app2" theme={theme2}>
  <div className="app2">
    {/* App 2 内容 */}
  </div>
</ConfigProvider>
```

### Q: 主题切换后样式没有更新?

A: 确保：
1. 状态变化触发了组件重新渲染
2. 没有使用内联样式覆盖主题配置
3. 使用了正确的 theme 配置结构

### Q: 如何获取当前主题的 token?

A: 使用 `theme.useToken()` Hook：

```tsx
const { token, hashId } = theme.useToken();
console.log(token.colorPrimary); // 当前主题的主色
```

### Q: ConfigProvider 和 App 组件有什么区别?

A:
- **ConfigProvider**：提供配置（主题、语言、组件默认值等）
- **App**：提供全局方法（Message、Modal、Notification）

推荐一起使用：

```tsx
<ConfigProvider theme={...} locale={...}>
  <App>
    <YourApp />
  </App>
</ConfigProvider>
```

---

## 参考资料

- [ConfigProvider 官方文档](https://ant.design/components/config-provider-cn/)
- [App 组件官方文档](https://ant.design/components/app-cn/)
- [主题定制官方文档](https://ant.design/docs/react/customize-theme-cn)
- [Design Token 列表](https://ant.design/docs/react/customize-theme-cn#design-token)
- [国际化官方文档](https://ant.design/docs/react/i18n-cn)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- dayjs >= 1.11.0（用于日期处理）

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
