---
name: antd-validation-skills
description: Ant Design 数据验证完整指南 - 表单验证规则、自定义验证器、异步验证、跨字段验证、错误处理
---

# Ant Design 数据验证完整指南

## 概述

Ant Design Form 组件提供了强大且灵活的数据验证机制，基于 [rc-field-form](https://github.com/react-component/field-form) 实现，支持声明式验证规则、自定义验证器、异步验证、跨字段验证等高级特性。

## 核心特性

- **声明式验证**: 通过 rules 数组配置验证规则
- **内置验证器**: 提供常用验证规则（required、type、pattern、len 等）
- **自定义验证器**: 支持同步和异步验证函数
- **跨字段验证**: 支持依赖其他字段的验证逻辑
- **动态表单验证**: Form.List 支持动态增减表单项的验证
- **异步验证**: 支持 Promise 返回的异步验证
- **国际化支持**: 可自定义错误消息和国际化
- **错误处理**: 完善的错误状态管理和展示

## 架构设计

### 验证流程

```
用户输入 → validateTrigger 触发 → rules 验证 → validator 自定义验证 → 错误收集 → 错误显示
```

### 核心组件

```
antd-validation/
├── 内置验证规则              # 基础验证规则
├── 自定义验证器              # validator 函数
├── 跨字段验证                # dependencies 依赖验证
├── 异步验证                  # Promise 验证
├── 动态表单验证              # Form.List 验证
└── 错误处理                  # 错误状态和消息
```

### 验证规则类型

```typescript
interface Rule {
  // 验证触发时机
  validateTrigger?: string | string[];

  // 必填验证
  required?: boolean;

  // 类型验证
  type?: 'string' | 'number' | 'boolean' | 'method' | 'regexp' | 'integer' | 'float' |
        'array' | 'object' | 'enum' | 'date' | 'url' | 'hex' | 'email';

  // 长度验证
  min?: number;
  max?: number;
  len?: number;

  // 枚举验证
  enum?: any[];

  // 正则验证
  pattern?: RegExp;

  // 自定义验证器
  validator?: (rule: Rule, value: any) => Promise<void> | void;

  // 错误消息
  message?: string;

  // 白名单验证（只验证指定字段）
  whitespace?: boolean;
}
```

## 内置验证规则

### 1. required - 必填验证

**最基础的验证规则**，确保字段不为空：

```typescript
import { Form, Input } from 'antd';

<Form.Item
  name="username"
  rules={[{ required: true, message: '请输入用户名' }]}
>
  <Input placeholder="用户名" />
</Form.Item>

// 可选字段（不需要 required）
<Form.Item
  name="nickname"
  rules={[{ message: '昵称格式不正确' }]}
>
  <Input placeholder="昵称（可选）" />
</Form.Item>
```

### 2. type - 类型验证

**验证数据类型**，支持多种内置类型：

```typescript
import { Form, Input, DatePicker } from 'antd';

// Email 类型
<Form.Item
  name="email"
  rules={[
    { type: 'email', message: '请输入有效的邮箱地址' }
  ]}
>
  <Input placeholder="邮箱" />
</Form.Item>

// URL 类型
<Form.Item
  name="website"
  rules={[
    { type: 'url', message: '请输入有效的 URL' }
  ]}
>
  <Input placeholder="个人网站" />
</Form.Item>

// 数字类型
<Form.Item
  name="age"
  rules={[
    { type: 'number', message: '年龄必须是数字', transform: (value) => Number(value) }
  ]}
>
  <Input type="number" placeholder="年龄" />
</Form.Item>

// 整数类型
<Form.Item
  name="count"
  rules={[
    { type: 'integer', message: '必须是整数' }
  ]}
>
  <InputNumber placeholder="数量" />
</Form.Item>

// 数组类型
<Form.Item
  name="tags"
  rules={[
    { type: 'array', message: '请选择标签' }
  ]}
>
  <Select mode="tags" placeholder="标签" />
</Form.Item>

// 枚举类型
<Form.Item
  name="status"
  rules={[
    {
      type: 'enum',
      enum: ['active', 'inactive', 'pending'],
      message: '状态值必须是 active、inactive 或 pending'
    }
  ]}
>
  <Select>
    <Select.Option value="active">激活</Select.Option>
    <Select.Option value="inactive">未激活</Select.Option>
    <Select.Option value="pending">待定</Select.Option>
  </Select>
</Form.Item>
```

### 3. pattern - 正则表达式验证

**使用正则表达式自定义验证格式**：

```typescript
// 手机号验证（中国大陆）
<Form.Item
  name="phone"
  rules={[
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入有效的手机号码'
    }
  ]}
>
  <Input placeholder="手机号" />
</Form.Item>

// 用户名验证（字母开头，4-20位字母数字下划线）
<Form.Item
  name="username"
  rules={[
    {
      pattern: /^[a-zA-Z][a-zA-Z0-9_]{3,19}$/,
      message: '用户名必须以字母开头，4-20位字母数字下划线'
    }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>

// 密码验证（至少8位，包含字母和数字）
<Form.Item
  name="password"
  rules={[
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/,
      message: '密码至少8位，必须包含字母和数字'
    }
  ]}
>
  <Input.Password placeholder="密码" />
</Form.Item>

// 身份证号验证
<Form.Item
  name="idCard"
  rules={[
    {
      pattern: /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/,
      message: '请输入有效的身份证号码'
    }
  ]}
>
  <Input placeholder="身份证号" />
</Form.Item>

// 邮编验证
<Form.Item
  name="postcode"
  rules={[
    {
      pattern: /^\d{6}$/,
      message: '请输入6位邮编'
    }
  ]}
>
  <Input placeholder="邮编" />
</Form.Item>
```

### 4. len / min / max - 长度验证

**验证字符串长度或数值范围**：

```typescript
// 固定长度
<Form.Item
  name="captcha"
  rules={[
    { required: true },
    { len: 6, message: '验证码必须是6位' }
  ]}
>
  <Input placeholder="验证码" />
</Form.Item>

// 最小长度
<Form.Item
  name="username"
  rules={[
    { required: true },
    { min: 4, message: '用户名至少4个字符' }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>

// 最大长度
<Form.Item
  name="description"
  rules={[
    { max: 200, message: '描述不能超过200个字符' }
  ]}
>
  <Input.TextArea placeholder="描述" />
</Form.Item>

// 长度范围
<Form.Item
  name="title"
  rules={[
    { required: true },
    { min: 5, message: '标题至少5个字符' },
    { max: 50, message: '标题不能超过50个字符' }
  ]}
>
  <Input placeholder="标题" />
</Form.Item>

// 数值范围（配合 type 使用）
<Form.Item
  name="age"
  rules={[
    { type: 'number' },
    { min: 18, message: '年龄必须大于等于18岁' },
    { max: 65, message: '年龄必须小于等于65岁' }
  ]}
>
  <InputNumber placeholder="年龄" />
</Form.Item>
```

### 5. whitespace - 空白字符验证

**验证是否只包含空白字符**：

```typescript
<Form.Item
  name="name"
  rules={[
    { required: true },
    { whitespace: true, message: '不能只包含空格' }
  ]}
>
  <Input placeholder="姓名" />
</Form.Item>

// 组合使用
<Form.Item
  name="content"
  rules={[
    { required: true, message: '内容不能为空' },
    { whitespace: true, message: '内容不能只包含空格' },
    { min: 10, message: '内容至少10个字符' }
  ]}
>
  <Input.TextArea placeholder="内容" />
</Form.Item>
```

### 6. enum - 枚举值验证

**验证值是否在指定的枚举列表中**：

```typescript
<Form.Item
  name="gender"
  rules={[
    {
      type: 'enum',
      enum: ['male', 'female', 'other'],
      message: '性别必须是 male、female 或 other'
    }
  ]}
>
  <Select placeholder="性别">
    <Select.Option value="male">男</Select.Option>
    <Select.Option value="female">女</Select.Option>
    <Select.Option value="other">其他</Select.Option>
  </Select>
</Form.Item>

// 数值枚举
<Form.Item
  name="level"
  rules={[
    {
      type: 'enum',
      enum: [1, 2, 3, 4, 5],
      message: '等级必须是 1-5 之间的整数'
    }
  ]}
>
  <InputNumber placeholder="等级" />
</Form.Item>
```

### 7. message - 自定义错误消息

**每个验证规则都可以自定义错误消息**：

```typescript
<Form.Item
  name="email"
  rules={[
    { required: true, message: '邮箱是必填项' },
    { type: 'email', message: '邮箱格式不正确，例如：user@example.com' },
    { max: 100, message: '邮箱长度不能超过100个字符' }
  ]}
>
  <Input placeholder="邮箱" />
</Form.Item>

// 全局错误消息配置
const validateMessages = {
  required: '${label}是必填项',
  types: {
    email: '${label}格式不正确',
    number: '${label}必须是数字',
  },
  string: {
    min: '${label}至少${min}个字符',
    max: '${label}不能超过${max}个字符',
  },
};

<Form
  validateMessages={validateMessages}
>
  <Form.Item
    label="邮箱"
    name="email"
    rules={[{ required: true, type: 'email' }]}
  >
    <Input />
  </Form.Item>
</Form>
```

## 自定义验证器

### 1. 同步验证器

**使用 `validator` 函数实现自定义验证逻辑**：

```typescript
import { Form, Input, Button } from 'antd';

// 自定义验证器：检查用户名是否已存在
const checkUsername = async (rule: Rule, value: string) => {
  if (!value) {
    return Promise.reject('请输入用户名');
  }

  // 模拟同步验证
  const forbiddenNames = ['admin', 'root', 'system'];
  if (forbiddenNames.includes(value)) {
    return Promise.reject('该用户名不允许使用');
  }

  return Promise.resolve();
};

<Form.Item
  name="username"
  rules={[
    { required: true },
    { validator: checkUsername }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>
```

### 2. 异步验证器

**支持异步验证，例如检查数据库或 API**：

```typescript
// 异步验证：检查用户名是否已被注册
const checkUsernameExists = async (rule: Rule, value: string) => {
  if (!value) {
    return Promise.resolve();
  }

  try {
    // 模拟 API 请求
    const response = await fetch(`/api/check-username?username=${value}`);
    const data = await response.json();

    if (data.exists) {
      return Promise.reject('该用户名已被注册');
    }

    return Promise.resolve();
  } catch (error) {
    return Promise.reject('验证失败，请稍后重试');
  }
};

<Form.Item
  name="username"
  rules={[
    { required: true, message: '请输入用户名' },
    { validator: checkUsernameExists }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>
```

### 3. 验证规则组合

**多个验证规则可以组合使用**：

```typescript
// 组合使用内置规则和自定义验证器
<Form.Item
  name="password"
  rules={[
    // 内置规则
    { required: true, message: '请输入密码' },
    { min: 8, message: '密码至少8个字符' },
    { max: 32, message: '密码不能超过32个字符' },

    // 自定义验证器：检查密码强度
    {
      validator: async (rule, value) => {
        if (!value) return Promise.resolve();

        // 至少包含一个大写字母
        if (!/[A-Z]/.test(value)) {
          return Promise.reject('密码必须包含至少一个大写字母');
        }

        // 至少包含一个小写字母
        if (!/[a-z]/.test(value)) {
          return Promise.reject('密码必须包含至少一个小写字母');
        }

        // 至少包含一个数字
        if (!/\d/.test(value)) {
          return Promise.reject('密码必须包含至少一个数字');
        }

        // 至少包含一个特殊字符
        if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) {
          return Promise.reject('密码必须包含至少一个特殊字符');
        }

        return Promise.resolve();
      }
    }
  ]}
>
  <Input.Password placeholder="密码" />
</Form.Item>
```

### 4. 条件验证

**根据条件决定是否验证**：

```typescript
// 条件验证：根据用户类型决定是否需要企业名称
<Form.Item
  name="userType"
  rules={[{ required: true }]}
>
  <Select>
    <Select.Option value="personal">个人</Select.Option>
    <Select.Option value="enterprise">企业</Select.Option>
  </Select>
</Form.Item>

<Form.Item noStyle shouldUpdate={(prev, curr) => prev.userType !== curr.userType}>
  {({ getFieldValue }) => {
    const userType = getFieldValue('userType');

    if (userType === 'enterprise') {
      return (
        <Form.Item
          name="companyName"
          rules={[{ required: true, message: '企业用户必须填写企业名称' }]}
        >
          <Input placeholder="企业名称" />
        </Form.Item>
      );
    }

    return null;
  }}
</Form.Item>
```

## Form.Item 验证配置

### 1. rules 配置

**完整的 rules 配置示例**：

```typescript
<Form.Item
  name="email"
  label="邮箱"
  // 规则数组
  rules={[
    { required: true, message: '邮箱是必填项' },
    { type: 'email', message: '邮箱格式不正确' },
    { max: 100, message: '邮箱长度不能超过100个字符' }
  ]}
  // 验证触发时机
  validateTrigger="onChange"
  // 验证状态
  validateStatus="error"
  // 帮助文本
  help="用于登录和接收通知"
>
  <Input placeholder="请输入邮箱" />
</Form.Item>
```

### 2. validateTrigger - 验证触发时机

**控制何时触发验证**：

```typescript
// onChange - 输入时验证（实时验证）
<Form.Item
  name="username"
  validateTrigger="onChange"
  rules={[{ required: true }]}
>
  <Input />
</Form.Item>

// onBlur - 失去焦点时验证
<Form.Item
  name="email"
  validateTrigger="onBlur"
  rules={[{ type: 'email' }]}
>
  <Input />
</Form.Item>

// 多个触发时机
<Form.Item
  name="password"
  validateTrigger={['onChange', 'onBlur']}
  rules={[{ required: true, min: 8 }]}
>
  <Input.Password />
</Form.Item>
```

### 3. validateStatus - 验证状态

**手动控制验证状态**：

```typescript
const [status, setStatus] = useState<'success' | 'warning' | 'error' | 'validating'>('');

<Form.Item
  name="field"
  validateStatus={status}
  help={status === 'error' ? '验证失败' : undefined}
>
  <Input />
</Form.Item>
```

### 4. help - 帮助文本

**显示额外的帮助信息**：

```typescript
<Form.Item
  name="password"
  rules={[{ required: true, min: 8 }]}
  help="密码至少8个字符，包含字母和数字"
>
  <Input.Password />
</Form.Item>

// 动态帮助文本
<Form.Item
  name="username"
  help={usernameError || '用户名将用于登录，请牢记'}
  validateStatus={usernameError ? 'error' : ''}
>
  <Input />
</Form.Item>
```

## 跨字段验证

### 1. dependencies - 依赖字段验证

**验证时获取其他字段的值**：

```typescript
// 示例1：密码确认验证
<Form.Item
  name="password"
  label="密码"
  rules={[{ required: true, min: 8 }]}
>
  <Input.Password />
</Form.Item>

<Form.Item
  name="confirmPassword"
  label="确认密码"
  dependencies={['password']}
  rules={[
    { required: true, message: '请确认密码' },
    ({ getFieldValue }) => ({
      validator(_, value) {
        if (!value || getFieldValue('password') === value) {
          return Promise.resolve();
        }
        return Promise.reject('两次输入的密码不一致');
      },
    }),
  ]}
>
  <Input.Password />
</Form.Item>

// 示例2：开始时间必须早于结束时间
<Form.Item
  name="startTime"
  label="开始时间"
  rules={[{ required: true }]}
>
  <DatePicker />
</Form.Item>

<Form.Item
  name="endTime"
  label="结束时间"
  dependencies={['startTime']}
  rules={[
    { required: true },
    ({ getFieldValue }) => ({
      validator(_, value) {
        const startTime = getFieldValue('startTime');
        if (!value || !startTime || value.isAfter(startTime)) {
          return Promise.resolve();
        }
        return Promise.reject('结束时间必须晚于开始时间');
      },
    }),
  ]}
>
  <DatePicker />
</Form.Item>

// 示例3：最小值必须小于最大值
<Form.Item
  name="minPrice"
  label="最低价格"
  rules={[{ required: true }]}
>
  <InputNumber />
</Form.Item>

<Form.Item
  name="maxPrice"
  label="最高价格"
  dependencies={['minPrice']}
  rules={[
    { required: true },
    ({ getFieldValue }) => ({
      validator(_, value) {
        const minPrice = getFieldValue('minPrice');
        if (!value || !minPrice || value > minPrice) {
          return Promise.resolve();
        }
        return Promise.reject('最高价格必须大于最低价格');
      },
    }),
  ]}
>
  <InputNumber />
</Form.Item>
```

### 2. shouldUpdate - 条件渲染和验证

**根据其他字段的变化动态显示/隐藏字段**：

```typescript
// 示例1：根据支付方式显示不同字段
<Form.Item
  name="paymentMethod"
  rules={[{ required: true }]}
>
  <Select placeholder="选择支付方式">
    <Select.Option value="alipay">支付宝</Select.Option>
    <Select.Option value="wechat">微信支付</Select.Option>
    <Select.Option value="bank">银行转账</Select.Option>
  </Select>
</Form.Item>

<Form.Item noStyle shouldUpdate={(prev, curr) => prev.paymentMethod !== curr.paymentMethod}>
  {({ getFieldValue }) => {
    const method = getFieldValue('paymentMethod');

    if (method === 'alipay') {
      return (
        <Form.Item
          name="alipayAccount"
          label="支付宝账号"
          rules={[{ required: true, message: '请输入支付宝账号' }]}
        >
          <Input placeholder="请输入支付宝账号" />
        </Form.Item>
      );
    }

    if (method === 'wechat') {
      return (
        <Form.Item
          name="wechatId"
          label="微信号"
          rules={[{ required: true, message: '请输入微信号' }]}
        >
          <Input placeholder="请输入微信号" />
        </Form.Item>
      );
    }

    if (method === 'bank') {
      return (
        <>
          <Form.Item
            name="bankName"
            label="银行名称"
            rules={[{ required: true, message: '请输入银行名称' }]}
          >
            <Input placeholder="如：中国工商银行" />
          </Form.Item>
          <Form.Item
            name="bankAccount"
            label="银行账号"
            rules={[{ required: true, message: '请输入银行账号' }]}
          >
            <Input placeholder="请输入银行账号" />
          </Form.Item>
        </>
      );
    }

    return null;
  }}
</Form.Item>

// 示例2：根据年龄判断是否需要监护人信息
<Form.Item
  name="age"
  label="年龄"
  rules={[{ required: true }]}
>
  <InputNumber />
</Form.Item>

<Form.Item noStyle shouldUpdate={(prev, curr) => prev.age !== curr.age}>
  {({ getFieldValue }) => {
    const age = getFieldValue('age');

    if (age && age < 18) {
      return (
        <>
          <Form.Item
            name="guardianName"
            label="监护人姓名"
            rules={[{ required: true, message: '未成年人必须填写监护人信息' }]}
          >
            <Input placeholder="请输入监护人姓名" />
          </Form.Item>
          <Form.Item
            name="guardianPhone"
            label="监护人电话"
            rules={[
              { required: true, message: '请输入监护人电话' },
              { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
            ]}
          >
            <Input placeholder="请输入监护人电话" />
          </Form.Item>
        </>
      );
    }

    return null;
  }}
</Form.Item>
```

### 3. 复杂跨字段验证

**实现复杂的跨字段验证逻辑**：

```typescript
// 示例：优惠券验证
const validateCoupon = async (rule: Rule, value: string) => {
  const form = rule._f as FormInstance; // 获取表单实例
  const totalAmount = form.getFieldValue('totalAmount');
  const minAmount = form.getFieldValue('minAmount');

  if (value && totalAmount < minAmount) {
    return Promise.reject(`订单金额需满 ${minAmount} 元才能使用此优惠券`);
  }

  return Promise.resolve();
};

<Form.Item
  name="totalAmount"
  label="订单金额"
  rules={[{ required: true }]}
>
  <InputNumber />
</Form.Item>

<Form.Item
  name="coupon"
  label="优惠券码"
  dependencies={['totalAmount']}
  rules={[{ validator: validateCoupon }]}
>
  <Input placeholder="请输入优惠券码" />
</Form.Item>
```

## 动态表单验证

### 1. Form.List - 动态列表验证

**Form.List 支持动态增减表单项，并自动处理验证**：

```typescript
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

<Form.List
  name="users"
  rules={[
    { required: true, message: '请至少添加一个用户' },
    { type: 'array', min: 1, message: '至少需要一个用户' }
  ]}
>
  {(fields, { add, remove }, { errors }) => (
    <>
      {fields.map(({ key, name, ...restField }) => (
        <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
          <Form.Item
            {...restField}
            name={[name, 'username']}
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" />
          </Form.Item>

          <Form.Item
            {...restField}
            name={[name, 'email']}
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' }
            ]}
          >
            <Input placeholder="邮箱" />
          </Form.Item>

          <MinusCircleOutlined onClick={() => remove(name)} />
        </Space>
      ))}

      <Form.ErrorList errors={errors} />

      <Form.Item>
        <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
          添加用户
        </Button>
      </Form.Item>
    </>
  )}
</Form.List>
```

### 2. 嵌套动态表单

**多层嵌套的动态表单验证**：

```typescript
<Form.List name="companies">
  {(companyFields, { add: addCompany, remove: removeCompany }) => (
    <>
      {companyFields.map(({ key: companyKey, name: companyName, ...restCompanyField }) => (
        <Card
          key={companyKey}
          title={`公司 ${companyName + 1}`}
          extra={<Button onClick={() => removeCompany(companyName)}>删除</Button>}
        >
          <Form.Item
            {...restCompanyField}
            name={[companyName, 'name']}
            label="公司名称"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>

          {/* 嵌套的 Form.List */}
          <Form.List name={[companyName, 'departments']}>
            {(deptFields, { add: addDept, remove: removeDept }) => (
              <>
                {deptFields.map(({ key: deptKey, name: deptName, ...restDeptField }) => (
                  <Space key={deptKey} style={{ display: 'flex', marginBottom: 8 }}>
                    <Form.Item
                      {...restDeptField}
                      name={[deptName, 'name']}
                      rules={[{ required: true, message: '请输入部门名称' }]}
                    >
                      <Input placeholder="部门名称" />
                    </Form.Item>

                    <Form.Item
                      {...restDeptField}
                      name={[deptName, 'count']}
                      rules={[{ required: true, message: '请输入人数' }]}
                    >
                      <InputNumber placeholder="人数" />
                    </Form.Item>

                    <Button onClick={() => removeDept(deptName)}>删除</Button>
                  </Space>
                ))}

                <Button type="dashed" onClick={() => addDept()} block>
                  添加部门
                </Button>
              </>
            )}
          </Form.List>
        </Card>
      ))}

      <Button type="dashed" onClick={() => addCompany()} block>
        添加公司
      </Button>
    </>
  )}
</Form.List>
```

### 3. 动态字段验证

**根据条件动态添加验证规则**：

```typescript
const [isRequired, setIsRequired] = useState(false);

<Form.Item
  name="field"
  rules={isRequired ? [{ required: true, message: '此字段为必填项' }] : []}
>
  <Input />
</Form.Item>

<Switch checked={isRequired} onChange={setIsRequired} />
<span>设为必填</span>
```

## 异步验证

### 1. 防抖优化

**使用防抖优化异步验证性能**：

```typescript
import { debounce } from 'lodash';

// 防抖的异步验证
const debouncedCheckUsername = debounce(async (value) => {
  try {
    const response = await fetch(`/api/check-username?username=${value}`);
    const data = await response.json();
    return data.exists;
  } catch (error) {
    return false;
  }
}, 500);

<Form.Item
  name="username"
  rules={[
    { required: true },
    {
      validator: async (_, value) => {
        if (!value) return Promise.resolve();

        const exists = await debouncedCheckUsername(value);
        if (exists) {
          return Promise.reject('该用户名已被注册');
        }

        return Promise.resolve();
      }
    }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>
```

### 2. 加载状态管理

**在异步验证时显示加载状态**：

```typescript
const [checking, setChecking] = useState(false);
const [valid, setValid] = useState<boolean | null>(null);

const checkUsername = debounce(async (value: string) => {
  if (!value) {
    setValid(null);
    return;
  }

  setChecking(true);
  try {
    const response = await fetch(`/api/check-username?username=${value}`);
    const data = await response.json();
    setValid(!data.exists);
  } catch (error) {
    setValid(null);
  } finally {
    setChecking(false);
  }
}, 500);

<Form.Item
  name="username"
  rules={[
    { required: true },
    {
      validator: (_, value) => {
        if (valid === false) {
          return Promise.reject('该用户名已被注册');
        }
        return Promise.resolve();
      }
    }
  ]}
  validateStatus={checking ? 'validating' : valid === false ? 'error' : valid === true ? 'success' : ''}
  help={checking ? '检查中...' : valid === false ? '该用户名已被注册' : ''}
>
  <Input
    placeholder="用户名"
    onChange={(e) => checkUsername(e.target.value)}
  />
</Form.Item>
```

### 3. 取消异步请求

**使用 AbortController 取消未完成的请求**：

```typescript
let abortController: AbortController | null = null;

const checkUsername = async (value: string) => {
  // 取消上一次请求
  if (abortController) {
    abortController.abort();
  }

  abortController = new AbortController();

  try {
    const response = await fetch(`/api/check-username?username=${value}`, {
      signal: abortController.signal
    });
    const data = await response.json();
    return data.exists;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('请求被取消');
      return null;
    }
    throw error;
  }
};

<Form.Item
  name="username"
  rules={[
    {
      validator: async (_, value) => {
        if (!value) return Promise.resolve();

        const exists = await checkUsername(value);
        if (exists === true) {
          return Promise.reject('该用户名已被注册');
        }

        return Promise.resolve();
      }
    }
  ]}
>
  <Input placeholder="用户名" />
</Form.Item>
```

### 4. 批量异步验证

**多个字段的异步验证**：

```typescript
// 同时验证手机号和邮箱
const checkPhone = async (phone: string) => {
  const response = await fetch(`/api/check-phone?phone=${phone}`);
  return response.json();
};

const checkEmail = async (email: string) => {
  const response = await fetch(`/api/check-email?email=${email}`);
  return response.json();
};

// 并发验证
const validateAllFields = async () => {
  try {
    const values = await form.validateFields(['phone', 'email']);

    const [phoneResult, emailResult] = await Promise.all([
      checkPhone(values.phone),
      checkEmail(values.email)
    ]);

    if (phoneResult.exists) {
      form.setFields([
        { name: 'phone', errors: ['该手机号已注册'] }
      ]);
    }

    if (emailResult.exists) {
      form.setFields([
        { name: 'email', errors: ['该邮箱已注册'] }
      ]);
    }

    if (!phoneResult.exists && !emailResult.exists) {
      // 提交表单
    }
  } catch (error) {
    console.error('验证失败', error);
  }
};

<Button onClick={validateAllFields}>提交</Button>
```

## 错误处理和显示

### 1. 错误消息国际化

**配置多语言错误消息**：

```typescript
const validateMessages = {
  required: '${label}是必填项',
  types: {
    email: '${label}格式不正确',
    number: '${label}必须是数字',
  },
  string: {
    min: '${label}至少${min}个字符',
    max: '${label}不能超过${max}个字符',
    range: '${label}必须在 ${min} 到 ${max} 个字符之间',
  },
  number: {
    min: '${label}必须大于等于${min}',
    max: '${label}必须小于等于${max}',
    range: '${label}必须在 ${min} 到 ${max} 之间',
  },
  pattern: {
    mismatch: '${label}格式不正确',
  },
};

<Form
  validateMessages={validateMessages}
>
  <Form.Item
    name="email"
    label="邮箱"
    rules={[{ required: true, type: 'email', min: 5, max: 100 }]}
  >
    <Input />
  </Form.Item>
</Form>
```

### 2. 错误样式定制

**自定义错误显示样式**：

```typescript
import { Form, Input, Alert } from 'antd';

// 自定义错误提示组件
const CustomError = ({ errors }: { errors: string[] }) => {
  if (!errors || errors.length === 0) return null;

  return (
    <Alert
      message="验证失败"
      description={errors[0]}
      type="error"
      showIcon
      style={{ marginTop: 8 }}
    />
  );
};

<Form.Item
  name="email"
  rules={[{ required: true, type: 'email' }]}
>
  <Input />
</Form.Item>

// 使用 Form.Item 的 children 函数获取错误状态
<Form.Item
  name="password"
  rules={[{ required: true, min: 8 }]}
>
  {({ value, onChange }, { errors }) => (
    <div>
      <Input.Password value={value} onChange={onChange} />
      {errors.length > 0 && (
        <div style={{ color: '#ff4d4f', fontSize: 14, marginTop: 4 }}>
          {errors[0]}
        </div>
      )}
    </div>
  )}
</Form.Item>
```

### 3. 全局错误处理

**在表单提交时处理所有错误**：

```typescript
const [form] = Form.useForm();

const handleSubmit = async () => {
  try {
    const values = await form.validateFields();
    console.log('提交成功', values);
    // 提交数据到服务器
  } catch (error) {
    console.error('验证失败', error);

    // 获取所有错误
    const errorFields = error.errorFields;
    const errors = errorFields.map(field => ({
      name: field.name[0],
      errors: field.errors
    }));

    console.log('错误列表:', errors);

    // 滚动到第一个错误字段
    const firstErrorField = errorFields[0];
    if (firstErrorField) {
      form.scrollToField(firstErrorField.name);
    }
  }
};

<Form form={form} onFinish={handleSubmit}>
  {/* 表单项 */}
</Form>
```

### 4. 错误状态重置

**手动重置错误状态**：

```typescript
// 重置单个字段的错误
form.setFields([
  {
    name: 'username',
    errors: []
  }
]);

// 重置多个字段的错误
form.setFields([
  { name: 'username', errors: [] },
  { name: 'email', errors: [] },
  { name: 'password', errors: [] }
]);

// 重置整个表单
form.resetFields();

// 清除所有验证状态但保留值
form.clearValidate();
```

## 最佳实践

### 1. 验证规则组织

**将验证规则抽取为常量**：

```typescript
// validation-rules.ts
export const USERNAME_RULES = [
  { required: true, message: '请输入用户名' },
  { min: 4, message: '用户名至少4个字符' },
  { max: 20, message: '用户名不能超过20个字符' },
  {
    pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
    message: '用户名必须以字母开头，只能包含字母、数字和下划线'
  }
];

export const EMAIL_RULES = [
  { required: true, message: '请输入邮箱' },
  { type: 'email' as const, message: '邮箱格式不正确' }
];

export const PASSWORD_RULES = [
  { required: true, message: '请输入密码' },
  { min: 8, message: '密码至少8个字符' },
  { max: 32, message: '密码不能超过32个字符' }
];

// 使用
import { USERNAME_RULES, EMAIL_RULES, PASSWORD_RULES } from './validation-rules';

<Form.Item name="username" rules={USERNAME_RULES}>
  <Input />
</Form.Item>
```

### 2. 自定义验证器复用

**将常用验证器封装为函数**：

```typescript
// validators.ts
export const createRequiredValidator = (message: string) => ({
  validator: (_: Rule, value: any) => {
    if (!value) {
      return Promise.reject(message);
    }
    return Promise.resolve();
  }
});

export const createLengthValidator = (min: number, max: number) => ({
  validator: (_: Rule, value: string) => {
    if (value && (value.length < min || value.length > max)) {
      return Promise.reject(`长度必须在 ${min} 到 ${max} 之间`);
    }
    return Promise.resolve();
  }
});

export const createAsyncValidator = (
  checkFn: (value: any) => Promise<boolean>,
  errorMessage: string
) => ({
  validator: async (_: Rule, value: any) => {
    if (!value) return Promise.resolve();

    const isValid = await checkFn(value);
    if (!isValid) {
      return Promise.reject(errorMessage);
    }

    return Promise.resolve();
  }
});

// 使用
<Form.Item
  name="username"
  rules={[
    createRequiredValidator('请输入用户名'),
    createLengthValidator(4, 20),
    createAsyncValidator(
      async (value) => !(await checkUsernameExists(value)),
      '该用户名已被注册'
    )
  ]}
>
  <Input />
</Form.Item>
```

### 3. 性能优化

**优化表单验证性能**：

```typescript
// 1. 使用 validateTrigger 控制验证时机
// 对于异步验证，建议使用 onBlur 而不是 onChange
<Form.Item
  name="email"
  validateTrigger="onBlur"
  rules={[
    { type: 'email' },
    { validator: checkEmailExists }
  ]}
>
  <Input />
</Form.Item>

// 2. 防抖异步验证
const debouncedCheck = debounce(async (value) => {
  return await checkApi(value);
}, 300);

// 3. 条件验证
<Form.Item
  name="field"
  rules={showField ? [{ required: true }] : []}
>
  <Input />
</Form.Item>

// 4. 避免不必要的验证
// 静默模式：只在提交时验证
<Form
  validateTrigger="onSubmit"
>
  {/* 表单项 */}
</Form>
```

### 4. 用户体验优化

**提供良好的用户体验**：

```typescript
// 1. 实时反馈 + 友好提示
<Form.Item
  name="password"
  validateTrigger="onChange"
  rules={[
    { required: true, message: '请输入密码' },
    { min: 8, message: '密码至少8个字符' }
  ]}
  hasFeedback
  help="建议使用字母、数字和特殊字符的组合"
>
  <Input.Password />
</Form.Item>

// 2. 密码强度指示器
const [passwordStrength, setPasswordStrength] = useState(0);

const checkPasswordStrength = (value: string) => {
  let strength = 0;
  if (value.length >= 8) strength++;
  if (/[A-Z]/.test(value)) strength++;
  if (/[a-z]/.test(value)) strength++;
  if (/\d/.test(value)) strength++;
  if (/[^A-Za-z0-9]/.test(value)) strength++;
  setPasswordStrength(strength);
};

<Form.Item
  name="password"
  rules={[{ required: true, min: 8 }]}
>
  <Input.Password onChange={(e) => checkPasswordStrength(e.target.value)} />
</Form.Item>

<Progress
  percent={passwordStrength * 20}
  status={passwordStrength < 2 ? 'exception' : passwordStrength < 4 ? 'active' : 'success'}
  showInfo={false}
/>

// 3. 成功提示
<Form.Item
  name="username"
  rules={[{ required: true }]}
  validateStatus={usernameValid ? 'success' : ''}
  hasFeedback
>
  <Input />
</Form.Item>
```

## 完整示例

### 用户注册表单

```typescript
import React, { useState } from 'react';
import { Form, Input, Button, DatePicker, Select, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';

const RegisterForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 检查用户名是否存在
  const checkUsernameExists = async (username: string) => {
    try {
      const response = await fetch(`/api/check-username?username=${username}`);
      const data = await response.json();
      return data.exists;
    } catch (error) {
      return false;
    }
  };

  // 检查邮箱是否存在
  const checkEmailExists = async (email: string) => {
    try {
      const response = await fetch(`/api/check-email?email=${email}`);
      const data = await response.json();
      return data.exists;
    } catch (error) {
      return false;
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 提交注册信息
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      const data = await response.json();

      if (data.success) {
        message.success('注册成功！');
        form.resetFields();
      } else {
        message.error(data.message || '注册失败');
      }
    } catch (error) {
      message.error('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      autoComplete="off"
      validateMessages={{
        required: '${label}是必填项',
        types: {
          email: '${label}格式不正确',
        },
        string: {
          min: '${label}至少${min}个字符',
          max: '${label}不能超过${max}个字符',
        },
      }}
    >
      <Form.Item
        label="用户名"
        name="username"
        rules={[
          { required: true },
          { min: 4, message: '用户名至少4个字符' },
          { max: 20, message: '用户名不能超过20个字符' },
          {
            pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
            message: '用户名必须以字母开头，只能包含字母、数字和下划线'
          },
          {
            validator: async (_, value) => {
              if (!value) return Promise.resolve();

              const exists = await checkUsernameExists(value);
              if (exists) {
                return Promise.reject('该用户名已被注册');
              }

              return Promise.resolve();
            }
          }
        ]}
        validateTrigger="onBlur"
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="请输入用户名"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="邮箱"
        name="email"
        rules={[
          { required: true },
          { type: 'email' },
          {
            validator: async (_, value) => {
              if (!value) return Promise.resolve();

              const exists = await checkEmailExists(value);
              if (exists) {
                return Promise.reject('该邮箱已被注册');
              }

              return Promise.resolve();
            }
          }
        ]}
        validateTrigger="onBlur"
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="请输入邮箱"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="手机号"
        name="phone"
        rules={[
          { required: true },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }
        ]}
      >
        <Input
          prefix={<PhoneOutlined />}
          placeholder="请输入手机号"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="密码"
        name="password"
        rules={[
          { required: true },
          { min: 8, message: '密码至少8个字符' },
          { max: 32, message: '密码不能超过32个字符' },
          {
            validator: (_, value) => {
              if (!value) return Promise.resolve();

              if (!/[A-Z]/.test(value)) {
                return Promise.reject('密码必须包含至少一个大写字母');
              }
              if (!/[a-z]/.test(value)) {
                return Promise.reject('密码必须包含至少一个小写字母');
              }
              if (!/\d/.test(value)) {
                return Promise.reject('密码必须包含至少一个数字');
              }
              if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) {
                return Promise.reject('密码必须包含至少一个特殊字符');
              }

              return Promise.resolve();
            }
          }
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="请输入密码"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="确认密码"
        name="confirmPassword"
        dependencies={['password']}
        rules={[
          { required: true },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject('两次输入的密码不一致');
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="请再次输入密码"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="生日"
        name="birthday"
        rules={[
          { required: true },
          {
            validator: (_, value) => {
              if (!value) return Promise.resolve();

              const now = moment();
              const age = now.diff(value, 'years');

              if (age < 13) {
                return Promise.reject('年龄必须大于13岁');
              }
              if (age > 120) {
                return Promise.reject('请输入有效的生日');
              }

              return Promise.resolve();
            }
          }
        ]}
      >
        <DatePicker
          placeholder="请选择生日"
          style={{ width: '100%' }}
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="性别"
        name="gender"
        rules={[{ required: true }]}
      >
        <Select placeholder="请选择性别" size="large">
          <Select.Option value="male">男</Select.Option>
          <Select.Option value="female">女</Select.Option>
          <Select.Option value="other">其他</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          size="large"
          block
        >
          注册
        </Button>
      </Form.Item>
    </Form>
  );
};

export default RegisterForm;
```

### 动态表单示例

```typescript
import React from 'react';
import { Form, Input, Button, Card, Space, DatePicker, Select } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

const DynamicForm = () => {
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    console.log('提交的数据:', values);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
    >
      <Form.Item
        label="项目名称"
        name="projectName"
        rules={[{ required: true, message: '请输入项目名称' }]}
      >
        <Input placeholder="请输入项目名称" />
      </Form.Item>

      <Form.List name="tasks">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Card
                key={key}
                title={`任务 ${name + 1}`}
                extra={
                  <Button
                    type="link"
                    danger
                    icon={<MinusCircleOutlined />}
                    onClick={() => remove(name)}
                  >
                    删除
                  </Button>
                }
                style={{ marginBottom: 16 }}
              >
                <Form.Item
                  {...restField}
                  name={[name, 'title']}
                  label="任务标题"
                  rules={[{ required: true, message: '请输入任务标题' }]}
                >
                  <Input placeholder="请输入任务标题" />
                </Form.Item>

                <Form.Item
                  {...restField}
                  name={[name, 'description']}
                  label="任务描述"
                  rules={[{ required: true, message: '请输入任务描述' }]}
                >
                  <Input.TextArea placeholder="请输入任务描述" rows={3} />
                </Form.Item>

                <Space direction="vertical" style={{ width: '100%' }}>
                  <Form.Item
                    {...restField}
                    name={[name, 'deadline']}
                    label="截止日期"
                    rules={[{ required: true, message: '请选择截止日期' }]}
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'priority']}
                    label="优先级"
                    rules={[{ required: true, message: '请选择优先级' }]}
                  >
                    <Select placeholder="请选择优先级">
                      <Select.Option value="high">高</Select.Option>
                      <Select.Option value="medium">中</Select.Option>
                      <Select.Option value="low">低</Select.Option>
                    </Select>
                  </Form.Item>
                </Space>

                {/* 子任务 */}
                <Form.List name={[name, 'subtasks']}>
                  {(subFields, { add: addSub, remove: removeSub }) => (
                    <>
                      <div style={{ marginBottom: 8 }}>
                        <strong>子任务</strong>
                      </div>
                      {subFields.map((subKey, subName) => (
                        <Space key={subKey} style={{ display: 'flex', marginBottom: 8 }}>
                          <Form.Item
                            {...subKey}
                            name={[subName, 'name']}
                            rules={[{ required: true, message: '请输入子任务' }]}
                            style={{ marginBottom: 0 }}
                          >
                            <Input placeholder="请输入子任务" style={{ width: 300 }} />
                          </Form.Item>
                          <Button onClick={() => removeSub(subName)}>删除</Button>
                        </Space>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => addSub()}
                        block
                        icon={<PlusOutlined />}
                      >
                        添加子任务
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            ))}

            <Button
              type="dashed"
              onClick={() => add()}
              block
              icon={<PlusOutlined />}
            >
              添加任务
            </Button>
          </>
        )}
      </Form.List>

      <Form.Item style={{ marginTop: 24 }}>
        <Button type="primary" htmlType="submit" size="large" block>
          提交
        </Button>
      </Form.Item>
    </Form>
  );
};

export default DynamicForm;
```

## 注意事项

1. **异步验证优化**：使用 `debounce` 和 `validateTrigger="onBlur"` 避免频繁请求
2. **错误消息**：提供清晰、友好的错误提示，帮助用户理解问题
3. **性能考虑**：复杂表单使用 `shouldUpdate` 时注意性能，避免不必要的重渲染
4. **跨字段验证**：使用 `dependencies` 声明依赖字段，确保验证正确触发
5. **动态表单**：Form.List 的验证规则配置在 Form.Item 上，不是 rules 数组
6. **类型安全**：使用 TypeScript 时，为表单数据定义类型接口
7. **国际化**：使用 `validateMessages` 配置多语言错误消息
8. **验证时机**：合理选择 `validateTrigger`，平衡实时性和性能
9. **错误处理**：使用 `try-catch` 捕获验证错误，提供友好的用户反馈
10. **表单重置**：提交成功后使用 `form.resetFields()` 清空表单

## 参考资源

- **官方文档**: https://ant.design/components/form-cn/
- **API 参考**: https://ant.design/components/form-cn/#API
- **验证示例**: https://ant.design/components/form-cn/#components-form-demo-validate-static
- **rc-field-form**: https://github.com/react-component/field-form
- **TypeScript 类型定义**: https://github.com/ant-design/ant-design/tree/master/components/form
