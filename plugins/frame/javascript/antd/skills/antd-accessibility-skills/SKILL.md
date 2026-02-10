---
name: antd-accessibility-skills
description: Ant Design 无障碍访问完整指南 - ARIA、键盘导航、屏幕阅读器、语义化、颜色对比度
---

# Ant Design 无障碍访问完整指南

## Overview

Ant Design 5.x 内置完善的无障碍访问（Accessibility/A11y）支持，遵循 WAI-ARIA 1.2、WCAG 2.1 Level AA 标准，提供语义化 HTML、键盘导航、屏幕阅读器支持、焦点管理和颜色对比度等核心功能。本指南全面介绍如何使用 Ant Design 构建符合无障碍标准的应用。

## 核心特性

- **WAI-ARIA 1.2 完整支持**: 所有组件内置正确的 ARIA 属性和角色
- **键盘导航友好**: 全键盘操作支持，标准快捷键模式
- **屏幕阅读器兼容**: 与 NVDA、JAWS、VoiceOver 等主流屏幕阅读器完美配合
- **语义化 HTML**: 自动生成符合规范的 HTML 结构
- **焦点管理**: 智能焦点陷阱、焦点恢复、焦点可见性
- **颜色对比度**: 默认符合 WCAG 2.1 Level AA（4.5:1）
- **国际化支持**: 多语言屏幕阅读器文本
- **可扩展性**: 提供自定义 ARIA 属性和回调接口

## WAI-ARIA 基础

### ARIA 角色（Roles）

Ant Design 组件自动添加正确的 ARIA 角色。

#### 常见组件角色

```typescript
// Button 组件
<Button role="button">Click me</Button>
// 渲染为：<button role="button" ...>

// Link 组件
<Link href="/home" role="link">Home</Link>
// 渲染为：<a role="link" ...>

// Modal 组件
<Modal open={true} role="dialog">
  <p>Modal content</p>
</Modal>
// 渲染为：<div role="dialog" aria-modal="true" ...>

// Alert 组件
<Alert message="Success" type="success" role="alert">
// 渲染为：<div role="alert" ...>
```

#### 地标角色（Landmark Roles）

```typescript
import { Layout } from 'antd';

const { Header, Footer, Sider, Content } = Layout;

function App() {
  return (
    <Layout>
      <Header role="banner"> {/* 页眉 */}
        <h1>Application Title</h1>
      </Header>

      <Layout>
        <Sider role="complementary" width={200}> {/* 侧边栏 */}
          <nav aria-label="Main navigation">
            {/* 导航菜单 */}
          </nav>
        </Sider>

        <Content role="main"> {/* 主内容区 */}
          <main>
            <h2>Main Content</h2>
          </main>
        </Content>
      </Layout>

      <Footer role="contentinfo"> {/* 页脚 */}
        © 2024 Company
      </Footer>
    </Layout>
  );
}
```

**常用地标角色**:
- `banner`: 页眉区域
- `main`: 主内容区
- `complementary`: 侧边栏、补充内容
- `contentinfo`: 页脚、版权信息
- `navigation`: 导航区域
- `search`: 搜索区域
- `form`: 表单区域

### ARIA 属性（Attributes）

#### 状态属性

```typescript
import { Switch, Checkbox, Radio } from 'antd';

// Switch - aria-checked 表示开关状态
<Switch
  aria-checked={checked}
  aria-label="Dark mode toggle"
  checked={checked}
  onChange={setChecked}
/>

// Checkbox - aria-checked 表示选中状态
<Checkbox
  aria-checked={checked}
  aria-label="Accept terms and conditions"
  checked={checked}
  onChange={(e) => setChecked(e.target.checked)}
>
  I agree to the terms
</Checkbox>

// Radio - aria-checked 表示单选状态
<Radio.Group
  aria-label="Select notification preference"
  value={value}
  onChange={(e) => setValue(e.target.value)}
>
  <Radio value="email">Email</Radio>
  <Radio value="sms">SMS</Radio>
  <Radio value="push">Push</Radio>
</Radio.Group>
```

#### 关系属性

```typescript
import { Form, Input, Label } from 'antd';

// 表单字段关联
<Form.Item
  label="Email"
  name="email"
  htmlFor="email-input" // 显式关联
>
  <Input
    id="email-input"
    aria-label="Email address"
    aria-required="true"
    aria-invalid={hasError}
    aria-describedby="email-help" // 关联帮助文本
  />
</Form.Item>

<div id="email-help" className="ant-form-item-explain">
  We'll never share your email with anyone else.
</div>

// 错误消息关联
<Form.Item
  validateStatus={error ? 'error' : ''}
  help={error}
>
  <Input
    aria-invalid={!!error}
    aria-errormessage={error ? 'password-error' : undefined}
  />
  {error && <span id="password-error">{error}</span>}
</Form.Item>
```

#### 描述属性

```typescript
import { Tooltip, Popover } from 'antd';

// Tooltip - 使用 aria-describedby
<Tooltip title="This is a helpful tooltip">
  <Button aria-label="Help" aria-describedby="tooltip-help">
    Help
  </Button>
</Tooltip>

// Popover - 详细描述
<Popover
  content={
    <div>
      <p>Additional information about this feature.</p>
      <p>Learn more in our documentation.</p>
    </div>
  }
  trigger="click"
>
  <Button aria-label="More info" aria-describedby="popover-details">
    Learn More
  </Button>
</Popover>

// 进度条描述
<Progress
  percent={75}
  aria-label="File upload progress"
  aria-valuetext="75 percent completed"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-valuenow="75"
/>
```

### ARIA 实时区域（Live Regions）

```typescript
import { Alert, message } from 'antd';

// Alert 组件内置 aria-live
<Alert
  message="Notification"
  description="This is an important announcement"
  type="info"
  showIcon
  role="status"
  aria-live="polite" // 礼貌模式，不中断当前操作
  aria-atomic="true" // 整个区域作为单一单元朗读
/>

// 紧急警告使用 aria-live="assertive"
<Alert
  message="Critical Error"
  description="System will shutdown in 5 minutes"
  type="error"
  showIcon
  role="alert"
  aria-live="assertive" // 立即中断并朗读
  aria-atomic="true"
/>

// 自定义实时区域
const [status, setStatus] = useState<string>('');

<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  aria-label="Upload status"
>
  {status}
</div>

// Message 组件（全局通知）
message.success('Operation successful!', 3); // 自动使用 aria-live
```

**实时区域级别**:
- `aria-live="off"`: 不朗读更新（默认）
- `aria-live="polite"`: 空闲时朗读（推荐用于状态更新）
- `aria-live="assertive"`: 立即朗读并中断（仅用于紧急通知）

## 键盘导航

### 标准键盘快捷键

Ant Design 组件遵循标准的键盘导航模式。

#### 通用快捷键

| 按键 | 功能 | 适用组件 |
|------|------|----------|
| `Tab` / `Shift+Tab` | 焦点移动 | 所有可聚焦元素 |
| `Enter` / `Space` | 激活/选择 | Button, Checkbox, Radio, Link |
| `Escape` | 关闭/取消 | Modal, Drawer, Popover, Dropdown |
| `Arrow Keys` | 导航/选择 | Menu, Select, DatePicker, Slider |
| `Home` / `End` | 跳到首/尾 | List, Menu, Select (下拉列表) |
| `Page Up` / `Page Down` | 快速翻页 | Select, DatePicker |
| `Type-ahead` | 快速搜索 | Select, Tree, Menu (输入字符跳转) |

#### 按钮组件

```typescript
import { Button } from 'antd';

// 基本按钮 - 支持 Enter 和 Space 激活
<Button onClick={handleClick} tabIndex={0}>
  Click me
</Button>

// 链接按钮 - 仍然支持键盘操作
<Button type="link" href="/home">
  Go to home
</Button>

// 危险操作 - 二次确认
<Popconfirm
  title="Are you sure?"
  onConfirm={handleDelete}
  okText="Yes"
  cancelText="No"
  keyboard // 启用键盘操作
>
  <Button danger icon={<DeleteOutlined />}>
    Delete
  </Button>
</Popconfirm>
```

#### 表单组件

```typescript
import { Form, Input, InputNumber, Select, DatePicker } from 'antd';

// Input - 支持所有标准编辑快捷键
<Input
  placeholder="Type here..."
  onKeyDown={(e) => {
    // Ctrl+A: 全选
    // Ctrl+C/V: 复制/粘贴
    // Ctrl+Z: 撤销
  }}
/>

// InputNumber - 支持上下箭头调整数值
<InputNumber
  min={0}
  max={100}
  step={10}
  onKeyDown={(e) => {
    if (e.key === 'ArrowUp') increment();
    if (e.key === 'ArrowDown') decrement();
  }}
/>

// Select - 支持键盘导航
<Select
  mode="tags"
  placeholder="Select options"
  showSearch
  filterOption={(input, option) =>
    option.label.toLowerCase().includes(input.toLowerCase())
  }
  // 键盘支持:
  // - Down/Up: 导航选项
  // - Enter: 选择当前选项
  // - Escape: 关闭下拉框
  // - 字母键: 快速搜索
  options={[
    { value: 'apple', label: 'Apple' },
    { value: 'banana', label: 'Banana' },
    { value: 'orange', label: 'Orange' },
  ]}
/>

// DatePicker - 完整键盘导航
<DatePicker
  // 方向键: 选择日期
  // Page Up/Down: 切换月份
  // Shift+Page Up/Down: 切换年份
  // Home: 跳到本月第一天
  // End: 跳到本月最后一天
  // Enter: 确认选择
/>
```

#### 下拉菜单组件

```typescript
import { Dropdown, Menu } from 'antd';

const items = [
  { key: '1', label: 'Option 1' },
  { key: '2', label: 'Option 2' },
  { key: '3', label: 'Option 3' },
];

<Dropdown menu={{ items }} trigger={['click']}>
  <Button>
    Open menu (Press Enter or Space)
  </Button>
</Dropdown>

// 键盘操作:
// - Enter/Space: 打开菜单
// - Escape: 关闭菜单
// - Down/Up: 导航菜单项
// - Enter: 选择当前项
// - Home/End: 跳到首/尾项
```

#### 模态框焦点管理

```typescript
import { Modal, Button } from 'antd';

const [isModalOpen, setIsModalOpen] = useState(false);

<Modal
  title="Basic Modal"
  open={isModalOpen}
  onOk={() => setIsModalOpen(false)}
  onCancel={() => setIsModalOpen(false)}
  autoFocusButton="ok" // 自动聚焦到 OK 按钮
  focusTriggerAfterClose // 关闭后焦点返回触发元素
>
  <p>Modal content...</p>
  <Button onClick={() => setIsModalOpen(false)}>
    Cancel (Escape)
  </Button>
</Modal>

<Button onClick={() => setIsModalOpen(true)}>
  Open Modal
</Button>

// 键盘操作:
// - Escape: 关闭模态框
// - Tab/Shift+Tab: 在模态框内循环焦点（焦点陷阱）
// - 关闭后: 焦点自动返回触发按钮
```

### 自定义键盘处理

```typescript
import { useEffect } from 'react';

function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K: 打开搜索
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openSearch();
      }

      // Ctrl/Cmd + /: 打开帮助
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        openHelp();
      }

      // Escape: 关闭所有面板
      if (e.key === 'Escape') {
        closeAllPanels();
      }

      // 数字键: 快速切换标签
      if (e.altKey && /^[1-9]$/.test(e.key)) {
        e.preventDefault();
        switchTab(parseInt(e.key));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return null;
}

// 使用
function App() {
  useKeyboardShortcuts();

  return (
    <div>
      <kbd>Ctrl + K</kbd>: Open search<br />
      <kbd>Ctrl + /</kbd>: Open help<br />
      <kbd>Alt + 1-9</kbd>: Switch tabs
    </div>
  );
}
```

### 键盘陷阱避免

```typescript
import { useEffect, useRef } from 'react';

// 避免焦点陷阱在模态框中
function ModalContent() {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const focusableElements = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (!focusableElements || focusableElements.length === 0) return;

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[
        focusableElements.length - 1
      ] as HTMLElement;

      // Shift + Tab
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      }
      // Tab
      else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleTabKey);
    return () => document.removeEventListener('keydown', handleTabKey);
  }, []);

  return (
    <div ref={modalRef} role="dialog" aria-modal="true">
      {/* Modal content */}
    </div>
  );
}
```

## 焦点管理

### 焦点可见性

```typescript
import { ConfigProvider } from 'antd';

// 启用全局焦点可见样式
ConfigProvider.config({
  theme: {
    token: {
      // 确保焦点指示器清晰可见
      controlOutlineWidth: 2,
      controlOutline: 'focus',
    },
  },
});

// 自定义焦点样式（推荐）
const focusStyles = `
  *:focus-visible {
    outline: 2px solid #1890ff;
    outline-offset: 2px;
    border-radius: 2px;
  }

  *:focus:not(:focus-visible) {
    outline: none;
  }
`;

// 应用样式
injectStyles(focusStyles);
```

**焦点可见性要求**:
- 对比度至少 3:1（WCAG 2.1 Level AA）
- 焦点指示器清晰可辨
- 不依赖颜色变化（必须提供形状或轮廓）
- 支持高对比度模式

### 焦点陷阱

```typescript
import { Modal, Drawer } from 'antd';

// Modal 自动管理焦点陷阱
<Modal
  open={open}
  onOk={handleOk}
  onCancel={handleCancel}
  // 自动行为:
  // 1. 打开时聚焦到模态框
  // 2. Tab 循环在模态框内
  // 3. 关闭后焦点返回触发元素
>
  <p>Content</p>
</Modal>

// Drawer 同样支持焦点陷阱
<Drawer
  open={open}
  onClose={onClose}
  // 焦点管理行为同 Modal
>
  <p>Content</p>
</Drawer>
```

### 焦点恢复

```typescript
import { useState, useRef } from 'react';

function FocusRestoreExample() {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const handleOpen = () => {
    // 保存触发元素
    triggerRef.current = document.activeElement as HTMLElement;
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    // 恢复焦点到触发元素
    setTimeout(() => {
      triggerRef.current?.focus();
    }, 0);
  };

  return (
    <>
      <Button onClick={handleOpen} ref={triggerRef}>
        Open dialog
      </Button>
      <Modal open={open} onCancel={handleClose}>
        <p>Dialog content</p>
      </Modal>
    </>
  );
}
```

### 自定义焦点管理

```typescript
import { useRef, useEffect } from 'react';

// 自定义焦点管理 Hook
function useFocusManagement(isOpen: boolean) {
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // 保存当前焦点
      previousFocusRef.current = document.activeElement as HTMLElement;

      // 聚焦到容器内第一个可聚焦元素
      const firstFocusable = containerRef.current?.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement;

      firstFocusable?.focus();
    } else {
      // 恢复之前的焦点
      previousFocusRef.current?.focus();
    }
  }, [isOpen]);

  return containerRef;
}

// 使用
function CustomDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useFocusManagement(open);

  if (!open) return null;

  return (
    <div
      ref={ref}
      role="dialog"
      aria-modal="true"
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <button onClick={onClose}>Close</button>
      <p>Dialog content</p>
    </div>
  );
}
```

### 跳过导航链接

```typescript
// "Skip to main content" 链接 - 提升键盘导航体验
function SkipLinks() {
  return (
    <a
      href="#main-content"
      style={{
        position: 'absolute',
        left: '-9999px',
        zIndex: 999,
        padding: '8px',
        background: '#1890ff',
        color: 'white',
        textDecoration: 'none',
      }}
      onFocus={(e) => {
        e.target.style.left = '8px';
        e.target.style.top = '8px';
      }}
      onBlur={(e) => {
        e.target.style.left = '-9999px';
      }}
    >
      Skip to main content
    </a>
  );
}

// 在应用中使用
function App() {
  return (
    <>
      <SkipLinks />
      <Header>...</Header>
      <main id="main-content" tabIndex={-1}>
        <h1>Main Content</h1>
      </main>
      <Footer>...</Footer>
    </>
  );
}
```

## 屏幕阅读器支持

### 语义化 HTML

```typescript
import { Typography, Space } from 'antd';

const { Title, Paragraph, Text } = Typography;

function SemanticContent() {
  return (
    <article>
      <header>
        <Title level={1}>Article Title</Title>
        <Text type="secondary">Published on Jan 1, 2024</Text>
      </header>

      <section aria-labelledby="section-1">
        <Title level={2} id="section-1">
          Section 1
        </Title>
        <Paragraph>
          This is the first section of the article.
        </Paragraph>
      </section>

      <section aria-labelledby="section-2">
        <Title level={2} id="section-2">
          Section 2
        </Title>
        <Paragraph>
          This is the second section of the article.
        </Paragraph>
      </section>

      <footer>
        <Text type="secondary">© 2024 Company</Text>
      </footer>
    </article>
  );
}
```

### 隐藏视觉元素但保留屏幕阅读器

```typescript
import { Button, Space } from 'antd';

// sr-only 类 - 仅屏幕阅读器可见
const srOnlyStyle = {
  position: 'absolute' as const,
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap' as const,
  border: 0,
};

function ButtonWithLabel() {
  return (
    <Button icon={<SearchOutlined />}>
      <span style={srOnlyStyle}>Search</span>
    </Button>
  );
}

// Icon 按钮必须提供标签
<Button
  icon={<DeleteOutlined />}
  aria-label="Delete item"
  onClick={handleDelete}
/>

// 使用 title 和 aria-label
<Tooltip title="Delete">
  <Button
    icon={<DeleteOutlined />}
    aria-label="Delete item"
  />
</Tooltip>
```

### 屏幕阅读器专用文本

```typescript
import { Alert, Progress } from 'antd';

// 加载状态 - 通知屏幕阅读器
function LoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading"
    >
      <Spin />
      <span style={srOnlyStyle}>Loading content...</span>
    </div>
  );
}

// 进度指示器
<Progress
  percent={60}
  status="active"
  aria-label="File upload progress"
  aria-valuetext="60 percent completed"
/>

// 表格排序状态
const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    sorter: true,
    sortOrder: 'ascend' as const,
    // 屏幕阅读器会朗读:
    // "Name, sorted ascending"
  },
];

// 动态内容更新
function LiveRegion() {
  const [message, setMessage] = useState('');

  const updateMessage = (msg: string) => {
    setMessage(msg);
  };

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {message}
    </div>
  );
}
```

### 表单无障碍

```typescript
import { Form, Input, Checkbox, Radio, Select } from 'antd';

function AccessibleForm() {
  const [form] = Form.useForm();

  return (
    <Form
      form={form}
      layout="vertical"
      aria-label="User registration form"
    >
      {/* 字段必须有标签 */}
      <Form.Item
        label="Email"
        name="email"
        rules={[
          { required: true, message: 'Please input your email!' },
          { type: 'email', message: 'Invalid email format!' },
        ]}
      >
        <Input
          aria-required="true"
          aria-invalid="false"
          aria-describedby="email-help"
        />
      </Form.Item>

      <div id="email-help" style={{ fontSize: 12, color: '#888' }}>
        We'll never share your email with anyone else.
      </div>

      {/* Checkbox 组 */}
      <Form.Item
        name="agreement"
        valuePropName="checked"
        rules={[{ required: true, message: 'Please accept the agreement!' }]}
      >
        <Checkbox aria-required="true">
          I have read and agree to the <a href="/terms">terms</a>
        </Checkbox>
      </Form.Item>

      {/* Radio 组 - 必须提供 aria-label */}
      <Form.Item label="Gender" name="gender">
        <Radio.Group aria-label="Select gender">
          <Radio value="male">Male</Radio>
          <Radio value="female">Female</Radio>
          <Radio value="other">Other</Radio>
        </Radio.Group>
      </Form.Item>

      {/* Select - 使用 aria-labelledby */}
      <Form.Item
        label={<span id="country-label">Country</span>}
        name="country"
      >
        <Select
          aria-labelledby="country-label"
          placeholder="Select your country"
          options={countryOptions}
        />
      </Form.Item>

      {/* 错误消息关联 */}
      <Form.Item
        label="Password"
        name="password"
        validateStatus={error ? 'error' : ''}
        help={error}
      >
        <Input.Password
          aria-invalid={!!error}
          aria-errormessage={error ? 'password-error' : undefined}
        />
      </Form.Item>
      {error && <span id="password-error">{error}</span>}

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
}
```

### 列表和表格

```typescript
import { List, Table } from 'antd';

// 列表 - 语义化标记
function AccessibleList() {
  const data = [
    { id: 1, title: 'Item 1', description: 'Description 1' },
    { id: 2, title: 'Item 2', description: 'Description 2' },
  ];

  return (
    <List
      dataSource={data}
      renderItem={(item) => (
        <List.Item id={`item-${item.id}`}>
          <List.Item.Meta
            title={<a href={`/items/${item.id}`}>{item.title}</a>}
            description={item.description}
          />
        </List.Item>
      )}
    />
  );
}

// 表格 - 完整无障碍支持
function AccessibleTable() {
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      // 屏幕阅读器会朗读排序状态
    },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
      sorter: true,
    },
    {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
    },
  ];

  const data = [
    { key: '1', name: 'John Brown', age: 32, address: 'New York' },
    { key: '2', name: 'Jim Green', age: 42, address: 'London' },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      // 自动生成:
      // - <caption> 表格标题
      // - <thead> 表头
      // - <tbody> 表体
      // - aria-sort 排序状态
      pagination={{
        showTotal: (total) => `Total ${total} items`,
        // 屏幕阅读器会朗读分页信息
      }}
    />
  );
}
```

## 语义化与结构

### HTML5 语义元素

```typescript
import { Layout, Breadcrumb } from 'antd';

const { Header, Footer, Sider, Content } = Layout;

function SemanticStructure() {
  return (
    <Layout>
      {/* 页眉 */}
      <Header role="banner">
        <div className="logo" />
        <nav aria-label="Main navigation">
          <Menu mode="horizontal" defaultSelectedKeys={['1']}>
            <Menu.Item key="1">Home</Menu.Item>
            <Menu.Item key="2">About</Menu.Item>
            <Menu.Item key="3">Contact</Menu.Item>
          </Menu>
        </nav>
      </Header>

      <Layout>
        {/* 侧边栏 */}
        <Sider
          width={200}
          style={{ background: '#fff' }}
          role="complementary"
          aria-label="Additional links"
        >
          <Menu mode="inline" defaultSelectedKeys={['1']}>
            <Menu.Item key="1">Option 1</Menu.Item>
            <Menu.Item key="2">Option 2</Menu.Item>
          </Menu>
        </Sider>

        {/* 主内容 */}
        <Content style={{ padding: '24px' }}>
          {/* 面包屑导航 */}
          <Breadcrumb aria-label="Breadcrumb">
            <Breadcrumb.Item>Home</Breadcrumb.Item>
            <Breadcrumb.Item>Library</Breadcrumb.Item>
            <Breadcrumb.Item>Data</Breadcrumb.Item>
          </Breadcrumb>

          {/* 主体内容 */}
          <main role="main" id="main-content">
            <h1>Page Title</h1>
            <article>
              <section aria-labelledby="section-1">
                <h2 id="section-1">Section 1</h2>
                <p>Content...</p>
              </section>

              <section aria-labelledby="section-2">
                <h2 id="section-2">Section 2</h2>
                <p>Content...</p>
              </section>
            </article>
          </main>
        </Content>
      </Layout>

      {/* 页脚 */}
      <Footer role="contentinfo">
        © 2024 Company Name. All rights reserved.
      </Footer>
    </Layout>
  );
}
```

### 标题层级

```typescript
import { Typography } from 'antd';

const { Title, Paragraph, Text } = Typography;

function HeadingHierarchy() {
  return (
    <article>
      {/* h1 - 页面/文章标题（每页仅一个） */}
      <Title level={1}>Main Article Title</Title>

      <Paragraph>
        Introduction text...
      </Paragraph>

      {/* h2 - 主要章节 */}
      <Title level={2} id="chapter-1">
        Chapter 1: Introduction
      </Title>

      <Paragraph>
        Chapter content...
      </Paragraph>

      {/* h3 - 子章节 */}
      <Title level={3} id="section-1-1">
        Section 1.1: Background
      </Title>

      <Paragraph>
        Section content...
      </Paragraph>

      <Title level={3} id="section-1-2">
        Section 1.2: Overview
      </Title>

      <Paragraph>
        Section content...
      </Paragraph>

      {/* h2 - 下一章节 */}
      <Title level={2} id="chapter-2">
        Chapter 2: Methodology
      </Title>

      <Paragraph>
        Chapter content...
      </Paragraph>
    </article>
  );
}
```

**标题层级规则**:
- 每个页面只有一个 `h1`
- 标题层级不能跳级（h1 → h2 → h3，不能 h1 → h3）
- 使用 `id` 属性关联标题和内容区域
- 使用 `aria-labelledby` 关联章节

### 列表语义化

```typescript
import { List, Menu, Dropdown } from 'antd';

// 无序列表
function UnorderedList() {
  const data = [
    'Apple',
    'Banana',
    'Orange',
  ];

  return (
    <ul>
      {data.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

// 有序列表
function OrderedList() {
  const steps = [
    'Register an account',
    'Verify your email',
    'Complete your profile',
  ];

  return (
    <ol>
      {steps.map((step, index) => (
        <li key={index}>{step}</li>
      ))}
    </ol>
  );

  // 屏幕阅读器会朗读:
  // "Step 1 of 3: Register an account"
  // "Step 2 of 3: Verify your email"
  // "Step 3 of 3: Complete your profile"
}

// 定义列表
function DefinitionList() {
  return (
    <dl>
      <dt>HTML</dt>
      <dd>HyperText Markup Language</dd>

      <dt>CSS</dt>
      <dd>Cascading Style Sheets</dd>

      <dt>JavaScript</dt>
      <dd>Programming language of the web</dd>
    </dl>
  );
}
```

## 颜色对比度

### WCAG 2.1 对比度标准

| 对比度级别 | 正常文本 | 大文本（18pt+ 或 14pt+ 粗体） | 图形/UI 组件 |
|-----------|----------|------------------------------|-------------|
| **Level AA** | 4.5:1 | 3:1 | 3:1 |
| **Level AAA** | 7:1 | 4.5:1 | 4.5:1 |

### Ant Design 默认对比度

Ant Design 5.x 默认主题符合 WCAG 2.1 Level AA 标准。

```typescript
// 主要颜色对比度
const primaryColors = {
  // 蓝色主色 (#1890ff) 对白色背景
  primary: '#1890ff', // 对比度 4.52:1 ✅ AA
  primaryHover: '#40a9ff', // 对比度 3.91:1 ✅ AA
  primaryActive: '#096dd9', // 对比度 4.92:1 ✅ AA

  // 文本颜色对比度
  textPrimary: 'rgba(0, 0, 0, 0.88)', // 对比度 13.77:1 ✅ AAA
  textSecondary: 'rgba(0, 0, 0, 0.65)', // 对比度 9.56:1 ✅ AAA
  textTertiary: 'rgba(0, 0, 0, 0.45)', // 对比度 5.91:1 ✅ AA

  // 边框颜色对比度
  borderColor: '#d9d9d9', // 对比度 2.07:1 ❌ 不用于文本
  colorBorder: '#d9d9d9', // 对比度 2.07:1 ❌ 不用于文本
};
```

### 自定义主题对比度

```typescript
import { ConfigProvider, theme } from 'antd';

// 自定义主题 - 确保对比度
function CustomTheme() {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 主色 - 蓝色系
          colorPrimary: '#1677ff', // 对比度 4.72:1 ✅ AA
          colorSuccess: '#52c41a', // 对比度 3.98:1 ✅ AA
          colorWarning: '#faad14', // 对比度 2.67:1 ⚠️ 大文本
          colorError: '#ff4d4f', // 对比度 3.96:1 ✅ AA
          colorInfo: '#1677ff', // 对比度 4.72:1 ✅ AA

          // 文本颜色 - 高对比度
          colorTextBase: 'rgba(0, 0, 0, 0.88)', // 13.77:1 ✅ AAA
          colorTextSecondary: 'rgba(0, 0, 0, 0.65)', // 9.56:1 ✅ AAA
          colorTextTertiary: 'rgba(0, 0, 0, 0.45)', // 5.91:1 ✅ AA

          // 背景色
          colorBgBase: '#ffffff',
          colorBgContainer: '#ffffff',
        },
        algorithm: theme.defaultAlgorithm, // 使用默认算法
      }}
    >
      <App />
    </ConfigProvider>
  );
}
```

### 高对比度模式

```typescript
// 支持系统高对比度模式
const highContrastStyles = `
  @media (prefers-contrast: high) {
    .ant-btn-primary {
      background-color: WindowText;
      color: Window;
      border: 2px solid WindowText;
    }

    .ant-input {
      border: 2px solid WindowText;
    }

    .ant-table {
      border: 2px solid WindowText;
    }

    /* 所有文本使用最高对比度 */
    * {
      color: WindowText !important;
    }
  }
`;

// 检测系统偏好
function useHighContrastMode() {
  const [isHighContrast, setIsHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setIsHighContrast(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => {
      setIsHighContrast(e.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return isHighContrast;
}
```

### 暗色模式对比度

```typescript
// 暗色模式 - 确保对比度
function DarkModeTheme() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          // 暗色模式对比度验证
          colorBgBase: '#141414', // 深色背景
          colorTextBase: 'rgba(255, 255, 255, 0.85)', // 对比度 12.63:1 ✅ AAA
          colorTextSecondary: 'rgba(255, 255, 255, 0.65)', // 对比度 9.12:1 ✅ AAA

          // 主色在暗色背景上的对比度
          colorPrimary: '#177ddc', // 对比度 4.72:1 ✅ AA
          colorSuccess: '#49aa19', // 对比度 4.06:1 ✅ AA
          colorWarning: '#d89614', // 对比度 3.05:1 ✅ AA
          colorError: '#d32029', // 对比度 4.63:1 ✅ AA
        },
      }}
    >
      <App />
    </ConfigProvider>
  );
}
```

### 颜色对比度检测

```typescript
// 计算对比度的工具函数
function calculateContrastRatio(
  foreground: string,
  background: string
): number {
  // 将颜色转换为 RGB
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : { r: 0, g: 0, b: 0 };
  };

  const fg = hexToRgb(foreground);
  const bg = hexToRgb(background);

  // 计算相对亮度
  const luminance = (r: number, g: number, b: number) => {
    const [R, G, B] = [r, g, b].map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * R + 0.7152 * G + 0.0722 * B;
  };

  const L1 = luminance(fg.r, fg.g, fg.b);
  const L2 = luminance(bg.r, bg.g, bg.b);

  const lighter = Math.max(L1, L2);
  const darker = Math.min(L1, L2);

  // 对比度公式
  return (lighter + 0.05) / (darker + 0.05);
}

// 使用示例
const ratio = calculateContrastRatio('#1890ff', '#ffffff');
console.log(`Contrast ratio: ${ratio.toFixed(2)}:1`);
// Output: Contrast ratio: 4.52:1

// 验证 WCAG 级别
function getWCAGLevel(ratio: number, isLargeText: boolean = false) {
  if (isLargeText) {
    if (ratio >= 4.5) return 'AAA';
    if (ratio >= 3) return 'AA';
  } else {
    if (ratio >= 7) return 'AAA';
    if (ratio >= 4.5) return 'AA';
  }
  return 'Fail';
}
```

### 不仅仅是颜色

```typescript
// ✅ 正确：使用多个指示器
<Alert
  message="Success"
  type="success"
  icon={<CheckCircleFilled />} // 图标
  showIcon
  style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}
  // 颜色 + 图标 + 文本 + 边框
/>

// ❌ 错误：仅依赖颜色
<div style={{ color: 'green' }}>
  Success message
</div>

// ✅ 正确：表格行状态
<Table
  dataSource={data}
  rowClassName={(record) => {
    if (record.status === 'error') return 'error-row';
    if (record.status === 'success') return 'success-row';
    return '';
  }}
  // 添加图标列提供额外信息
  columns={[
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status) => {
        if (status === 'error') return <CloseCircleOutlined />;
        if (status === 'success') return <CheckCircleOutlined />;
        return <MinusCircleOutlined />;
      },
    },
  ]}
/>

// ✅ 正确：表单验证
<Form.Item
  validateStatus="error"
  help="This field is required"
>
  <Input aria-invalid="true" />
  // 颜色 + 文本 + aria-invalid 属性
</Form.Item>
```

## 最佳实践

### 1. 始终提供标签

```typescript
// ✅ 正确
<Button aria-label="Close dialog" icon={<CloseOutlined />} />

<Input
  id="email"
  aria-label="Email address"
  placeholder="Enter your email"
/>

<Checkbox aria-label="Remember me">
  Remember me
</Checkbox>

// ❌ 错误
<Button icon={<CloseOutlined />} />

<Input placeholder="Email" />

<Checkbox>Remember me</Checkbox> // 无 aria-label
```

### 2. 焦点管理

```typescript
// ✅ 正确：模态框焦点管理
<Modal
  open={open}
  onOk={handleOk}
  onCancel={handleCancel}
  autoFocusButton="ok"
  focusTriggerAfterClose
>
  <p>Content</p>
</Modal>

// ✅ 正确：自定义焦点管理
const dialogRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (open) {
    const firstFocusable = dialogRef.current?.querySelector(
      'button, [href], input'
    ) as HTMLElement;
    firstFocusable?.focus();
  }
}, [open]);

// ❌ 错误：无焦点管理
{open && (
  <div>
    <p>Content</p>
  </div>
)}
```

### 3. 键盘导航

```typescript
// ✅ 正确：完整的键盘支持
<Dropdown menu={{ items }} trigger={['click']}>
  <Button>Open menu</Button>
</Dropdown>
// 支持: Enter, Space, Escape, Arrow keys

// ✅ 正确：自定义键盘处理
const handleKeyDown = (e: React.KeyboardEvent) => {
  switch (e.key) {
    case 'Enter':
    case ' ':
      handleClick();
      break;
    case 'Escape':
      handleCancel();
      break;
    case 'ArrowDown':
      handleNext();
      break;
    case 'ArrowUp':
      handlePrevious();
      break;
  }
};

// ❌ 错误：鼠标事件仅
<div onClick={handleClick}>
  Click me
</div>
```

### 4. 屏幕阅读器文本

```typescript
// ✅ 正确：提供屏幕阅读器文本
<Button icon={<SearchOutlined />}>
  <span className="sr-only">Search</span>
</Button>

<Spin />
<span className="sr-only">Loading content...</span>

<Progress
  percent={75}
  aria-label="Upload progress"
  aria-valuetext="75 percent completed"
/>

// ❌ 错误：无屏幕阅读器文本
<Button icon={<SearchOutlined />} />

<Spin />

<Progress percent={75} />
```

### 5. ARIA 属性使用

```typescript
// ✅ 正确：必需的 ARIA 属性
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Dialog Title</h2>
  <p id="dialog-desc">Dialog description</p>
</div>

// ✅ 正确：动态 ARIA 属性
<Input
  aria-invalid={hasError}
  aria-errormessage={hasError ? 'error-msg' : undefined}
/>
{hasError && <span id="error-msg">{error}</span>}

// ❌ 错误：冗余的 ARIA（优先使用原生 HTML）
<button role="button">Click</button> {/* 冗余 */}
<div role="button">Click</div> {/* 应使用 <button> */}

// ❌ 错误：缺少必需的 ARIA 属性
<div role="dialog">
  <p>Content</p>
</div>
// 缺少 aria-modal, aria-labelledby
```

### 6. 表单无障碍

```typescript
// ✅ 正确：完整的表单标签
<Form.Item
  label={<span id="email-label">Email</span>}
  name="email"
  rules={[{ required: true }]}
>
  <Input
    id="email"
    aria-labelledby="email-label"
    aria-describedby="email-help"
    aria-required="true"
    aria-invalid={hasError}
  />
</Form.Item>
<div id="email-help">We'll never share your email.</div>

// ✅ 正确：错误消息关联
<Form.Item
  validateStatus={error ? 'error' : ''}
  help={error}
>
  <Input
    aria-invalid={!!error}
    aria-errormessage={error ? 'password-error' : undefined}
  />
  {error && <span id="password-error">{error}</span>}
</Form.Item>

// ❌ 错误：无标签
<Form.Item name="email">
  <Input placeholder="Email" />
</Form.Item>
```

### 7. 颜色对比度

```typescript
// ✅ 正确：高对比度文本
<ConfigProvider
  theme={{
    token: {
      colorTextBase: 'rgba(0, 0, 0, 0.88)', // 13.77:1 ✅ AAA
      colorTextSecondary: 'rgba(0, 0, 0, 0.65)', // 9.56:1 ✅ AAA
    },
  }}
>
  <App />
</ConfigProvider>

// ✅ 正确：多种指示器
<Alert
  message="Error"
  type="error"
  icon={<CloseCircleFilled />}
  showIcon
/>

// ❌ 错误：低对比度文本
<span style={{ color: '#d9d9d9', backgroundColor: '#ffffff' }}>
  This text has low contrast (2.07:1)
</span>

// ❌ 错误：仅依赖颜色
<div style={{ color: 'green' }}>Success</div>
```

## 常见问题（Q&A）

### Q1: Ant Design 组件默认是无障碍的吗？

**A**: 是的，Ant Design 5.x 的所有组件都内置无障碍支持，包括：
- 正确的 ARIA 角色和属性
- 键盘导航支持
- 焦点管理
- 屏幕阅读器兼容

但对于自定义组件和复杂交互，仍需要手动添加无障碍属性。

### Q2: 如何测试应用的无障碍性？

**A**: 推荐以下测试方法：

1. **自动化测试**:
```typescript
import { axe } from 'jest-axe';

it('should not have accessibility violations', async () => {
  const { container } = render(<App />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

2. **浏览器工具**:
- Chrome DevTools Lighthouse (Accessibility audit)
- axe DevTools (浏览器扩展)
- WAVE (Web Accessibility Evaluation Tool)

3. **屏幕阅读器测试**:
- Windows: NVDA (免费), JAWS (付费)
- macOS: VoiceOver (内置)
- 移动端: TalkBack (Android), VoiceOver (iOS)

4. **键盘测试**:
- 拔掉鼠标，仅使用键盘导航整个应用
- 检查焦点顺序是否合理
- 确认所有交互都可通过键盘完成

### Q3: 如何为图标按钮添加无障碍标签？

**A**:

```typescript
// 方法 1: 使用 aria-label
<Button
  icon={<SearchOutlined />}
  aria-label="Search"
  onClick={handleSearch}
/>

// 方法 2: 使用 sr-only 文本
<Button icon={<SearchOutlined />}>
  <span className="sr-only">Search</span>
</Button>

// 方法 3: 使用 Tooltip
<Tooltip title="Search">
  <Button icon={<SearchOutlined />} aria-label="Search" />
</Tooltip>
```

### Q4: Modal 关闭后焦点不返回怎么办？

**A**: 使用 `focusTriggerAfterClose` 属性：

```typescript
<Modal
  open={open}
  onOk={handleOk}
  onCancel={handleCancel}
  focusTriggerAfterClose // 确保关闭后焦点返回触发元素
>
  <p>Content</p>
</Modal>
```

### Q5: 如何处理动态内容更新的无障碍？

**A**: 使用 `aria-live` 区域：

```typescript
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  {loadingMessage}
</div>

// 紧急通知使用 aria-live="assertive"
<div
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
>
  {criticalError}
</div>
```

### Q6: Table 组件如何支持屏幕阅读器？

**A**: Ant Design Table 自动添加无障碍属性：

```typescript
<Table
  columns={columns}
  dataSource={data}
  // 自动生成:
  // - <caption> 表格标题
  // - aria-sort 排序状态
  // - aria-rowindex 行索引
  // - aria-colindex 列索引
  pagination={{
    showTotal: (total) => `Total ${total} items`,
  }}
/>
```

手动增强：

```typescript
<Table
  title={() => <h2>User List</h2>} // 提供标题
  columns={columns.map((col) => ({
    ...col,
    title: <span id={`col-${col.key}`}>{col.title}</span>,
    'aria-labelledby': `col-${col.key}`,
  }))}
  dataSource={data.map((row, index) => ({
    ...row,
    key: `row-${index}`,
  }))}
  rowKey="key"
/>
```

### Q7: 如何确保自定义颜色符合对比度要求？

**A**: 使用对比度计算工具：

```typescript
// 使用在线工具
// - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
// - Contrast Ratio: https://contrast-ratio.com/

// 或使用编程方式
function calculateContrastRatio(fg: string, bg: string): number {
  // 实现见上文"颜色对比度检测"章节
  const ratio = calculateContrastRatio('#1890ff', '#ffffff');
  console.log(`Ratio: ${ratio.toFixed(2)}:1`);
  console.log(`WCAG Level: ${getWCAGLevel(ratio)}`);
  // Output: Ratio: 4.52:1, WCAG Level: AA
}
```

### Q8: DatePicker 如何支持键盘导航？

**A**: Ant Design DatePicker 内置完整键盘支持：

```typescript
<DatePicker
  // 键盘快捷键:
  // - Arrow keys: 选择日期
  // - Page Up/Down: 切换月份
  // - Shift + Page Up/Down: 切换年份
  // - Home: 跳到本月第一天
  // - End: 跳到本月最后一天
  // - Enter: 确认选择
  // - Escape: 关闭面板
/>
```

### Q9: 如何为多语言应用添加无障碍？

**A**: 使用国际化库提供 ARIA 标签翻译：

```typescript
import { IntlProvider, useIntl } from 'react-intl';

const messages = {
  en: {
    searchLabel: 'Search',
    closeDialog: 'Close dialog',
    loadingStatus: 'Loading content...',
  },
  zh: {
    searchLabel: '搜索',
    closeDialog: '关闭对话框',
    loadingStatus: '正在加载内容...',
  },
};

function SearchButton() {
  const intl = useIntl();

  return (
    <Button
      icon={<SearchOutlined />}
      aria-label={intl.formatMessage({ id: 'searchLabel' })}
    />
  );
}

function App() {
  return (
    <IntlProvider locale="zh" messages={messages['zh']}>
      <SearchButton />
    </IntlProvider>
  );
}
```

### Q10: Upload 组件如何提供无障碍支持？

**A**:

```typescript
<Upload
  aria-label="Upload files"
  aria-describedby="upload-help"
  multiple
  onChange={handleChange}
>
  <Button icon={<UploadOutlined />}>Select files</Button>
</Upload>
<div id="upload-help">
  Accepted file types: JPG, PNG, PDF (Max size: 5MB)
</div>

// 进度通知
<Upload
  onProgress={(percent) => {
    // 使用 aria-live 区域通知进度
    setProgress(percent);
  }}
/>

<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  aria-label="Upload progress"
>
  Upload progress: {progress}%
</div>
```

## 无障碍检查清单

### 开发阶段

- [ ] 所有交互元素可键盘访问（Tab, Enter, Escape, Arrow keys）
- [ ] 焦点顺序符合逻辑
- [ ] 焦点指示器清晰可见（对比度 ≥ 3:1）
- [ ] 所有图片提供 alt 文本
- [ ] 图标按钮提供 aria-label
- [ ] 表单字段有明确标签
- [ ] 错误消息与字段关联（aria-errormessage）
- [ ] 颜色对比度符合 WCAG AA 标准（文本 ≥ 4.5:1）
- [ ] 不仅依赖颜色传达信息
- [ ] 模态框/对话框实现焦点陷阱
- [ ] 动态内容更新使用 aria-live 区域

### 测试阶段

- [ ] 键盘导航测试（拔掉鼠标测试）
- [ ] 屏幕阅读器测试（NVDA/JAWS/VoiceOver）
- [ ] 自动化测试（axe-core, jest-axe）
- [ ] Lighthouse Accessibility 评分 ≥ 90
- [ ] 高对比度模式测试
- [ ] 放大至 200% 测试
- [ ] 语音控制测试（语音输入）

### 上线前

- [ ] 多语言无障碍测试
- [ ] 跨浏览器测试（Chrome, Firefox, Safari, Edge）
- [ ] 移动端测试（iOS, Android）
- [ ] 真实用户测试（残障用户）
- [ ] 第三方无障碍审计

## 工具与资源

### 开发工具

1. **浏览器扩展**:
   - axe DevTools (Chrome/Firefox)
   - WAVE (Chrome/Firefox)
   - Accessibility Insights for Web (Chrome)
   - Lighthouse (Chrome 内置)

2. **屏幕阅读器**:
   - NVDA (Windows, 免费)
   - JAWS (Windows, 付费)
   - VoiceOver (macOS/iOS, 内置)
   - TalkBack (Android, 内置)

3. **自动化测试**:
   - jest-axe (React 测试)
   - @axe-core/react (集成测试)
   - pa11y (CI/CD 集成)

### 在线工具

- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Contrast Ratio: https://contrast-ratio.com/
- WAVE: https://wave.webaim.org/
- ARIA DevTools: https://www.tpgi.com/aria-devtools/

### 文档与规范

- WAI-ARIA 1.2: https://www.w3.org/TR/wai-aria-1.2/
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- Ant Design Accessibility: https://ant.design/docs/spec/accessibility
- React Accessibility: https://react.dev/learn/accessibility

## 总结

Ant Design 5.x 提供了完善的无障碍访问支持，通过以下方式构建包容性应用：

**核心能力**:
- 内置 WAI-ARIA 1.2 支持
- 完整的键盘导航
- 智能焦点管理
- 屏幕阅读器兼容
- 符合 WCAG 2.1 Level AA 标准

**开发原则**:
1. **语义优先**: 使用正确的 HTML 元素和 ARIA 属性
2. **键盘友好**: 确保所有功能可通过键盘访问
3. **焦点可见**: 提供清晰的焦点指示器
4. **多重指示**: 不仅依赖颜色传达信息
5. **测试驱动**: 使用自动化工具和真实用户测试

**最佳实践**:
- 优先使用 Ant Design 内置组件（已包含无障碍）
- 为自定义组件添加 ARIA 属性
- 实施焦点陷阱和焦点恢复
- 提供屏幕阅读器专用文本
- 确保颜色对比度符合标准
- 进行多维度无障碍测试

通过遵循本指南，可以构建出高质量、包容性强、符合国际标准的无障碍应用，让所有用户都能平等访问和使用您的产品。
