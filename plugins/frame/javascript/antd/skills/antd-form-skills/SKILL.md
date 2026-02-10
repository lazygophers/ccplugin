---
name: antd-form-skills
description: Ant Design 表单系统完整指南 - Form、验证、React Hook Form 集成、动态表单、复杂表单场景
---

# antd-form-skills - Ant Design 表单系统完整指南

## 概述

Ant Design Form 是一套高性能、功能强大的表单解决方案,提供数据采集、校验、提交等完整功能。它采用受控组件模式,支持复杂的表单场景,包括动态表单、跨字段验证、多步骤表单等,是企业级 React 应用的表单首选方案。

## 核心特性

- **声明式验证**: 通过 rules 配置验证规则,支持同步和异步验证
- **动态表单**: Form.List 支持动态增减表单项,轻松处理数组字段
- **类型安全**: 完整的 TypeScript 支持,提供类型推断
- **高性能**: 优化的重渲染机制,支持大表单场景
- **状态管理集成**: 可与 Redux、Zustand 等状态管理库无缝集成
- **灵活布局**: 支持水平、垂直、内联等多种布局模式
- **跨字段验证**: dependencies 和 shouldUpdate 实现字段联动和复杂验证
- **国际化支持**: 内置多语言错误提示

## 架构设计

### 核心组件

```
Form
├── Form                    # 表单容器
├── Form.Item              # 表单项容器
├── Form.List              # 动态表单数组
├── Form.ErrorList         # 错误列表
├── Form.Provider          # 跨组件表单上下文
├── useForm                # 表单实例 Hook
└── Form.useWatch          # 监听字段变化
```

### 表单实例 API

```typescript
interface FormInstance {
  // 获取/设置字段值
  getFieldValue: (name: NamePath) => StoreValue
  getFieldsValue: (nameList?: NamePath[] | true) => Store
  setFieldValue: (name: NamePath, value: StoreValue) => void
  setFieldsValue: (values: Partial<Store>) => void

  // 字段操作
  setFields: (fields: FieldData[]) => void
  resetFields: (fields?: NamePath[]) => void

  // 验证
  validateFields: (nameList?: NamePath[] | NamePath[][] | false) => Promise
  validateFields: (nameList: NamePath[], options: ValidateOptions) => Promise

  // 提交
  submit: () => void
  scrollToField: (name: NamePath, options?: ScrollOptions) => void

  // 状态
  getFieldsError: (nameList?: NamePath[]) => FieldError[]
  getFieldError: (name: NamePath) => string[]
  isFieldTouched: (name: NamePath) => boolean
  isFieldsTouched: (nameList?: NamePath[] | true, allFieldsTouched?: boolean) => boolean
  isFieldValidating: (name: NamePath) => boolean
}
```

## 基础用法

### 创建表单

```typescript
import { Form, Input, Button } from 'antd';
import type { FormInstance } from 'antd/es/form';

const BasicForm = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form
      form={form}
      onFinish={onFinish}
      onFinishFailed={(errorInfo) => {
        console.log('Failed:', errorInfo);
      }}
    >
      <Form.Item
        label="Username"
        name="username"
        rules={[{ required: true, message: 'Please input your username!' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Password"
        name="password"
        rules={[{ required: true, message: 'Please input your password!' }]}
      >
        <Input.Password />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

### 表单布局

```typescript
import { Form, Input, Button, Select, Radio } from 'antd';

const LayoutExample = () => {
  const [form] = Form.useForm();

  return (
    <>
      {/* 水平布局 (默认) */}
      <Form
        form={form}
        layout="horizontal"
        labelCol={{ span: 4 }}
        wrapperCol={{ span: 20 }}
      >
        <Form.Item label="Horizontal" name="field1">
          <Input />
        </Form.Item>
      </Form>

      {/* 垂直布局 */}
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item label="Vertical" name="field2">
          <Input />
        </Form.Item>
      </Form>

      {/* 内联布局 */}
      <Form
        form={form}
        layout="inline"
      >
        <Form.Item label="Inline1" name="field3">
          <Input />
        </Form.Item>
        <Form.Item label="Inline2" name="field4">
          <Input />
        </Form.Item>
      </Form>
    </>
  );
};
```

### 初始化表单值

```typescript
import { Form, Input, Button, DatePicker } from 'antd';
import { useEffect } from 'react';

const InitialValuesForm = () => {
  const [form] = Form.useForm();

  // 方式1: 使用 initialValues 属性
  const initialValues = {
    username: 'john',
    email: 'john@example.com',
    age: 30,
    birthDate: null,
  };

  // 方式2: 使用 setFieldsValue 方法
  useEffect(() => {
    // 异步加载数据后设置表单值
    setTimeout(() => {
      form.setFieldsValue({
        username: 'jane',
        email: 'jane@example.com',
      });
    }, 1000);
  }, []);

  const onReset = () => {
    form.resetFields(); // 重置为 initialValues
  };

  return (
    <Form
      form={form}
      initialValues={initialValues}
      onFinish={(values) => console.log(values)}
    >
      <Form.Item label="Username" name="username">
        <Input />
      </Form.Item>

      <Form.Item label="Email" name="email">
        <Input />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
        <Button htmlType="button" onClick={onReset} style={{ marginLeft: 8 }}>
          Reset
        </Button>
      </Form.Item>
    </Form>
  );
};
```

## Form.Item 验证

### 内置验证规则

```typescript
import { Form, Input } from 'antd';

const ValidationRules = () => {
  return (
    <Form>
      {/* 必填验证 */}
      <Form.Item
        label="Required"
        name="required"
        rules={[{ required: true, message: 'This field is required' }]}
      >
        <Input />
      </Form.Item>

      {/* 长度验证 */}
      <Form.Item
        label="Min Length"
        name="minLength"
        rules={[
          { required: true },
          { min: 6, message: 'Must be at least 6 characters' }
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Max Length"
        name="maxLength"
        rules={[
          { required: true },
          { max: 20, message: 'Must be at most 20 characters' }
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Exact Length"
        name="exactLength"
        rules={[
          { required: true },
          { len: 11, message: 'Must be exactly 11 characters' }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 类型验证 */}
      <Form.Item
        label="Email"
        name="email"
        rules={[
          { required: true },
          { type: 'email', message: 'Invalid email format' }
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Number"
        name="number"
        rules={[
          { required: true },
          { type: 'number', message: 'Must be a number' }
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="URL"
        name="url"
        rules={[
          { required: true },
          { type: 'url', message: 'Invalid URL format' }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 正则验证 */}
      <Form.Item
        label="Phone"
        name="phone"
        rules={[
          { required: true },
          { pattern: /^1[3-9]\d{9}$/, message: 'Invalid phone number' }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 数值范围 */}
      <Form.Item
        label="Age"
        name="age"
        rules={[
          { required: true },
          { type: 'number', min: 18, max: 65, message: 'Age must be between 18 and 65' }
        ]}
      >
        <Input type="number" />
      </Form.Item>

      {/* 空白字符验证 */}
      <Form.Item
        label="Username"
        name="username"
        rules={[
          { required: true },
          { whitespace: true, message: 'Username cannot be empty spaces' }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 枚举验证 */}
      <Form.Item
        label="Type"
        name="type"
        rules={[
          { required: true },
          { type: 'enum', enum: ['admin', 'user'], message: 'Must be admin or user' }
        ]}
      >
        <Input />
      </Form.Item>
    </Form>
  );
};
```

### 自定义验证器

```typescript
import { Form, Input } from 'antd';

const CustomValidator = () => {
  return (
    <Form>
      {/* 同步自定义验证 */}
      <Form.Item
        label="Username"
        name="username"
        rules={[
          { required: true },
          {
            validator: (_, value) => {
              if (!value) {
                return Promise.resolve();
              }
              if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(value)) {
                return Promise.reject(new Error('Username must start with letter and contain only letters, numbers, and underscores'));
              }
              if (value.length < 4 || value.length > 20) {
                return Promise.reject(new Error('Username must be between 4 and 20 characters'));
              }
              return Promise.resolve();
            }
          }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 异步验证 */}
      <Form.Item
        label="Email"
        name="email"
        rules={[
          { required: true, type: 'email' },
          {
            validator: async (_, value) => {
              if (!value) {
                return;
              }
              // 模拟 API 检查邮箱是否已注册
              await new Promise((resolve) => setTimeout(resolve, 1000));
              const isExists = await checkEmailExists(value);
              if (isExists) {
                throw new Error('This email is already registered');
              }
            }
          }
        ]}
      >
        <Input />
      </Form.Item>

      {/* 跨字段验证 */}
      <Form.Item
        label="Password"
        name="password"
        rules={[
          { required: true, min: 8 },
          {
            validator: (_, value) => {
              if (!value) {
                return Promise.resolve();
              }
              if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
                return Promise.reject(new Error('Password must contain uppercase, lowercase, and number'));
              }
              return Promise.resolve();
            }
          }
        ]}
      >
        <Input.Password />
      </Form.Item>

      <Form.Item
        label="Confirm Password"
        name="confirmPassword"
        dependencies={['password']}
        rules={[
          { required: true },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('Passwords do not match'));
            }
          })
        ]}
      >
        <Input.Password />
      </Form.Item>
    </Form>
  );
};

// 模拟 API
async function checkEmailExists(email: string): Promise<boolean> {
  // 实际应用中调用真实 API
  return email === 'existing@example.com';
}
```

### 验证触发时机

```typescript
import { Form, Input } from 'antd';

const ValidationTrigger = () => {
  return (
    <Form>
      {/* onChange 触发 (默认) */}
      <Form.Item
        label="onChange"
        name="field1"
        validateTrigger="onChange"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>

      {/* onBlur 触发 */}
      <Form.Item
        label="onBlur"
        name="field2"
        validateTrigger="onBlur"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>

      {/* 多触发时机 */}
      <Form.Item
        label="onChange + onBlur"
        name="field3"
        validateTrigger={['onChange', 'onBlur']}
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>

      {/* 手动触发 */}
      <Form.Item
        label="Manual"
        name="field4"
        rules={[{ required: true }]}
        validateTrigger={[]} // 禁用自动触发
      >
        <Input />
      </Form.Item>
    </Form>
  );
};
```

## 动态表单

### Form.List 基础用法

```typescript
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

const DynamicForm = () => {
  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.List name="users">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'first']}
                  rules={[{ required: true, message: 'Missing first name' }]}
                >
                  <Input placeholder="First Name" style={{ width: 150 }} />
                </Form.Item>

                <Form.Item
                  {...restField}
                  name={[name, 'last']}
                  rules={[{ required: true, message: 'Missing last name' }]}
                >
                  <Input placeholder="Last Name" style={{ width: 150 }} />
                </Form.Item>

                <MinusCircleOutlined onClick={() => remove(name)} />
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
  );
};
```

### 带默认值的动态表单

```typescript
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

const DynamicFormWithDefaults = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form
      form={form}
      onFinish={onFinish}
      initialValues={{
        users: [{ first: 'John', last: 'Doe' }]
      }}
    >
      <Form.List name="users">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'first']}
                  rules={[{ required: true, message: 'Missing first name' }]}
                >
                  <Input placeholder="First Name" />
                </Form.Item>

                <Form.Item
                  {...restField}
                  name={[name, 'last']}
                  rules={[{ required: true, message: 'Missing last name' }]}
                >
                  <Input placeholder="Last Name" />
                </Form.Item>

                <MinusCircleOutlined onClick={() => remove(name)} />
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
  );
};
```

### 嵌套动态表单

```typescript
import { Form, Input, Button, Space, Select } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

const NestedDynamicForm = () => {
  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form onFinish={onFinish}>
      <Form.List name="projects">
        {(projectFields, { add: addProject, remove: removeProject }) => (
          <>
            {projectFields.map(({ key: pKey, name: pName, ...pRestField }) => (
              <div key={pKey} style={{ marginBottom: 16, padding: 16, border: '1px solid #d9d9d9' }}>
                <h4>Project {pName + 1}</h4>

                <Form.Item
                  {...pRestField}
                  name={[pName, 'name']}
                  label="Project Name"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>

                {/* 嵌套的动态表单 */}
                <Form.Item label="Team Members">
                  <Form.List name={[pName, 'members']}>
                    {(memberFields, { add: addMember, remove: removeMember }) => (
                      <>
                        {memberFields.map(({ key: mKey, name: mName, ...mRestField }) => (
                          <Space key={mKey} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                            <Form.Item
                              {...mRestField}
                              name={[mName, 'name']}
                              rules={[{ required: true }]}
                            >
                              <Input placeholder="Member Name" style={{ width: 150 }} />
                            </Form.Item>

                            <Form.Item
                              {...mRestField}
                              name={[mName, 'role']}
                              rules={[{ required: true }]}
                            >
                              <Select placeholder="Select Role" style={{ width: 120 }}>
                                <Select.Option value="developer">Developer</Select.Option>
                                <Select.Option value="designer">Designer</Select.Option>
                                <Select.Option value="pm">PM</Select.Option>
                              </Select>
                            </Form.Item>

                            <MinusCircleOutlined onClick={() => removeMember(mName)} />
                          </Space>
                        ))}
                        <Button type="dashed" onClick={() => addMember()} block icon={<PlusOutlined />}>
                          Add Member
                        </Button>
                      </>
                    )}
                  </Form.List>
                </Form.Item>

                <Button danger onClick={() => removeProject(pName)}>
                  Remove Project
                </Button>
              </div>
            ))}
            <Button type="dashed" onClick={() => addProject()} block icon={<PlusOutlined />}>
              Add Project
            </Button>
          </>
        )}
      </Form.List>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

### 动态表单操作 - 移动、清空

```typescript
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const AdvancedDynamicForm = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.List name="items">
        {(fields, { add, remove, move }) => (
          <>
            {fields.map((field, index) => (
              <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  name={[field.name, 'name']}
                  rules={[{ required: true }]}
                >
                  <Input placeholder="Item Name" style={{ width: 200 }} />
                </Form.Item>

                {/* 移动操作 */}
                {index > 0 && (
                  <Button
                    type="text"
                    icon={<ArrowUpOutlined />}
                    onClick={() => move(index, index - 1)}
                  />
                )}
                {index < fields.length - 1 && (
                  <Button
                    type="text"
                    icon={<ArrowDownOutlined />}
                    onClick={() => move(index, index + 1)}
                  />
                )}

                <MinusCircleOutlined onClick={() => remove(field.name)} />
              </Space>
            ))}

            <Form.Item>
              <Space>
                <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />}>
                  Add Item
                </Button>
                <Button
                  type="dashed"
                  onClick={() => {
                    form.setFieldsValue({ items: [] });
                  }}
                  danger
                >
                  Clear All
                </Button>
              </Space>
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
  );
};
```

## 依赖字段和联动

### dependencies - 字段依赖验证

```typescript
import { Form, Input, Checkbox } from 'antd';

const DependenciesForm = () => {
  return (
    <Form>
      <Form.Item
        label="Enable Notifications"
        name="enableNotifications"
        valuePropName="checked"
      >
        <Checkbox />
      </Form.Item>

      <Form.Item
        label="Email"
        name="email"
        dependencies={['enableNotifications']}
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (getFieldValue('enableNotifications') && !value) {
                return Promise.reject(new Error('Email is required when notifications are enabled'));
              }
              return Promise.resolve();
            }
          })
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Enable SMS"
        name="enableSms"
        valuePropName="checked"
      >
        <Checkbox />
      </Form.Item>

      <Form.Item
        label="Phone"
        name="phone"
        dependencies={['enableSms']}
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (getFieldValue('enableSms') && !value) {
                return Promise.reject(new Error('Phone is required when SMS is enabled'));
              }
              return Promise.resolve();
            }
          })
        ]}
      >
        <Input />
      </Form.Item>
    </Form>
  );
};
```

### shouldUpdate - 条件渲染和验证

```typescript
import { Form, Input, Select, InputNumber } from 'antd';

const ShouldUpdateForm = () => {
  return (
    <Form>
      <Form.Item
        label="User Type"
        name="userType"
        rules={[{ required: true }]}
      >
        <Select>
          <Select.Option value="individual">Individual</Select.Option>
          <Select.Option value="company">Company</Select.Option>
        </Select>
      </Form.Item>

      {/* 根据 userType 显示不同字段 */}
      <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.userType !== currentValues.userType}>
        {({ getFieldValue }) => {
          const userType = getFieldValue('userType');
          if (userType === 'individual') {
            return (
              <Form.Item
                label="Full Name"
                name="fullName"
                rules={[{ required: true }]}
              >
                <Input />
              </Form.Item>
            );
          }
          if (userType === 'company') {
            return (
              <>
                <Form.Item
                  label="Company Name"
                  name="companyName"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  label="Tax ID"
                  name="taxId"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
              </>
            );
          }
          return null;
        }}
      </Form.Item>

      {/* 动态计算字段 */}
      <Form.Item label="Price" name="price" rules={[{ required: true }]}>
        <InputNumber style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item label="Quantity" name="quantity" rules={[{ required: true }]}>
        <InputNumber style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.price !== currentValues.price || prevValues.quantity !== currentValues.quantity}>
        {({ getFieldValue }) => {
          const price = getFieldValue('price') || 0;
          const quantity = getFieldValue('quantity') || 0;
          const total = price * quantity;
          return (
            <Form.Item label="Total">
              <Input value={total.toFixed(2)} disabled />
            </Form.Item>
          );
        }}
      </Form.Item>
    </Form>
  );
};
```

### 复杂联动表单

```typescript
import { Form, Input, Select, InputNumber, DatePicker, Radio } from 'antd';
import dayjs from 'dayjs';

const ComplexLinkedForm = () => {
  return (
    <Form>
      <Form.Item label="Country" name="country" rules={[{ required: true }]}>
        <Select>
          <Select.Option value="CN">China</Select.Option>
          <Select.Option value="US">United States</Select.Option>
          <Select.Option value="JP">Japan</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) => prevValues.country !== currentValues.country}
      >
        {({ getFieldValue }) => {
          const country = getFieldValue('country');
          if (country === 'CN') {
            return (
              <Form.Item
                label="Province"
                name="province"
                rules={[{ required: true }]}
              >
                <Select>
                  <Select.Option value="beijing">Beijing</Select.Option>
                  <Select.Option value="shanghai">Shanghai</Select.Option>
                  <Select.Option value="guangdong">Guangdong</Select.Option>
                </Select>
              </Form.Item>
            );
          }
          if (country === 'US') {
            return (
              <Form.Item
                label="State"
                name="state"
                rules={[{ required: true }]}
              >
                <Select>
                  <Select.Option value="ca">California</Select.Option>
                  <Select.Option value="ny">New York</Select.Option>
                  <Select.Option value="tx">Texas</Select.Option>
                </Select>
              </Form.Item>
            );
          }
          return null;
        }}
      </Form.Item>

      <Form.Item
        label="Start Date"
        name="startDate"
        rules={[{ required: true }]}
      >
        <DatePicker style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="Duration"
        name="duration"
        rules={[{ required: true }]}
      >
        <Select>
          <Select.Option value={30}>30 Days</Select.Option>
          <Select.Option value={90}>90 Days</Select.Option>
          <Select.Option value={180}>180 Days</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) =>
          prevValues.startDate !== currentValues.startDate ||
          prevValues.duration !== currentValues.duration
        }
      >
        {({ getFieldValue }) => {
          const startDate = getFieldValue('startDate');
          const duration = getFieldValue('duration');
          if (startDate && duration) {
            const endDate = dayjs(startDate).add(duration, 'day');
            return (
              <Form.Item label="End Date">
                <DatePicker value={endDate} disabled style={{ width: '100%' }} />
              </Form.Item>
            );
          }
          return null;
        }}
      </Form.Item>

      <Form.Item label="Payment Method" name="paymentMethod" rules={[{ required: true }]}>
        <Radio.Group>
          <Radio value="credit">Credit Card</Radio>
          <Radio value="paypal">PayPal</Radio>
          <Radio value="bank">Bank Transfer</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) => prevValues.paymentMethod !== currentValues.paymentMethod}
      >
        {({ getFieldValue }) => {
          const method = getFieldValue('paymentMethod');
          if (method === 'credit') {
            return (
              <Form.Item
                label="Card Number"
                name="cardNumber"
                rules={[{ required: true, len: 16 }]}
              >
                <Input placeholder="16-digit card number" />
              </Form.Item>
            );
          }
          if (method === 'paypal') {
            return (
              <Form.Item
                label="PayPal Email"
                name="paypalEmail"
                rules={[{ required: true, type: 'email' }]}
              >
                <Input placeholder="PayPal email address" />
              </Form.Item>
            );
          }
          if (method === 'bank') {
            return (
              <>
                <Form.Item
                  label="Bank Name"
                  name="bankName"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  label="Account Number"
                  name="accountNumber"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
              </>
            );
          }
          return null;
        }}
      </Form.Item>
    </Form>
  );
};
```

## 多步骤表单

### Steps + Form 组合

```typescript
import { Form, Input, Button, Steps, DatePicker, Select, Result } from 'antd';
import { useState } from 'react';
import dayjs from 'dayjs';

const { Step } = Steps;

const MultiStepForm = () => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [finished, setFinished] = useState(false);

  const steps = [
    {
      title: 'Account Information',
      content: (
        <>
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, min: 4, max: 20 }]}
          >
            <Input placeholder="Enter your username" />
          </Form.Item>
          <Form.Item
            label="Password"
            name="password"
            rules={[{ required: true, min: 8 }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>
          <Form.Item
            label="Confirm Password"
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match'));
                }
              })
            ]}
          >
            <Input.Password placeholder="Confirm your password" />
          </Form.Item>
        </>
      )
    },
    {
      title: 'Personal Information',
      content: (
        <>
          <Form.Item
            label="Full Name"
            name="fullName"
            rules={[{ required: true }]}
          >
            <Input placeholder="Enter your full name" />
          </Form.Item>
          <Form.Item
            label="Email"
            name="email"
            rules={[{ required: true, type: 'email' }]}
          >
            <Input placeholder="Enter your email" />
          </Form.Item>
          <Form.Item
            label="Phone"
            name="phone"
            rules={[{ required: true, pattern: /^1[3-9]\d{9}$/ }]}
          >
            <Input placeholder="Enter your phone number" />
          </Form.Item>
          <Form.Item
            label="Date of Birth"
            name="dob"
            rules={[{ required: true }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </>
      )
    },
    {
      title: 'Review & Submit',
      content: (
        <>
          <Form.Item noStyle shouldUpdate>
            {() => {
              const values = form.getFieldsValue();
              return (
                <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                  <p><strong>Username:</strong> {values.username}</p>
                  <p><strong>Full Name:</strong> {values.fullName}</p>
                  <p><strong>Email:</strong> {values.email}</p>
                  <p><strong>Phone:</strong> {values.phone}</p>
                  <p><strong>Date of Birth:</strong> {values.dob ? dayjs(values.dob).format('YYYY-MM-DD') : '-'}</p>
                </div>
              );
            }}
          </Form.Item>
        </>
      )
    }
  ];

  const next = async () => {
    try {
      if (current === steps.length - 1) {
        await form.validateFields();
        console.log('Form values:', form.getFieldsValue());
        setFinished(true);
      } else {
        await form.validateFields();
        setCurrent(current + 1);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const prev = () => {
    setCurrent(current - 1);
  };

  if (finished) {
    return (
      <Result
        status="success"
        title="Successfully Registered!"
        subTitle="Your account has been created. Please check your email to verify your account."
        extra={[
          <Button type="primary" key="home" onClick={() => {
            form.resetFields();
            setCurrent(0);
            setFinished(false);
          }}>
            Back Home
          </Button>
        ]}
      />
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Steps current={current} style={{ marginBottom: 24 }}>
        {steps.map((step, index) => (
          <Step key={index} title={step.title} />
        ))}
      </Steps>

      <Form form={form} layout="vertical">
        <div style={{ minHeight: 300 }}>
          {steps[current].content}
        </div>

        <div style={{ marginTop: 24 }}>
          {current > 0 && (
            <Button style={{ marginRight: 8 }} onClick={prev}>
              Previous
            </Button>
          )}
          {current < steps.length - 1 && (
            <Button type="primary" onClick={next}>
              Next
            </Button>
          )}
          {current === steps.length - 1 && (
            <Button type="primary" onClick={next}>
              Submit
            </Button>
          )}
        </div>
      </Form>
    </div>
  );
};
```

## React Hook Form 集成

### 使用 Controller 包装 Antd 组件

```typescript
import { Controller, useForm } from 'react-hook-form';
import { Form, Input, Button, Select } from 'antd';
import { useState } from 'react';

const ReactHookFormIntegration = () => {
  const [submitted, setSubmitted] = useState<any>(null);
  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      username: '',
      email: '',
      role: 'user'
    }
  });

  const onSubmit = (data: any) => {
    console.log('Form data:', data);
    setSubmitted(data);
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Form layout="vertical">
          <Controller
            name="username"
            control={control}
            rules={{
              required: 'Username is required',
              minLength: { value: 4, message: 'Username must be at least 4 characters' },
              maxLength: { value: 20, message: 'Username must be at most 20 characters' }
            }}
            render={({ field }) => (
              <Form.Item
                label="Username"
                validateStatus={errors.username ? 'error' : ''}
                help={errors.username?.message as string}
              >
                <Input {...field} placeholder="Enter username" />
              </Form.Item>
            )}
          />

          <Controller
            name="email"
            control={control}
            rules={{
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email format'
              }
            }}
            render={({ field }) => (
              <Form.Item
                label="Email"
                validateStatus={errors.email ? 'error' : ''}
                help={errors.email?.message as string}
              >
                <Input {...field} placeholder="Enter email" />
              </Form.Item>
            )}
          />

          <Controller
            name="role"
            control={control}
            rules={{ required: 'Role is required' }}
            render={({ field }) => (
              <Form.Item
                label="Role"
                validateStatus={errors.role ? 'error' : ''}
                help={errors.role?.message as string}
              >
                <Select {...field} placeholder="Select role">
                  <Select.Option value="admin">Admin</Select.Option>
                  <Select.Option value="user">User</Select.Option>
                  <Select.Option value="guest">Guest</Select.Option>
                </Select>
              </Form.Item>
            )}
          />

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Submit
            </Button>
          </Form.Item>
        </Form>
      </form>

      {submitted && (
        <div style={{ marginTop: 16, padding: 16, background: '#f0f0f0' }}>
          <h4>Submitted Data:</h4>
          <pre>{JSON.stringify(submitted, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

### 封装 FormItem 组件

```typescript
import { Controller, useForm, ControllerProps, FieldValues } from 'react-hook-form';
import { Form, Input, InputProps, Select, SelectProps } from 'antd';

// 通用 Input FormItem
type FormInputProps<T extends FieldValues> = {
  name: string;
  label?: string;
  control: Control<T>;
  rules?: ControllerProps<T>['rules'];
  inputProps?: InputProps;
};

function FormInput<T extends FieldValues>({
  name,
  label,
  control,
  rules,
  inputProps
}: FormInputProps<T>) {
  return (
    <Controller
      name={name as any}
      control={control}
      rules={rules}
      render={({ field, fieldState: { error } }) => (
        <Form.Item
          label={label}
          validateStatus={error ? 'error' : ''}
          help={error?.message}
        >
          <Input {...field} {...inputProps} />
        </Form.Item>
      )}
    />
  );
}

// 通用 Select FormItem
type FormSelectProps<T extends FieldValues> = {
  name: string;
  label?: string;
  control: Control<T>;
  rules?: ControllerProps<T>['rules'];
  selectProps?: SelectProps<any>;
  options: Array<{ value: string | number; label: string }>;
};

function FormSelect<T extends FieldValues>({
  name,
  label,
  control,
  rules,
  selectProps,
  options
}: FormSelectProps<T>) {
  return (
    <Controller
      name={name as any}
      control={control}
      rules={rules}
      render={({ field, fieldState: { error } }) => (
        <Form.Item
          label={label}
          validateStatus={error ? 'error' : ''}
          help={error?.message}
        >
          <Select {...field} {...selectProps}>
            {options.map(opt => (
              <Select.Option key={opt.value} value={opt.value}>
                {opt.label}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      )}
    />
  );
}

// 使用示例
const OptimizedRHFIntegration = () => {
  const { control, handleSubmit } = useForm({
    defaultValues: {
      username: '',
      email: '',
      role: 'user'
    }
  });

  const onSubmit = (data: any) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Form layout="vertical" style={{ maxWidth: 600 }}>
        <FormInput
          name="username"
          label="Username"
          control={control}
          rules={{ required: 'Username is required' }}
          inputProps={{ placeholder: 'Enter username' }}
        />

        <FormInput
          name="email"
          label="Email"
          control={control}
          rules={{
            required: 'Email is required',
            pattern: { value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i, message: 'Invalid email' }
          }}
          inputProps={{ placeholder: 'Enter email', type: 'email' }}
        />

        <FormSelect
          name="role"
          label="Role"
          control={control}
          rules={{ required: 'Role is required' }}
          options={[
            { value: 'admin', label: 'Admin' },
            { value: 'user', label: 'User' },
            { value: 'guest', label: 'Guest' }
          ]}
          selectProps={{ placeholder: 'Select role' }}
        />

        <button type="submit">Submit</button>
      </Form>
    </form>
  );
};
```

### React Hook Form + Antd Form 性能对比

```typescript
import { Form as AntdForm, Input, Button } from 'antd';
import { useForm, Controller } from 'react-hook-form';
import { renderCount } from './performance-utils';

// Antd Form 实现
const AntdFormImpl = () => {
  const [form] = AntdForm.useForm();

  const onFinish = (values: any) => {
    console.log(values);
  };

  renderCount('AntdForm');

  return (
    <AntdForm form={form} onFinish={onFinish}>
      <AntdForm.Item name="f1" rules={[{ required: true }]}>
        <Input />
      </AntdForm.Item>
      {/* 更多字段... */}
      <AntdForm.Item name="f100" rules={[{ required: true }]}>
        <Input />
      </AntdForm.Item>
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </AntdForm>
  );
};

// React Hook Form 实现
const RHFImpl = () => {
  const { control, handleSubmit } = useForm({
    defaultValues: Array.from({ length: 100 }, (_, i) => [`f${i + 1}`, ''])
    .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {})
  });

  const onSubmit = (values: any) => {
    console.log(values);
  };

  renderCount('RHF');

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {Array.from({ length: 100 }, (_, i) => (
        <Controller
          key={`f${i + 1}`}
          name={`f${i + 1}`}
          control={control}
          rules={{ required: true }}
          render={({ field }) => <Input {...field} />}
        />
      ))}
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </form>
  );
};

/*
性能对比结果:
- Antd Form: 所有字段共享状态,修改一个字段会触发布局更新,但优化了批量更新
- React Hook Form: 通过 ref 直接访问 DOM,最小化重渲染,性能更优
- 选择建议:
  - 小表单 (< 50 字段): Antd Form 更简单,性能足够
  - 大表单 (> 100 字段): React Hook Form 性能更好
  - 动态表单: React Hook Form 的性能优势更明显
*/
```

## 表单性能优化

### 大表单优化 - 按需渲染

```typescript
import { Form, Input, Button } from 'antd';
import { memo, useMemo } from 'react';

// 使用 memo 防止不必要的重渲染
const MemoizedFormItem = memo(({ name, label }: { name: string; label: string }) => {
  console.log(`Rendering ${name}`);
  return (
    <Form.Item name={name} label={label}>
      <Input />
    </Form.Item>
  );
});

const LargeFormOptimized = () => {
  const [form] = Form.useForm();

  // 使用 useMemo 缓存字段配置
  const fields = useMemo(() => {
    return Array.from({ length: 100 }, (_, i) => ({
      name: `field${i}`,
      label: `Field ${i}`
    }));
  }, []);

  const onFinish = (values: any) => {
    console.log(values);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      {fields.map((field) => (
        <MemoizedFormItem key={field.name} {...field} />
      ))}
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

### 使用 preserve 避免重渲染

```typescript
import { Form, Input, Button, Checkbox } from 'antd';

const PreserveForm = () => {
  const [form] = Form.useForm();

  return (
    <Form
      form={form}
      // preserve=false 时,字段卸载后会清除其状态
      // preserve=true (默认) 时,字段卸载后保留状态
      preserve={false}
    >
      <Form.Item name="field1">
        <Input />
      </Form.Item>

      <Form.Item noStyle shouldUpdate>
        {({ getFieldValue }) => {
          const showField2 = getFieldValue('showField2');
          return showField2 ? (
            <Form.Item name="field2">
              <Input />
            </Form.Item>
          ) : null;
        }}
      </Form.Item>

      <Form.Item name="showField2" valuePropName="checked">
        <Checkbox>Show Field 2</Checkbox>
      </Form.Item>
    </Form>
  );
};
```

### 虚拟滚动优化长列表表单

```typescript
import { Form, Input, Button } from 'antd';
import { FixedSizeList as List } from 'react-window';

const VirtualScrollForm = () => {
  const [form] = Form.useForm();
  const fieldCount = 1000;

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <Form.Item
        name={`field${index}`}
        label={`Field ${index}`}
        style={{ marginBottom: 16 }}
      >
        <Input />
      </Form.Item>
    </div>
  );

  return (
    <div style={{ height: 600 }}>
      <Form form={form}>
        <List
          height={600}
          itemCount={fieldCount}
          itemSize={80}
          width="100%"
        >
          {Row}
        </List>
        <Form.Item style={{ marginTop: 16 }}>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};
```

### 表单分片渲染

```typescript
import { Form, Input, Button } from 'antd';
import { useState, useEffect } from 'react';

const CHUNK_SIZE = 50; // 每次渲染的字段数

const ChunkedForm = () => {
  const [form] = Form.useForm();
  const [visibleCount, setVisibleCount] = useState(CHUNK_SIZE);
  const totalFields = 500;

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && visibleCount < totalFields) {
        setVisibleCount(prev => Math.min(prev + CHUNK_SIZE, totalFields));
      }
    });

    const sentinel = document.getElementById('sentinel');
    if (sentinel) {
      observer.observe(sentinel);
    }

    return () => observer.disconnect();
  }, [visibleCount, totalFields]);

  return (
    <Form form={form}>
      {Array.from({ length: visibleCount }, (_, i) => (
        <Form.Item key={i} name={`field${i}`} label={`Field ${i}`}>
          <Input />
        </Form.Item>
      ))}
      <div id="sentinel" style={{ height: 20 }} />
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

## 完整示例

### 用户注册表单

```typescript
import { Form, Input, Button, DatePicker, Select, Checkbox, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface RegisterFormValues {
  username: string;
  password: string;
  confirmPassword: string;
  email: string;
  phone: string;
  birthDate: dayjs.Dayjs;
  gender: 'male' | 'female' | 'other';
  country: string;
  agreement: boolean;
}

const UserRegisterForm = () => {
  const [form] = Form.useForm<RegisterFormValues>();

  const onFinish = async (values: RegisterFormValues) => {
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('Registration successful!');
      console.log('Form values:', values);
    } catch (error) {
      message.error('Registration failed. Please try again.');
    }
  };

  const validatePassword = async (_: unknown, value: string) => {
    if (!value) {
      return Promise.reject(new Error('Please input your password!'));
    }
    if (value.length < 8) {
      return Promise.reject(new Error('Password must be at least 8 characters!'));
    }
    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
      return Promise.reject(new Error('Password must contain uppercase, lowercase, and number!'));
    }
    return Promise.resolve();
  };

  return (
    <div style={{ maxWidth: 500, margin: '0 auto', padding: 24 }}>
      <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Create Account</h2>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        autoComplete="off"
      >
        <Form.Item
          label="Username"
          name="username"
          rules={[
            { required: true, message: 'Please input your username!' },
            { min: 4, message: 'Username must be at least 4 characters!' },
            { max: 20, message: 'Username must be at most 20 characters!' },
            {
              pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
              message: 'Username must start with letter and contain only letters, numbers, and underscores!'
            }
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="Enter username"
            size="large"
          />
        </Form.Item>

        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please input your email!' },
            { type: 'email', message: 'Invalid email format!' }
          ]}
        >
          <Input
            prefix={<MailOutlined />}
            placeholder="Enter email"
            size="large"
          />
        </Form.Item>

        <Form.Item
          label="Phone"
          name="phone"
          rules={[
            { required: true, message: 'Please input your phone number!' },
            { pattern: /^1[3-9]\d{9}$/, message: 'Invalid phone number!' }
          ]}
        >
          <Input
            prefix={<PhoneOutlined />}
            placeholder="Enter phone number"
            size="large"
          />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, validator: validatePassword }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Enter password"
            size="large"
          />
        </Form.Item>

        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Passwords do not match!'));
              }
            })
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Confirm password"
            size="large"
          />
        </Form.Item>

        <Form.Item
          label="Date of Birth"
          name="birthDate"
          rules={[{ required: true, message: 'Please select your date of birth!' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            size="large"
            disabledDate={(current) => current && current > dayjs().endOf('day')}
          />
        </Form.Item>

        <Form.Item
          label="Gender"
          name="gender"
          rules={[{ required: true, message: 'Please select your gender!' }]}
        >
          <Select size="large" placeholder="Select gender">
            <Select.Option value="male">Male</Select.Option>
            <Select.Option value="female">Female</Select.Option>
            <Select.Option value="other">Other</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Country"
          name="country"
          rules={[{ required: true, message: 'Please select your country!' }]}
        >
          <Select size="large" placeholder="Select country" showSearch>
            <Select.Option value="CN">China</Select.Option>
            <Select.Option value="US">United States</Select.Option>
            <Select.Option value="UK">United Kingdom</Select.Option>
            <Select.Option value="JP">Japan</Select.Option>
            <Select.Option value="KR">South Korea</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="agreement"
          valuePropName="checked"
          rules={[
            {
              validator: (_, value) =>
                value ? Promise.resolve() : Promise.reject(new Error('You must accept the terms and conditions!'))
            }
          ]}
        >
          <Checkbox>
            I have read and agree to the <a href="#">Terms and Conditions</a>
          </Checkbox>
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" size="large" block>
            Register
          </Button>
        </Form.Item>

        <div style={{ textAlign: 'center' }}>
          Already have an account? <a href="#">Login here</a>
        </div>
      </Form>
    </div>
  );
};
```

### 复杂配置表单

```typescript
import { Form, Input, InputNumber, Select, Switch, Button, Card, Space, message } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';

interface ConfigFormValues {
  appName: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retryCount: number;
  enableCache: boolean;
  cacheTTL: number;
  services: Array<{
    name: string;
    url: string;
    healthCheck: string;
    timeout: number;
  }>;
  advanced: {
    enableMetrics: boolean;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
    maxConnections: number;
  };
}

const ComplexConfigForm = () => {
  const [form] = Form.useForm<ConfigFormValues>();

  const onFinish = (values: ConfigFormValues) => {
    console.log('Config values:', values);
    message.success('Configuration saved successfully!');
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <h2 style={{ marginBottom: 24 }}>Application Configuration</h2>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          environment: 'development',
          timeout: 30,
          retryCount: 3,
          enableCache: true,
          cacheTTL: 3600,
          services: [{ name: 'api', url: 'https://api.example.com', healthCheck: '/health', timeout: 10 }],
          advanced: {
            enableMetrics: false,
            logLevel: 'info',
            maxConnections: 100
          }
        }}
      >
        {/* Basic Configuration */}
        <Card title="Basic Configuration" style={{ marginBottom: 16 }}>
          <Form.Item
            label="Application Name"
            name="appName"
            rules={[{ required: true, message: 'Please enter application name!' }]}
          >
            <Input placeholder="My Application" />
          </Form.Item>

          <Form.Item
            label="Environment"
            name="environment"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="development">Development</Select.Option>
              <Select.Option value="staging">Staging</Select.Option>
              <Select.Option value="production">Production</Select.Option>
            </Select>
          </Form.Item>

          <Space style={{ width: '100%' }}>
            <Form.Item
              label="Timeout (seconds)"
              name="timeout"
              rules={[{ required: true }]}
            >
              <InputNumber min={1} max={300} style={{ width: 150 }} />
            </Form.Item>

            <Form.Item
              label="Retry Count"
              name="retryCount"
              rules={[{ required: true }]}
            >
              <InputNumber min={0} max={10} style={{ width: 150 }} />
            </Form.Item>
          </Space>
        </Card>

        {/* Cache Configuration */}
        <Card title="Cache Configuration" style={{ marginBottom: 16 }}>
          <Form.Item
            label="Enable Cache"
            name="enableCache"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.enableCache !== curr.enableCache}>
            {({ getFieldValue }) =>
              getFieldValue('enableCache') ? (
                <Form.Item
                  label="Cache TTL (seconds)"
                  name="cacheTTL"
                  rules={[{ required: true }]}
                >
                  <InputNumber min={60} max={86400} style={{ width: 200 }} />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Card>

        {/* Services Configuration */}
        <Card title="Services" style={{ marginBottom: 16 }}>
          <Form.List name="services">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Card
                    key={key}
                    size="small"
                    style={{ marginBottom: 16 }}
                    extra={
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ cursor: 'pointer' }} />
                    }
                  >
                    <Form.Item
                      {...restField}
                      name={[name, 'name']}
                      label="Service Name"
                      rules={[{ required: true }]}
                    >
                      <Input placeholder="Service name" />
                    </Form.Item>

                    <Form.Item
                      {...restField}
                      name={[name, 'url']}
                      label="Service URL"
                      rules={[
                        { required: true },
                        { type: 'url', message: 'Invalid URL!' }
                      ]}
                    >
                      <Input placeholder="https://api.example.com" />
                    </Form.Item>

                    <Form.Item
                      {...restField}
                      name={[name, 'healthCheck']}
                      label="Health Check Path"
                      rules={[{ required: true }]}
                    >
                      <Input placeholder="/health" />
                    </Form.Item>

                    <Form.Item
                      {...restField}
                      name={[name, 'timeout']}
                      label="Timeout (seconds)"
                      rules={[{ required: true }]}
                    >
                      <InputNumber min={1} max={60} style={{ width: 150 }} />
                    </Form.Item>
                  </Card>
                ))}

                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  Add Service
                </Button>
              </>
            )}
          </Form.List>
        </Card>

        {/* Advanced Configuration */}
        <Card title="Advanced Configuration" style={{ marginBottom: 16 }}>
          <Form.Item
            label={['advanced', 'enableMetrics']}
            name={['advanced', 'enableMetrics']}
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label={['advanced', 'logLevel']}
            name={['advanced', 'logLevel']}
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="debug">Debug</Select.Option>
              <Select.Option value="info">Info</Select.Option>
              <Select.Option value="warn">Warn</Select.Option>
              <Select.Option value="error">Error</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label={['advanced', 'maxConnections']}
            name={['advanced', 'maxConnections']}
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={1000} style={{ width: 200 }} />
          </Form.Item>
        </Card>

        {/* Actions */}
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Save Configuration
            </Button>
            <Button onClick={() => form.resetFields()}>
              Reset
            </Button>
            <Button
              onClick={() => {
                const values = form.getFieldsValue();
                console.log('Current values:', values);
                message.info('Check console for current values');
              }}
            >
              Debug Values
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
};
```

### 问卷表单

```typescript
import { Form, Input, Radio, Rate, Button, Card, Space, message, Progress } from 'antd';
import { useState } from 'react';

interface SurveyValues {
  satisfaction: number;
  recommend: number;
  features: string[];
  improvement: string;
  contact: string;
}

const SurveyForm = () => {
  const [form] = Form.useForm<SurveyValues>();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const questions = [
    {
      title: 'Overall Satisfaction',
      name: 'satisfaction',
      type: 'rate',
      question: 'How satisfied are you with our service?',
      required: true
    },
    {
      title: 'NPS Score',
      name: 'recommend',
      type: 'rate',
      question: 'How likely are you to recommend us to a friend or colleague?',
      required: true,
      max: 10
    },
    {
      title: 'Feature Usage',
      name: 'features',
      type: 'checkbox',
      question: 'Which features do you use most? (Select all that apply)',
      options: ['Dashboard', 'Reports', 'Analytics', 'Integrations', 'Mobile App', 'API']
    },
    {
      title: 'Improvement Suggestions',
      name: 'improvement',
      type: 'textarea',
      question: 'What can we do to improve our service?',
      required: false
    },
    {
      title: 'Contact Information',
      name: 'contact',
      type: 'input',
      question: 'Would you like us to follow up with you? (Optional)',
      placeholder: 'Email or phone number'
    }
  ];

  const currentQuestion = questions[currentStep];
  const progress = ((currentStep + 1) / questions.length) * 100;

  const next = async () => {
    try {
      await form.validateFields([currentQuestion.name as any]);
      if (currentStep < questions.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        await submitSurvey();
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const prev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const submitSurvey = async () => {
    setLoading(true);
    try {
      const values = form.getFieldsValue();
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Survey submitted:', values);
      message.success('Thank you for your feedback!');
      form.resetFields();
      setCurrentStep(0);
    } catch (error) {
      message.error('Failed to submit survey. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderQuestion = () => {
    switch (currentQuestion.type) {
      case 'rate':
        return (
          <Form.Item
            name={currentQuestion.name as any}
            rules={[{ required: currentQuestion.required }]}
          >
            <Rate
              count={currentQuestion.max || 5}
              style={{ fontSize: 32 }}
              character={currentQuestion.max === 10 ? '' : '★'}
            />
          </Form.Item>
        );

      case 'checkbox':
        return (
          <Form.Item
            name={currentQuestion.name as any}
            rules={[{ required: currentQuestion.required, type: 'array', min: 1 }]}
          >
            <Radio.Group>
              <Space direction="vertical">
                {currentQuestion.options!.map((option) => (
                  <Radio key={option} value={option}>
                    {option}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </Form.Item>
        );

      case 'textarea':
        return (
          <Form.Item
            name={currentQuestion.name as any}
            rules={[{ required: currentQuestion.required }]}
          >
            <Input.TextArea rows={4} placeholder="Your feedback..." />
          </Form.Item>
        );

      case 'input':
        return (
          <Form.Item
            name={currentQuestion.name as any}
            rules={[{ required: currentQuestion.required }]}
          >
            <Input placeholder={currentQuestion.placeholder} size="large" />
          </Form.Item>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 24 }}>
      <Card>
        <h2 style={{ textAlign: 'center', marginBottom: 8 }}>Customer Satisfaction Survey</h2>
        <Progress percent={progress} showInfo={false} style={{ marginBottom: 24 }} />

        <Form form={form} layout="vertical">
          <div style={{ minHeight: 200 }}>
            <h3 style={{ marginBottom: 16 }}>
              Question {currentStep + 1} of {questions.length}
            </h3>
            <p style={{ fontSize: 16, marginBottom: 24 }}>{currentQuestion.question}</p>
            {renderQuestion()}
          </div>

          <div style={{ marginTop: 32, textAlign: 'right' }}>
            <Space>
              {currentStep > 0 && (
                <Button onClick={prev}>
                  Previous
                </Button>
              )}
              <Button
                type="primary"
                onClick={next}
                loading={loading}
              >
                {currentStep === questions.length - 1 ? 'Submit' : 'Next'}
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
};
```

## 最佳实践

### 1. 表单结构设计

```typescript
// ✅ 推荐: 按功能模块分组
const GoodFormStructure = () => (
  <Form>
    {/* 基础信息 */}
    <Card title="Basic Information">
      <Form.Item name="username" />
      <Form.Item name="email" />
    </Card>

    {/* 详细信息 */}
    <Card title="Details">
      <Form.Item name="bio" />
      <Form.Item name="website" />
    </Card>
  </Form>
);

// ❌ 不推荐: 扁平化所有字段
const BadFormStructure = () => (
  <Form>
    <Form.Item name="username" />
    <Form.Item name="email" />
    <Form.Item name="bio" />
    <Form.Item name="website" />
  </Form>
);
```

### 2. 验证规则组织

```typescript
// ✅ 推荐: 集中管理验证规则
const validationRules = {
  username: [
    { required: true, message: 'Username is required' },
    { min: 4, message: 'Username must be at least 4 characters' },
    { max: 20, message: 'Username must be at most 20 characters' }
  ],
  email: [
    { required: true, message: 'Email is required' },
    { type: 'email' as const, message: 'Invalid email format' }
  ]
};

// ❌ 不推荐: 在每个 Form.Item 中重复定义
```

### 3. 类型安全

```typescript
// ✅ 推荐: 使用 TypeScript 定义表单数据类型
interface FormData {
  username: string;
  email: string;
  age: number;
}

const TypedForm = () => {
  const [form] = Form.useForm<FormData>();
  // form 的方法都会自动推断类型
};

// ❌ 不推荐: 使用 any
const UntypedForm = () => {
  const [form] = Form.useForm<any>(); // 失去类型检查
};
```

### 4. 错误处理

```typescript
// ✅ 推荐: 详细的错误提示
<Form.Item
  name="email"
  rules={[
    { required: true, message: 'Email is required' },
    { type: 'email', message: 'Please enter a valid email address' }
  ]}
>
  <Input />
</Form.Item>

// ❌ 不推荐: 模糊的错误提示
<Form.Item
  name="email"
  rules={[{ required: true, message: 'Invalid input' }]}
>
  <Input />
</Form.Item>
```

### 5. 性能优化

```typescript
// ✅ 推荐: 使用 shouldUpdate 精确控制更新
<Form.Item noStyle shouldUpdate={(prev, curr) => prev.type !== curr.type}>
  {({ getFieldValue }) => {
    const type = getFieldValue('type');
    return type === 'special' ? <SpecialField /> : null;
  }}
</Form.Item>

// ❌ 不推荐: 使用 shouldUpdate 无条件更新
<Form.Item noStyle shouldUpdate>
  {({ getFieldValue }) => <SomeComponent />}
</Form.Item>
```

## 参考资源

### 官方文档
- [Ant Design Form 组件](https://ant.design/components/form/) - 官方 Form 组件文档
- [Ant Design Form 表单 (中文)](https://ant.design/components/form-cn/) - 中文文档
- [ProForm - ProComponents](https://procomponents.ant.design/en-US/components/form/) - 高级表单组件

### 相关文章
- [AntD Form Validation With ReactJS - Medium](https://medium.com/@iamsurajdev/antd-form-validation-with-reactjs-d08b65f12f7d)
- [Custom Form Validation - Refine.dev](https://refine.dev/docs/3.xx.xx/examples/form/antd/custom-form-validation/) (2024)
- [告别繁琐!Ant Design动态表单Form.List完全指南](https://blog.csdn.net/gitblog_01163/article/details/152105083) (中文)
- [Building Dynamic Forms in Ant Design - Medium](https://medium.com/@anjaskpkd/building-dynamic-forms-in-ant-design-antd-with-react-a-practical-guide-50c3341f8ae3)
- [如何在Ant Design 中使用React Hook Form?](https://juejin.cn/post/7222484074480713783) (中文)
- [Ant Design性能调优终极指南](https://blog.csdn.net/gitblog_01148/article/details/152345304) (中文)
- [Virtual Table - Ant Design Blog](https://ant.design/docs/blog/virtual-table/) - 虚拟滚动优化
- [Unnecessary Rerender - Ant Design Blog](https://ant.design/docs/blog/render-times/) - 渲染性能优化

### GitHub Issues
- [Form validation isFormValid #15674](https://github.com/ant-design/ant-design/issues/15674)
- [Virtual Scroll problem #52308](https://github.com/ant-design/ant-design/discussions/52308)
- [Two validation messages shown for InputNumber #51075](https://github.com/ant-design/ant-design/issues/51075)

### 工具和库
- [react-hook-form](https://react-hook-form.com/) - 高性能表单库
- [react-window](https://github.com/bvaughn/react-window) - 虚拟滚动库

### 示例和代码
- [AntD Form List - CodeSandbox](https://codesandbox.io/s/antd-form-list-multiple-formitem-dynamic-fields-forked-c9ohm) - 交互式动态表单示例
- [How to Create Dynamic Forms in React CRUD app - Refine](https://refine.dev/blog/react-crud-app-with-dynamic-form-ant-design/) (2024)

## 注意事项

1. **Form.Item name 属性**: Form.Item 必须设置 name 属性才能参与表单验证和提交
2. **字段命名规范**: 建议使用 camelCase 命名,与 JavaScript 对象保持一致
3. **initialValues 与 resetFields**: resetFields 会重置为 initialValues,而不是清空
4. **异步验证**: 异步验证器必须返回 Promise,通过 reject 触发错误
5. **跨字段验证**: 使用 dependencies 声明依赖字段,避免闭包陷阱
6. **动态表单性能**: Form.List 中使用 key 属性优化渲染性能
7. **shouldUpdate 使用**: 谨慎使用 shouldUpdate,避免不必要的重渲染
8. **表单实例复用**: 不要在多个表单之间共享同一个 form 实例
9. **时间组件**: DatePicker 返回 dayjs 对象,提交前可能需要格式化
10. **数值组件**: InputNumber 返回 number 类型,注意处理 undefined 和 null
