---
name: antd-feedback-skills
description: Ant Design 反馈组件完整指南 - Alert、Message、Modal、Notification、Popconfirm、Popover
---

# antd-feedback-skills - Ant Design 反馈组件完整指南

## 概述

Ant Design 反馈组件是一套用于向用户提供操作反馈、确认和提示的完整解决方案,包括警告提示、全局消息、对话框、通知框、气泡确认框等。这些组件遵循 Ant Design 设计规范,提供一致的用户体验,支持全局配置、自定义样式和丰富的交互场景。

## 核心特性

- **全局方法支持** - Message、Modal、Notification 提供全局静态方法,无需手动挂载组件
- **App.useApp() Hook** - 5.x 新特性,通过 Context API 提供类型安全的全局方法访问
- **ConfigProvider 集成** - 支持全局主题配置、国际化、样式定制
- **Promise 支持** - Modal、Popconfirm 支持 Promise 风格的异步确认
- **可访问性** - 内置 ARIA 属性和键盘导航支持,符合 WCAG 标准
- **灵活定位** - 支持自定义弹出层容器,解决滚动和定位问题
- **主题定制** - 基于 Design Token 的主题系统,支持暗色模式
- **性能优化** - 消息队列管理、防抖处理、自动销毁机制

---

## Alert 警告提示

### 基础用法

Alert 组件用于页面中展示重要的提示信息,常用于表单验证错误、操作结果反馈等场景。

```typescript
import { Alert } from 'antd';

const BasicAlert = () => (
  <>
    <Alert message="Success Text" type="success" />
    <Alert message="Info Text" type="info" />
    <Alert message="Warning Text" type="warning" />
    <Alert message="Error Text" type="error" />
  </>
);
```

### 带描述的 Alert

```typescript
import { Alert } from 'antd';

const DescriptiveAlert = () => (
  <>
    <Alert
      message="Success Tips"
      description="Detailed description and advice about successful copywriting."
      type="success"
      showIcon
    />
    <Alert
      message="Informational Notes"
      description="Additional description and information about copywriting."
      type="info"
      showIcon
    />
    <Alert
      message="Warning"
      description="This is a warning notice about copywriting."
      type="warning"
      showIcon
    />
    <Alert
      message="Error"
      description="This is an error message about copywriting."
      type="error"
      showIcon
    />
  </>
);
```

### 可关闭的 Alert

```typescript
import { Alert, Space } from 'antd';
import { useState } from 'react';

const ClosableAlert = () => {
  const [closed, setClosed] = useState({});

  const close = (key: string) => {
    setClosed(prev => ({ ...prev, [key]: true }));
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Alert
        message="Warning Text Warning Text Warning Text Warning Text Warning Text Warning Text Warning Text"
        type="warning"
        closable
        onClose={() => console.log('Alert closed')}
      />

      <Alert
        message="Error Text"
        description="Error Description Error Description Error Description Error Description"
        type="error"
        closable
        onClose={() => console.log('Alert closed')}
      />
    </Space>
  );
};
```

### 带图标的 Alert

```typescript
import { Alert } from 'antd';
import { CheckCircleOutlined, InfoCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons';

const CustomIconAlert = () => (
  <>
    <Alert
      message="Success"
      type="success"
      showIcon
      icon={<CheckCircleOutlined />}
    />
    <Alert
      message="Informational Notes"
      description="Additional description and information about copywriting."
      type="info"
      showIcon
      icon={<InfoCircleOutlined />}
    />
    <Alert
      message="Warning"
      description="This is a warning notice about copywriting."
      type="warning"
      showIcon
      icon={<WarningOutlined />}
    />
    <Alert
      message="Error"
      description="This is an error message about copywriting."
      type="error"
      showIcon
      icon={<CloseCircleOutlined />}
    />
  </>
);
```

### 自定义关闭文字

```typescript
import { Alert } from 'antd';

const CustomCloseTextAlert = () => (
  <Alert
    message="Info Text"
    description="Info Description Info Description Info Description Info Description"
    type="info"
    closable={{
      closeText: 'Close Now',
    }}
    onClose={() => console.log('Alert closed')}
  />
);
```

### Alert 作为 Banner 使用

```typescript
import { Alert, Space } from 'antd';

const BannerAlert = () => (
  <Space direction="vertical" style={{ width: '100%' }} size="large">
    <Alert
      message="Warning text"
      banner
      closable
    />
    <Alert
      message="Very long warning text warning text warning text warning text warning text warning text"
      banner
      closable
    />
  </Space>
);
```

### Alert 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `afterClose` | `() => void` | - | 关闭后的回调 |
| `banner` | `boolean` | - | 是否用作顶部公告 |
| `closeIcon` | `ReactNode` | - | 自定义关闭图标 |
| `closeText` | `ReactNode` | - | 自定义关闭文字 |
| `closable` | `boolean \| CustomCloseIcon` | - | 是否可关闭 |
| `description` | `ReactNode` | - | 警告提示的辅助性文字介绍 |
| `icon` | `ReactNode` | - | 自定义图标 |
| `message` | `ReactNode` | - | 警告提示内容 |
| `showIcon` | `boolean` | - | 是否显示图标 |
| `type` | `'success' \| 'info' \| 'warning' \| 'error'` | - | 指定警告提示的样式 |
| `onClose` | `() => void` | - | 关闭时触发的回调 |

---

## Message 全局提示

### 全局方法使用

Ant Design 5.x 推荐使用 `App.useApp()` Hook 访问全局方法,确保在 App 组件内部使用。

```typescript
import { Button, App } from 'antd';

const MessageExample = () => {
  const { message } = App.useApp();

  const success = () => {
    message.success('This is a success message');
  };

  const error = () => {
    message.error('This is an error message');
  };

  const info = () => {
    message.info('This is an info message');
  };

  const warning = () => {
    message.warning('This is a warning message');
  };

  const loading = () => {
    const hide = message.loading('Action in progress..', 0);
    // 异步操作完成后隐藏
    setTimeout(hide, 2500);
  };

  return (
    <>
      <Button onClick={success}>Success</Button>
      <Button onClick={error}>Error</Button>
      <Button onClick={info}>Info</Button>
      <Button onClick={warning}>Warning</Button>
      <Button onClick={loading}>Loading</Button>
    </>
  );
};
```

### 持续时间自定义

```typescript
import { Button, App } from 'antd';

const DurationMessage = () => {
  const { message } = App.useApp();

  const showLongMessage = () => {
    message.success('This message will be visible for 10 seconds', 10);
  };

  return <Button onClick={showLongMessage}>Show Long Message</Button>;
};
```

### 加载中状态

```typescript
import { Button, App } from 'antd';

const LoadingMessage = () => {
  const { message } = App.useApp();

  const simulateAsyncOperation = async () => {
    const hide = message.loading('Loading...', 0);

    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      hide();
      message.success('Loading completed!');
    } catch (error) {
      hide();
      message.error('Loading failed!');
    }
  };

  return <Button onClick={simulateAsyncOperation}>Start Loading</Button>;
};
```

### Promise 风格

```typescript
import { Button, App } from 'antd';

const PromiseMessage = () => {
  const { message } = App.useApp();

  const showPromiseMessage = () => {
    message.loading('Loading...', 0)
      .then(() => message.success('Loaded successfully!'))
      .catch(() => message.error('Loading failed!'));
  };

  return <Button onClick={showPromiseMessage}>Promise Message</Button>;
};
```

### Message API

| 方法 | 参数 | 说明 |
|------|------|------|
| `success` | `(content, duration, onClose?)` | 成功提示 |
| `error` | `(content, duration, onClose?)` | 错误提示 |
| `info` | `(content, duration, onClose?)` | 信息提示 |
| `warning` | `(content, duration, onClose?)` | 警告提示 |
| `loading` | `(content, duration, onClose?)` | 加载提示,返回关闭函数 |
| `open` | `(config)` | 显示自定义消息 |

**参数说明**:
- `content`: 消息内容 (ReactNode)
- `duration`: 持续时间(秒),默认 3 秒,为 0 时不自动关闭
- `onClose`: 关闭时的回调函数

### Message 全局配置

```typescript
import { App, ConfigProvider } from 'antd';

const MessageConfig = () => {
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
};
```

### 使用 hooks (React 19+)

```typescript
import { useMessage } from 'antd'; // 未来版本可能支持

// 当前版本推荐使用 App.useApp()
const MessageComponent = () => {
  const [message, contextHolder] = message.useMessage();

  const showMessage = () => {
    message.success('Hello!');
  };

  return (
    <>
      <Button onClick={showMessage}>Show Message</Button>
      {contextHolder}
    </>
  );
};
```

---

## Modal 对话框

### 基础用法

```typescript
import { Button, Modal } from 'antd';
import { useState } from 'react';

const BasicModal = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = () => {
    setIsModalOpen(false);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };

  return (
    <>
      <Button type="primary" onClick={showModal}>
        Open Modal
      </Button>
      <Modal
        title="Basic Modal"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <p>Some contents...</p>
        <p>Some contents...</p>
        <p>Some contents...</p>
      </Modal>
    </>
  );
};
```

### 使用 App.useApp() Hook

```typescript
import { Button, App } from 'antd';

const ModalWithHook = () => {
  const { modal } = App.useApp();

  const showConfirm = () => {
    modal.confirm({
      title: 'Confirm',
      content: 'Do you want to delete these items?',
      onOk() {
        console.log('OK');
      },
      onCancel() {
        console.log('Cancel');
      },
    });
  };

  const showInfo = () => {
    modal.info({
      title: 'This is a notification message',
      content: (
        <div>
          <p>Some messages...</p>
          <p>Some messages...</p>
        </div>
      ),
      onOk() {},
    });
  };

  return (
    <>
      <Button onClick={showConfirm}>Confirm</Button>
      <Button onClick={showInfo}>Info</Button>
    </>
  );
};
```

### 异步关闭

```typescript
import { Button, App } from 'antd';

const AsyncModal = () => {
  const { modal } = App.useApp();

  const showAsyncConfirm = () => {
    modal.confirm({
      title: 'Do you want to delete these items?',
      content: 'When clicked the OK button, this dialog will be closed after 1 second',
      onOk() {
        return new Promise((resolve, reject) => {
          setTimeout(Math.random() > 0.5 ? resolve : reject, 1000);
        }).catch(() => console.log('Oops errors!'));
      },
      onCancel() {},
    });
  };

  return <Button onClick={showAsyncConfirm}>Async Confirm</Button>;
};
```

### 页面内操作

```typescript
import { Button, Modal, Form, Input } from 'antd';
import { useState } from 'react';

const ModalWithForm = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      console.log('Form values:', values);
      setIsModalOpen(false);
      form.resetFields();
    } catch (error) {
      console.log('Validation failed:', error);
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    form.resetFields();
  };

  return (
    <>
      <Button type="primary" onClick={showModal}>
        Add User
      </Button>
      <Modal
        title="Add User"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form
          form={form}
          layout="vertical"
          name="userForm"
        >
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: 'Please input username!' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Email"
            name="email"
            rules={[
              { required: true, message: 'Please input email!' },
              { type: 'email', message: 'Invalid email!' }
            ]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
```

### 自定义页脚

```typescript
import { Button, Modal } from 'antd';
import { useState } from 'react';

const CustomFooterModal = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Button type="primary" onClick={() => setIsModalOpen(true)}>
        Open Modal
      </Button>
      <Modal
        title="Custom Footer"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={[
          <Button key="back" onClick={() => setIsModalOpen(false)}>
            Return
          </Button>,
          <Button key="submit" type="primary" onClick={() => setIsModalOpen(false)}>
            Submit
          </Button>,
          <Button
            key="link"
            type="link"
            onClick={() => setIsModalOpen(false)}
          >
            Forgot password
          </Button>,
        ]}
      >
        <p>Some contents...</p>
        <p>Some contents...</p>
        <p>Some contents...</p>
      </Modal>
    </>
  );
};
```

### Modal.confirm 方法

```typescript
import { Button, App } from 'antd';

const ConfirmModal = () => {
  const { modal } = App.useApp();

  const showConfirm = () => {
    modal.confirm({
      title: 'Do you Want to delete these items?',
      content: 'Some descriptions',
      onOk() {
        console.log('OK');
      },
      onCancel() {
        console.log('Cancel');
      },
    });
  };

  const showDeleteConfirm = () => {
    modal.confirm({
      title: 'Are you sure delete this task?',
      icon: <ExclamationCircleOutlined />,
      content: 'Some descriptions',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        console.log('OK');
      },
      onCancel() {
        console.log('Cancel');
      },
    });
  };

  return (
    <>
      <Button onClick={showConfirm}>Confirm</Button>
      <Button onClick={showDeleteConfirm} danger>
        Delete Confirm
      </Button>
    </>
  );
};
```

### 完整的 Modal API

| 方法 | 说明 |
|------|------|
| `modal.config()` | 全局配置 |
| `modal.confirm()` | 确认框 |
| `modal.info()` | 信息提示框 |
| `modal.success()` | 成功提示框 |
| `modal.error()` | 错误提示框 |
| `modal.warning()` | 警告提示框 |

---

## Notification 通知提示框

### 基础用法

```typescript
import { Button, App } from 'antd';

const NotificationExample = () => {
  const { notification } = App.useApp();

  const openNotification = () => {
    notification.open({
      message: 'Notification Title',
      description:
        'This is the content of the notification. This is the content of the notification. This is the content of the notification.',
      onClick: () => {
        console.log('Notification Clicked!');
      },
    });
  };

  return <Button type="primary" onClick={openNotification}>
    Open the notification
  </Button>;
};
```

### 不同类型的通知

```typescript
import { Button, App } from 'antd';

const NotificationTypes = () => {
  const { notification } = App.useApp();

  return (
    <>
      <Button
        onClick={() => {
          notification.success({
            message: 'Success',
            description: 'This is a success notification',
          });
        }}
      >
        Success
      </Button>
      <Button
        onClick={() => {
          notification.info({
            message: 'Info',
            description: 'This is an info notification',
          })}
      >
        Info
      </Button>
      <Button
        onClick={() => {
          notification.warning({
            message: 'Warning',
            description: 'This is a warning notification',
          })}
      >
        Warning
      </Button>
      <Button
        onClick={() => {
          notification.error({
            message: 'Error',
            description: 'This is an error notification',
          })}
      >
        Error
      </Button>
    </>
  );
};
```

### 带图标的通知

```typescript
import { Button, App } from 'antd';
import { SmileOutlined, ClockCircleOutlined } from '@ant-design/icons';

const NotificationWithIcon = () => {
  const { notification } = App.useApp();

  const openNotification = () => {
    notification.open({
      message: 'Notification Title',
      description:
        'This is the content of the notification. This is the content of the notification. This is the content of the notification.',
      icon: <SmileOutlined style={{ color: '#108ee9' }} />,
    });
  };

  return <Button onClick={openNotification}>With Icon</Button>;
};
```

### 自定义持续时间

```typescript
import { Button, App } from 'antd';

const DurationNotification = () => {
  const { notification } = App.useApp();

  const openNotification = () => {
    notification.open({
      message: 'New Notification',
      description: 'This notification will be closed after 10 seconds',
      duration: 10,
    });
  };

  return <Button onClick={openNotification}>Open Notification</Button>;
};
```

### 通知位置

```typescript
import { Button, App, Space } from 'antd';

const NotificationPositions = () => {
  const { notification } = App.useApp();

  const openNotification = (placement: NotificationPlacement) => {
    notification.open({
      message: `Notification ${placement}`,
      description:
        'This is the content of the notification.',
      placement,
    });
  };

  return (
    <Space>
      {['topLeft', 'topRight', 'bottomLeft', 'bottomRight'].map(placement => (
        <Button
          key={placement}
          onClick={() => openNotification(placement as NotificationPlacement)}
        >
          {placement}
        </Button>
      ))}
    </Space>
  );
};

type NotificationPlacement = 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
```

### 更新和关闭通知

```typescript
import { Button, App } from 'antd';
import { useState } from 'react';

const UpdateNotification = () => {
  const { notification } = App.useApp();
  const [api, contextHolder] = notification.useNotification();

  const openNotification = () => {
    const key = `open${Date.now()}`;
    const btn = (
      <Button
        type="primary"
        size="small"
        onClick={() => notification.open({
          message: 'Notification Title',
          description: 'Updated content',
          key,
        })}
      >
        Update
      </Button>
    );
    notification.open({
      message: 'New Notification',
      description: 'This notification can be updated',
      btn,
      key,
    });
  };

  return (
    <>
      <Button type="primary" onClick={openNotification}>
        Open Notification with Update Button
      </Button>
      {contextHolder}
    </>
  );
};
```

---

## Popconfirm 气泡确认框

### 基础用法

```typescript
import { Popconfirm, Button } from 'antd';

const BasicPopconfirm = () => (
  <Popconfirm
    title="Delete the task"
    description="Are you sure to delete this task?"
    onConfirm={() => console.log('Confirmed')}
    onCancel={() => console.log('Cancelled')}
    okText="Yes"
    cancelText="No"
  >
    <Button danger>Delete</Button>
  </Popconfirm>
);
```

### Promise 异步关闭

```typescript
import { Popconfirm, Button } from 'antd';

const AsyncPopconfirm = () => {
  const confirm = () => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(true), 2000);
    });
  };

  return (
    <Popconfirm
      title="Delete the task"
      description="Are you sure to delete this task?"
      onConfirm={confirm}
      okText="Yes"
      cancelText="No"
    >
      <Button danger>Delete (async)</Button>
    </Popconfirm>
  );
};
```

### 自定义图标

```typescript
import { Popconfirm, Button } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

const CustomIconPopconfirm = () => (
  <Popconfirm
    title="Delete the task"
    description="Are you sure to delete this task?"
    icon={<QuestionCircleOutlined style={{ color: 'red' }} />}
    onConfirm={() => console.log('Confirmed')}
  >
    <Button danger>Delete</Button>
  </Popconfirm>
);
```

### 条件渲染

```typescript
import { Popconfirm, Button, Switch } from 'antd';
import { useState } from 'react';

const ConditionalPopconfirm = () => {
  const [visible, setVisible] = useState(false);

  return (
    <Popconfirm
      title="Are you sure?"
      open={visible}
      onOpenChange={(visible) => setVisible(visible)}
      onConfirm={() => {
        setVisible(false);
        console.log('Confirmed');
      }}
      onCancel={() => setVisible(false)}
    >
      <Switch /> Click to show confirm
    </Popconfirm>
  );
};
```

---

## Popover 气泡卡片

### 基础用法

```typescript
import { Popover, Button } from 'antd';

const BasicPopover = () => (
  <Popover content="Content" title="Title">
    <Button>Hover me</Button>
  </Popover>
);
```

### 三种触发方式

```typescript
import { Popover, Button } from 'antd';

const TriggerPopover = () => (
  <>
    <Popover content="Click to see content" title="Click trigger" trigger="click">
      <Button>Click</Button>
    </Popover>
    <Popover content="Hover to see content" title="Hover trigger" trigger="hover">
      <Button>Hover</Button>
    </Popover>
    <Popover content="Focus to see content" title="Focus trigger" trigger="focus">
      <Button>Focus (Tab key)</Button>
    </Popover>
  </>
);
```

### 位置

```typescript
import { Popover, Button } from 'antd';

const PopoverPositions = () => (
  <div style={{ marginLeft: 60, marginTop: 60 }}>
    {['top', 'left', 'right', 'bottom', 'topLeft', 'topRight', 'bottomLeft', 'bottomRight'].map(
      (placement) => (
        <Popover
          key={placement}
          placement={placement}
          content={placement}
          title="Placement"
        >
          <Button>{placement}</Button>
        </Popover>
      )
    )}
  </div>
);
```

### 控制显示和隐藏

```typescript
import { Popover, Button } from 'antd';
import { useState } from 'react';

const ControlledPopover = () => {
  const [open, setOpen] = useState(false);

  const hide = () => {
    setOpen(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
  };

  return (
    <Popover
      content={<a onClick={hide}>Close</a>}
      title="Title"
      trigger="click"
      open={open}
      onOpenChange={handleOpenChange}
    >
      <Button type="primary">Click me</Button>
    </Popover>
  );
};
```

---

## 最佳实践

### 1. 统一错误处理系统

**✅ 推荐**: 封装统一的错误处理函数

```typescript
// utils/feedback.ts
import { App } from 'antd';

export const useFeedback = () => {
  const { message, modal, notification } = App.useApp();

  const handleError = (error: Error) => {
    console.error('Error:', error);
    message.error(error.message || 'An error occurred');
  };

  const handleAsyncError = async (asyncFn: () => Promise<void>) => {
    try {
      await asyncFn();
    } catch (error) {
      handleError(error as Error);
    }
  };

  const confirmDelete = async (onDelete: () => Promise<void>) => {
    return new Promise<void>((resolve, reject) => {
      modal.confirm({
        title: 'Confirm Delete',
        content: 'Are you sure you want to delete this item?',
        okText: 'Yes',
        okType: 'danger',
        cancelText: 'No',
        onOk: async () => {
          try {
            await onDelete();
            message.success('Deleted successfully');
            resolve();
          } catch (error) {
            handleError(error as Error);
            reject(error);
          }
        },
        onCancel: () => reject(new Error('Cancelled')),
      });
    });
  };

  return {
    message,
    modal,
    notification,
    handleError,
    handleAsyncError,
    confirmDelete,
  };
};

// 使用示例
const MyComponent = () => {
  const { handleError, confirmDelete } = useFeedback();

  const deleteItem = async () => {
    await confirmDelete(async () => {
      await api.deleteItem(id);
    });
  };

  return <Button onClick={deleteItem}>Delete</Button>;
};
```

### 2. 异步操作反馈

**✅ 推荐**: 结合 loading 状态和成功/失败提示

```typescript
import { Button, App } from 'antd';
import { useState } from 'react';

const AsyncFeedback = () => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await api.submitForm(data);
      message.success('Form submitted successfully!');
    } catch (error) {
      message.error('Failed to submit form. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button type="primary" onClick={handleSubmit} loading={loading}>
      Submit
    </Button>
  );
};
```

### 3. 表单确认对话框

**✅ 推荐**: 在关键操作前使用 Modal.confirm

```typescript
import { Button, App, Form, Input } from 'antd';
import { useForm } from 'antd/es/form/Form';

const FormWithConfirm = () => {
  const { modal } = App.useApp();
  const [form] = useForm();

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      modal.confirm({
        title: 'Confirm Submission',
        content: (
          <div>
            <p>Please review your information:</p>
            <p><strong>Username:</strong> {values.username}</p>
            <p><strong>Email:</strong> {values.email}</p>
          </div>
        ),
        onOk: async () => {
          try {
            await api.submitForm(values);
            modal.success({
              title: 'Success',
              content: 'Form submitted successfully!',
            });
            form.resetFields();
          } catch (error) {
            modal.error({
              title: 'Error',
              content: 'Failed to submit form. Please try again.',
            });
          }
        },
      });
    });
  };

  return (
    <Form form={form} layout="vertical">
      <Form.Item name="username" label="Username" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
        <Input />
      </Form.Item>
      <Button type="primary" onClick={handleSubmit}>
        Submit
      </Button>
    </Form>
  );
};
```

### 4. 通知系统

**✅ 推荐**: 使用 Notification 展示系统级消息

```typescript
import { App, notification } from 'antd';
import { useEffect } from 'react';

const NotificationSystem = () => {
  const { notification } = App.useApp();

  useEffect(() => {
    // 显示新消息通知
    const showNewMessageNotification = () => {
      notification.open({
        message: 'New Message',
        description: 'You have received a new message from John Doe',
        icon: <MessageOutlined style={{ color: '#108ee9' }} />,
        placement: 'topRight',
        duration: 5,
      });
    };

    // 模拟接收消息
    const timer = setTimeout(showNewMessageNotification, 3000);
    return () => clearTimeout(timer);
  }, [notification]);

  return <div>Your App Content</div>;
};
```

### 5. 危险操作确认

**✅ 推荐**: 使用 Popconfirm 确认单条删除,Modal.confirm 确认批量删除

```typescript
import { Popconfirm, Modal, Button, Table } from 'antd';
import { useState } from 'react';

const DangerousActions = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const { modal } = App.useApp();

  const deleteSingle = (id: number) => {
    console.log('Delete single item:', id);
  };

  const batchDelete = () => {
    modal.confirm({
      title: 'Batch Delete',
      content: `Are you sure you want to delete ${selectedRowKeys.length} items?`,
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        console.log('Batch delete:', selectedRowKeys);
        setSelectedRowKeys([]);
      },
    });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string, record: any) => (
        <Popconfirm
          title="Delete this item?"
          onConfirm={() => deleteSingle(record.id)}
          okText="Yes"
          cancelText="No"
        >
          <Button type="link" danger>
            {text}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <Table
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        columns={columns}
        dataSource={data}
      />
      {selectedRowKeys.length > 0 && (
        <Button danger onClick={batchDelete}>
          Batch Delete ({selectedRowKeys.length})
        </Button>
      )}
    </>
  );
};
```

### 6. 自定义 Modal

**✅ 推荐**: 封装可复用的 Modal 组件

```typescript
import { Modal, Form, Input, Button } from 'antd';
import { useEffect } from 'react';

interface CustomModalProps {
  open: boolean;
  onCancel: () => void;
  onOk: (values: any) => Promise<void>;
  title: string;
  initialValues?: any;
}

const CustomModal = ({
  open,
  onCancel,
  onOk,
  title,
  initialValues,
}: CustomModalProps) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      form.resetFields();
      if (initialValues) {
        form.setFieldsValue(initialValues);
      }
    }
  }, [open, initialValues, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await onOk(values);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      title={title}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="Name"
          rules={[{ required: true, message: 'Please input name' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Please input email' },
            { type: 'email', message: 'Invalid email' },
          ]}
        >
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
};
```

### 7. UX 设计原则

**✅ 反馈时机**:
- 立即反馈: 使用 Message 展示操作结果(成功/失败)
- 重要确认: 使用 Modal.confirm 确认关键操作
- 通知提醒: 使用 Notification 展示系统级消息
- 持续提示: 使用 Alert 展示页面级警告

**✅ 消息优先级**:
- **Success**: 操作成功,绿色,3秒自动关闭
- **Info**: 普通信息,蓝色,4.5秒自动关闭
- **Warning**: 警告信息,黄色,4.5秒自动关闭
- **Error**: 错误信息,红色,4.5秒自动关闭,建议手动关闭

**❌ 避免的陷阱**:
```typescript
// ❌ 避免过长的消息
message.success('This is a very long message that should be truncated because it will look bad on the UI and annoy users...');

// ✅ 使用 description 参数
notification.success({
  message: 'Operation Successful',
  description: 'Your request has been processed and the changes have been saved.',
});

// ❌ 避免连续触发多个消息
for (let i = 0; i < 10; i++) {
  message.success('Item ' + i); // 会造成消息堆叠
}

// ✅ 使用单个消息汇总
message.success(`${count} items deleted successfully`);
```

### 8. 性能优化

**✅ 推荐**: 防抖用户操作

```typescript
import { Button, App } from 'antd';
import { debounce } from 'lodash';
import { useCallback } from 'react';

const OptimizedFeedback = () => {
  const { message } = App.useApp();

  const handleSearch = useCallback(
    debounce((query: string) => {
      message.info(`Searching for: ${query}`);
      // 执行搜索
    }, 500),
    [message]
  );

  return <Button onClick={() => handleSearch('test')}>Search</Button>;
};
```

**✅ 推荐**: 合并多个通知

```typescript
import { notification } from 'antd';

const NotificationQueue = () => {
  const queue: any[] = [];
  let processing = false;

  const processQueue = async () => {
    if (processing || queue.length === 0) return;

    processing = true;
    const item = queue.shift();

    await notification.open(item);

    setTimeout(() => {
      processing = false;
      processQueue();
    }, 1000); // 间隔1秒
  };

  const addNotification = (config: any) => {
    queue.push(config);
    processQueue();
  };

  return <Button onClick={() => addNotification({ message: 'Test' })}>
    Add Notification
  </Button>;
};
```

### 9. 可访问性 (A11y)

**✅ 推荐**: 确保屏幕阅读器可访问

```typescript
import { Modal, Button } from 'antd';

const AccessibleModal = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Button
        type="primary"
        onClick={() => setIsModalOpen(true)}
        aria-label="Open user settings modal"
      >
        Open Modal
      </Button>
      <Modal
        title="User Settings"
        open={isModalOpen}
        onOk={() => setIsModalOpen(false)}
        onCancel={() => setIsModalOpen(false)}
        // ARIA 属性
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        aria-describedby="modal-description"
      >
        <h2 id="modal-title">User Settings</h2>
        <p id="modal-description">Configure your user preferences here.</p>
        {/* 表单内容 */}
      </Modal>
    </>
  );
};
```

### 10. 国际化支持

**✅ 推荐**: 结合 ConfigProvider 实现 i18n

```typescript
import { Modal, ConfigProvider, App } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

const I18nFeedback = () => {
  const { modal } = App.useApp();

  const showConfirm = () => {
    modal.confirm({
      title: 'Confirm',
      content: 'Are you sure?',
      // 中文: 确定/取消
      // English: OK/Cancel (自动跟随 ConfigProvider.locale)
    });
  };

  return (
    <ConfigProvider locale={zhCN}>
      <App>
        <Button onClick={showConfirm}>Show Confirm</Button>
      </App>
    </ConfigProvider>
  );
};
```

---

## 常见问题

### Q1: Message 和 Notification 有什么区别?

**A**:
- **Message**: 全局提示,显示在页面顶部中央,用于操作反馈,适合简短提示
- **Notification**: 通知提示框,显示在页面角落,适合系统级消息、后台通知

选择建议:
- 操作成功/失败 → Message
- 后台收到新消息 → Notification
- 系统公告 → Notification
- 表单验证错误 → Alert

### Q2: Modal.confirm 如何处理异步确认?

**A**: 返回 Promise,Modal 会自动显示 loading 状态

```typescript
modal.confirm({
  title: 'Confirm Delete',
  onOk: async () => {
    await api.deleteItem(); // Modal 会显示 loading
    message.success('Deleted!');
  },
  onCancel: () => {
    // 用户取消
  },
});
```

### Q3: 如何防止用户重复点击触发多个消息?

**A**: 使用防抖或禁用按钮

```typescript
const [loading, setLoading] = useState(false);

const handleClick = async () => {
  if (loading) return;
  setLoading(true);
  try {
    await api.submit();
    message.success('Success!');
  } finally {
    setLoading(false);
  }
};

<Button onClick={handleClick} disabled={loading}>
  Submit
</Button>
```

### Q4: Popconfirm 和 Modal.confirm 如何选择?

**A**:
- **Popconfirm**: 气泡确认框,轻量级,适合单条记录确认
- **Modal.confirm**: 对话框,更正式,适合重要操作、批量操作

示例:
- 删除单个用户 → Popconfirm
- 删除选中用户(批量) → Modal.confirm
- 提交表单 → Modal.confirm
- 取消订单 → Modal.confirm

### Q5: 如何自定义 Modal 的样式?

**A**: 通过 ConfigProvider 或 style 属性

```typescript
// 方式1: ConfigProvider 全局配置
<ConfigProvider
  theme={{
    components: {
      Modal: {
        contentBg: '#f0f0f0',
        headerBg: '#1890ff',
      },
    },
  }}
>
  <App><YourApp /></App>
</ConfigProvider>

// 方式2: style 属性
<Modal
  style={{
    content: { backgroundColor: '#f0f0f0' },
  }}
>
  {/* content */}
</Modal>
```

### Q6: App.useApp() 必须在 App 组件内使用吗?

**A**: 是的,`App.useApp()` 必须在 `<App>` 组件内部使用

```typescript
// ✅ 正确
<ConfigProvider theme={...}>
  <App>
    <YourComponent /> {/* 可以在这里使用 App.useApp() */}
  </App>
</ConfigProvider>

// ❌ 错误
<YourComponent /> {/* 不能在这里使用 App.useApp() */}
```

### Q7: 如何实现消息队列(依次显示多个消息)?

**A**: 手动管理消息队列

```typescript
import { message } from 'antd';

const messageQueue = [
  'Processing step 1...',
  'Processing step 2...',
  'Processing step 3...',
  'Done!',
];

const showSequentialMessages = async () => {
  for (const msg of messageQueue) {
    await new Promise(resolve => {
      message.loading(msg, 0);
      setTimeout(resolve, 1000);
    });
    message.destroy();
  }
  message.success('All steps completed!');
};
```

### Q8: Alert 和 Message 如何选择?

**A**:
- **Alert**: 页面内常驻提示,适合表单验证错误、页面级警告
- **Message**: 临时提示,适合操作反馈

场景选择:
- 表单验证错误 → Alert (显示在表单顶部)
- 保存成功 → Message (全局提示,3秒后消失)
- 网络错误 → Alert (显示详细错误信息和重试按钮)

---

## 参考资源

### 官方文档
- [Alert 组件](https://ant.design/components/alert-cn/)
- [Message 组件](https://ant.design/components/message-cn/)
- [Modal 组件](https://ant.design/components/modal-cn/)
- [Notification 组件](https://ant.design/components/notification-cn/)
- [Popconfirm 组件](https://ant.design/components/popconfirm-cn/)
- [Popover 组件](https://ant.design/components/popover-cn/)
- [App 组件](https://ant.design/components/app-cn/)

### 设计指南
- [Ant Design 反馈组件设计规范](https://ant.design/spec/feedback-cn/)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)

### 相关文章
- [Ant Design 5.x App 组件最佳实践](https://ant.design/docs/react/migration-v5-cn#app-%E7%BB%84%E4%BB%B6) (中文)
- [Modal.confirm 异步处理指南](https://ant.design/components/modal-cn#modalconfirm) (中文)
- [UX设计: 如何设计好的反馈系统](https://www.nngroup.com/articles/redesigning-through-microinteractions/)
- [可访问性指南: ARIA 和对话框](https://www.w3.org/WAI/tutorials/dialogs/)

### 示例代码
- [Ant Design Feedback Components - StackBlitz](https://stackblitz.com/edit/react-antd-feedback-example)
- [Complete Feedback System - CodeSandbox](https://codesandbox.io/s/antd-feedback-system-forked-xyz)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0 (推荐 18+)

---

## 注意事项

1. **App.useApp() 使用**: 必须在 `<App>` 组件内部使用,否则会报错
2. **Message 全局方法**: 5.x 版本推荐使用 App.useApp(),而非直接导入 message
3. **Modal 内容溢出**: 长内容需要设置 `width` 或使用 `bodyStyle={{ maxHeight: '70vh', overflow: 'auto' }}`
4. **Popconfirm 位置**: 确保触发元素有足够空间,避免气泡被截断
5. **Notification 队列**: 默认最多显示 3 个,可通过 ConfigProvider 调整
6. **Alert Banner**: 设置 `banner` 属性后,左侧会显示蓝色边框
7. **键盘操作**: Modal、Popconfirm 支持 ESC 键关闭,符合无障碍标准
8. **异步关闭**: Modal.confirm 的 onOk 返回 Promise 时,按钮会自动显示 loading 状态
9. **销毁方法**: `message.destroy()` 和 `notification.destroy()` 可手动清除所有消息
10. **主题定制**: 所有反馈组件都支持通过 ConfigProvider.theme 定制样式

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
