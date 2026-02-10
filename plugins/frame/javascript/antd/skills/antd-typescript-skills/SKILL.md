---
name: antd-typescript-skills
description: Ant Design TypeScript 完整指南 - 类型定义、泛型组件、类型推导、类型增强
---

# antd-typescript: TypeScript 完整指南

Ant Design 提供了完整的 TypeScript 类型定义系统，支持类型安全的组件开发、泛型封装、类型推导和类型增强。本文档涵盖 Ant Design TypeScript 的所有核心概念和最佳实践。

---

## 概述

### TypeScript 支持

Ant Design 从 4.0 版本开始完全使用 TypeScript 编写，提供以下特性：

- **完整的类型定义** - 所有组件 Props 都有明确的类型定义
- **泛型支持** - Form、Table 等组件支持泛型参数
- **类型推导** - 智能推导组件属性类型
- **类型增强** - 支持模块声明扩展和类型合并
- **严格模式兼容** - 完全支持 TypeScript strict mode

### 类型系统优势

```typescript
// ✅ 类型安全 - 编译时捕获错误
<Button type="primary">Click</Button>
// <Button type="invalid">  // TypeScript 报错：类型不匹配

// ✅ 智能提示 - IDE 自动补全
const { data, loading } = useRequest<User[]>(url);
// data 自动推导为 User[] | undefined

// ✅ 重构安全 - 修改类型时自动发现所有使用
interface User { name: string }
// 修改为 interface User { fullName: string }
// TypeScript 会标记所有使用 name 的地方
```

---

## 核心类型系统

### 组件 Props 类型

所有 Ant Design 组件都导出对应的 Props 类型：

```typescript
import type {
  ButtonProps,
  InputProps,
  FormProps,
  TableProps,
  ModalProps,
  ConfigProviderProps,
} from 'antd';

// 使用示例：自定义按钮组件
type CustomButtonProps = ButtonProps & {
  // 扩展自定义属性
  loadingText?: string;
};

function CustomButton({ loadingText, children, ...rest }: CustomButtonProps) {
  return (
    <Button {...rest}>
      {rest.loading && loadingText ? loadingText : children}
    </Button>
  );
}
```

### 组件实例类型

使用 `React.ComponentRef` 获取组件实例类型：

```typescript
import type { ReactComponentElement } from 'react';
import { Input, Form, Modal } from 'antd';

// 获取 Input 组件实例类型
type InputInstance = React.ComponentRef<typeof Input>;

// 获取 Form 组件实例类型
type FormInstance = React.ComponentRef<typeof Form>;

// 使用实例方法
const formRef = React.useRef<FormInstance>(null);

// 类型安全的方法调用
formRef.current?.setFieldsValue({ name: 'John' });
formRef.current?.validateFields(); // 返回 Promise
formRef.current?.resetFields();
```

### 泛型组件 Props

某些组件（如 Form、Table）支持泛型参数：

```typescript
// Form 组件泛型
import type { FormInstance, FormProps } from 'antd';

// 定义表单数据类型
interface UserFormValues {
  name: string;
  email: string;
  age: number;
}

// Form 泛型参数指定表单数据类型
type UserFormProps = FormProps<UserFormValues>;

// 使用
const UserForm: React.FC<UserFormProps> = (props) => {
  return <Form {...props} />;
};

// Table 组件泛型
import type { TableProps } from 'antd';

interface User {
  id: number;
  name: string;
  email: string;
}

type UserTableProps = TableProps<User>;

// 使用
const UserTable: React.FC<UserTableProps> = (props) => {
  return <Table<User> {...props} />;
};
```

---

## Form 表单类型

### FormInstance 类型

`FormInstance` 是表单实例的核心类型，包含所有表单操作方法：

```typescript
import type { FormInstance } from 'antd';

const formRef = React.useRef<FormInstance>(null);

// 类型安全的表单操作
formRef.current?.setFieldsValue({ name: 'John' });
formRef.current?.setFieldValue('name', 'John');

// 获取字段值 - 类型推导
const nameValue = formRef.current?.getFieldValue('name');
// nameValue 类型推导为 any，可以指定泛型
const nameValueSafe = formRef.current?.getFieldValue<string>('name');

// 验证字段 - 返回 Promise
formRef.current?.validateFields(['name']).then((values) => {
  // values 类型为 { name: any }
});

// 验证所有字段
const allValues = await formRef.current?.validateFields();
// allValues 类型为 Record<string, any>
```

### Form 泛型参数

使用泛型参数增强类型安全：

```typescript
import { Form } from 'antd';

// 定义表单数据类型
interface LoginFormValues {
  username: string;
  password: string;
  remember?: boolean;
}

// 使用泛型参数
const LoginForm: React.FC = () => {
  const [form] = Form.useForm<LoginFormValues>();

  // setFieldsValue 类型安全
  form.setFieldsValue({ username: 'john' });
  // form.setFieldsValue({ invalid: 'value' }); // TypeScript 报错

  // validateFields 返回正确类型
  const handleSubmit = async () => {
    const values = await form.validateFields();
    // values 类型为 LoginFormValues

    console.log(values.username); // ✅ 类型安全
    // console.log(values.invalid); // ❌ TypeScript 报错
  };

  return <Form form={form} onSubmit={handleSubmit} />;
};
```

### Form.Item 类型推导

`Form.Item` 会自动推导字段类型：

```typescript
import { Form, Input } from 'antd';

interface UserFormValues {
  name: string;
  age: number;
  email: string;
}

const UserForm: React.FC = () => {
  const [form] = Form.useForm<UserFormValues>();

  return (
    <Form form={form}>
      {/* name 属性自动推导为 'name' | 'age' | 'email' */}
      <Form.Item name="name" label="姓名">
        <Input />
      </Form.Item>

      <Form.Item name="age" label="年龄">
        <Input type="number" />
      </Form.Item>

      <Form.Item name="email" label="邮箱">
        <Input type="email" />
      </Form.Item>

      {/* <Form.Item name="invalid" label="无效字段">
        TypeScript 报错：'invalid' 不在联合类型中
      </Form.Item> */}
    </Form>
  );
};
```

### Form Rules 类型

表单验证规则的类型定义：

```typescript
import type { Rule } from 'antd/es/form';

// Rule 类型定义
interface RuleObject {
  /** 验证失败时的错误信息 */
  message?: string | React.ReactNode;

  /** 验证器函数 */
  validator?: (
    rule: RuleObject,
    value: any,
    callback: (error?: string | Error) => void,
  ) => Promise<void | any> | void;

  /** 是否必需 */
  required?: boolean;

  /** 字段类型 */
  type?: 'string' | 'number' | 'boolean' | 'method' | 'regexp' | 'integer' | 'float' | 'array' | 'object' | 'enum' | 'date' | 'url' | 'hex' | 'email';

  /** 最小长度/最小值 */
  min?: number;

  /** 最大长度/最大值 */
  max?: number;

  /** 字符串长度 */
  len?: number;

  /** 正则表达式 */
  pattern?: RegExp;

  /** 枚举值 */
  enum?: any[];

  /** 自定义验证函数 */
  validateTrigger?: string | string[];

  /** 是否深度验证对象/数组 */
  deep?: boolean;
}

// 使用示例
const rules: Rule[] = [
  { required: true, message: '请输入用户名' },
  { min: 3, max: 20, message: '用户名长度为 3-20 个字符' },
  {
    pattern: /^[a-zA-Z0-9_]+$/,
    message: '用户名只能包含字母、数字和下划线',
  },
  {
    validator: async (rule, value) => {
      if (!value) {
        return Promise.reject('用户名不能为空');
      }
      if (await checkUsernameExists(value)) {
        return Promise.reject('用户名已存在');
      }
      return Promise.resolve();
    },
  },
];
```

### Form.useForm Hook

`Form.useForm` Hook 返回类型安全的表单实例：

```typescript
import { Form } from 'antd';

// 无泛型参数 - 返回 FormInstance
const [form] = Form.useForm();

// 带泛型参数 - 返回 FormInstance<Values>
interface UserFormValues {
  name: string;
  email: string;
}

const [form] = Form.useForm<UserFormValues>();

// form 类型为 FormInstance<UserFormValues>
form.setFieldsValue({ name: 'John' });
// form.setFieldsValue({ invalid: 'value' }); // TypeScript 报错
```

---

## Table 数据类型

### TableProps 泛型

`TableProps` 接受泛型参数指定数据类型：

```typescript
import type { TableProps } from 'antd';

// 定义数据类型
interface User {
  id: number;
  name: string;
  email: string;
  age: number;
  role: 'admin' | 'user' | 'guest';
}

// TableProps 泛型参数
type UserTableProps = TableProps<User>;

// 使用
const UserTable: React.FC<UserTableProps> = (props) => {
  return <Table<User> {...props} />;
};

// dataSource 类型自动推导为 UserType[]
const columns: ColumnsType<User> = [
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    // record 类型为 User
    render: (value: string, record: User) => {
      return `${value} (${record.role})`;
    },
  },
];
```

### ColumnsType 类型

`ColumnsType` 定义表格列配置的类型：

```typescript
import type { ColumnsType } from 'antd';

interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

const columns: ColumnsType<User> = [
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    // dataIndex 可以是字符串数组（嵌套路径）
    // ['user', 'name'] => record.user.name

    // 自定义渲染函数
    render: (value: string, record: User, index: number) => {
      // value 类型推导为 string（dataIndex 指定）
      // record 类型为 User
      // index 类型为 number
      return <a href={`/users/${record.id}`}>{value}</a>;
    },

    // 过滤器
    filters: [
      { text: '年龄 > 30', value: 'gt30' },
      { text: '年龄 <= 30', value: 'lte30' },
    ],
    onFilter: (value: any, record: User) => {
      return value === 'gt30' ? record.age > 30 : record.age <= 30;
    },

    // 排序
    sorter: (a: User, b: User) => a.age - b.age,

    // 响应式
    responsive: ['md', 'lg'],
  },
];
```

### TableRowSelection 类型

行选择配置的类型定义：

```typescript
import type { TableRowSelection } from 'antd';

interface User {
  id: number;
  name: string;
}

const rowSelection: TableRowSelection<User> = {
  // 选中的行 key 数组
  selectedRowKeys: React.Key[],

  // 变化回调
  onChange: (
    selectedRowKeys: React.Key[],
    selectedRows: User[],
  ) => {
    console.log('选中行:', selectedRowKeys, selectedRows);
  },

  // 选择类型
  type: 'checkbox', // 'checkbox' | 'radio'

  // 列配置
  columnWidth: '50px',
  fixed: true,

  // 禁用选择
  getCheckboxProps: (record: User) => ({
    disabled: record.id === 1,
  }),

  // 隐藏选择列
  hideSelectAll: false,

  // 跨页选择
  preserveSelectedRowKeys: true,
};
```

### Table 分页类型

分页配置的类型定义：

```typescript
import type { PaginationProps } from 'antd';

interface User {
  id: number;
  name: string;
}

const pagination: PaginationProps = {
  current: 1,
  pageSize: 10,
  total: 100,

  // 显示大小切换器
  showSizeChanger: true,
  pageSizeOptions: ['10', '20', '50', '100'],

  // 快速跳转
  showQuickJumper: true,

  // 显示总数
  showTotal: (total: number, range: [number, number]) => {
    return `第 ${range[0]}-${range[1]} 条，共 ${total} 条`;
  },

  // 变化回调
  onChange: (page: number, pageSize: number) => {
    console.log('页码变化:', page, pageSize);
  },
};
```

---

## ConfigProvider 类型

### ConfigProviderProps 类型

`ConfigProvider` 组件的属性类型：

```typescript
import type { ConfigProviderProps, ThemeConfig } from 'antd';

interface AppConfig {
  // 主题配置
  theme?: ThemeConfig;

  // 语言配置
  locale?: Locale;

  // 组件默认配置
  componentSize?: 'small' | 'middle' | 'large';
  componentDisabled?: boolean;

  // 方向
  direction?: 'ltr' | 'rtl';

  // 前缀
  prefixCls?: string;
  iconPrefixCls?: string;

  // 容器配置
  getPopupContainer?: (node: HTMLElement) => HTMLElement;
  getTargetContainer?: () => HTMLElement;

  // 空状态渲染
  renderEmpty?: () => React.ReactNode;

  // Form 全局配置
  form?: {
    requiredMark?: boolean | 'optional';
    colon?: boolean;
    scrollToFirstError?: boolean | ScrollToFirstErrorConfig;
  };

  // Input 全局配置
  input?: {
    autoComplete?: string;
  };

  // Select 全局配置
  select?: {
    showSearch?: boolean;
  };
}

// 使用示例
const appConfig: ConfigProviderProps = {
  theme: {
    token: {
      colorPrimary: '#1890ff',
    },
  },
  locale: zhCN,
  componentSize: 'middle',
  componentDisabled: false,
};
```

### ThemeConfig 类型

主题配置的完整类型定义：

```typescript
import type { ThemeConfig } from 'antd';

// 预设算法类型
type ThemeAlgorithm =
  | typeof theme.defaultAlgorithm
  | typeof theme.compactAlgorithm
  | typeof theme.darkAlgorithm;

// 主题配置
const themeConfig: ThemeConfig = {
  // 主题算法
  algorithm: theme.defaultAlgorithm,

  // Seed Token（种子令牌）
  token: {
    // 颜色
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    colorLink: '#1890ff',

    // 文本颜色
    colorTextBase: '#000',
    colorTextSecondary: '#000000d9',
    colorTextTertiary: '#00000073',
    colorTextQuaternary: '#00000040',

    // 背景颜色
    colorBgBase: '#fff',
    colorBgContainer: '#fff',
    colorBgElevated: '#fff',
    colorBgLayout: '#f5f5f5',
    colorBgSpotlight: '#ffffffa6',

    // 边框颜色
    colorBorder: '#d9d9d9',
    colorBorderSecondary: '#f0f0f0',

    // 字体
    fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial`,
    fontSize: 14,
    fontSizeHeading1: 38,
    fontSizeHeading2: 30,
    fontSizeHeading3: 24,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,

    // 圆角
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,

    // 间距
    marginXS: 8,
    marginSM: 12,
    margin: 16,
    marginMD: 20,
    marginLG: 24,
    marginXL: 32,

    // 其他
    lineWidth: 1,
    lineWidthBold: 2,
    motionDurationSlow: '0.3s',
    motionDuration: '0.2s',
    motionDurationFast: '0.1s',
  },

  // 组件级别的 Token
  components: {
    Button: {
      colorPrimary: '#00b96b',
      algorithm: true, // 继承主算法
    },
    Input: {
      colorBgContainer: '#f0f0f0',
      borderRadiusLG: 10,
    },
    Table: {
      headerBg: '#f0f0f0',
      headerColor: '#000',
    },
  },
};
```

---

## 泛型组件开发

### 基础泛型组件

创建类型安全的泛型组件：

```typescript
import { Table, Form, Input } from 'antd';
import type { TableProps, FormInstance } from 'antd';

// 示例 1：泛型表格包装器
interface GenericTableProps<T> {
  data: T[];
  columns: ColumnsType<T>;
  loading?: boolean;
  onRowClick?: (record: T) => void;
}

function GenericTable<T extends Record<string, any>>({
  data,
  columns,
  loading,
  onRowClick,
}: GenericTableProps<T>) {
  const tableProps: TableProps<T> = {
    dataSource: data,
    columns,
    loading,
    onRow: (record) => ({
      onClick: () => onRowClick?.(record),
    }),
  };

  return <Table<T> {...tableProps} />;
}

// 使用
interface User {
  id: number;
  name: string;
  email: string;
}

const UserList: React.FC = () => {
  const [users, setUsers] = React.useState<User[]>([]);

  const columns: ColumnsType<User> = [
    { title: '姓名', dataIndex: 'name' },
    { title: '邮箱', dataIndex: 'email' },
  ];

  return (
    <GenericTable
      data={users}
      columns={columns}
      onRowClick={(user) => console.log(user)}
    />
  );
};
```

### 表单泛型包装器

```typescript
// 示例 2：泛型表单包装器
interface GenericFormProps<T> {
  initialValues?: T;
  onFinish: (values: T) => void;
  children: React.ReactNode;
}

function GenericForm<T extends Record<string, any>>({
  initialValues,
  onFinish,
  children,
}: GenericFormProps<T>) {
  const [form] = Form.useForm<T>();

  return (
    <Form<T>
      form={form}
      initialValues={initialValues}
      onFinish={onFinish}
    >
      {children}
    </Form>
  );
}

// 使用
interface LoginFormValues {
  username: string;
  password: string;
  remember?: boolean;
}

const LoginPage: React.FC = () => {
  const handleSubmit = (values: LoginFormValues) => {
    console.log(values);
    // values.username, values.password 类型安全
  };

  return (
    <GenericForm<LoginFormValues>
      initialValues={{ username: '', password: '' }}
      onFinish={handleSubmit}
    >
      <Form.Item name="username" label="用户名">
        <Input />
      </Form.Item>
      <Form.Item name="password" label="密码">
        <Input.Password />
      </Form.Item>
    </GenericForm>
  );
};
```

### 类型约束与推导

使用类型约束确保泛型参数满足特定条件：

```typescript
// 示例 3：带类型约束的泛型组件
interface Entity {
  id: number | string;
}

// T 必须包含 id 字段
function EntityList<T extends Entity>({ data }: { data: T[] }) {
  return (
    <Table<T>
      dataSource={data}
      columns={[
        {
          title: 'ID',
          dataIndex: 'id',
          key: 'id',
          sorter: (a, b) => {
            // a.id, b.id 类型安全（number | string）
            if (typeof a.id === 'number' && typeof b.id === 'number') {
              return a.id - b.id;
            }
            return String(a.id).localeCompare(String(b.id));
          },
        },
      ]}
    />
  );
}

// 使用
interface User extends Entity {
  name: string;
}

const UserList: React.FC = () => {
  const users: User[] = [
    { id: 1, name: 'John' },
    { id: 2, name: 'Jane' },
  ];

  return <EntityList data={users} />;
};
```

### 条件类型

使用条件类型实现高级类型逻辑：

```typescript
// 示例 4：条件类型
type DataType<T> = T extends TableProps<infer U> ? U : never;

// 从 TableProps 提取数据类型
type UserTableDataType = DataType<TableProps<User>>; // User

// 示例 5：根据属性类型返回不同类型
type FieldType<T, K extends keyof T> = T[K] extends string
  ? InputProps
  : T[K] extends number
  ? InputProps & { type: 'number' }
  : T[K] extends boolean
  ? { type: 'checkbox' }
  : InputProps;

// 动态生成表单项
function FormField<T extends Record<string, any>, K extends keyof T>({
  name,
  label,
}: {
  name: K;
  label: string;
}) {
  return <Form.Item name={name as string} label={label} />;
}
```

---

## 类型推导技巧

### infer 关键字

使用 `infer` 推导类型：

```typescript
// 推导 Promise 返回类型
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;

type User = { name: string };
type AsyncUser = Promise<User>;

type Mapped = UnwrapPromise<AsyncUser>; // { name: string }

// 推导数组元素类型
type ElementType<T> = T extends (infer U)[] ? U : never;

type Users = User[];
type OneUser = ElementType<Users>; // User

// 推导函数返回类型
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any;

type Fn = () => User;
type FnReturn = ReturnType<Fn>; // User
```

### 组件 Props 推导

从组件推导 Props 类型：

```typescript
import { Button, Input } from 'antd';

// 推导组件 Props 类型
type ButtonPropsType = React.ComponentProps<typeof Button>;
type InputPropsType = React.ComponentProps<typeof Input>;

// 提取部分 Props
type BaseButtonProps = Pick<ButtonPropsType, 'type' | 'size' | 'disabled'>;

// 扩展 Props
type ExtendedButtonProps = BaseButtonProps & {
  customProp: string;
};

// 使用
function CustomButton({ type, size, disabled, customProp }: ExtendedButtonProps) {
  return <Button type={type} size={size} disabled={disabled}>{customProp}</Button>;
}
```

### 表单值推导

从表单配置推导表单值类型：

```typescript
// 表单项配置
interface FormItemConfig {
  name: string;
  type: 'text' | 'number' | 'email' | 'password';
  label: string;
  required?: boolean;
}

// 从配置推导表单值类型
type FormValuesFromConfig<T extends FormItemConfig[]> = {
  [K in T[number]['name']]: Extract<T[number], { name: K }> extends infer Item
    ? Item extends { type: 'number' }
      ? number
      : string
    : never;
};

// 使用
const formConfig = [
  { name: 'username', type: 'text' as const, label: '用户名' },
  { name: 'age', type: 'number' as const, label: '年龄' },
  { name: 'email', type: 'email' as const, label: '邮箱' },
] as const;

type LoginFormValues = FormValuesFromConfig<typeof formConfig>;
// {
//   username: string;
//   age: number;
//   email: string;
// }
```

---

## 类型增强

### 模块声明（Module Augmentation）

扩展 Ant Design 组件的类型：

```typescript
// antd.d.ts
import { ConfigProviderProps } from 'antd';

// 扩展 ConfigProvider 主题类型
declare module 'antd' {
  interface ThemeConfig {
    // 添加自定义 Token
    customColor?: string;
    customBorderRadius?: number;
  }
}

// 使用
const customTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    customColor: '#52c41a', // ✅ 类型安全
    customBorderRadius: 12,  // ✅ 类型安全
  },
};
```

### 组件 Props 扩展

```typescript
// 扩展 Button Props
declare module 'antd' {
  interface ButtonProps {
    // 添加自定义属性
    loadingText?: string;
    customData?: Record<string, any>;
  }
}

// 使用
<Button
  type="primary"
  loading={true}
  loadingText="加载中..."  // ✅ 类型安全
>
  点击
</Button>
```

### 类型合并

```typescript
// 合并多个组件类型
import type { ButtonProps, InputProps } from 'antd';

type ButtonInputProps = ButtonProps & InputProps & {
  // 解决冲突属性
  size?: ButtonProps['size']; // 使用 Button 的 size
  type?: ButtonProps['type']; // 使用 Button 的 type
  // Input 的其他属性
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
};

// 使用
function HybridButtonInput(props: ButtonInputProps) {
  return <div>{/* ... */}</div>;
}
```

### 全局类型声明

```typescript
// global.d.ts
import { FormInstance } from 'antd';

// 全局表单实例类型
declare global {
  interface Window {
    formInstances: {
      [key: string]: FormInstance;
    };
  }
}

// 使用
window.formInstances = {
  loginForm: loginFormInstance,
  registerForm: registerFormInstance,
};
```

---

## 实用类型工具

### 常用 Utility Types

```typescript
// Partial - 所有属性变为可选
type PartialUser = Partial<User>;
// { id?: number; name?: string; email?: string; }

// Required - 所有属性变为必需
type RequiredUser = Required<Partial<User>>;
// { id: number; name: string; email: string; }

// Readonly - 所有属性变为只读
type ReadonlyUser = Readonly<User>;
// { readonly id: number; readonly name: number; ... }

// Pick - 选择部分属性
type UserName = Pick<User, 'name' | 'email'>;
// { name: string; email: string; }

// Omit - 排除部分属性
type UserWithoutId = Omit<User, 'id'>;
// { name: string; email: string; }

// Record - 构造对象类型
type UserRecord = Record<string, User>;
// { [key: string]: User; }

// Extract - 提取联合类型中的指定类型
type StringType = Extract<string | number, string>;
// string

// Exclude - 排除联合类型中的指定类型
type NonString = Exclude<string | number, string>;
// number
```

### 自定义类型工具

```typescript
// 深度 Partial
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object
    ? DeepPartial<T[P]>
    : T[P];
};

// 深度 Required
type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object
    ? DeepRequired<T[P]>
    : T[P];
};

// 只读可选
type ReadonlyPartial<T> = {
  readonly [P in keyof T]?: T[P];
};

// 提取函数属性
type FunctionPropertyNames<T> = {
  [K in keyof T]: T[K] extends Function ? K : never;
}[keyof T];

type FunctionProperties<T> = Pick<T, FunctionPropertyNames<T>>;

// 提取对象属性
type NonFunctionPropertyNames<T> = {
  [K in keyof T]: T[K] extends Function ? never : K;
}[keyof T];

type NonFunctionProperties<T> = Pick<T, NonFunctionPropertyNames<T>>;

// 使用
interface User {
  id: number;
  name: string;
  getName(): string;
  setName(name: string): void;
}

type UserDataOnly = NonFunctionProperties<User>;
// { id: number; name: string; }

type UserMethodsOnly = FunctionProperties<User>;
// { getName(): string; setName(name: string): void; }
```

---

## 最佳实践

### ✅ 推荐做法

```typescript
// 1. 使用泛型参数增强类型安全
const [form] = Form.useForm<UserFormValues>();
const data = await form.validateFields(); // 返回 UserFormValues

// 2. 明确指定组件 Props 类型
interface CustomButtonProps extends ButtonProps {
  loadingText?: string;
}

// 3. 使用类型推导而非 any
const columns: ColumnsType<User> = [
  {
    dataIndex: 'name',
    render: (value, record: User) => {
      // value 类型为 string
      // record 类型为 User
      return <span>{record.name}</span>;
    },
  },
];

// 4. 为表单定义明确的值类型
interface LoginFormValues {
  username: string;
  password: string;
  remember?: boolean;
}

const LoginForm: React.FC = () => {
  const [form] = Form.useForm<LoginFormValues>();
  // ...
};

// 5. 使用类型工具简化代码
type UserFormData = Omit<User, 'id'>; // 排除 id 字段

// 6. 为泛型组件提供合理的默认类型
interface GenericListProps<T = any> {
  data: T[];
  renderItem: (item: T) => React.ReactNode;
}

// 7. 使用条件类型实现高级类型逻辑
type FieldType<T> = T extends string
  ? 'text'
  : T extends number
  ? 'number'
  : 'text';
```

### ❌ 避免的做法

```typescript
// 1. 避免使用 any
const columns: ColumnsType<any> = [
  {
    render: (value: any, record: any) => {
      // 类型不安全
      return record.invalidProperty;
    },
  },
];

// 2. 避免类型断言（除非确信类型正确）
const user = data as User; // ❌ 不安全
const user = data; // ✅ 让 TypeScript 推导

// 3. 避免忽略类型检查
// @ts-ignore
const value: any = form.getFieldValue('name');

// 4. 避免过度使用泛型
// ❌ 过于复杂
interface SuperGeneric<T extends Record<string, any>, K extends keyof T> {
  // ...
}

// ✅ 简单明了
interface UserFormProps {
  user: User;
}
```

---

## 常见问题

### Q1: 如何为 Form.Item 的 name 属性获得类型提示？

**A**: 使用泛型参数和模板字面量类型：

```typescript
interface UserFormValues {
  name: string;
  email: string;
  age: number;
}

const UserForm: React.FC = () => {
  const [form] = Form.useForm<UserFormValues>();

  return (
    <Form form={form}>
      {/* name 属性有类型提示 */}
      <Form.Item name="name" label="姓名">
        <Input />
      </Form.Item>

      {/* <Form.Item name="invalid" label="无效字段">
        TypeScript 报错：'invalid' 不在联合类型中
      </Form.Item> */}
    </Form>
  );
};
```

### Q2: 如何从 Table 的 dataSource 推导 columns 类型？

**A**: 使用 `ColumnsType` 泛型：

```typescript
interface User {
  id: number;
  name: string;
}

const UserTable: React.FC = () => {
  const [data, setData] = React.useState<User[]>([]);

  const columns: ColumnsType<User> = [
    {
      title: '姓名',
      dataIndex: 'name',
      render: (value, record) => {
        // record 类型为 User
        return <span>{record.name}</span>;
      },
    },
  ];

  return <Table<User> dataSource={data} columns={columns} />;
};
```

### Q3: 如何扩展 Ant Design 组件的类型？

**A**: 使用模块声明（module augmentation）：

```typescript
// antd.d.ts
declare module 'antd' {
  interface ButtonProps {
    customProp?: string;
  }

  interface ThemeConfig {
    customToken?: string;
  }
}

// 使用
<Button customProp="value" />
<ConfigProvider theme={{ customToken: '#fff' }} />
```

### Q4: 如何处理表单的嵌套数据类型？

**A**: 定义嵌套的表单值类型：

```typescript
interface AddressFormValues {
  street: string;
  city: string;
  zipCode: string;
}

interface UserFormValues {
  name: string;
  email: string;
  address: AddressFormValues;
}

const UserForm: React.FC = () => {
  const [form] = Form.useForm<UserFormValues>();

  form.setFieldsValue({
    name: 'John',
    email: 'john@example.com',
    address: {
      street: 'Main St',
      city: 'New York',
      zipCode: '10001',
    },
  });

  return (
    <Form form={form}>
      <Form.Item name="name">
        <Input />
      </Form.Item>
      <Form.Item name={['address', 'street']}>
        <Input />
      </Form.Item>
      <Form.Item name={['address', 'city']}>
        <Input />
      </Form.Item>
      <Form.Item name={['address', 'zipCode']}>
        <Input />
      </Form.Item>
    </Form>
  );
};
```

### Q5: 如何为自定义组件添加 Ant Design 组件的类型？

**A**: 使用 `extends` 继承组件类型：

```typescript
import type { InputProps, InputRef } from 'antd';

interface CustomInputProps extends Omit<InputProps, 'ref'> {
  customProp?: string;
}

const CustomInput = React.forwardRef<InputRef, CustomInputProps>(
  ({ customProp, ...rest }, ref) => {
    return <Input ref={ref} {...rest} />;
  }
);

// 使用
<CustomInput
  customProp="value"
  placeholder="输入"
  onPressEnter={(e) => {
    // e 类型为 React.KeyboardEvent<HTMLInputElement>
  }}
/>
```

### Q6: 如何处理 Table 的 sorter 和 filter 类型？

**A**: 使用泛型参数确保类型安全：

```typescript
interface User {
  id: number;
  name: string;
  age: number;
  role: 'admin' | 'user';
}

const columns: ColumnsType<User> = [
  {
    title: '姓名',
    dataIndex: 'name',
    sorter: (a: User, b: User) => a.name.localeCompare(b.name),
  },
  {
    title: '年龄',
    dataIndex: 'age',
    sorter: (a: User, b: User) => a.age - b.age,
    filters: [
      { text: '年龄 > 30', value: 'gt30' },
      { text: '年龄 <= 30', value: 'lte30' },
    ],
    onFilter: (value: string | number | boolean, record: User) => {
      return value === 'gt30' ? record.age > 30 : record.age <= 30;
    },
  },
  {
    title: '角色',
    dataIndex: 'role',
    filters: [
      { text: '管理员', value: 'admin' },
      { text: '用户', value: 'user' },
    ],
    onFilter: (value: string | number | boolean, record: User) => {
      return record.role === value;
    },
  },
];
```

### Q7: 如何为动态表单生成类型？

**A**: 使用工具类型从配置推导类型：

```typescript
interface FormFieldConfig {
  name: string;
  type: 'text' | 'number' | 'email' | 'password';
  label: string;
}

type FormValuesFromFields<T extends FormFieldConfig[]> = {
  [K in T[number]['name']]: Extract<T[number], { name: K }> extends infer Field
    ? Field extends { type: 'number' }
      ? number
      : string
    : never;
};

const formFields: FormFieldConfig[] = [
  { name: 'username', type: 'text', label: '用户名' },
  { name: 'age', type: 'number', label: '年龄' },
] as const;

type FormValues = FormValuesFromFields<typeof formFields>;
// { username: string; age: number; }
```

### Q8: 如何处理 ConfigProvider 的 theme 类型？

**A**: 使用 `ThemeConfig` 类型：

```typescript
import type { ThemeConfig } from 'antd';

const customTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 8,
  },
  components: {
    Button: {
      colorPrimary: '#00b96b',
      algorithm: true,
    },
    Input: {
      colorBgContainer: '#f0f0f0',
    },
  },
};

<ConfigProvider theme={customTheme}>
  <App />
</ConfigProvider>
```

---

## 参考资源

- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [Ant Design TypeScript 指南](https://ant.design/docs/react/typescript-cn)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Utility Types 参考](https://www.typescriptlang.org/docs/handbook/utility-types.html)
