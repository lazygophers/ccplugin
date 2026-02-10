---
name: antd-troubleshooting-skills
description: Ant Design 问题排查完整指南 - 常见错误、调试技巧、性能问题、兼容性问题
---

# antd-troubleshooting: Ant Design 问题排查完整指南

Ant Design 问题排查指南提供了系统化的调试方法、常见错误解决方案、性能优化技巧和兼容性处理方案，帮助开发者快速定位和解决使用 Ant Design 过程中遇到的各种问题。

---

## 概述

### 问题排查方法论

**问题排查五步法**:

1. **问题复现** - 在可控环境中重现问题
2. **信息收集** - 收集错误信息、控制台日志、网络请求
3. **隔离定位** - 缩小问题范围，确定问题组件或代码段
4. **假设验证** - 提出解决方案假设并验证
5. **修复验证** - 实施修复并验证问题解决

### 核心特性

- **系统化调试流程** - 提供完整的问题排查步骤
- **常见错误库** - 涵盖 80% 常见问题的解决方案
- **性能分析工具** - 定位和解决性能瓶颈
- **兼容性指南** - 处理浏览器、React 版本兼容问题
- **调试工具集成** - React DevTools、浏览器开发者工具等
- **最佳实践对比** - ✅/❌ 对比展示正确和错误用法

---

## 开发工具

### React DevTools

#### 安装与配置

```bash
# Chrome/Edge
npm install --save-dev react-devtools

# Firefox
npm install --save-dev react-devtools
```

#### 使用技巧

**1. 查看组件 Props 和 State**

```tsx
import { Button } from 'antd';

function MyComponent() {
  const [loading, setLoading] = useState(false);

  return (
    <Button
      type="primary"
      loading={loading}
      onClick={() => setLoading(true)}
    >
      Click Me
    </Button>
  );
}

// 在 React DevTools 中：
// 1. 选择 Button 组件
// 2. 在右侧面板查看 props: { type: "primary", loading: true, onClick: ... }
// 3. 查看 State: { loading: true }
```

**2. 追踪组件渲染**

```tsx
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  console.log({
    id,
    phase,
    actualDuration,
    baseDuration,
    startTime,
    commitTime,
  });
}

function ProfiledApp() {
  return (
    <Profiler id="Button" onRender={onRenderCallback}>
      <Button type="primary">Profiled Button</Button>
    </Profiler>
  );
}
```

**3. 调试 Context**

```tsx
import { ConfigProvider } from 'antd';

// 在 React DevTools 中查看 Context
// 1. 选择任意组件
// 2. 在右侧面板查看 context
// 3. 可以看到 ConfigProvider 提供的 theme、locale 等配置
```

### 浏览器开发者工具

#### Chrome DevTools

**1. 元素检查**

```tsx
// 检查 Ant Design 组件的 DOM 结构
<Button type="primary">Click Me</Button>

// DOM 结构：
// <button class="ant-btn ant-btn-primary">
//   <span>Click Me</span>
// </button>

// 调试步骤：
// 1. 右键点击按钮 -> 检查
// 2. 查看 .ant-btn 和 .ant-btn-primary 类
// 3. 在 Styles 面板查看应用的样式
// 4. 检查是否有样式被覆盖
```

**2. Console 调试**

```tsx
import { message } from 'antd';

// 使用 console.log 调试
function handleClick() {
  console.log('Button clicked');

  message.success('Success!')
    .then(() => {
      console.log('Message displayed');
    })
    .catch((error) => {
      console.error('Message error:', error);
    });
}

// 使用 console.table 查看数据
const data = [
  { key: '1', name: 'John', age: 32 },
  { key: '2', name: 'Jane', age: 28 },
];

console.table(data);

// 使用 console.group 组织日志
console.group('Table Rendering');
console.log('Data source:', data);
console.log('Columns:', columns);
console.groupEnd();
```

**3. 网络请求调试**

```tsx
import { Table } from 'antd';

function DataTable() {
  const [data, setData] = useState([]);

  const fetchData = async () => {
    console.time('fetchData');

    try {
      const response = await fetch('/api/data');
      const json = await response.json();

      console.timeEnd('fetchData');
      console.log('Response:', json);

      setData(json);
    } catch (error) {
      console.error('Fetch error:', error);

      // 在 Network 面板查看请求详情
      // 1. 打开 Network 面板
      // 2. 找到 /api/data 请求
      // 3. 查看 Headers、Preview、Response 等信息
    }
  };

  return <Table dataSource={data} columns={columns} />;
}
```

**4. 性能分析**

```tsx
// 使用 Performance API
function PerformanceTest() {
  useEffect(() => {
    const startTime = performance.now();

    // 执行操作
    const data = Array(10000).fill(0).map((_, i) => ({ id: i }));

    const endTime = performance.now();

    console.log(`Operation took ${endTime - startTime}ms`);

    // 使用 Performance 面板
    // 1. 打开 Performance 面板
    // 2. 点击 Record
    // 3. 执行操作
    // 4. 停止录制并分析结果
  }, []);

  return <div>Performance Test</div>;
}
```

### Ant Design 专用工具

#### Ant Design Theme Editor

```bash
# 安装主题编辑器
npm install -g @ant-design/theme-editor

# 启动主题编辑器
ant-design-theme-editor
```

#### antd-tools

```bash
# 安装 antd-tools
npm install -g antd-tools

# 检查 Ant Design 版本
antd-tools --version

# 检查依赖冲突
antd-tools check-dependencies
```

---

## 常见错误类型

### 样式问题

#### 问题 1: 样式不生效

**症状**: 组件样式与预期不符，自定义样式无法覆盖

**原因分析**:

1. CSS 优先级问题
2. ConfigProvider 配置错误
3. 内联样式覆盖
4. 类名冲突

**解决方案**:

```tsx
// ❌ 错误：样式优先级不够
<style>
  .custom-button {
    background-color: red;
  }
</style>
<Button className="custom-button">Click</Button>

// ✅ 正确：使用 :global 提高优先级
<style>
  .custom-button :global(.ant-btn) {
    background-color: red !important;
  }
</style>

// ✅ 正确：使用 ConfigProvider
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: 'red',
      },
    },
  }}
>
  <Button type="primary">Click</Button>
</ConfigProvider>

// ✅ 正确：使用内联样式
<Button style={{ backgroundColor: 'red' }}>Click</Button>
```

#### 问题 2: 主题颜色不生效

**症状**: 修改 ConfigProvider theme 后，组件颜色没有变化

**原因分析**:

1. Token 名称错误
2. ConfigProvider 未包裹组件
3. 组件使用了内联样式

**解决方案**:

```tsx
// ❌ 错误：Token 名称错误
<ConfigProvider
  theme={{
    token: {
      primaryColor: '#1890ff', // 错误：应该是 colorPrimary
    },
  }}
>
  <Button type="primary">Click</Button>
</ConfigProvider>

// ✅ 正确：使用正确的 Token 名称
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
    },
  }}
>
  <Button type="primary">Click</Button>
</ConfigProvider>

// ✅ 正确：组件级别配置
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: '#722ed1',
      },
    },
  }}
>
  <Button type="primary">Click</Button>
</ConfigProvider>
```

#### 问题 3: 响应式样式失效

**症状**: 在不同屏幕尺寸下，样式表现不一致

**解决方案**:

```tsx
import { Grid, Button } from 'antd';

const { useBreakpoint } = Grid;

function ResponsiveButton() {
  const screens = useBreakpoint();

  return (
    <Button
      type="primary"
      size={screens.xs ? 'small' : 'large'}
      style={{
        width: screens.xs ? '100%' : 'auto',
      }}
    >
      Responsive Button
    </Button>
  );
}

// 或者使用 CSS Grid
function ResponsiveLayout() {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 16,
      }}
    >
      <Button>Button 1</Button>
      <Button>Button 2</Button>
      <Button>Button 3</Button>
    </div>
  );
}
```

### 渲染问题

#### 问题 1: 组件不渲染

**症状**: 组件没有显示在页面上

**原因分析**:

1. 组件未导入
2. 条件渲染错误
3. 错误导致组件崩溃
4. CSS 隐藏了组件

**解决方案**:

```tsx
// ❌ 错误：未导入组件
function App() {
  return <Button type="primary">Click</Button>;
  // Error: Button is not defined
}

// ✅ 正确：导入组件
import { Button } from 'antd';

function App() {
  return <Button type="primary">Click</Button>;
}

// ❌ 错误：条件渲染错误
function App() {
  const [show, setShow] = useState(false);

  return (
    <>
      {show && <Button type="primary">Click</Button>}
      {/* Button 永远不会显示，因为 show 初始为 false */}
    </>
  );
}

// ✅ 正确：使用正确的条件渲染
function App() {
  const [show, setShow] = useState(true);

  if (!show) return null;

  return <Button type="primary">Click</Button>;
}

// 调试技巧：添加错误边界
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }

    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Button type="primary">Click</Button>
    </ErrorBoundary>
  );
}
```

#### 问题 2: 组件渲染性能差

**症状**: 页面卡顿、滚动不流畅

**原因分析**:

1. 不必要的重渲染
2. 大列表未使用虚拟滚动
3. 复杂计算未优化

**解决方案**:

```tsx
import { List } from 'antd';
import { useMemo, useCallback } from 'react';

// ❌ 错误：每次渲染都重新创建数据
function BadList() {
  const data = Array(10000).fill(0).map((_, i) => ({
    id: i,
    name: `Item ${i}`,
  }));

  return <List dataSource={data} renderItem={(item) => <List.Item>{item.name}</List.Item>} />;
}

// ✅ 正确：使用 useMemo 缓存数据
function GoodList() {
  const data = useMemo(
    () =>
      Array(10000).fill(0).map((_, i) => ({
        id: i,
        name: `Item ${i}`,
      })),
    []
  );

  return <List dataSource={data} renderItem={(item) => <List.Item>{item.name}</List.Item>} />;
}

// ✅ 更好：使用虚拟滚动
function VirtualList() {
  const data = Array(100000).fill(0).map((_, i) => ({
    id: i,
    name: `Item ${i}`,
  }));

  return (
    <List
      dataSource={data}
      renderItem={(item) => <List.Item>{item.name}</List.Item>}
      pagination={{
        pageSize: 20,
      }}
    />
  );
}

// ✅ 使用 useCallback 避免函数重新创建
function ButtonList() {
  const handleClick = useCallback((id: number) => {
    console.log('Clicked:', id);
  }, []);

  return (
    <div>
      {Array(100).fill(0).map((_, i) => (
        <Button key={i} onClick={() => handleClick(i)}>
          Button {i}
        </Button>
      ))}
    </div>
  );
}
```

#### 问题 3: 组件闪烁

**症状**: 组件在加载时短暂闪烁

**解决方案**:

```tsx
import { Spin } from 'antd';

// ❌ 错误：加载时显示空白
function DataDisplay() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData().then(setData);
  }, []);

  return <div>{data && <Table dataSource={data} />}</div>;
}

// ✅ 正确：显示加载状态
function DataDisplay() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Spin />;
  }

  return <Table dataSource={data} />;
}

// ✅ 更好：使用骨架屏
import { Skeleton } from 'antd';

function DataDisplay() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Skeleton active />;
  }

  return <Table dataSource={data} />;
}
```

### 表单问题

#### 问题 1: 表单验证失效

**症状**: 表单提交时验证不生效

**原因分析**:

1. Form.Item 未设置 name
2. rules 配置错误
3. 未使用 Form.useForm()
4. 自定义验证逻辑错误

**解决方案**:

```tsx
import { Form, Input, Button } from 'antd';

// ❌ 错误：Form.Item 未设置 name
function BadForm() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    console.log(values);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.Item rules={[{ required: true }]}>
        <Input placeholder="Username" />
      </Form.Item>
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}

// ✅ 正确：设置 name 和 rules
function GoodForm() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    console.log(values);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.Item
        name="username"
        label="Username"
        rules={[
          { required: true, message: 'Please input your username!' },
          { min: 3, message: 'Username must be at least 3 characters!' },
        ]}
      >
        <Input placeholder="Username" />
      </Form.Item>
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}

// ✅ 自定义验证
function CustomValidationForm() {
  const [form] = Form.useForm();

  const validateUsername = async (_rule, value) => {
    if (!value) {
      return Promise.reject('Please input your username!');
    }
    if (value.length < 3) {
      return Promise.reject('Username must be at least 3 characters!');
    }
    if (!/^[a-zA-Z0-9]+$/.test(value)) {
      return Promise.reject('Username can only contain letters and numbers!');
    }
    return Promise.resolve();
  };

  return (
    <Form form={form}>
      <Form.Item
        name="username"
        label="Username"
        rules={[{ validator: validateUsername }]}
      >
        <Input placeholder="Username" />
      </Form.Item>
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}
```

#### 问题 2: 表单初始值不生效

**症状**: initialValues 设置后，表单字段没有初始值

**解决方案**:

```tsx
// ❌ 错误：initialValues 在表单创建后设置
function BadForm() {
  const [form] = Form.useForm();
  const [initialValues, setInitialValues] = useState({});

  useEffect(() => {
    setInitialValues({ username: 'john' });
  }, []);

  return (
    <Form form={form} initialValues={initialValues}>
      <Form.Item name="username">
        <Input />
      </Form.Item>
    </Form>
  );
}

// ✅ 正确：使用 form.setFieldsValue
function GoodForm() {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue({ username: 'john' });
  }, []);

  return (
    <Form form={form}>
      <Form.Item name="username">
        <Input />
      </Form.Item>
    </Form>
  );
}

// ✅ 正确：异步数据加载
function AsyncForm() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData()
      .then((response) => {
        setData(response);
        form.setFieldsValue(response);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Spin />;
  }

  return (
    <Form form={form}>
      <Form.Item name="username">
        <Input />
      </Form.Item>
    </Form>
  );
}
```

#### 问题 3: 动态表单字段问题

**症状**: 动态添加/删除的表单字段无法正常工作

**解决方案**:

```tsx
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

function DynamicForm() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    console.log('Received values of form:', values);
  };

  return (
    <Form form={form} onFinish={onFinish} autoComplete="off">
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
}
```

### 表格问题

#### 问题 1: Table 性能问题

**症状**: 大数据量时表格卡顿

**解决方案**:

```tsx
import { Table } from 'antd';

// ❌ 错误：一次性渲染大量数据
function BadTable() {
  const data = Array(10000).fill(0).map((_, i) => ({
    key: i,
    name: `User ${i}`,
    age: Math.floor(Math.random() * 100),
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  return <Table dataSource={data} columns={columns} />;
}

// ✅ 正确：使用分页
function GoodTable() {
  const data = Array(10000).fill(0).map((_, i) => ({
    key: i,
    name: `User ${i}`,
    age: Math.floor(Math.random() * 100),
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  return (
    <Table
      dataSource={data}
      columns={columns}
      pagination={{
        pageSize: 50,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `Total ${total} items`,
      }}
    />
  );
}

// ✅ 更好：使用虚拟滚动
import { Table } from 'antd';

function VirtualTable() {
  const data = Array(100000).fill(0).map((_, i) => ({
    key: i,
    name: `User ${i}`,
    age: Math.floor(Math.random() * 100),
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  return (
    <Table
      dataSource={data}
      columns={columns}
      scroll={{ y: 500 }}
      pagination={false}
      virtual
      rowHeight={54}
    />
  );
}
```

#### 问题 2: 列渲染错误

**症状**: 列显示内容不正确或报错

**解决方案**:

```tsx
// ❌ 错误：dataIndex 错误
function BadTable() {
  const data = [
    { id: 1, userName: 'John' },
    { id: 2, userName: 'Jane' },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    // dataIndex 应该是 'userName' 而不是 'name'
  ];

  return <Table dataSource={data} columns={columns} />;
}

// ✅ 正确：使用正确的 dataIndex
function GoodTable() {
  const data = [
    { id: 1, userName: 'John' },
    { id: 2, userName: 'Jane' },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'userName', key: 'userName' },
  ];

  return <Table dataSource={data} columns={columns} />;
}

// ✅ 使用 render 自定义渲染
function CustomRenderTable() {
  const data = [
    { id: 1, firstName: 'John', lastName: 'Doe' },
    { id: 2, firstName: 'Jane', lastName: 'Smith' },
  ];

  const columns = [
    {
      title: 'Name',
      key: 'name',
      render: (_text, record) => `${record.firstName} ${record.lastName}`,
    },
  ];

  return <Table dataSource={data} columns={columns} />;
}
```

#### 问题 3: 排序和筛选问题

**症状**: 排序和筛选不工作

**解决方案**:

```tsx
// ❌ 错误：未设置 sorter
function BadTable() {
  const data = [
    { key: '1', name: 'John Brown', age: 32 },
    { key: '2', name: 'Jim Green', age: 42 },
    { key: '3', name: 'Joe Black', age: 28 },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  return <Table dataSource={data} columns={columns} />;
}

// ✅ 正确：配置 sorter
function GoodTable() {
  const data = [
    { key: '1', name: 'John Brown', age: 32 },
    { key: '2', name: 'Jim Green', age: 42 },
    { key: '3', name: 'Joe Black', age: 28 },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
      sorter: (a, b) => a.age - b.age,
      sortDirections: ['descend', 'ascend'],
    },
  ];

  return <Table dataSource={data} columns={columns} />;
}

// ✅ 远程排序和筛选
function RemoteTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  const fetchData = async (params = {}) => {
    setLoading(true);
    try {
      const response = await fetch('/api/data', {
        method: 'POST',
        body: JSON.stringify(params),
      });
      const json = await response.json();

      setData(json.data);
      setPagination({
        ...pagination,
        total: json.total,
      });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
    },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
      sorter: true,
    },
  ];

  const handleTableChange = (pagination, filters, sorter) => {
    fetchData({
      page: pagination.current,
      pageSize: pagination.pageSize,
      sortField: sorter.field,
      sortOrder: sorter.order,
      ...filters,
    });
  };

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="key"
      pagination={pagination}
      loading={loading}
      onChange={handleTableChange}
    />
  );
}
```

### 日期问题

#### 问题 1: DatePicker 日期格式错误

**症状**: 日期显示格式不正确或提交后格式错误

**解决方案**:

```tsx
import { DatePicker } from 'antd';
import dayjs from 'dayjs';

// ❌ 错误：使用原生 Date 对象
function BadDatePicker() {
  const [date, setDate] = useState(new Date());

  return (
    <DatePicker
      value={date}
      onChange={(date) => setDate(date)}
    />
  );
}

// ✅ 正确：使用 dayjs 对象
function GoodDatePicker() {
  const [date, setDate] = useState(dayjs());

  return (
    <DatePicker
      value={date}
      onChange={(date) => setDate(date)}
    />
  );
}

// ✅ 正确：提交时转换格式
function FormDatePicker() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    // 将 dayjs 对象转换为字符串
    const submitData = {
      ...values,
      birthDate: values.birthDate.format('YYYY-MM-DD'),
    };
    console.log(submitData);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.Item name="birthDate" label="Birth Date" rules={[{ required: true }]}>
        <DatePicker />
      </Form.Item>
      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}
```

#### 问题 2: 时区问题

**症状**: 日期显示与实际不符

**解决方案**:

```tsx
import { DatePicker } from 'antd';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

function TimeZonePicker() {
  const handleChange = (date) => {
    // 转换为 UTC
    const utcDate = date.utc();
    console.log('UTC:', utcDate.format());

    // 转换为特定时区
    const tzDate = date.tz('America/New_York');
    console.log('New York:', tzDate.format());
  };

  return (
    <DatePicker showTime onChange={handleChange} />
  );
}
```

### 图标问题

#### 问题 1: 图标不显示

**症状**: 图标组件使用后不显示

**原因分析**:

1. 未安装 @ant-design/icons
2. 图标名称错误
3. 图标未正确导入

**解决方案**:

```tsx
// ❌ 错误：未安装图标包
function BadIcon() {
  return <SearchOutlined />;
  // Error: SearchOutlined is not defined
}

// ✅ 正确：安装并导入图标包
import { SearchOutlined } from '@ant-design/icons';

function GoodIcon() {
  return <SearchOutlined />;
}

// ✅ 使用自定义图标
import { Icon } from '@ant-design/icons';

const CustomIcon = (props) => (
  <svg viewBox="0 0 1024 1024" width="1em" height="1em" fill="currentColor" {...props}>
    <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" />
  </svg>
);

function App() {
  return <Icon component={CustomIcon} />;
}
```

---

## 具体问题排查

### 样式不生效

#### 排查步骤

1. **检查 CSS 加载**

```tsx
// 在浏览器控制台检查
document.styleSheets; // 查看所有样式表

// 检查特定样式
window.getComputedStyle(document.querySelector('.ant-btn'));
```

2. **检查类名**

```tsx
// 检查元素类名
console.log(document.querySelector('.ant-btn').className);

// 检查 ConfigProvider 配置
import { ConfigProvider } from 'antd';

<ConfigProvider prefixCls="custom" iconPrefixCls="custom-icon">
  <Button type="primary">Custom Button</Button>
</ConfigProvider>
// 按钮类名变为 .custom-btn 而不是 .ant-btn
```

3. **使用 !important 谨慎**

```tsx
// ❌ 不推荐：过度使用 !important
<style>
  .custom-button {
    background-color: red !important;
    color: blue !important;
    border-color: green !important;
  }
</style>

// ✅ 推荐：提高选择器优先级
<style>
  .parent .custom-button.ant-btn {
    background-color: red;
  }
</style>
```

### 组件不渲染

#### 排查步骤

1. **检查组件导入**

```tsx
// 检查 antd 是否正确安装
npm list antd

// 检查导入路径
import { Button } from 'antd'; // ✅ 正确
import { Button } from 'antd/lib/button'; // ❌ 错误
```

2. **检查 React 版本**

```tsx
// 检查 package.json
{
  "dependencies": {
    "react": "^18.0.0",
    "antd": "^5.0.0"
  }
}

// antd 5.x 需要 React >= 16.9.0
```

3. **检查错误边界**

```tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h2>Something went wrong!</h2>
          <pre>{this.state.error?.stack}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}

// 使用错误边界包裹可疑组件
<ErrorBoundary>
  <ProblematicComponent />
</ErrorBoundary>
```

### 表单验证失效

#### 排查步骤

1. **检查 Form 配置**

```tsx
import { Form } from 'antd';

function DebugForm() {
  const [form] = Form.useForm();

  // 检查表单实例
  console.log('Form instance:', form);

  // 手动触发验证
  const handleValidate = async () => {
    try {
      await form.validateFields();
      console.log('Validation passed');
    } catch (error) {
      console.log('Validation failed:', error);
    }
  };

  return (
    <Form form={form}>
      <Form.Item name="username" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Button onClick={handleValidate}>Validate</Button>
    </Form>
  );
}
```

2. **检查字段状态**

```tsx
function FormWithDebug() {
  const [form] = Form.useForm();

  useEffect(() => {
    // 监听表单变化
    const handleFieldsChange = () => {
      console.log('Form values:', form.getFieldsValue());
      console.log('Form fields:', form.getFields());
      console.log('Field errors:', form.getFieldsError());
    };

    const internalHooks = form.getInternalHooks('RC_FORM_INTERNAL_HOOKS');
    const unsubscribe = internalHooks.registerWatch(handleFieldsChange);

    return () => unsubscribe();
  }, []);

  return (
    <Form form={form}>
      <Form.Item name="username" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
    </Form>
  );
}
```

### Table 性能问题

#### 排查步骤

1. **使用 React Profiler**

```tsx
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  console.log({
    id,
    phase,
    actualDuration,
    baseDuration,
  });
}

function ProfiledTable() {
  return (
    <Profiler id="Table" onRender={onRenderCallback}>
      <Table dataSource={data} columns={columns} />
    </Profiler>
  );
}
```

2. **优化渲染**

```tsx
import { memo } from 'react';

// 使用 memo 优化单元格渲染
const CustomCell = memo(({ value }) => {
  console.log('Rendering cell:', value);
  return <span>{value}</span>;
});

// 使用 memo 优化行渲染
const CustomRow = memo(({ record, index }) => {
  console.log('Rendering row:', index);
  return <tr>{/* ... */}</tr>;
});

// 在 columns 中使用
const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    render: (value) => <CustomCell value={value} />,
  },
];
```

3. **使用虚拟滚动**

```tsx
import { Table } from 'antd';

function VirtualizedTable() {
  const data = Array(100000).fill(0).map((_, i) => ({
    key: i,
    name: `User ${i}`,
  }));

  const columns = [{ title: 'Name', dataIndex: 'name' }];

  return (
    <Table
      dataSource={data}
      columns={columns}
      scroll={{ y: 400 }}
      pagination={false}
      virtual
      rowHeight={54}
    />
  );
}
```

### DatePicker 日期错误

#### 排查步骤

1. **检查 dayjs 版本**

```bash
npm list dayjs
# antd 5.x 需要 dayjs >= 1.11.0
```

2. **检查日期格式**

```tsx
import { DatePicker } from 'antd';
import dayjs from 'dayjs';

function DebugDatePicker() {
  const handleChange = (date, dateString) => {
    console.log('dayjs object:', date);
    console.log('formatted string:', dateString);
    console.log('ISO string:', date?.toISOString());
    console.log('Unix timestamp:', date?.unix());
  };

  return (
    <DatePicker
      onChange={handleChange}
      format="YYYY-MM-DD"
    />
  );
}
```

3. **处理时区**

```tsx
import { DatePicker } from 'antd';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

function TimeZoneDatePicker() {
  const handleChange = (date) => {
    // 本地时间
    console.log('Local:', date.format('YYYY-MM-DD HH:mm:ss'));

    // UTC
    console.log('UTC:', date.utc().format('YYYY-MM-DD HH:mm:ss'));

    // 特定时区
    console.log('New York:', date.tz('America/New_York').format('YYYY-MM-DD HH:mm:ss'));
  };

  return (
    <DatePicker showTime onChange={handleChange} />
  );
}
```

### Modal 遮罩问题

#### 排查步骤

1. **检查 z-index**

```tsx
import { Modal } from 'antd';

// 调整 Modal 的 z-index
<Modal
  open={visible}
  zIndex={1000}
>
  Content
</Modal>

// 全局配置
<ConfigProvider
  theme={{
    components: {
      Modal: {
        zIndexPopup: 1000,
      },
    },
  }}
>
  <YourApp />
</ConfigProvider>
```

2. **检查容器挂载**

```tsx
function CustomModalContainer() {
  const modalContainerRef = useRef<HTMLDivElement>(null);

  return (
    <div>
      <div ref={modalContainerRef} id="modal-container" />

      <Modal
        open={visible}
        getContainer={() => modalContainerRef.current || document.body}
      >
        Content
      </Modal>
    </div>
  );
}
```

### Menu 路由不匹配

#### 排查步骤

1. **检查 selectedKeys**

```tsx
import { Menu } from 'antd';
import { useLocation } from 'react-router-dom';

function RouterMenu() {
  const location = useLocation();

  const items = [
    { key: '/home', label: 'Home' },
    { key: '/about', label: 'About' },
    { key: '/contact', label: 'Contact' },
  ];

  // 根据当前路由设置 selectedKeys
  const selectedKeys = [location.pathname];

  return (
    <Menu
      selectedKeys={selectedKeys}
      mode="horizontal"
      items={items}
    />
  );
}
```

2. **自定义匹配逻辑**

```tsx
function CustomMenu() {
  const location = useLocation();

  const getSelectedKey = () => {
    // 自定义路由匹配逻辑
    if (location.pathname.startsWith('/users')) {
      return '/users';
    }
    if (location.pathname.startsWith('/settings')) {
      return '/settings';
    }
    return location.pathname;
  };

  return (
    <Menu
      selectedKeys={[getSelectedKey()]}
      mode="horizontal"
      items={items}
    />
  );
}
```

---

## 调试技巧

### Console 日志

#### 基础日志

```tsx
// console.log - 普通日志
console.log('Component rendered');

// console.info - 信息日志
console.info('Data loaded');

// console.warn - 警告日志
console.warn('Deprecated API used');

// console.error - 错误日志
console.error('Failed to fetch data');

// console.debug - 调试日志（生产环境自动移除）
console.debug('Debugging info');
```

#### 高级日志

```tsx
// console.table - 表格显示
const data = [
  { id: 1, name: 'John', age: 32 },
  { id: 2, name: 'Jane', age: 28 },
];
console.table(data);

// console.group - 分组日志
console.group('Data Fetching');
console.log('Request URL:', url);
console.log('Response:', response);
console.groupEnd();

// console.time / console.timeEnd - 计时
console.time('fetchData');
fetchData().then(() => {
  console.timeEnd('fetchData');
});

// console.count - 计数
function handleClick() {
  console.count('Button clicked');
  // Button clicked: 1
  // Button clicked: 2
  // Button clicked: 3
}

// console.assert - 断言
function validateData(data) {
  console.assert(data.length > 0, 'Data is empty!');
}
```

### 断点调试

#### 使用 debugger

```tsx
function handleClick() {
  debugger; // 执行到这里会暂停

  const data = fetchData();
  console.log(data);
}
```

#### Chrome DevTools 断点

```tsx
// 1. 在 Sources 面板打开文件
// 2. 点击行号设置断点
// 3. 触发事件执行到断点
// 4. 在 Scope 面板查看变量
// 5. 使用 Console 执行表达式

// 条件断点
// 右键点击行号 -> Add conditional breakpoint
// 输入条件：data.length > 100

// 日志断点
// 右键点击行号 -> Add logpoint
// 输入日志：'Data:', data
```

### 网络请求调试

#### Fetch 调试

```tsx
async function fetchData() {
  console.log('Fetching data...');

  try {
    const response = await fetch('/api/data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: 'test' }),
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Response data:', data);

    return data;
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}
```

#### Axios 调试

```tsx
import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 5000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('Request config:', config);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('Response data:', response.data);
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    return Promise.reject(error);
  }
);

// 使用
async function fetchData() {
  try {
    const response = await api.get('/data');
    return response.data;
  } catch (error) {
    console.error('API error:', error);
    throw error;
  }
}
```

### 状态调试

#### Redux DevTools

```tsx
import { configureStore } from '@reduxjs/toolkit';

const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production',
});

// 在组件中查看状态
function MyComponent() {
  const state = useSelector((state) => state);

  useEffect(() => {
    console.log('Current state:', state);
  }, [state]);

  return <div>...</div>;
}
```

#### Context 调试

```tsx
import { createContext, useContext } from 'react';

const MyContext = createContext(null);

function DebugProvider({ children }) {
  const [state, setState] = useState(initialState);

  // 调试 Context 变化
  useEffect(() => {
    console.log('Context state changed:', state);
  }, [state]);

  return (
    <MyContext.Provider value={state}>
      {children}
    </MyContext.Provider>
  );
}

// 在组件中使用
function MyComponent() {
  const context = useContext(MyContext);

  useEffect(() => {
    console.log('Component context:', context);
  }, [context]);

  return <div>...</div>;
}
```

---

## 性能问题排查

### 渲染性能

#### 问题检测

```tsx
import { Profiler, useState } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  console.log({
    id,
    phase,
    actualDuration: `${actualDuration.toFixed(2)}ms`,
    baseDuration: `${baseDuration.toFixed(2)}ms`,
  });
}

function ProfiledApp() {
  const [count, setCount] = useState(0);

  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <div>
        <Button onClick={() => setCount(count + 1)}>Count: {count}</Button>
      </div>
    </Profiler>
  );
}
```

#### 优化方案

```tsx
import { memo, useMemo, useCallback } from 'react';

// 1. 使用 memo 避免不必要的重渲染
const ExpensiveComponent = memo(function ExpensiveComponent({ data }) {
  return <div>{/* ... */}</div>;
});

// 2. 使用 useMemo 缓存计算结果
function DataProcessor({ rawData }) {
  const processedData = useMemo(() => {
    console.log('Processing data...');
    return rawData.map((item) => ({
      ...item,
      processed: true,
    }));
  }, [rawData]);

  return <div>{/* 使用 processedData */}</div>;
}

// 3. 使用 useCallback 缓存函数
function ButtonList() {
  const handleClick = useCallback((id) => {
    console.log('Clicked:', id);
  }, []);

  return (
    <div>
      {Array(100).fill(0).map((_, i) => (
        <Button key={i} onClick={() => handleClick(i)}>
          Button {i}
        </Button>
      ))}
    </div>
  );
}

// 4. 使用虚拟列表
import { List } from 'antd';

function VirtualList({ data }) {
  return (
    <List
      dataSource={data}
      renderItem={(item) => <List.Item>{item.name}</List.Item>}
      pagination={{
        pageSize: 20,
      }}
    />
  );
}
```

### 包体积分析

#### 使用 webpack-bundle-analyzer

```bash
# 安装
npm install --save-dev webpack-bundle-analyzer

# 配置 webpack
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
    }),
  ],
};

# 运行分析
npm run build
# 查看 dist/report.html
```

#### 优化方案

```tsx
// 1. 按需导入 antd 组件
// ❌ 错误：导入整个 antd
import antd from 'antd';

// ✅ 正确：按需导入
import { Button, Input, Table } from 'antd';

// 2. 动态导入
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Spin />}>
      <HeavyComponent />
    </Suspense>
  );
}

// 3. Tree shaking
// 确保 package.json 中设置
{
  "sideEffects": false
}
```

### 内存泄漏

#### 问题检测

```tsx
import { useEffect, useRef } from 'react';

function MemoryLeakDetector() {
  const dataRef = useRef([]);

  useEffect(() => {
    // 定时器未清理
    const interval = setInterval(() => {
      dataRef.current.push(Date.now());
    }, 1000);

    // ❌ 忘记清理
    // return () => clearInterval(interval);

    // ✅ 正确：清理副作用
    return () => {
      clearInterval(interval);
      console.log('Cleanup interval');
    };
  }, []);

  return <div>Check memory</div>;
}
```

#### 预防方案

```tsx
// 1. 正确清理副作用
function ComponentWithEffect() {
  useEffect(() => {
    const subscription = someApi.subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return <div>...</div>;
}

// 2. 避免闭包陷阱
function ClosureTrap() {
  const [data, setData] = useState([]);

  useEffect(() => {
    // ❌ 错误：每次都创建新的订阅
    const subscription = api.subscribe((newData) => {
      setData([...data, newData]);
    });

    return () => subscription.unsubscribe();
  }, [data]);

  // ✅ 正确：使用函数更新
  useEffect(() => {
    const subscription = api.subscribe((newData) => {
      setData((prevData) => [...prevData, newData]);
    });

    return () => subscription.unsubscribe();
  }, []);

  return <div>...</div>;
}

// 3. 使用 WeakMap/WeakSet
const cache = new WeakMap();

function processData(data) {
  if (cache.has(data)) {
    return cache.get(data);
  }

  const result = /* 处理数据 */;
  cache.set(data, result);
  return result;
}
```

---

## 兼容性问题

### 浏览器兼容性

#### 检查浏览器支持

```tsx
// 检查浏览器特性
function checkBrowserSupport() {
  const checks = {
    // ES6+
    arrowFunction: () => {},
    asyncAwait: async () => {},
    optionalChaining: null?.toString(),

    // Web APIs
    fetch: typeof fetch !== 'undefined',
    intersectionObserver: typeof IntersectionObserver !== 'undefined',
    resizeObserver: typeof ResizeObserver !== 'undefined',
  };

  console.table(checks);
}

// 使用 polyfills
import 'core-js/stable';
import 'regenerator-runtime/runtime';
```

#### 处理不支持的浏览器

```tsx
function BrowserCompatibilityCheck() {
  const [isSupported, setIsSupported] = useState(true);

  useEffect(() => {
    // 检查是否是 IE
    const isIE = /MSIE|Trident/.test(navigator.userAgent);

    if (isIE) {
      setIsSupported(false);
    }
  }, []);

  if (!isSupported) {
    return (
      <div>
        <h2>Browser Not Supported</h2>
        <p>Please use a modern browser like Chrome, Firefox, or Edge.</p>
      </div>
    );
  }

  return <YourApp />;
}
```

### React 版本兼容性

#### 版本要求

```json
{
  "peerDependencies": {
    "react": "^16.9.0 || ^17.0.0 || ^18.0.0",
    "react-dom": "^16.9.0 || ^17.0.0 || ^18.0.0"
  }
}
```

#### 升级指南

```bash
# 升级 React
npm install react@latest react-dom@latest

# 升级 antd
npm install antd@latest

# 检查版本冲突
npm ls react react-dom antd
```

### 第三方库冲突

#### 样式冲突

```tsx
// 使用 CSS Modules
import styles from './App.module.css';

function App() {
  return (
    <div className={styles.container}>
      <Button type="primary">Click</Button>
    </div>
  );
}

// 使用 CSS-in-JS
import styled from 'styled-components';

const StyledButton = styled(Button)`
  background-color: custom-color;
`;

function App() {
  return <StyledButton type="primary">Click</StyledButton>;
}
```

#### 类名冲突

```tsx
// 使用 ConfigProvider 修改前缀
import { ConfigProvider } from 'antd';

function App() {
  return (
    <ConfigProvider prefixCls="my-app">
      <div className="my-app-container">
        <Button type="primary">
          This button has class "my-app-btn" instead of "ant-btn"
        </Button>
      </div>
    </ConfigProvider>
  );
}
```

---

## 最佳实践

### 组件使用

#### ✅ 推荐做法

```tsx
// 1. 正确的表单使用
function GoodForm() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    console.log('Form values:', values);
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.Item
        name="username"
        label="Username"
        rules={[{ required: true, message: 'Required!' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
}

// 2. 正确的 Table 使用
function GoodTable() {
  const columns = useMemo(
    () => [
      {
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
      },
    ],
    []
  );

  const data = useMemo(
    () =>
      Array(1000).fill(0).map((_, i) => ({
        key: i,
        name: `User ${i}`,
      })),
    []
  );

  return (
    <Table
      dataSource={data}
      columns={columns}
      pagination={{ pageSize: 50 }}
    />
  );
}

// 3. 正确的 Modal 使用
function GoodModal() {
  const [visible, setVisible] = useState(false);

  const handleOk = () => {
    // 异步操作
    fetchData().then(() => {
      setVisible(false);
    });
  };

  return (
    <Modal
      open={visible}
      onOk={handleOk}
      onCancel={() => setVisible(false)}
      confirmLoading={loading}
    >
      Content
    </Modal>
  );
}
```

#### ❌ 避免的做法

```tsx
// 1. 直接操作 DOM
function BadComponent() {
  const handleClick = () => {
    document.querySelector('.ant-btn').click();
    // ❌ 不要直接操作 DOM
  };

  return <Button onClick={handleClick}>Click</Button>;
}

// 2. 在 render 中修改状态
function BadComponent() {
  const [count, setCount] = useState(0);

  // ❌ 会导致无限循环
  setCount(count + 1);

  return <div>{count}</div>;
}

// 3. 忽略错误处理
function BadComponent() {
  useEffect(() => {
    fetchData().then(setData);
    // ❌ 没有错误处理
  }, []);

  return <div>{data}</div>;
}

// 4. 过度使用 useEffect
function BadComponent() {
  const [name, setName] = useState('');
  const [age, setAge] = useState(0);

  // ❌ 不必要的 useEffect
  useEffect(() => {
    localStorage.setItem('name', name);
  }, [name]);

  // ✅ 直接在事件处理中保存
  const handleNameChange = (value) => {
    setName(value);
    localStorage.setItem('name', value);
  };

  return <Input onChange={handleNameChange} />;
}
```

### 性能优化

#### ✅ 推荐做法

```tsx
// 1. 使用 memo 避免不必要的渲染
const ExpensiveRow = memo(function Row({ data }) {
  return <tr>{/* ... */}</tr>;
});

// 2. 使用 useMemo 缓存计算
function DataTable({ rawData }) {
  const sortedData = useMemo(() => {
    return rawData.slice().sort((a, b) => a.id - b.id);
  }, [rawData]);

  return <Table dataSource={sortedData} />;
}

// 3. 使用 useCallback 缓存函数
function ButtonList({ items }) {
  const handleClick = useCallback((id) => {
    console.log('Clicked:', id);
  }, []);

  return (
    items.map((item) => (
      <Button key={item.id} onClick={() => handleClick(item.id)}>
        {item.name}
      </Button>
    ))
  );
}

// 4. 使用虚拟滚动
import { List } from 'antd';

function LargeList({ items }) {
  return (
    <List
      dataSource={items}
      renderItem={(item) => <List.Item>{item.name}</List.Item>}
      pagination={{ pageSize: 20 }}
    />
  );
}
```

#### ❌ 避免的做法

```tsx
// 1. 在 render 中创建大量对象
function BadComponent() {
  const items = Array(10000).fill(0).map((_, i) => ({
    id: i,
    name: `Item ${i}`,
    // ❌ 每次渲染都创建新对象
  }));

  return <List dataSource={items} />;
}

// 2. 不必要的嵌套组件
function BadComponent() {
  return (
    <div>
      {data.map((item) => (
        <div key={item.id}>
          {/* ❌ 每次都创建新组件 */}
          {() => <ExpensiveChild data={item} />}
        </div>
      ))}
    </div>
  );
}

// 3. 过度的 context 更新
function BadProvider({ children }) {
  const [state, setState] = useState(initialState);

  // ❌ 整个 state 变化导致所有消费者重新渲染
  return (
    <MyContext.Provider value={state}>
      {children}
    </MyContext.Provider>
  );
}
```

### 错误处理

#### ✅ 推荐做法

```tsx
// 1. 使用错误边界
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error:', error, errorInfo);
    // 上报错误
    reportError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}

// 2. 异步错误处理
function DataFetcher() {
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData()
      .then(setData)
      .catch((err) => {
        console.error('Fetch error:', err);
        setError(err);
        message.error('Failed to load data');
      });
  }, []);

  if (error) {
    return <ErrorDisplay error={error} />;
  }

  return <DataDisplay data={data} />;
}

// 3. 表单验证错误处理
function ValidatedForm() {
  const [form] = Form.useForm();

  const onFinish = async (values) => {
    try {
      await submitData(values);
      message.success('Submitted successfully!');
    } catch (error) {
      console.error('Submit error:', error);
      message.error('Submission failed');
    }
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Form validation failed:', errorInfo);
  };

  return (
    <Form form={form} onFinish={onFinish} onFinishFailed={onFinishFailed}>
      {/* ... */}
    </Form>
  );
}
```

---

## 常见问题

### Q: 如何处理 Ant Design 样式覆盖不生效的问题?

A: 有几种方法可以提高样式优先级：

```tsx
// 方法 1: 使用 :global()
<style>
  .custom :global(.ant-btn) {
    background-color: red;
  }
</style>

// 方法 2: 使用 ConfigProvider
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: 'red',
      },
    },
  }}
>
  <Button type="primary">Click</Button>
</ConfigProvider>

// 方法 3: 使用内联样式
<Button style={{ backgroundColor: 'red' }}>Click</Button>
```

### Q: Table 组件如何处理大量数据?

A: 使用分页、虚拟滚动或服务端排序：

```tsx
// 方法 1: 分页
<Table
  dataSource={data}
  columns={columns}
  pagination={{ pageSize: 50 }}
/>

// 方法 2: 虚拟滚动
<Table
  dataSource={data}
  columns={columns}
  scroll={{ y: 500 }}
  virtual
/>

// 方法 3: 服务端处理
<Table
  dataSource={data}
  columns={columns}
  pagination={{
    pageSize: 50,
    total: total,
    onChange: (page, pageSize) => {
      fetchData({ page, pageSize });
    },
  }}
  onChange={handleTableChange}
/>
```

### Q: DatePicker 日期格式如何转换?

A: 使用 dayjs 进行格式转换：

```tsx
import dayjs from 'dayjs';

// 格式化为字符串
const dateStr = dayjs(date).format('YYYY-MM-DD');

// 从字符串解析
const dateObj = dayjs('2024-01-01', 'YYYY-MM-DD');

// 提交时转换
const onSubmit = (values) => {
  const submitData = {
    ...values,
    date: values.date.format('YYYY-MM-DD'),
  };
};

// 加载时转换
const loadData = async () => {
  const data = await fetchData();
  form.setFieldsValue({
    date: dayjs(data.date, 'YYYY-MM-DD'),
  });
};
```

### Q: 如何调试 Form 表单验证问题?

A: 使用以下方法：

```tsx
const [form] = Form.useForm();

// 1. 检查表单值
console.log('Form values:', form.getFieldsValue());

// 2. 检查字段错误
console.log('Field errors:', form.getFieldsError());

// 3. 手动触发验证
const validate = async () => {
  try {
    await form.validateFields();
    console.log('Validation passed');
  } catch (error) {
    console.log('Validation failed:', error);
  }
};

// 4. 监听表单变化
useEffect(() => {
  const watchFields = () => {
    console.log('Fields changed:', form.getFieldsValue());
  };

  const internalHooks = form.getInternalHooks('RC_FORM_INTERNAL_HOOKS');
  const unsubscribe = internalHooks.registerWatch(watchFields);

  return () => unsubscribe();
}, []);
```

### Q: Modal 组件如何处理异步操作?

A: 使用 confirmLoading 属性：

```tsx
const [visible, setVisible] = useState(false);
const [loading, setLoading] = useState(false);

const handleOk = async () => {
  setLoading(true);
  try {
    await submitData();
    setVisible(false);
  } catch (error) {
    console.error('Submit error:', error);
  } finally {
    setLoading(false);
  }
};

<Modal
  open={visible}
  onOk={handleOk}
  onCancel={() => setVisible(false)}
  confirmLoading={loading}
>
  Content
</Modal>
```

### Q: 如何实现多语言切换?

A: 使用 ConfigProvider 和 dayjs/locale：

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';

function I18nApp() {
  const [locale, setLocale] = useState('zh');

  const changeLocale = (newLocale) => {
    setLocale(newLocale);
    dayjs.locale(newLocale);
  };

  return (
    <ConfigProvider locale={locale === 'zh' ? zhCN : enUS}>
      <Button onClick={() => changeLocale('zh')}>中文</Button>
      <Button onClick={() => changeLocale('en')}>English</Button>

      <DatePicker />
    </ConfigProvider>
  );
}
```

### Q: 如何优化 Ant Design 包体积?

A: 使用以下方法：

```tsx
// 1. 按需导入
import { Button, Input, Table } from 'antd';

// 2. 动态导入
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// 3. Tree shaking
// package.json
{
  "sideEffects": false
}

// 4. 使用 CDN
// html
<script src="https://cdn.jsdelivr.net/npm/antd/dist/antd.min.js"></script>
```

### Q: 如何处理浏览器兼容性问题?

A: 使用 polyfills 和正确的配置：

```tsx
// 1. 安装 polyfills
npm install core-js regenerator-runtime

// 2. 在入口文件导入
import 'core-js/stable';
import 'regenerator-runtime/runtime';

// 3. 配置 babel
{
  "presets": [
    ["@babel/preset-env", {
      "targets": "> 0.5%, last 2 versions, not dead"
    }]
  ]
}

// 4. 检查浏览器特性
if (!window.fetch) {
  // 加载 fetch polyfill
}
```

---

## 参考资源

### 官方文档

- [Ant Design 官方文档](https://ant.design/index-cn)
- [Ant Design 常见问题](https://ant.design/faq-cn)
- [React 官方文档](https://react.dev)
- [dayjs 官方文档](https://day.js.org)

### 调试工具

- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools)
- [Redux DevTools](https://github.com/reduxjs/redux-devtools)

### 性能优化

- [React 性能优化](https://react.dev/learn/render-and-commit)
- [Web 性能优化](https://web.dev/performance/)
- [webpack Bundle Analyzer](https://github.com/webpack-contrib/webpack-bundle-analyzer)

### 社区资源

- [Ant Design GitHub](https://github.com/ant-design/ant-design)
- [Stack Overflow - antd](https://stackoverflow.com/questions/tagged/antd)
- [Ant Design 中文网](https://ant.design/index-cn)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- React DOM >= 16.9.0
- dayjs >= 1.11.0

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
