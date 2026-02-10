---
name: antd-migration-skills
description: Ant Design 版本迁移完整指南 - 4.x 到 5.x 迁移、破坏性变更、兼容性处理
---

# antd-migration: Ant Design 版本迁移完整指南

Ant Design 5.0 是一个重要的版本升级，引入了 CSS-in-JS 技术栈、全新的主题系统、性能优化等多个重大变更。本指南提供完整的迁移路径，帮助您从 Ant Design 4.x 平滑升级到 5.x。

---

## 概述

### 迁移必要性

- **性能提升**：5.x 使用 CSS-in-JS，按需生成样式，体积更小、加载更快
- **主题系统重构**：全新的 Design Token 系统，主题定制更灵活
- **更好的 TypeScript 支持**：类型定义更完善
- **长期维护**：4.x 已停止维护，5.x 是当前稳定版本
- **新特性**：如 App 组件、更好的暗色模式支持等

### 版本差异对比

| 特性 | Ant Design 4.x | Ant Design 5.x |
|------|---------------|---------------|
| 样式方案 | Less + CSS Modules | CSS-in-JS (@ant-design/cssinjs) |
| 主题定制 | 修改 Less 变量 | Design Token |
| 图标 | 内置图标库 | 独立包 @ant-design/icons |
| Form 表单 | `validator` 返回 `Promise` | 保持不变 |
| DatePicker | 使用 moment | 默认使用 dayjs |
| 组件 API | 部分废弃 | 更简洁的 API |
| 性能 | 全量样式（~3MB） | 按需样式（~500KB） |
| 暗色模式 | 需要额外配置 | 内置算法 |

---

## 特性列表

### 核心变更

- **CSS-in-JS**：使用 `@ant-design/cssinjs` 替代 Less
- **Design Token**：全新的主题系统
- **独立图标包**：图标从主包分离
- **日期库切换**：默认使用 dayjs（可选 moment）
- **App 组件**：统一管理全局方法
- **性能优化**：按需加载、Tree Shaking

### 移除功能

- **Less 变量定制**：不再支持修改 Less 变量
- **旧版 Form API**：`getFieldDecorator` 等
- **部分组件**：BackTop、Comment 等
- **IE 支持**：不再支持 IE 浏览器

### 新增功能

- **主题算法**：`theme.defaultAlgorithm`、`theme.darkAlgorithm`、`theme.compactAlgorithm`
- **`theme.useToken()` Hook**：组件内访问主题 Token
- **App.useApp() Hook**：访问全局方法
- **更好的 TypeScript 支持**：更精确的类型推断

---

## 主要变更

### 1. CSS-in-JS

#### 变更说明

Ant Design 5.x 使用 CSS-in-JS 技术替代 Less，样式在运行时动态生成。

#### 4.x 方式（Less）

```tsx
// ❌ 4.x - 需要导入样式文件
import 'antd/dist/antd.css';
import { Button } from 'antd';

function App() {
  return <Button type="primary">Button</Button>;
}
```

#### 5.x 方式（CSS-in-JS）

```tsx
// ✅ 5.x - 无需导入样式文件
import { Button } from 'antd';

function App() {
  return <Button type="primary">Button</Button>;
}
```

#### 影响

- **体积减少**：不再需要全量导入 CSS 文件
- **定制方式变更**：通过 ConfigProvider 的 theme 属性定制
- **SSR 支持**：需要额外配置（参考 SSR 章节）

### 2. 组件 API 变更

#### 移除的 API

| 组件 | 移除 API | 替代方案 |
|------|---------|---------|
| Form | `getFieldDecorator` | 使用 `<Form.Item>` 的 `name` 属性 |
| Form | `getFieldValue` | `Form.useForm()` 的 `getFieldValue` |
| Form | `setFieldsValue` | `Form.useForm()` 的 `setFieldsValue` |
| DatePicker | `defaultValue` (moment) | 使用 `dayjs` |
| DatePicker | `moment` 对象 | 使用 `dayjs` 对象 |

#### 新增的 API

| 组件 | 新增 API | 说明 |
|------|---------|------|
| Form | `variant` | 支持 `outlined`、`filled`、`borderless` |
| Input | `variant` | 统一的风格变体 |
| Button | - | 保持不变 |

#### 4.x 到 5.x 表单迁移示例

**4.x 写法（已废弃）：**

```tsx
// ❌ 4.x - 旧版 Form API
import { Form, Input, Button } from 'antd';

const { getFieldDecorator } = Form;

function OldForm() {
  const handleSubmit = (e) => {
    e.preventDefault();
    // 获取表单值
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Item>
        {getFieldDecorator('username', {
          rules: [{ required: true, message: 'Please input username!' }],
        })(<Input placeholder="Username" />)}
      </Form.Item>

      <Form.Item>
        {getFieldDecorator('password', {
          rules: [{ required: true, message: 'Please input password!' }],
        })(<Input.Password placeholder="Password" />)}
      </Form.Item>

      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}
```

**5.x 写法（推荐）：**

```tsx
// ✅ 5.x - 新版 Form API
import { Form, Input, Button } from 'antd';

function NewForm() {
  const [form] = Form.useForm();

  const handleSubmit = (values) => {
    console.log('Form values:', values);
  };

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      layout="vertical"
    >
      <Form.Item
        label="Username"
        name="username"
        rules={[{ required: true, message: 'Please input username!' }]}
      >
        <Input placeholder="Username" />
      </Form.Item>

      <Form.Item
        label="Password"
        name="password"
        rules={[{ required: true, message: 'Please input password!' }]}
      >
        <Input.Password placeholder="Password" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
}
```

### 3. 图标库分离

#### 变更说明

Ant Design 5.x 不再内置图标库，需要单独安装 `@ant-design/icons` 包。

#### 4.x 方式（内置图标）

```tsx
// ❌ 4.x - 图标内置在主包
import { Button, Icon } from 'antd';
import { UserOutlined } from '@ant-design/icons';

function App() {
  return (
    <Button icon={<UserOutlined />}>
      Click me
    </Button>
  );
}
```

#### 5.x 方式（独立包）

```tsx
// ✅ 5.x - 需要单独导入图标
import { Button } from 'antd';
import { UserOutlined } from '@ant-design/icons';

function App() {
  return (
    <Button icon={<UserOutlined />}>
      Click me
    </Button>
  );
}
```

#### 图标迁移步骤

1. **安装图标包**：

```bash
npm install @ant-design/icons
# 或
yarn add @ant-design/icons
# 或
pnpm add @ant-design/icons
```

2. **更新导入路径**：

```tsx
// ❌ 旧方式
import { Icon } from 'antd';

// ✅ 新方式
import { UserOutlined } from '@ant-design/icons';
```

3. **按需引入图标**：

```tsx
// ✅ 推荐 - 只导入需要的图标
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';

// ❌ 不推荐 - 导入所有图标（体积大）
// import * as Icons from '@ant-design/icons';
```

#### 图标组件映射

| 4.x | 5.x |
|-----|-----|
| `<Icon type="user" />` | `<UserOutlined />` |
| `<Icon type="lock" />` | `<LockOutlined />` |
| `<Icon type="mail" />` | `<MailOutlined />` |
| `<Icon type="search" />` | `<SearchOutlined />` |

### 4. 移除的组件

以下组件在 5.x 中被移除：

| 组件 | 移除原因 | 替代方案 |
|------|---------|---------|
| `BackTop` | 功能简单 | 自己实现或使用第三方库 |
| `Comment` | 使用场景少 | 使用 Card + 自定义布局 |
| `ConfigProvider.IconProvider` | 图标库分离 | 使用 `@ant-design/icons` |
| `Statistic.Countdown` | 功能重复 | 使用 dayjs 的倒计时 |

#### BackTop 替代方案

```tsx
// ✅ 5.x - 自己实现 BackTop
import { useState, useEffect } from 'react';
import { FloatButton } from 'antd';

function BackTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > 400);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <FloatButton.BackTop
      onClick={scrollToTop}
      visibilityHeight={400}
    />
  );
}
```

---

## 破坏性变更详解

### 1. Form 表单变更

#### 破坏性变更

- **`getFieldDecorator` 完全移除**：必须使用 `<Form.Item name="...">`
- **表单实例获取方式变更**：从 `props.form` 改为 `Form.useForm()`
- **验证规则位置变更**：从 `getFieldDecorator` 的 `rules` 迁移到 `Form.Item`

#### 完整迁移示例

**4.x 代码：**

```tsx
// ❌ 4.x Form
import React from 'react';
import { Form, Input, Button, Select } from 'antd';

const { Option } = Select;

class UserForm extends React.Component {
  handleSubmit = (e) => {
    e.preventDefault();
    this.props.form.validateFields((err, values) => {
      if (!err) {
        console.log('Received values of form: ', values);
      }
    });
  };

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit} layout="vertical">
        <Form.Item label="Username">
          {getFieldDecorator('username', {
            rules: [{ required: true, message: 'Please input username!' }],
          })(<Input />)}
        </Form.Item>

        <Form.Item label="Email">
          {getFieldDecorator('email', {
            rules: [
              { required: true, message: 'Please input email!' },
              { type: 'email', message: 'Invalid email!' },
            ],
          })(<Input />)}
        </Form.Item>

        <Form.Item label="Role">
          {getFieldDecorator('role', {
            initialValue: 'user',
          })(
            <Select>
              <Option value="admin">Admin</Option>
              <Option value="user">User</Option>
            </Select>
          )}
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>
      </Form>
    );
  }
}

const WrappedUserForm = Form.create({ name: 'user_form' })(UserForm);
```

**5.x 迁移后代码：**

```tsx
// ✅ 5.x Form
import React from 'react';
import { Form, Input, Button, Select } from 'antd';

const { Option } = Select;

function UserForm() {
  const [form] = Form.useForm();

  const handleSubmit = (values) => {
    console.log('Received values of form: ', values);
  };

  const handleFailed = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      onFinishFailed={handleFailed}
      layout="vertical"
      initialValues={{
        role: 'user',
      }}
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
          { type: 'email', message: 'Invalid email!' },
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Role"
        name="role"
      >
        <Select>
          <Option value="admin">Admin</Option>
          <Option value="user">User</Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
}
```

### 2. Table 表格变更

#### 破坏性变更

- **`rowSelection` 类型变更**：`selectedRowKeys` 现在必须明确指定
- **`pagination` 默认值变更**：默认 `false`（4.x 是 `true`）
- **`columns.render` 签名变更**：参数顺序调整

#### 4.x 到 5.x 迁移示例

**4.x 代码：**

```tsx
// ❌ 4.x Table
import { Table } from 'antd';

function UserTable({ data }) {
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
      render: (text, record, index) => {
        return text;
      },
    },
  ];

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="id"
      pagination
    />
  );
}
```

**5.x 代码：**

```tsx
// ✅ 5.x Table
import { Table } from 'antd';

function UserTable({ data }) {
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
      render: (value, record, index) => {
        return value;
      },
    },
  ];

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="id"
      pagination={{ pageSize: 10 }}
    />
  );
}
```

#### Table rowSelection 迁移

**4.x 代码：**

```tsx
// ❌ 4.x
const rowSelection = {
  onChange: (selectedRowKeys, selectedRows) => {
    console.log('selectedRows: ', selectedRows);
  },
};
```

**5.x 代码：**

```tsx
// ✅ 5.x
const [selectedRowKeys, setSelectedRowKeys] = useState([]);

const rowSelection = {
  selectedRowKeys,
  onChange: (newSelectedRowKeys, selectedRows) => {
    setSelectedRowKeys(newSelectedRowKeys);
    console.log('selectedRows: ', selectedRows);
  },
};

<Table rowSelection={rowSelection} ... />
```

### 3. DatePicker 变更

#### 破坏性变更

- **默认使用 dayjs**：不再内置 moment
- **`value` 和 `defaultValue` 类型变更**：从 `moment` 对象改为 `dayjs` 对象
- **需要手动配置 dayjs locale**：不再自动导入

#### 4.x 到 5.x 迁移示例

**4.x 代码（moment）：**

```tsx
// ❌ 4.x - 使用 moment
import { DatePicker } from 'antd';
import moment from 'moment';

function DateRangePicker() {
  const [dates, setDates] = useState([
    moment().subtract(7, 'days'),
    moment(),
  ]);

  return (
    <DatePicker.RangePicker
      value={dates}
      onChange={setDates}
      format="YYYY-MM-DD"
    />
  );
}
```

**5.x 代码（dayjs）：**

```tsx
// ✅ 5.x - 使用 dayjs
import { DatePicker } from 'antd';
import dayjs from 'dayjs';

function DateRangePicker() {
  const [dates, setDates] = useState([
    dayjs().subtract(7, 'days'),
    dayjs(),
  ]);

  return (
    <DatePicker.RangePicker
      value={dates}
      onChange={setDates}
      format="YYYY-MM-DD"
    />
  );
}
```

### 4. Modal 变更

#### 破坏性变更

- **`visible` 改为 `open`**：属性名称变更
- **`afterClose` 行为微调**：关闭动画结束后的回调时机

#### 4.x 到 5.x 迁移示例

**4.x 代码：**

```tsx
// ❌ 4.x Modal
import { Modal, Button } from 'antd';

function MyModal() {
  const [visible, setVisible] = useState(false);

  const showModal = () => setVisible(true);
  const handleCancel = () => setVisible(false);
  const handleOk = () => {
    console.log('OK');
    setVisible(false);
  };

  return (
    <>
      <Button onClick={showModal}>Open Modal</Button>
      <Modal
        title="Basic Modal"
        visible={visible}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <p>Modal content</p>
      </Modal>
    </>
  );
}
```

**5.x 代码：**

```tsx
// ✅ 5.x Modal
import { Modal, Button } from 'antd';

function MyModal() {
  const [open, setOpen] = useState(false);

  const showModal = () => setOpen(true);
  const handleCancel = () => setOpen(false);
  const handleOk = () => {
    console.log('OK');
    setOpen(false);
  };

  return (
    <>
      <Button onClick={showModal}>Open Modal</Button>
      <Modal
        title="Basic Modal"
        open={open}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <p>Modal content</p>
      </Modal>
    </>
  );
}
```

### 5. Menu 变更

#### 破坏性变更

- **`selectedKeys` 和 `defaultSelectedKeys` 类型严格化**：必须是字符串数组
- **`openKeys` 行为微调**：受控模式下需要完全控制

#### 4.x 到 5.x 迁移示例

**4.x 代码：**

```tsx
// ❌ 4.x Menu
import { Menu } from 'antd';

const { SubMenu } = Menu;

function MyMenu() {
  return (
    <Menu
      defaultSelectedKeys={['1']}
      defaultOpenKeys={['sub1']}
      mode="inline"
    >
      <SubMenu key="sub1" title="Navigation One">
        <Menu.Item key="1">Option 1</Menu.Item>
        <Menu.Item key="2">Option 2</Menu.Item>
      </SubMenu>
    </Menu>
  );
}
```

**5.x 代码：**

```tsx
// ✅ 5.x Menu
import { Menu } from 'antd';

function MyMenu() {
  const items = [
    {
      key: 'sub1',
      label: 'Navigation One',
      children: [
        { key: '1', label: 'Option 1' },
        { key: '2', label: 'Option 2' },
      ],
    },
  ];

  return (
    <Menu
      defaultSelectedKeys={['1']}
      defaultOpenKeys={['sub1']}
      mode="inline"
      items={items}
    />
  );
}
```

### 6. Select 变更

#### 破坏性变更

- **`optionLabelProp` 行为调整**：在某些场景下需要显式指定
- **`showSearch` 行为优化**：搜索逻辑更加智能

#### 4.x 到 5.x 迁移示例

**4.x 代码：**

```tsx
// ❌ 4.x Select
import { Select } from 'antd';

const { Option } = Select;

function UserSelect() {
  return (
    <Select
      placeholder="Select user"
      showSearch
      optionFilterProp="children"
    >
      <Option value="jack">Jack</Option>
      <Option value="lucy">Lucy</Option>
      <Option value="tom">Tom</Option>
    </Select>
  );
}
```

**5.x 代码：**

```tsx
// ✅ 5.x Select
import { Select } from 'antd';

function UserSelect() {
  const options = [
    { value: 'jack', label: 'Jack' },
    { value: 'lucy', label: 'Lucy' },
    { value: 'tom', label: 'Tom' },
  ];

  return (
    <Select
      placeholder="Select user"
      showSearch
      options={options}
      filterOption={(input, option) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
      }
    />
  );
}
```

---

## 迁移步骤

### 第一步：升级前准备

#### 1.1 备份代码

```bash
# 创建备份分支
git checkout -b backup/antd-4.x
git push origin backup/antd-4.x

# 创建迁移分支
git checkout -b feature/antd-5-migration
```

#### 1.2 检查当前依赖

```bash
# 查看 antd 版本
npm list antd

# 检查是否有 less 相关依赖
npm list less less-loader

# 检查是否有 @ant-design/icons
npm list @ant-design/icons
```

#### 1.3 评估迁移范围

**检查清单：**

- [ ] 统计使用 `getFieldDecorator` 的表单数量
- [ ] 检查是否自定义了 Less 变量
- [ ] 检查日期选择器是否使用了 moment
- [ ] 检查图标导入方式
- [ ] 检查 Modal 的 `visible` 属性
- [ ] 检查是否使用了移除的组件

### 第二步：安装新版本

#### 2.1 卸载旧版本

```bash
# npm
npm uninstall antd

# yarn
yarn remove antd

# pnpm
pnpm remove antd
```

#### 2.2 安装 Ant Design 5.x

```bash
# npm
npm install antd@^5.0.0

# yarn
yarn add antd@^5.0.0

# pnpm
pnpm add antd@^5.0.0
```

#### 2.3 安装依赖包

```bash
# 安装图标包
npm install @ant-design/icons

# 如果使用 dayjs（推荐）
npm install dayjs

# 如果需要继续使用 moment
npm install moment
```

### 第三步：代码修改

#### 3.1 更新样式导入

**全局搜索并替换：**

```typescript
// ❌ 删除所有 antd 样式导入
import 'antd/dist/antd.css';
import 'antd/dist/antd.min.css';

// ✅ 5.x 无需导入样式文件
// 直接删除这些导入即可
```

**批量查找命令：**

```bash
# 查找所有导入 antd 样式的文件
grep -r "antd/dist/antd" src/
```

#### 3.2 迁移图标

**批量替换工具：**

```bash
# 使用 antd-migration-helper
antd-migration-helper icons ./src
```

#### 3.3 迁移 Form 表单

**步骤：**

1. 将 `getFieldDecorator` 迁移到 `Form.Item name`
2. 使用 `Form.useForm()` 替代 `Form.create()`
3. 更新表单提交逻辑

#### 3.4 迁移 DatePicker

**步骤：**

1. 安装 dayjs
2. 更新所有 `moment` 导入为 `dayjs`
3. 更新日期格式化逻辑

#### 3.5 迁移 Modal

**批量替换：**

```bash
# 搜索: visible=
# 替换为: open=
```

#### 3.6 迁移主题定制

**4.x Less 变量方式：**

```less
// ❌ 4.x - 不再支持
@import '~antd/lib/style/themes/default.less';
@primary-color: #1890ff;
```

**5.x Design Token 方式：**

```tsx
// ✅ 5.x - 使用 ConfigProvider
import { ConfigProvider } from 'antd';

<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
    },
  }}
>
  <App />
</ConfigProvider>
```

### 第四步：测试验证

#### 4.1 单元测试

**更新测试用例：**

```typescript
// ✅ 5.x 测试
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should submit form', async () => {
  const user = userEvent.setup();
  render(<UserForm />);

  await user.type(screen.getByLabelText('Username'), 'test');
  await user.click(screen.getByRole('button', { name: /submit/i }));
});
```

#### 4.2 手动测试清单

- [ ] 所有表单可以正常提交和验证
- [ ] 日期选择器显示正确的日期
- [ ] Modal 可以正常打开和关闭
- [ ] Table 分页和排序正常
- [ ] 所有图标正确显示
- [ ] 主题定制正常工作
- [ ] 国际化正常工作

---

## 常见迁移场景

### 场景 1：主题定制迁移

#### 4.x Less 定制

```less
// global.less
@import '~antd/lib/style/themes/default.less';

@primary-color: #722ed1;
@link-color: #722ed1;
@border-radius-base: 4px;
```

#### 5.x Design Token 定制

```tsx
// App.tsx
import { ConfigProvider, theme } from 'antd';

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#722ed1',
          colorLink: '#722ed1',
          borderRadius: 4,
        },
      }}
    >
      <YourApp />
    </ConfigProvider>
  );
}
```

### 场景 2：图标迁移

#### 批量图标迁移

使用查找替换：

```bash
# 查找所有 Icon type 属性
grep -r "Icon type=" src/

# 手动替换为新图标
# <Icon type="user" /> -> <UserOutlined />
```

### 场景 3：Form 表单迁移

参考前面的"破坏性变更详解 - Form 表单变更"章节。

### 场景 4：ConfigProvider 迁移

#### 4.x 到 5.x ConfigProvider

**4.x 基础配置：**

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/lib/locale-provider/zh_CN';

<ConfigProvider locale={zhCN}>
  <App />
</ConfigProvider>
```

**5.x 配置：**

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

<ConfigProvider locale={zhCN}>
  <App />
</ConfigProvider>
```

**路径变更：**

```tsx
// ❌ 4.x
import zhCN from 'antd/lib/locale-provider/zh_CN';

// ✅ 5.x
import zhCN from 'antd/locale/zh_CN';
```

---

## 兼容性处理

### 降级方案

#### 方案 1：保持 4.x（不推荐）

如果暂时无法迁移，可以继续使用 4.x：

```bash
npm install antd@^4.24.0
```

**注意：** 4.x 已停止维护，建议尽快迁移。

#### 方案 2：渐进式迁移

分模块逐步迁移：

```tsx
// 阶段 1：升级到 5.x，但保持兼容模式
import { ConfigProvider } from 'antd';

// 阶段 2：逐个模块迁移
// 优先迁移影响小的模块

// 阶段 3：完全迁移到 5.x
```

### 临时兼容包

#### @ant-design/compatible

提供临时的兼容性支持：

```bash
npm install @ant-design/compatible
```

**使用示例：**

```tsx
import { Alert } from '@ant-design/compatible';

// 使用 4.x 的 API
<Alert message="Warning" type="warning" closable />
```

**注意：** 该包仅用于过渡，不应长期依赖。

---

## 自动迁移工具

### codemod

Ant Design 提供了官方 codemod 脚本：

#### 安装

```bash
npm install -g jscodeshift
```

#### 使用

```bash
# 1. 克隆 codemod 仓库
git clone https://github.com/ant-design/antd-codemod.git
cd antd-codemod

# 2. 运行迁移脚本
# Form 表单迁移
npx jscodeshift -t transforms/form.js ./src

# Modal 属性迁移
npx jscodeshift -t transforms/modal.js ./src

# 图标迁移
npx jscodeshift -t transforms/icons.js ./src
```

---

## 最佳实践

### 1. 迁移策略

**✅ 推荐**：分阶段迁移

```
阶段 1: 升级依赖 + 修复编译错误
阶段 2: 迁移 Form 表单
阶段 3: 迁移 DatePicker
阶段 4: 迁移主题定制
阶段 5: 测试和优化
```

**❌ 避免**：一次性大规模重构

### 2. 代码质量

**✅ 推荐**：使用 TypeScript

```tsx
interface UserFormValues {
  username: string;
  email: string;
  age?: number;
}

function UserForm() {
  const [form] = Form.useForm<UserFormValues>();

  const onFinish = (values: UserFormValues) => {
    console.log(values);
  };

  return <Form form={form} onFinish={onFinish}>...</Form>;
}
```

**❌ 避免**：大量使用 `any`

### 3. 性能优化

**✅ 推荐**：按需导入组件

```tsx
// ✅ 推荐 - 按需导入
import { Button, Input } from 'antd';

// ❌ 避免 - 导入所有
import * as antd from 'antd';
```

### 4. 测试覆盖

**✅ 推荐**：高测试覆盖率

```tsx
it('should submit form with correct values', async () => {
  const onSubmit = jest.fn();
  const { getByLabelText, getByRole } = render(<UserForm onSubmit={onSubmit} />);

  await userEvent.type(getByLabelText('Username'), 'test');
  await userEvent.click(getByRole('button', { name: /submit/i }));

  expect(onSubmit).toHaveBeenCalledWith({ username: 'test' });
});
```

**❌ 避免**：缺少测试

---

## 常见问题（Q&A）

### Q1: 升级后样式完全丢失？

**A:** 检查以下几点：

1. 确认已删除所有 `import 'antd/dist/antd.css'`
2. 检查是否有全局样式覆盖
3. 确认使用的是 5.x 版本

```tsx
// 检查版本
console.log(antd.version); // 应该显示 5.x.x
```

### Q2: 表单验证不工作？

**A:** 确保正确使用了 `rules`：

```tsx
// ✅ 正确
<Form.Item
  name="username"
  rules={[{ required: true, message: 'Required' }]}
>
  <Input />
</Form.Item>

// ❌ 错误
<Form.Item name="username">
  <Input rules={[{ required: true }]} />
</Form.Item>
```

### Q3: 图标不显示？

**A:** 确保正确导入图标：

```tsx
// ✅ 正确
import { UserOutlined } from '@ant-design/icons';
<UserOutlined />

// ❌ 错误
import { Icon } from 'antd';
<Icon type="user" />
```

### Q4: DatePicker 报错 "dayjs is not defined"？

**A:** 安装并导入 dayjs：

```bash
npm install dayjs
```

```tsx
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';

dayjs.extend(customParseFormat);
```

### Q5: 主题定制不生效？

**A:** 检查 ConfigProvider 配置：

```tsx
// ✅ 正确
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
    },
  }}
>
  <App />
</ConfigProvider>
```

### Q6: 如何在 SSR 中使用？

**A:** 参考 SSR 官方文档：

```tsx
import { StyleProvider } from '@ant-design/cssinjs';

export function render(req, res) {
  const html = ReactDOM.renderToString(
    <StyleProvider cache={extractedCache}>
      <App />
    </StyleProvider>
  );

  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        ${extractedCache.toHtml()}
      </head>
      <body>${html}</body>
    </html>
  `);
}
```

### Q7: 迁移后体积变大了？

**A:** 检查以下几点：

1. 确保开启了 Tree Shaking
2. 使用 `import { Button } from 'antd'` 而不是 `import antd from 'antd'`
3. 检查是否有重复导入

### Q8: Modal.method() 如何获取 Context？

**A:** 使用 App.useApp() Hook：

```tsx
import { App, Button } from 'antd';

function MyComponent() {
  const { modal } = App.useApp();

  const showConfirm = () => {
    modal.confirm({
      title: 'Confirm',
      content: '...',
    });
  };

  return <Button onClick={showConfirm}>Show Modal</Button>;
}
```

---

## 参考资源

### 官方文档

- [Ant Design 5.0 升级指南](https://ant.design/docs/react/migration-v5-cn)
- [Ant Design 官方文档](https://ant.design/index-cn)
- [主题定制文档](https://ant.design/docs/react/customize-theme-cn)
- [组件 API 文档](https://ant.design/components/overview-cn/)

### 迁移工具

- [antd-codemod](https://github.com/ant-design/antd-codemod) - 官方代码迁移工具
- [@ant-design/compatible](https://www.npmjs.com/package/@ant-design/compatible) - 临时兼容包

### 社区资源

- [Ant Design 讨论区](https://github.com/ant-design/ant-design/discussions)
- [Stack Overflow - ant-design](https://stackoverflow.com/questions/tagged/ant-design)

### 相关技术

- [dayjs 文档](https://day.js.org/)
- [CSS-in-JS 文档](https://cssinjs.org/)
- [React 官方文档](https://react.dev/)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- dayjs >= 1.11.0（推荐）
- @ant-design/icons >= 4.0.0

---

## 迁移检查清单

### 准备阶段

- [ ] 备份当前代码
- [ ] 创建迁移分支
- [ ] 评估迁移范围
- [ ] 阅读官方迁移指南

### 依赖升级

- [ ] 卸载 antd 4.x
- [ ] 安装 antd 5.x
- [ ] 安装 @ant-design/icons
- [ ] 安装 dayjs
- [ ] 卸载 Less（如果不再需要）

### 代码修改

- [ ] 删除 `import 'antd/dist/antd.css'`
- [ ] 迁移所有图标导入
- [ ] 迁移 Form 组件
- [ ] 迁移 DatePicker
- [ ] 迁移 Modal.visible → Modal.open
- [ ] 迁移主题定制
- [ ] 更新 ConfigProvider 路径

### 测试验证

- [ ] 运行单元测试
- [ ] 手动测试所有表单
- [ ] 测试日期选择器
- [ ] 测试 Modal 和弹窗
- [ ] 测试主题切换
- [ ] 性能测试
- [ ] 视觉回归测试

### 上线准备

- [ ] 更新 CHANGELOG
- [ ] 更新文档
- [ ] Code Review
- [ ] 灰度发布
- [ ] 监控错误日志

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
**版本**: 1.0.0
