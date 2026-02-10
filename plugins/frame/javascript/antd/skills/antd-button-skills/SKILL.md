---
name: antd-button-skills
description: Ant Design 按钮组件完整指南 - Button 深度使用、按钮组、加载状态、图标按钮、下拉按钮
---

# antd-button: Ant Design 按钮组件完整指南

Button（按钮）是用户界面中最常用的交互元素，用于触发操作、提交表单、导航页面等。Ant Design 的 Button 组件提供了丰富的类型、尺寸、状态和组合方式，支持高度定制化，是构建现代化 Web 应用的基础组件。

---

## 概述

### 核心功能

- **多种按钮类型** - 主要、次要、虚线、链接、文本等
- **多种尺寸** - 大、中、小三种尺寸
- **状态管理** - 加载、禁用、危险等状态
- **图标支持** - 前缀图标、后缀图标、仅图标
- **按钮组** - Button.Group 组合按钮
- **危险操作** - 红色警告样式
- **块级按钮** - 占满父容器宽度
- **Ghost 模式** - 幽灵按钮（透明背景）

### 按钮类型

| 类型 | 说明 | 典型场景 |
|------|------|---------|
| **primary** | 主要按钮 | 页面主要操作、提交表单 |
| **default** | 默认按钮 | 次要操作、取消操作 |
| **dashed** | 虚线按钮 | 添加操作、次要入口 |
| **text** | 文本按钮 | 工具栏操作、链接式按钮 |
| **link** | 链接按钮 | 页面内导航、跳转链接 |

---

## Button 组件

### 基础按钮

Button 组件提供了多种类型和样式。

**核心属性：**

```typescript
interface ButtonProps {
  type?: 'primary' | 'default' | 'dashed' | 'text' | 'link'; // 按钮类型
  htmlType?: 'button' | 'submit' | 'reset'; // 原生 type 值
  icon?: ReactNode; // 设置按钮的图标组件
  disabled?: boolean; // 按钮是否禁用
  loading?: boolean | { delay: number }; // 设置按钮载入状态
  size?: 'large' | 'middle' | 'small'; // 设置按钮大小
  shape?: 'default' | 'circle' | 'round'; // 按钮形状
  block?: boolean; // 将按钮宽度调整为其父宽度的选项
  danger?: boolean; // 设置危险按钮
  ghost?: boolean; // 幽灵属性，使按钮背景透明
  target?: string; // 相当于 a 链接的 target 属性，href 存在时生效
  href?: string; // 点击跳转的地址，指定此属性 button 的行为和 a 链接一致
  onClick?: (event: React.MouseEvent<HTMLElement>) => void; // 点击事件
  children?: ReactNode; // 按钮内容
}
```

**示例 1：基础按钮（多种类型）**

```tsx
import React from 'react';
import { Button, Space, Divider } from 'antd';

const BasicButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Space wrap>
        <Button type="primary">Primary Button</Button>
        <Button>Default Button</Button>
        <Button type="dashed">Dashed Button</Button>
        <Button type="text">Text Button</Button>
        <Button type="link">Link Button</Button>
      </Space>

      <Divider />

      <Space wrap>
        <Button type="primary" danger>
          Danger Primary
        </Button>
        <Button danger>Danger Default</Button>
        <Button type="dashed" danger>
          Danger Dashed
        </Button>
        <Button type="text" danger>
          Danger Text
        </Button>
        <Button type="link" danger>
          Danger Link
        </Button>
      </Space>
    </Space>
  );
};

export default BasicButtons;
```

### 按钮尺寸

通过 `size` 属性控制按钮大小，提供 `large`、`middle`（默认）、`small` 三种尺寸。

**示例 2：不同尺寸的按钮**

```tsx
import React from 'react';
import { Button, Space } from 'antd';

const SizeButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space size="middle">
        <Button type="primary" size="large">
          Large Primary
        </Button>
        <Button type="primary">Middle Primary</Button>
        <Button type="primary" size="small">
          Small Primary
        </Button>
      </Space>

      <Space size="middle">
        <Button size="large">Large Default</Button>
        <Button>Middle Default</Button>
        <Button size="small">Small Default</Button>
      </Space>

      <Space size="middle">
        <Button type="dashed" size="large">
          Large Dashed
        </Button>
        <Button type="dashed">Middle Dashed</Button>
        <Button type="dashed" size="small">
          Small Dashed
        </Button>
      </Space>
    </Space>
  );
};

export default SizeButtons;
```

### 加载状态按钮

通过 `loading` 属性设置按钮为加载中状态，加载中时按钮不可点击。

**示例 3：加载状态按钮（异步操作）**

```tsx
import React, { useState } from 'react';
import { Button, Space, message } from 'antd';

const LoadingButtons: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [iconLoading, setIconLoading] = useState(false);

  const enterLoading = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      message.success('Loading complete!');
    }, 3000);
  };

  const enterIconLoading = () => {
    setIconLoading(true);
    setTimeout(() => {
      setIconLoading(false);
      message.success('Icon loading complete!');
    }, 3000);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space>
        <Button type="primary" loading>
          Loading
        </Button>
        <Button type="primary" size="small" loading>
          Loading
        </Button>
        <Button type="primary" icon={<PoweroffOutlined />} loading>
          Loading with icon
        </Button>
      </Space>

      <Space>
        <Button type="primary" loading={loading} onClick={enterLoading}>
          Click me!
        </Button>
        <Button
          type="primary"
          icon={<PoweroffOutlined />}
          loading={iconLoading}
          onClick={enterIconLoading}
        >
          Click me too!
        </Button>
        <Button type="primary" loading={{ delay: 500 }}>
          Delay 500ms
        </Button>
      </Space>
    </Space>
  );
};

export default LoadingButtons;
```

### 图标按钮

通过 `icon` 属性在按钮中添加图标，支持前缀图标、后缀图标和仅图标按钮。

**示例 4：图标按钮（多种图标位置）**

```tsx
import React from 'react';
import { Button, Space, Divider } from 'antd';
import {
  SearchOutlined,
  DownloadOutlined,
  LeftOutlined,
  RightOutlined,
  UpOutlined,
  DownOutlined,
} from '@ant-design/icons';

const IconButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Space wrap>
        <Button type="primary" icon={<SearchOutlined />}>
          Search
        </Button>
        <Button type="primary" icon={<DownloadOutlined />}>
          Download
        </Button>
        <Button icon={<SearchOutlined />}>Default</Button>
        <Button type="dashed" icon={<DownloadOutlined />}>
          Dashed
        </Button>
        <Button type="text" icon={<SearchOutlined />}>
          Text
        </Button>
        <Button type="link" icon={<DownloadOutlined />}>
          Link
        </Button>
      </Space>

      <Divider />

      <Space wrap>
        <Button type="primary" icon={<SearchOutlined />} size="large">
          Large
        </Button>
        <Button type="primary" icon={<DownloadOutlined />}>
          Middle
        </Button>
        <Button type="primary" icon={<SearchOutlined />} size="small">
          Small
        </Button>
      </Space>

      <Divider />

      <Space wrap>
        <Button type="primary" icon={<PoweroffOutlined />} />
        <Button type="default" icon={<SearchOutlined />} />
        <Button type="dashed" icon={<DownloadOutlined />} />
        <Button type="primary" shape="circle" icon={<SearchOutlined />} />
        <Button type="primary" shape="round" icon={<DownloadOutlined />}>
          Download
        </Button>
      </Space>

      <Divider />

      <Space>
        <Button type="primary" icon={<LeftOutlined />}>
          Previous
        </Button>
        <Button type="primary">
          Next <RightOutlined />
        </Button>
        <Button type="dashed" icon={<UpOutlined />} />
        <Button type="dashed" icon={<DownOutlined />} />
      </Space>
    </Space>
  );
};

export default IconButtons;
```

### 按钮形状

通过 `shape` 属性设置按钮形状，支持圆形（`circle`）和圆角（`round`）。

**示例 5：不同形状的按钮**

```tsx
import React from 'react';
import { Button, Space, Divider } from 'antd';
import {
  SearchOutlined,
  DownloadOutlined,
  PlusOutlined,
  MinusOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons';

const ShapeButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Space wrap>
        <Button type="primary" shape="circle" icon={<SearchOutlined />} />
        <Button type="primary" shape="circle">
          A
        </Button>
        <Button type="primary" shape="round" icon={<DownloadOutlined />}>
          Download
        </Button>
        <Button type="primary" shape="round">
          Round
        </Button>
        <Button type="dashed" shape="circle" icon={<PlusOutlined />} />
        <Button type="dashed" shape="round" icon={<MinusOutlined />}>
          Minus
        </Button>
      </Space>

      <Divider />

      <Space wrap>
        <Button type="primary" shape="circle" icon={<SearchOutlined />} size="large" />
        <Button type="primary" shape="circle" icon={<SearchOutlined />} />
        <Button type="primary" shape="circle" icon={<SearchOutlined />} size="small" />
      </Space>

      <Divider />

      <Space wrap>
        <Button type="primary" shape="round" icon={<CheckOutlined />}>
          Approve
        </Button>
        <Button danger shape="round" icon={<CloseOutlined />}>
          Reject
        </Button>
      </Space>
    </Space>
  );
};

export default ShapeButtons;
```

### 块级按钮

通过 `block` 属性使按钮宽度占满父容器，适合移动端或需要全宽按钮的场景。

**示例 6：块级按钮（占满容器宽度）**

```tsx
import React from 'react';
import { Button, Space, Card } from 'antd';

const BlockButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="Block Buttons" style={{ width: 400 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Button type="primary" block>
            Primary Block Button
          </Button>
          <Button block>Default Block Button</Button>
          <Button type="dashed" block>
            Dashed Block Button
          </Button>
          <Button type="text" block>
            Text Block Button
          </Button>
          <Button danger block>
            Danger Block Button
          </Button>
        </Space>
      </Card>
    </Space>
  );
};

export default BlockButtons;
```

### Ghost 模式

Ghost 模式使按钮背景透明，适合深色背景或需要轻量级按钮的场景。

**示例 7：Ghost 模式按钮（透明背景）**

```tsx
import React from 'react';
import { Button, Space, Card, Typography } from 'antd';

const { Title } = Typography;

const GhostButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card
        title="Light Background"
        style={{ background: '#f0f2f5', border: 'none' }}
      >
        <Space wrap>
          <Button type="primary" ghost>
            Primary Ghost
          </Button>
          <Button ghost>Default Ghost</Button>
          <Button type="dashed" ghost>
            Dashed Ghost
          </Button>
          <Button danger ghost>
            Danger Ghost
          </Button>
        </Space>
      </Card>

      <Card
        title="Dark Background"
        style={{ background: '#001529', color: '#fff', border: 'none' }}
      >
        <Space wrap>
          <Button type="primary" ghost>
            Primary Ghost
          </Button>
          <Button ghost>Default Ghost</Button>
          <Button type="dashed" ghost>
            Dashed Ghost
          </Button>
          <Button danger ghost>
            Danger Ghost
          </Button>
        </Space>
      </Card>

      <Card title="Colored Backgrounds">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div style={{ background: '#52c41a', padding: 16 }}>
            <Button type="primary" ghost style={{ color: '#fff', borderColor: '#fff' }}>
              Green Ghost
            </Button>
          </div>

          <div style={{ background: '#722ed1', padding: 16 }}>
            <Button type="primary" ghost style={{ color: '#fff', borderColor: '#fff' }}>
              Purple Ghost
            </Button>
          </div>

          <div style={{ background: '#faad14', padding: 16 }}>
            <Button type="primary" ghost style={{ color: '#fff', borderColor: '#fff' }}>
              Orange Ghost
            </Button>
          </div>
        </Space>
      </Card>
    </Space>
  );
};

export default GhostButtons;
```

### 禁用状态

通过 `disabled` 属性禁用按钮，禁用状态下按钮不可点击且样式变灰。

**示例 8：禁用状态按钮（多种类型）**

```tsx
import React from 'react';
import { Button, Space } from 'antd';

const DisabledButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space wrap>
        <Button type="primary">Primary</Button>
        <Button type="primary" disabled>
          Primary(Disabled)
        </Button>
      </Space>

      <Space wrap>
        <Button>Default</Button>
        <Button disabled>Default(Disabled)</Button>
      </Space>

      <Space wrap>
        <Button type="dashed">Dashed</Button>
        <Button type="dashed" disabled>
          Dashed(Disabled)
        </Button>
      </Space>

      <Space wrap>
        <Button type="text">Text</Button>
        <Button type="text" disabled>
          Text(Disabled)
        </Button>
      </Space>

      <Space wrap>
        <Button type="link">Link</Button>
        <Button type="link" disabled>
          Link(Disabled)
        </Button>
      </Space>

      <Space wrap>
        <Button type="primary" danger>
          Danger
        </Button>
        <Button type="primary" danger disabled>
          Danger(Disabled)
        </Button>
      </Space>

      <Space wrap>
        <Button type="primary" ghost>
          Ghost
        </Button>
        <Button type="primary" ghost disabled>
          Ghost(Disabled)
        </Button>
      </Space>
    </Space>
  );
};

export default DisabledButtons;
```

### 链接按钮

通过 `href` 和 `target` 属性使按钮行为类似链接，支持页面跳转。

**示例 9：链接按钮（跳转功能）**

```tsx
import React from 'react';
import { Button, Space, Divider } from 'antd';

const LinkButtons: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Space wrap>
        <Button type="primary" href="https://ant.design/" target="_blank">
          Primary Link
        </Button>
        <Button href="https://ant.design/">Default Link</Button>
        <Button type="dashed" href="https://ant.design/">
          Dashed Link
        </Button>
        <Button type="link" href="https://ant.design/">
          Text Link
        </Button>
      </Space>

      <Divider />

      <Space>
        <Button type="primary" href="https://ant.design/" target="_blank">
          Open in New Tab
        </Button>
        <Button type="primary" href="https://ant.design/" target="_self">
          Open in Same Tab
        </Button>
      </Space>

      <Divider />

      <Space>
        <Button type="primary" danger href="https://ant.design/" target="_blank">
          Danger Link
        </Button>
        <Button type="link" danger href="https://ant.design/">
          Danger Text Link
        </Button>
      </Space>
    </Space>
  );
};

export default LinkButtons;
```

---

## Button.Group 按钮组

### 基础按钮组

Button.Group 用于将多个按钮组合在一起，形成一组相关操作。

**核心属性：**

```typescript
interface ButtonGroupProps {
  size?: 'large' | 'middle' | 'small'; // 按钮组内按钮的大小
  style?: React.CSSProperties; // 自定义样式
  className?: string; // 自定义类名
  children?: ReactNode; // 子节点（多个 Button）
}
```

**示例 10：基础按钮组（多种组合）**

```tsx
import React from 'react';
import { Button, Space } from 'antd';
import { LeftOutlined, RightOutlined, UpOutlined, DownOutlined } from '@ant-design/icons';

const BasicButtonGroup: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Button.Group>
        <Button>Cancel</Button>
        <Button type="primary">OK</Button>
      </Button.Group>

      <Button.Group>
        <Button disabled>Left</Button>
        <Button disabled>Middle</Button>
        <Button disabled>Right</Button>
      </Button.Group>

      <Button.Group>
        <Button type="primary" icon={<LeftOutlined />}>
          Previous
        </Button>
        <Button type="primary">
          Next <RightOutlined />
        </Button>
      </Button.Group>

      <Button.Group>
        <Button type="primary" icon={<LeftOutlined />} />
        <Button type="primary" icon={<UpOutlined />} />
        <Button type="primary" icon={<DownOutlined />} />
        <Button type="primary" icon={<RightOutlined />} />
      </Button.Group>

      <Button.Group>
        <Button type="primary">Primary</Button>
        <Button>Default</Button>
        <Button type="dashed">Dashed</Button>
        <Button type="text">Text</Button>
      </Button.Group>

      <Button.Group>
        <Button type="primary">Primary</Button>
        <Button type="primary" danger>
          Danger Primary
        </Button>
        <Button danger>Danger Default</Button>
      </Button.Group>
    </Space>
  );
};

export default BasicButtonGroup;
```

### 带图标的按钮组

按钮组支持各种图标组合，常用于工具栏。

**示例 11：工具栏按钮组（图标按钮组）**

```tsx
import React from 'react';
import { Button, Space, Divider } from 'antd';
import {
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  AlignLeftOutlined,
  AlignCenterOutlined,
  AlignRightOutlined,
  UndoOutlined,
  RedoOutlined,
  SearchOutlined,
  DownloadOutlined,
  UploadOutlined,
} from '@ant-design/icons';

const ToolbarButtonGroup: React.FC = () => {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Button.Group>
        <Button icon={<BoldOutlined />} />
        <Button icon={<ItalicOutlined />} />
        <Button icon={<UnderlineOutlined />} />
      </Button.Group>

      <Divider />

      <Button.Group>
        <Button icon={<AlignLeftOutlined />} />
        <Button icon={<AlignCenterOutlined />} />
        <Button icon={<AlignRightOutlined />} />
      </Button.Group>

      <Divider />

      <Button.Group>
        <Button icon={<UndoOutlined />} />
        <Button icon={<RedoOutlined />} />
      </Button.Group>

      <Divider />

      <Button.Group>
        <Button icon={<SearchOutlined />}>Search</Button>
        <Button icon={<DownloadOutlined />}>Download</Button>
        <Button icon={<UploadOutlined />}>Upload</Button>
      </Button.Group>
    </Space>
  );
};

export default ToolbarButtonGroup;
```

---

## 完整使用示例

### 示例 12：表单提交按钮

```tsx
import React, { useState } from 'react';
import { Button, Form, Input, Space, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';

interface FormValues {
  username: string;
  email: string;
  password: string;
}

const FormSubmitButtons: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = (values: FormValues) => {
    setLoading(true);
    console.log('Received values of form: ', values);

    // 模拟 API 调用
    setTimeout(() => {
      setLoading(false);
      message.success('Registration successful!');
      form.resetFields();
    }, 2000);
  };

  const onReset = () => {
    form.resetFields();
  };

  return (
    <Form
      form={form}
      name="register"
      onFinish={onFinish}
      style={{ maxWidth: 400 }}
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: 'Please input your username!' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="Username" />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: 'Please input your email!' },
          { type: 'email', message: 'Invalid email format!' },
        ]}
      >
        <Input prefix={<MailOutlined />} placeholder="Email" />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: 'Please input your password!' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="Password" />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            Register
          </Button>
          <Button htmlType="button" onClick={onReset}>
            Reset
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default FormSubmitButtons;
```

### 示例 13：确认对话框按钮

```tsx
import React from 'react';
import { Button, Space, Modal, message } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';

const ConfirmButtons: React.FC = () => {
  const showConfirm = () => {
    Modal.confirm({
      title: 'Confirm',
      icon: <ExclamationCircleOutlined />,
      content: 'Do you want to delete these items?',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        message.success('Items deleted successfully!');
      },
      onCancel() {
        console.log('Cancel');
      },
    });
  };

  const showDeleteConfirm = () => {
    Modal.confirm({
      title: 'Are you sure delete this task?',
      icon: <ExclamationCircleOutlined />,
      content: 'Some descriptions',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        message.success('Task deleted!');
      },
      onCancel() {
        console.log('Cancel');
      },
    });
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <Button type="primary" onClick={showConfirm}>
          Show Confirm
        </Button>
        <Button danger onClick={showDeleteConfirm}>
          Delete
        </Button>
      </Space>
    </Space>
  );
};

export default ConfirmButtons;
```

### 示例 14：动态操作按钮

```tsx
import React, { useState } from 'react';
import { Button, Space, Dropdown, Menu, message } from 'antd';
import { DownOutlined, UserOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';

const DynamicActionButtons: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [disabled, setDisabled] = useState(false);

  const handleAction = (action: string) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      message.success(`${action} completed!`);
    }, 1500);
  };

  const menuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
    },
  ];

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    message.info(`Clicked on menu item: ${e.key}`);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <Button type="primary" onClick={() => handleAction('Save')} loading={loading}>
          Save
        </Button>
        <Button onClick={() => handleAction('Cancel')} disabled={disabled}>
          Cancel
        </Button>
        <Dropdown menu={{ items: menuItems, onClick: handleMenuClick }}>
          <Button>
            Actions <DownOutlined />
          </Button>
        </Dropdown>
      </Space>

      <Space>
        <Button onClick={() => setDisabled(!disabled)}>
          {disabled ? 'Enable' : 'Disable'} Cancel Button
        </Button>
      </Space>
    </Space>
  );
};

export default DynamicActionButtons;
```

### 示例 15：权限控制按钮

```tsx
import React from 'react';
import { Button, Space } from 'antd';

// 权限类型
type Permission = 'read' | 'write' | 'delete' | 'admin';

// 用户权限
interface UserPermissions {
  canRead: boolean;
  canWrite: boolean;
  canDelete: boolean;
  isAdmin: boolean;
}

interface PermissionButtonProps {
  userPermissions: UserPermissions;
  requiredPermission: Permission;
  onClick?: () => void;
  children: React.ReactNode;
  buttonProps?: React.ComponentProps<typeof Button>;
}

const PermissionButton: React.FC<PermissionButtonProps> = ({
  userPermissions,
  requiredPermission,
  onClick,
  children,
  buttonProps = {},
}) => {
  const checkPermission = (): boolean => {
    switch (requiredPermission) {
      case 'read':
        return userPermissions.canRead;
      case 'write':
        return userPermissions.canWrite;
      case 'delete':
        return userPermissions.canDelete;
      case 'admin':
        return userPermissions.isAdmin;
      default:
        return false;
    }
  };

  const hasPermission = checkPermission();

  const handleClick = () => {
    if (hasPermission) {
      onClick?.();
    }
  };

  return (
    <Button
      {...buttonProps}
      onClick={handleClick}
      disabled={!hasPermission}
      title={!hasPermission ? 'You do not have permission' : undefined}
    >
      {children}
    </Button>
  );
};

const PermissionControlButtons: React.FC = () => {
  // 模拟当前用户权限
  const currentUser: UserPermissions = {
    canRead: true,
    canWrite: true,
    canDelete: false,
    isAdmin: false,
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <h3>Permission Control Example</h3>
      <p>Current User: Read ✓, Write ✓, Delete ✗, Admin ✗</p>

      <Space>
        <PermissionButton
          userPermissions={currentUser}
          requiredPermission="read"
          type="default"
          onClick={() => console.log('View clicked')}
        >
          View
        </PermissionButton>

        <PermissionButton
          userPermissions={currentUser}
          requiredPermission="write"
          type="primary"
          onClick={() => console.log('Edit clicked')}
        >
          Edit
        </PermissionButton>

        <PermissionButton
          userPermissions={currentUser}
          requiredPermission="delete"
          type="primary"
          danger
          onClick={() => console.log('Delete clicked')}
        >
          Delete
        </PermissionButton>

        <PermissionButton
          userPermissions={currentUser}
          requiredPermission="admin"
          type="primary"
          onClick={() => console.log('Admin clicked')}
        >
          Admin Panel
        </PermissionButton>
      </Space>
    </Space>
  );
};

export default PermissionControlButtons;
```

### 示例 16：进度按钮（多步骤操作）

```tsx
import React, { useState } from 'react';
import { Button, Space, Steps, Card, message } from 'antd';
import { CheckOutlined, CloseOutlined, LoadingOutlined } from '@ant-design/icons';

const ProgressButtons: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const steps = [
    { title: 'First', description: 'Step 1: Upload files' },
    { title: 'Second', description: 'Step 2: Verify data' },
    { title: 'Third', description: 'Step 3: Complete' },
  ];

  const next = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setCurrentStep(currentStep + 1);
    }, 1000);
  };

  const prev = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleFinish = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      message.success('All steps completed!');
      setCurrentStep(0);
    }, 1000);
  };

  return (
    <Card title="Multi-step Process" style={{ width: 600 }}>
      <Steps current={currentStep} items={steps} style={{ marginBottom: 24 }} />

      <div style={{ marginBottom: 24 }}>
        {currentStep === 0 && <div>Step 1 Content: Upload your files here</div>}
        {currentStep === 1 && <div>Step 2 Content: Verify your data</div>}
        {currentStep === 2 && <div>Step 3 Content: Review and complete</div>}
      </div>

      <Space>
        {currentStep > 0 && (
          <Button onClick={prev} disabled={loading}>
            Previous
          </Button>
        )}
        {currentStep < steps.length - 1 && (
          <Button type="primary" onClick={next} loading={loading}>
            Next
          </Button>
        )}
        {currentStep === steps.length - 1 && (
          <Button type="primary" onClick={handleFinish} loading={loading}>
            Finish
          </Button>
        )}
        <Button onClick={() => setCurrentStep(0)} disabled={loading}>
          Reset
        </Button>
      </Space>
    </Card>
  );
};

export default ProgressButtons;
```

### 示例 17：自适应按钮（响应式）

```tsx
import React from 'react';
import { Button, Space, Col, Row } from 'antd';

const ResponsiveButtons: React.FC = () => {
  return (
    <div style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Button type="primary" block>
            Full Width on Mobile
          </Button>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Button type="default" block>
            Block Button
          </Button>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Button type="dashed" block>
            Dashed Block
          </Button>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Button type="text" block>
            Text Block
          </Button>
        </Col>
      </Row>

      <div style={{ marginTop: 24 }}>
        <Space wrap>
          <Button type="primary">Always Visible</Button>
          <Button type="default">Responsive Wrap</Button>
          <Button type="dashed">Adaptive Space</Button>
        </Space>
      </div>
    </div>
  );
};

export default ResponsiveButtons;
```

### 示例 18：搜索按钮（带输入框）

```tsx
import React, { useState } from 'react';
import { Button, Input, Space, message } from 'antd';
import { SearchOutlined, ClearOutlined } from '@ant-design/icons';

const { Search } = Input;

const SearchButtons: React.FC = () => {
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSearch = (value: string) => {
    if (!value) {
      message.warning('Please enter search keyword');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      message.success(`Searching for: ${value}`);
    }, 1500);
  };

  const handleClear = () => {
    setSearchValue('');
    message.info('Search cleared');
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space.Compact style={{ width: '100%', maxWidth: 400 }}>
        <Search
          placeholder="Search..."
          allowClear
          enterButton={
            <Button type="primary" icon={<SearchOutlined />} loading={loading}>
              Search
            </Button>
          }
          size="large"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          onSearch={handleSearch}
        />
      </Space.Compact>

      <Space>
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={() => handleSearch(searchValue)}
          loading={loading}
        >
          Search
        </Button>
        <Button icon={<ClearOutlined />} onClick={handleClear} disabled={!searchValue}>
          Clear
        </Button>
      </Space>
    </Space>
  );
};

export default SearchButtons;
```

---

## 最佳实践

### ✅ 推荐做法

1. **明确按钮优先级**
   ```tsx
   // ✅ 正确：主要操作用 primary，次要操作用 default
   <Space>
     <Button type="primary">Submit</Button>
     <Button>Cancel</Button>
   </Space>

   // ❌ 错误：所有按钮都是 primary，无法区分优先级
   <Space>
     <Button type="primary">Submit</Button>
     <Button type="primary">Cancel</Button>
   </Space>
   ```

2. **提供加载反馈**
   ```tsx
   // ✅ 正确：异步操作时显示 loading 状态
   const [loading, setLoading] = useState(false);

   const handleSubmit = async () => {
     setLoading(true);
     await submitForm();
     setLoading(false);
   };

   <Button type="primary" onClick={handleSubmit} loading={loading}>
     Submit
   </Button>
   ```

3. **危险操作使用 danger 属性**
   ```tsx
   // ✅ 正确：删除等危险操作使用 danger 样式
   <Button type="primary" danger onClick={handleDelete}>
     Delete
   </Button>
   ```

4. **合理使用图标**
   ```tsx
   // ✅ 正确：图标增强按钮语义
   <Button type="primary" icon={<SearchOutlined />}>
     Search
   </Button>
   <Button icon={<DownloadOutlined />} />
   ```

5. **移动端使用 block 按钮**
   ```tsx
   // ✅ 正确：移动端使用 block 按钮提升点击体验
   <Button type="primary" block>
     Submit
   </Button>
   ```

### ❌ 避免的做法

1. **避免过多按钮类型**
   ```tsx
   // ❌ 错误：一个页面混合过多按钮类型
   <Button type="primary">Primary</Button>
   <Button type="dashed">Dashed</Button>
   <Button type="text">Text</Button>
   <Button type="link">Link</Button>

   // ✅ 正确：保持按钮类型一致性
   <Button type="primary">Main Action</Button>
   <Button>Secondary Action</Button>
   ```

2. **避免滥用 loading 状态**
   ```tsx
   // ❌ 错误：同步操作也使用 loading
   const handleClick = () => {
     setLoading(true);
     console.log('clicked');
     setLoading(false);
   };

   // ✅ 正确：只在异步操作时使用 loading
   const handleClick = async () => {
     setLoading(true);
     await fetchData();
     setLoading(false);
   };
   ```

3. **避免按钮文案过长**
   ```tsx
   // ❌ 错误：按钮文案过长
   <Button type="primary">
     Click here to submit your application form
   </Button>

   // ✅ 正确：简洁明了的文案
   <Button type="primary">Submit Application</Button>
   ```

4. **避免禁用状态用于提示**
   ```tsx
   // ❌ 错误：禁用按钮没有说明原因
   <Button type="primary" disabled>
     Submit
   </Button>

   // ✅ 正确：提供禁用原因的提示
   <Button type="primary" disabled title="Please complete all fields">
     Submit
   </Button>
   ```

5. **避免嵌套按钮**
   ```tsx
   // ❌ 错误：嵌套按钮导致交互混乱
   <Button>
     Click me
     <Button>Inner Button</Button>
   </Button>

   // ✅ 正确：使用按钮组
   <Button.Group>
     <Button>Button 1</Button>
     <Button>Button 2</Button>
   </Button.Group>
   ```

---

## 常见问题

### Q1: 如何自定义按钮样式？

**A**: 使用 `style` 或 `className` 属性：

```tsx
<Button
  type="primary"
  style={{
    backgroundColor: '#722ed1',
    borderColor: '#722ed1',
    borderRadius: 8,
    padding: '8px 24px',
  }}
>
  Custom Style
</Button>
```

### Q2: 如何防止按钮重复点击？

**A**: 使用 loading 状态或防抖函数：

```tsx
import { debounce } from 'lodash';

// 方法 1：使用 loading
const [loading, setLoading] = useState(false);

const handleClick = async () => {
  if (loading) return;
  setLoading(true);
  await submitData();
  setLoading(false);
};

// 方法 2：使用防抖
const debouncedClick = debounce(() => {
  console.log('Clicked');
}, 1000);

<Button onClick={debouncedClick}>Debounced Click</Button>
```

### Q3: 如何实现按钮权限控制？

**A**: 创建权限按钮组件（参见示例 15）：

```tsx
const PermissionButton: React.FC<PermissionButtonProps> = ({
  userPermissions,
  requiredPermission,
  ...props
}) => {
  const hasPermission = checkPermission(userPermissions, requiredPermission);

  return <Button {...props} disabled={!hasPermission} />;
};
```

### Q4: 如何实现按钮的水波纹效果？

**A**: Ant Design 5.x 默认启用水波纹效果，可通过 ConfigProvider 关闭：

```tsx
<ConfigProvider
  theme={{
    components: {
      Button: {
        wave: false, // 关闭水波纹
      },
    },
  }}
>
  <Button>No Wave Effect</Button>
</ConfigProvider>
```

### Q5: 如何实现按钮的快捷键支持？

**A**: 在 document 上监听键盘事件：

```tsx
import { useEffect } from 'react';

const ShortcutButton: React.FC = () => {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSubmit();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  const handleSubmit = () => {
    console.log('Form submitted!');
  };

  return (
    <Button type="primary" onClick={handleSubmit}>
      Save (Ctrl+S)
    </Button>
  );
};
```

### Q6: 如何实现按钮的 Tooltip 提示？

**A**: 使用 Tooltip 组件包裹按钮：

```tsx
import { Tooltip } from 'antd';

<Tooltip title="This is a tooltip">
  <Button>Hover Me</Button>
</Tooltip>
```

### Q7: 如何实现按钮的焦点管理？

**A**: 使用 autoRef 自动聚焦：

```tsx
import { useRef, useEffect } from 'react';

const FocusButton: React.FC = () => {
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    buttonRef.current?.focus();
  }, []);

  return (
    <Button ref={buttonRef} type="primary">
      Auto Focus
    </Button>
  );
};
```

### Q8: 如何实现按钮的确认对话框？

**A**: 使用 Modal.confirm（参见示例 13）：

```tsx
const showConfirm = () => {
  Modal.confirm({
    title: 'Confirm',
    content: 'Do you want to proceed?',
    onOk() {
      console.log('Confirmed');
    },
    onCancel() {
      console.log('Cancelled');
    },
  });
};

<Button danger onClick={showConfirm}>
  Delete
</Button>
```

---

## 参考资源

### 官方文档
- [Ant Design - Button](https://ant.design/components/button-cn/)
- [Ant Design - Button.Group](https://ant.design/components/button-cn/#components-button-demo-button-group)

### 相关文档
- [antd-core-skills](../antd-core-skills/SKILL.md) - 核心组件基础
- [antd-form-skills](../antd-form-skills/SKILL.md) - 表单中的按钮
- [antd-config-skills](../antd-config-skills/SKILL.md) - 全局按钮配置

### 扩展阅读
- [按钮设计指南](https://ant.design/docs/spec/buttons-cn)
- [交互最佳实践](../antd-best-practices-skills/SKILL.md)
- [无障碍访问指南](../antd-accessibility-skills/SKILL.md)

---

**维护者**: Claude Code & LazyGophers Community
**最后更新**: 2026-02-10
