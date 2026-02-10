---
name: antd-pro-skills
description: Ant Design ProComponents 完整指南 - ProTable、ProForm、ProLayout、ProList 高级组件
---

# antd-pro: ProComponents 完整指南

ProComponents 是 Ant Design 的高级组件库,专为解决中后台业务的复杂场景而生。它在 antd 基础组件之上进行了封装,提供了开箱即用的数据交互、表单处理、布局管理等高级功能。

---

## 概述

### 核心优势

- **开箱即用** - 预置了大量常见业务场景的最佳实践
- **类型安全** - 完整的 TypeScript 支持,提供智能提示
- **高度可配置** - 灵活的配置项满足各种定制需求
- **性能优化** - 内置虚拟滚动、懒加载等性能优化策略
- **简化样板代码** - 减少 60% 以上的重复代码

### 主要组件

| 组件 | 说明 | 适用场景 |
|------|------|----------|
| **ProTable** | 高级表格 | CRUD 列表页、数据查询、编辑表格 |
| **ProForm** | 高级表单 | 复杂表单、联动表单、动态表单 |
| **ProLayout** | 高级布局 | 中后台布局、菜单权限、面包屑 |
| **ProList** | 高级列表 | 卡片列表、网格列表、虚拟列表 |
| **ProDescriptions** | 高级详情 | 数据展示页、详情页 |
| **ProCard** | 高级卡片 | 页面容器、加载状态 |

### 安装

```bash
# 使用 npm
npm install @ant-design/pro-components @ant-design/pro-table

# 使用 yarn
yarn add @ant-design/pro-components @ant-design/pro-table

# 使用 pnpm
pnpm add @ant-design/pro-components @ant-design/pro-table
```

### 版本要求

- **ProComponents**: >= 2.0.0
- **Ant Design**: >= 5.0.0
- **React**: >= 17.0.0

---

## ProTable 高级表格

### 基础用法

ProTable 是一个高级表格组件,集成了搜索、分页、刷新、工具栏等功能。

```tsx
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns } from '@ant-design/pro-components';

type TableItem = {
  id: number;
  name: string;
  status: string;
  createdAt: number;
};

const columns: ProColumns<TableItem>[] = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 80,
  },
  {
    title: '名称',
    dataIndex: 'name',
  },
  {
    title: '状态',
    dataIndex: 'status',
    valueEnum: {
      open: { text: '开启', status: 'Success' },
      closed: { text: '关闭', status: 'Default' },
    },
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    valueType: 'dateTime',
  },
];

export default () => {
  return (
    <ProTable<TableItem>
      columns={columns}
      request={async (params) => {
        const res = await fetchTableData(params);
        return {
          data: res.list,
          success: true,
          total: res.total,
        };
      }}
      rowKey="id"
      pagination={{
        defaultPageSize: 10,
      }}
    />
  );
};
```

### 请求与数据加载

#### request 模式

```tsx
<ProTable
  request={async (params, sort, filter) => {
    // params: { current, pageSize, ...searchParams }
    // sort: { [key]: 'ascend' | 'descend' }
    // filter: { [key]: string[] }

    const msg = await fetchTableData({
      page: params.current,
      pageSize: params.pageSize,
      ...params,
      sort,
      filter,
    });

    return {
      data: msg.data,
      success: msg.success,
      total: msg.total,
    };
  }}
/>
```

#### dataSource 模式

```tsx
const [dataSource, setDataSource] = useState<TableItem[]>([]);

useEffect(() => {
  fetchTableData().then(setDataSource);
}, []);

<ProTable
  dataSource={dataSource}
  loading={loading}
  pagination={false}
/>
```

### 工具栏配置

#### 基础工具栏

```tsx
<ProTable
  toolBarRender={() => [
    <Button key="create" type="primary" onClick={handleCreate}>
      新建
    </Button>,
    <Button key="export" onClick={handleExport}>
      导出
    </Button>,
  ]}
  search={{
    span: 6,
  }}
/>
```

#### 工具栏操作

```tsx
<ProTable
  toolBarRender={() => [
    <Button
      key="reload"
      onClick={() => {
        actionRef.current?.reload();
      }}
    >
      刷新
    </Button>,
    <Button
      key="export"
      onClick={async () => {
        const data = await actionRef.current?.getFieldsValue();
        exportData(data);
      }}
    >
      导出数据
    </Button>,
  ]}
/>
```

### 列配置详解

#### valueType 类型

ProTable 内置了多种 valueType,简化常见字段的配置:

```tsx
const columns: ProColumns[] = [
  {
    title: '文本',
    dataIndex: 'text',
    valueType: 'text', // 默认
  },
  {
    title: '数字',
    dataIndex: 'amount',
    valueType: 'money', // 货币格式
  },
  {
    title: '日期',
    dataIndex: 'date',
    valueType: 'date', // 日期
  },
  {
    title: '日期时间',
    dataIndex: 'datetime',
    valueType: 'dateTime', // 日期时间
  },
  {
    title: '日期范围',
    dataIndex: 'dateRange',
    valueType: 'dateRange', // 日期范围查询
    search: {
      transform: (value) => {
        return {
          startTime: value[0],
          endTime: value[1],
        };
      },
    },
  },
  {
    title: '枚举',
    dataIndex: 'status',
    valueEnum: {
      open: { text: '开启', status: 'Success' },
      closed: { text: '关闭', status: 'Default' },
    },
  },
  {
    title: '标签',
    dataIndex: 'tags',
    valueType: 'select',
    fieldProps: {
      mode: 'tags',
    },
  },
  {
    title: '图片',
    dataIndex: 'image',
    valueType: 'image',
  },
  {
    title: '进度',
    dataIndex: 'progress',
    valueType: 'progress',
  },
  {
    title: '评分',
    dataIndex: 'rating',
    valueType: 'rating',
  },
  {
    title: '代码',
    dataIndex: 'code',
    valueType: 'code',
  },
  {
    title: 'JSON',
    dataIndex: 'json',
    valueType: 'jsonCode',
  },
];
```

#### 自定义渲染

```tsx
const columns: ProColumns<TableItem>[] = [
  {
    title: '自定义',
    dataIndex: 'custom',
    render: (_, record) => (
      <Space>
        <span>{record.name}</span>
        <Tag color="blue">自定义</Tag>
      </Space>
    ),
  },
  {
    title: '操作',
    valueType: 'option',
    width: 200,
    render: (_, record) => [
      <a key="edit" onClick={() => handleEdit(record)}>
        编辑
      </a>,
      <a key="delete" onClick={() => handleDelete(record)}>
        删除
      </a>,
    ],
  },
];
```

#### 隐藏列

```tsx
const columns: ProColumns[] = [
  {
    title: 'ID',
    dataIndex: 'id',
    hideInTable: true, // 在表格中隐藏
    hideInSearch: true, // 在搜索表单中隐藏
    hideInForm: true, // 在表单中隐藏
  },
  {
    title: '仅在搜索',
    dataIndex: 'searchOnly',
    hideInTable: true,
  },
];
```

### 搜索表单

#### 基础搜索

```tsx
<ProTable
  columns={columns}
  request={fetchData}
  search={{
    filterType: 'light', // 轻量筛选
  }}
  form={{
    // 表单配置
    syncToUrl: (values, type) => {
      if (type === 'get') {
        return {
          ...values,
          created_at: [values.startTime, values.endTime],
        };
      }
      return values;
    },
  }}
/>
```

#### 搜索表单项配置

```tsx
const columns: ProColumns[] = [
  {
    title: '名称',
    dataIndex: 'name',
    // 搜索配置
    search: {
      transform: (value) => {
        return {
          name_like: value,
        };
      },
    },
  },
  {
    title: '状态',
    dataIndex: 'status',
    valueType: 'select',
    valueEnum: {
      all: { text: '全部' },
      open: { text: '开启' },
      closed: { text: '关闭' },
    },
    // 默认值
    initialValue: 'all',
  },
  {
    title: '时间范围',
    dataIndex: 'createdAt',
    valueType: 'dateTimeRange',
    search: {
      transform: (value) => {
        return {
          startTime: value[0],
          endTime: value[1],
        };
      },
    },
  },
];
```

#### 搜索表单布局

```tsx
<ProTable
  search={{
    // 搜索表单的 Grid 配置
    defaultCollapsed: false, // 默认展开
    span: { xs: 24, sm: 12, md: 8, lg: 6, xl: 6, xxl: 4 },
    // 搜索表单的列数
    searchText: '查询',
    resetText: '重置',
    // 自定义搜索按钮
    optionRender: ({ searchText, resetText }, { form }) => [
      <Button key="search" type="primary" onClick={() => form?.submit()}>
        {searchText}
      </Button>,
      <Button key="reset" onClick={() => form?.resetFields()}>
        {resetText}
      </Button>,
    ],
  }}
/>
```

### 数据筛选与排序

#### 列筛选

```tsx
const columns: ProColumns[] = [
  {
    title: '状态',
    dataIndex: 'status',
    filters: [
      { text: '开启', value: 'open' },
      { text: '关闭', value: 'closed' },
    ],
    onFilter: true, // 自动在前端过滤
    // or
    onFilter: (value, record) => record.status === value,
  },
];
```

#### 列排序

```tsx
const columns: ProColumns[] = [
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    sorter: true, // 开启后端排序
    // or
    sorter: (a, b) => a.createdAt - b.createdAt, // 前端排序
    sortOrder: 'descend', // 默认排序
  },
];
```

### 分页配置

```tsx
<ProTable
  pagination={{
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showTotal: (total) => `共 ${total} 条`,
    // 是否改变时自动刷新
    onChange: (page, pageSize) => console.log(page, pageSize),
  }}
/>
```

### 行选择

#### 单选

```tsx
const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

<ProTable
  rowSelection={{
    type: 'radio',
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  }}
/>
```

#### 多选

```tsx
<ProTable
  rowSelection={{
    type: 'checkbox',
    selectedRowKeys,
    onChange: (keys, rows) => {
      setSelectedRowKeys(keys);
      console.log('选中的行:', rows);
    },
    // 选择配置
    selections: [
      Table.SELECTION_ALL,
      Table.SELECTION_INVERT,
      Table.SELECTION_NONE,
      {
        key: 'odd',
        text: '选择奇数行',
        onSelect: (changableRowKeys) => {
          const newSelectedRowKeys = changableRowKeys.filter((_, index) => index % 2 === 0);
          setSelectedRowKeys(newSelectedRowKeys);
        },
      },
    ],
  }}
/>
```

### 编辑表格

```tsx
import { ProTable } from '@ant-design/pro-components';
import { EditableProTable } from '@ant-design/pro-components';

type DataSourceType = {
  id: React.Key;
  name?: string;
  status?: string;
};

const EditableTable = () => {
  const [dataSource, setDataSource] = useState<DataSourceType[]>([]);
  const [editableKeys, setEditableRowKeys] = useState<React.Key[]>([]);

  const columns: ProColumns<DataSourceType>[] = [
    {
      title: '名称',
      dataIndex: 'name',
      width: '30%',
      formItemProps: {
        rules: [
          {
            required: true,
            message: '名称为必填项',
          },
        ],
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      valueType: 'select',
      valueEnum: {
        open: { text: '开启' },
        closed: { text: '关闭' },
      },
      width: '30%',
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      render: (text, record, _, action) => [
        <a
          key="editable"
          onClick={() => {
            action?.startEditable?.(record.id);
          }}
        >
          编辑
        </a>,
        <a
          key="delete"
          onClick={() => {
            setDataSource(dataSource.filter((item) => item.id !== record.id));
          }}
        >
          删除
        </a>,
      ],
    },
  ];

  return (
    <EditableProTable<DataSourceType>
      rowKey="id"
      value={dataSource}
      onChange={setDataSource}
      columns={columns}
      editable={{
        type: 'multiple',
        editableKeys,
        onSave: (_, row) => {
          console.log('保存:', row);
          return Promise.resolve(true);
        },
        onChange: setEditableRowKeys,
        actionRender: (row, config, defaultDoms) => [
          defaultDoms.save,
          defaultDoms.cancel,
        ],
      }}
      recordCreatorProps={{
        newRecordType: 'dataSource',
        record: () => ({
          id: Date.now(),
        }),
      }}
    />
  );
};
```

### 行展开

```tsx
const expandedRowRender = (record: TableItem) => (
  <ProDescriptions
    column={2}
    dataSource={record}
    columns={[
      { title: 'ID', dataIndex: 'id' },
      { title: '名称', dataIndex: 'name' },
      { title: '状态', dataIndex: 'status' },
    ]}
  />
);

<ProTable
  expandable={{
    expandedRowRender,
    defaultExpandAllRows: false,
  }}
/>
```

---

## ProForm 高级表单

### 基础用法

ProForm 基于 antd Form,提供了更强大的表单布局和字段配置能力。

```tsx
import { ProForm, ProFormText, ProFormSelect } from '@ant-design/pro-components';
import { message } from 'antd';

export default () => {
  return (
    <ProForm
      onFinish={async (values) => {
        console.log(values);
        message.success('提交成功');
        return true;
      }}
      initialValues={{
        name: '默认名称',
      }}
    >
      <ProFormText
        name="name"
        label="名称"
        placeholder="请输入名称"
        rules={[{ required: true, message: '请输入名称' }]}
      />

      <ProFormSelect
        name="status"
        label="状态"
        options={[
          { label: '开启', value: 'open' },
          { label: '关闭', value: 'closed' },
        ]}
      />
    </ProForm>
  );
};
```

### 表单布局

#### 垂直布局

```tsx
<ProForm
  layout="vertical"
  grid={true}
  rowProps={{
    gutter: [16, 16],
  }}
>
  <ProFormText name="field1" label="字段1" colProps={{ span: 12 }} />
  <ProFormText name="field2" label="字段2" colProps={{ span: 12 }} />
  <ProFormTextArea name="field3" label="字段3" colProps={{ span: 24 }} />
</ProForm>
```

#### 水平布局

```tsx
<ProForm
  layout="horizontal"
  labelCol={{ span: 4 }}
  wrapperCol={{ span: 16 }}
>
  <ProFormText name="name" label="名称" />
  <ProFormText name="email" label="邮箱" />
</ProForm>
```

#### 表单分组

```tsx
import { ProForm, ProFormText, ProFormGroup } from '@ant-design/pro-components';

<ProForm>
  <ProFormGroup title="基础信息">
    <ProFormText name="name" label="名称" />
    <ProFormText name="code" label="编码" />
  </ProFormGroup>

  <ProFormGroup title="详细配置">
    <ProFormText name="host" label="主机" />
    <ProFormText name="port" label="端口" />
  </ProFormGroup>
</ProForm>
```

### 表单字段

#### 文本输入

```tsx
<ProFormText
  name="username"
  label="用户名"
  placeholder="请输入用户名"
  rules={[
    { required: true, message: '请输入用户名' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符' },
  ]}
  fieldProps={{
    prefix: <UserOutlined />,
  }}
/>
```

#### 密码输入

```tsx
<ProFormText.Password
  name="password"
  label="密码"
  placeholder="请输入密码"
  rules={[
    { required: true, message: '请输入密码' },
    { min: 6, message: '密码至少6位' },
  ]}
/>
```

#### 文本域

```tsx
<ProFormTextArea
  name="description"
  label="描述"
  placeholder="请输入描述"
  fieldProps={{
    rows: 4,
    showCount: true,
    maxLength: 200,
  }}
/>
```

#### 数字输入

```tsx
<ProFormDigit
  name="price"
  label="价格"
  placeholder="请输入价格"
  min={0}
  max={99999}
  precision={2}
  fieldProps={{
    prefix: '¥',
  }}
/>
```

#### 日期选择

```tsx
<ProFormDatePicker
  name="date"
  label="日期"
  placeholder="请选择日期"
  rules={[{ required: true, message: '请选择日期' }]}
/>

<ProFormDateTimePicker
  name="datetime"
  label="日期时间"
  placeholder="请选择日期时间"
/>

<ProFormDateRangePicker
  name={['startDate', 'endDate']}
  label="日期范围"
  placeholder={['开始日期', '结束日期']}
  transform={(value) => {
    return {
      startTime: value[0],
      endTime: value[1],
    };
  }}
/>
```

#### 时间选择

```tsx
<ProFormTimePicker
  name="time"
  label="时间"
  placeholder="请选择时间"
  fieldProps={{
    format: 'HH:mm',
  }}
/>
```

#### 选择器

```tsx
<ProFormSelect
  name="category"
  label="分类"
  placeholder="请选择分类"
  options={[
    { label: '选项1', value: '1' },
    { label: '选项2', value: '2' },
  ]}
  rules={[{ required: true, message: '请选择分类' }]}
  fieldProps={{
    mode: 'multiple', // 多选
  }}
/>
```

#### 级联选择

```tsx
<ProFormCascader
  name="region"
  label="地区"
  placeholder="请选择地区"
  request={async () => {
    return [
      {
        value: 'zhejiang',
        label: '浙江',
        children: [
          {
            value: 'hangzhou',
            label: '杭州',
          },
        ],
      },
    ];
  }}
/>
```

#### 开关

```tsx
<ProFormSwitch
  name="enabled"
  label="启用状态"
  fieldProps={{
    checkedChildren: '开',
    unCheckedChildren: '关',
  }}
/>
```

#### 单选框

```tsx
<ProFormRadio
  name="type"
  label="类型"
  options={[
    { label: '类型A', value: 'a' },
    { label: '类型B', value: 'b' },
  ]}
  rules={[{ required: true, message: '请选择类型' }]}
/>
```

#### 复选框

```tsx
<ProFormCheckbox
  name="features"
  label="特性"
  options={[
    { label: '特性1', value: 'feat1' },
    { label: '特性2', value: 'feat2' },
    { label: '特性3', value: 'feat3' },
  ]}
/>
```

#### 滑块

```tsx
<ProFormSlider
  name="progress"
  label="进度"
  min={0}
  max={100}
  marks={{
    0: '0%',
    25: '25%',
    50: '50%',
    75: '75%',
    100: '100%',
  }}
/>
```

#### 评分

```tsx
<ProFormRate
  name="rating"
  label="评分"
  fieldProps={{
    count: 5,
    allowHalf: true,
  }}
/>
```

#### 上传

```tsx
<ProFormUploadButton
  name="file"
  label="文件"
  max={5}
  fieldProps={{
    name: 'file',
    listType: 'picture-card',
  }}
  extra="支持上传jpg、png格式,文件大小不超过2MB"
  rules={[{ required: true, message: '请上传文件' }]}
/>
```

#### 富文本

```tsx
<ProFormTextArea
  name="content"
  label="内容"
  fieldProps={{
    autoSize: { minRows: 6, maxRows: 12 },
  }}
/>
```

### 表单联动

#### 字段联动显示

```tsx
import { ProFormDependency } from '@ant-design/pro-components';

<ProForm>
  <ProFormRadio
    name="type"
    label="类型"
    options={[
      { label: '个人', value: 'personal' },
      { label: '企业', value: 'company' },
    ]}
  />

  <ProFormDependency name={['type']}>
    {({ type }) => {
      if (type === 'company') {
        return (
          <ProFormText
            name="companyName"
            label="公司名称"
            rules={[{ required: true }]}
          />
        );
      }
      return null;
    }}
  </ProFormDependency>
</ProForm>
```

#### 值联动

```tsx
<ProForm>
  <ProFormText name="firstName" label="姓" />
  <ProFormText name="lastName" label="名" />

  <ProFormDependency name={['firstName', 'lastName']}>
    {({ firstName, lastName }) => {
      return (
        <ProFormText
          name="fullName"
          label="全名"
          initialValue={`${firstName}${lastName}`}
          disabled
        />
      );
    }}
  </ProFormDependency>
</ProForm>
```

#### 动态字段

```tsx
import { ProFormList } from '@ant-design/pro-components';

<ProFormList
  name="users"
  label="用户列表"
  creatorButtonProps={{
    position: 'top',
    creatorButtonText: '添加用户',
  }}
>
  {(f, index, action) => (
    <>
      <ProFormText
        name={[index, 'name']}
        label="姓名"
        width="lg"
      />

      <ProFormText
        name={[index, 'email']}
        label="邮箱"
        width="lg"
      />

      <ProFormSelect
        name={[index, 'role']}
        label="角色"
        options={[
          { label: '管理员', value: 'admin' },
          { label: '普通用户', value: 'user' },
        ]}
        width="lg"
      />

      <Button
        type="link"
        danger
        onClick={() => action.remove(index)}
      >
        删除
      </Button>
    </>
  )}
</ProFormList>
```

### 表单验证

#### 同步验证

```tsx
<ProFormText
  name="email"
  label="邮箱"
  rules={[
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '邮箱格式不正确' },
  ]}
/>
```

#### 异步验证

```tsx
<ProFormText
  name="username"
  label="用户名"
  rules={[
    { required: true, message: '请输入用户名' },
    {
      validator: async (_, value) => {
        if (!value) return;
        const exists = await checkUsernameExists(value);
        if (exists) {
          throw new Error('用户名已存在');
        }
      },
    },
  ]}
  validateFirst={false}
/>
```

#### 自定义验证

```tsx
<ProFormDependency name={['password']}>
  {({ password }) => {
    return (
      <ProFormText.Password
        name="confirmPassword"
        label="确认密码"
        rules={[
          { required: true, message: '请确认密码' },
          {
            validator: (_, value) => {
              if (value !== password) {
                return Promise.reject('两次输入的密码不一致');
              }
              return Promise.resolve();
            },
          },
        ]}
      />
    );
  }}
</ProFormDependency>
```

### 提交处理

```tsx
<ProForm
  onFinish={async (values) => {
    try {
      await submitForm(values);
      message.success('提交成功');
      return true;
    } catch (error) {
      message.error('提交失败');
      return false;
    }
  }}
  onSubmit={(values) => {
    console.log('提交中:', values);
  }}
  onReset={() => {
    console.log('表单已重置');
  }}
/>
```

### 表单值变化监听

```tsx
<ProForm
  onValuesChange={(changedValues, allValues) => {
    console.log('变化的值:', changedValues);
    console.log('所有值:', allValues);
  }}
/>
```

---

## ProLayout 高级布局

### 基础用法

ProLayout 是一个开箱即用的中后台布局组件,包含顶部导航、侧边栏菜单、面包屑等功能。

```tsx
import { ProLayout } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';

export default () => {
  const navigate = useNavigate();

  return (
    <ProLayout
      route={{
        path: '/',
        routes: [
          {
            path: '/',
            name: '首页',
            icon: <HomeOutlined />,
          },
          {
            path: '/users',
            name: '用户管理',
            icon: <UserOutlined />,
            routes: [
              {
                path: '/users/list',
                name: '用户列表',
              },
              {
                path: '/users/create',
                name: '新建用户',
              },
            ],
          },
        ],
      }}
      location={{
        pathname: '/users/list',
      }}
      menuItemRender={(menuItemProps, defaultDom) => {
        return (
          <div onClick={() => navigate(menuItemProps.path || '/')}>
            {defaultDom}
          </div>
        );
      }}
    >
      <PageContainer>
        <YourContent />
      </PageContainer>
    </ProLayout>
  );
};
```

### 顶部导航

```tsx
<ProLayout
  headerContentRender={() => (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <div style={{ marginRight: 24 }}>Logo</div>
      <Input.Search
        placeholder="搜索"
        style={{ width: 200 }}
      />
    </div>
  )}
  headerTitleRender={(logo, title) => (
    <div>{title}</div>
  )}
  actionsRender={() => [
    <Button key="notification" icon={<NotificationOutlined />} />,
    <Dropdown key="user" menu={{ items: userMenuItems }}>
      <Avatar icon={<UserOutlined />} />
    </Dropdown>,
  ]}
/>
```

### 侧边栏菜单

```tsx
const menuData = [
  {
    path: '/dashboard',
    name: '仪表盘',
    icon: <DashboardOutlined />,
  },
  {
    path: '/management',
    name: '管理',
    icon: <SettingOutlined />,
    children: [
      {
        path: '/management/users',
        name: '用户管理',
      },
      {
        path: '/management/roles',
        name: '角色管理',
      },
    ],
  },
];

<ProLayout
  route={{
    path: '/',
    routes: menuData,
  }}
  menu={{
    type: 'sub', // sub | group
  }}
  menuFooterRender={(props) => {
    return (
      <div style={{ textAlign: 'center', padding: 16 }}>
        <div>Version 1.0.0</div>
      </div>
    );
  }}
/>
```

### 面包屑

```tsx
<ProLayout
  breadcrumbRender={(routers = []) => {
    return [
      {
        path: '/',
        breadcrumbName: '首页',
      },
      ...routers,
    ];
  }}
  breadcrumbProps={{
    itemRender: (route, params, routes, paths) => {
      const last = routes.indexOf(route) === routes.length - 1;
      return last ? (
        <span>{route.breadcrumbName}</span>
      ) : (
        <Link to={paths.join('/')}>{route.breadcrumbName}</Link>
      );
    },
  }}
/>
```

### 主题配置

```tsx
<ProLayout
  navTheme="light" // light | dark | realDark
  headerTheme="dark"
  primaryColor="#1890ff"
  layout="side" // side | top | mix
  contentWidth="Fluid" // Fluid | Fixed
  fixedHeader={false}
  fixSiderbar={true}
  splitMenus={false}
/>
```

### 权限控制

```tsx
const hasPermission = (permission: string) => {
  // 权限检查逻辑
  return true;
};

<ProLayout
  route={{
    path: '/',
    routes: [
      {
        path: '/admin',
        name: '管理员',
        access: 'canAdmin',
      },
    ],
  }}
  accessRender={(props) => {
    const { children } = props;
    if (!hasPermission(props.access)) {
      return null;
    }
    return children;
  }}
/>
```

### 标签页

```tsx
<ProLayout
  tabsProps={{
    hideAdd: true,
    type: 'editable-card',
    onChange: (key) => {
      console.log('切换标签:', key);
    },
    onEdit: (targetKey, action) => {
      console.log('编辑标签:', targetKey, action);
    },
  }}
/>
```

### PageContainer

```tsx
import { PageContainer } from '@ant-design/pro-components';

<PageContainer
  title="页面标题"
  subTitle="页面副标题"
  content="页面描述内容"
  extra={[
    <Button key="create">新建</Button>,
    <Button key="export">导出</Button>,
  ]}
  tabList={[
    {
      tab: '基本信息',
      key: 'base',
    },
    {
      tab: '详细信息',
      key: 'detail',
    },
  ]}
  tabActiveKey="base"
  onTabChange={(key) => console.log(key)}
  footer={[
    <Button key="cancel">取消</Button>,
    <Button key="submit" type="primary">提交</Button>,
  ]}
>
  <YourContent />
</PageContainer>
```

---

## ProList 高级列表

### 基础列表

```tsx
import { ProList } from '@ant-design/pro-components';

<ProList
  dataSource={dataSource}
  rowKey="id"
  renderItem={(item) => ({
    title: item.name,
    subTitle: item.description,
    actions: [
      <a key="edit">编辑</a>,
      <a key="delete">删除</a>,
    ],
    avatar: <Avatar src={item.avatar} />,
    content: (
      <div>
        <div>状态: {item.status}</div>
        <div>创建时间: {item.createdAt}</div>
      </div>
    ),
  })}
/>
```

### 网格列表

```tsx
<ProList
  grid={{ gutter: 16, column: 3 }}
  dataSource={dataSource}
  renderItem={(item) => ({
    title: item.name,
    subTitle: item.description,
    actions: [
      <a key="edit">编辑</a>,
    ],
    content: (
      <Card>
        <div>{item.content}</div>
      </Card>
    ),
  })}
/>
```

### 卡片列表

```tsx
<ProList
  grid={{ gutter: 16, column: 3 }}
  dataSource={dataSource}
  renderItem={(item) => ({
    title: item.name,
    subTitle: item.description,
    actions: [
      <Button key="edit" type="primary">
        编辑
      </Button>,
    ],
    content: (
      <Card
        hoverable
        cover={
          item.image ? (
            <div
              style={{
                height: 200,
                backgroundImage: `url(${item.image})`,
                backgroundSize: 'cover',
              }}
            />
          ) : null
        }
      >
        <Card.Meta
          title={item.name}
          description={item.description}
        />
        <div style={{ marginTop: 16 }}>
          <Tag color="blue">{item.category}</Tag>
          <Tag color="green">{item.status}</Tag>
        </div>
      </Card>
    ),
  })}
/>
```

### 虚拟列表

```tsx
<ProList
  dataSource={largeDataSource}
  rowKey="id"
  metas={{
    title: {
      dataIndex: 'name',
    },
    description: {
      dataIndex: 'description',
    },
    actions: {
      render: (_, item) => [
        <a key="edit">编辑</a>,
        <a key="delete">删除</a>,
      ],
    },
  }}
  pagination={{
    defaultPageSize: 20,
  }}
  tooltip={{
    title: '提示',
  }}
/>
```

---

## 高级功能

### 值枚举 (valueEnum)

```tsx
const columns: ProColumns[] = [
  {
    title: '状态',
    dataIndex: 'status',
    valueEnum: {
      all: { text: '全部', status: 'Default' },
      open: {
        text: '开启',
        status: 'Success',
        disabled: false,
      },
      closed: {
        text: '关闭',
        status: 'Default',
        disabled: true,
      },
      processing: {
        text: '处理中',
        status: 'Processing',
        disabled: false,
      },
    },
    // 在表格中渲染为 Tag
    // 在搜索中渲染为 Select
  },
];
```

### 请求拦截器

```tsx
<ProTable
  request={async (params, sort, filter) => {
    try {
      // 请求前处理
      const requestData = {
        ...params,
        sort,
        filter,
      };

      const response = await fetchTableData(requestData);

      // 响应后处理
      return {
        data: response.data,
        success: response.success,
        total: response.total,
      };
    } catch (error) {
      // 错误处理
      return {
        data: [],
        success: false,
        total: 0,
      };
    }
  }}
/>
```

### 数据转换

```tsx
const columns: ProColumns[] = [
  {
    title: '金额',
    dataIndex: 'amount',
    valueType: 'money',
    search: false,
    // 表格渲染时转换
    render: (_, record) => `¥${record.amount.toFixed(2)}`,
    // 搜索时转换
    params: (params) => ({
      ...params,
      amount_min: params.amount?.[0],
      amount_max: params.amount?.[1],
    }),
  },
];
```

### 错误处理

```tsx
<ProTable
  request={async (params) => {
    try {
      const response = await fetchData(params);
      if (response.success) {
        return {
          data: response.data,
          success: true,
          total: response.total,
        };
      } else {
        message.error(response.message);
        return {
          data: [],
          success: false,
          total: 0,
        };
      }
    } catch (error) {
      message.error('请求失败');
      return {
        data: [],
        success: false,
        total: 0,
      };
    }
  }}
  onError={(error) => {
    console.error('表格错误:', error);
  }}
/>
```

---

## 完整使用示例

### 示例 1: 完整的 CRUD 表格

```tsx
import { ProTable, ProFormText, ModalForm, ProFormTextArea } from '@ant-design/pro-components';
import { useRef, useState } from 'react';
import { message, Modal } from 'antd';

type TableItem = {
  id: number;
  name: string;
  email: string;
  status: string;
  createdAt: number;
};

export default () => {
  const actionRef = useRef<ActionType>();
  const [modalVisible, setModalVisible] = useState(false);
  const [currentRow, setCurrentRow] = useState<TableItem>();

  const columns: ProColumns<TableItem>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
      search: false,
    },
    {
      title: '名称',
      dataIndex: 'name',
      rules: [{ required: true, message: '请输入名称' }],
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      rules: [
        { required: true, message: '请输入邮箱' },
        { type: 'email', message: '邮箱格式不正确' },
      ],
    },
    {
      title: '状态',
      dataIndex: 'status',
      valueType: 'select',
      valueEnum: {
        all: { text: '全部' },
        active: { text: '启用', status: 'Success' },
        inactive: { text: '禁用', status: 'Default' },
      },
      initialValue: 'all',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      valueType: 'dateTime',
      search: false,
      sorter: true,
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      render: (_, record) => [
        <a
          key="edit"
          onClick={() => {
            setCurrentRow(record);
            setModalVisible(true);
          }}
        >
          编辑
        </a>,
        <a
          key="delete"
          onClick={() => {
            Modal.confirm({
              title: '确认删除',
              content: `确定要删除 "${record.name}" 吗?`,
              onOk: async () => {
                await deleteUser(record.id);
                message.success('删除成功');
                actionRef.current?.reload();
              },
            });
          }}
        >
          删除
        </a>,
      ],
    },
  ];

  return (
    <ProTable<TableItem>
      columns={columns}
      actionRef={actionRef}
      request={async (params, sort) => {
        const msg = await getUserList({
          ...params,
          sort,
        });
        return {
          data: msg.data.list,
          success: msg.success,
          total: msg.data.total,
        };
      }}
      rowKey="id"
      pagination={{
        defaultPageSize: 10,
        showSizeChanger: true,
      }}
      toolBarRender={() => [
        <Button
          key="create"
          type="primary"
          onClick={() => {
            setCurrentRow(undefined);
            setModalVisible(true);
          }}
        >
          新建用户
        </Button>,
      ]}
      search={{
        labelWidth: 'auto',
      }}
    />
  );
};
```

### 示例 2: 搜索和筛选表单

```tsx
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns } from '@ant-design/pro-components';

const columns: ProColumns[] = [
  {
    title: '订单号',
    dataIndex: 'orderNo',
    copyable: true,
  },
  {
    title: '客户名称',
    dataIndex: 'customerName',
  },
  {
    title: '订单状态',
    dataIndex: 'status',
    valueType: 'select',
    valueEnum: {
      all: { text: '全部' },
      pending: { text: '待处理', status: 'Default' },
      processing: { text: '处理中', status: 'Processing' },
      completed: { text: '已完成', status: 'Success' },
      cancelled: { text: '已取消', status: 'Error' },
    },
  },
  {
    title: '订单金额',
    dataIndex: 'amount',
    valueType: 'money',
    search: false,
    sorter: true,
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    valueType: 'dateTimeRange',
    search: {
      transform: (value) => {
        return {
          startTime: value[0],
          endTime: value[1],
        };
      },
    },
    hideInTable: true,
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    valueType: 'dateTime',
    search: false,
    sorter: true,
  },
];

export default () => {
  return (
    <ProTable
      columns={columns}
      request={async (params) => {
        const { startTime, endTime, ...rest } = params;
        const msg = await getOrderList({
          ...rest,
          created_at_gte: startTime,
          created_at_lte: endTime,
        });
        return {
          data: msg.data.list,
          success: msg.success,
          total: msg.data.total,
        };
      }}
      rowKey="id"
      pagination={{
        defaultPageSize: 20,
        showSizeChanger: true,
        showQuickJumper: true,
      }}
      search={{
        span: 6,
        defaultCollapsed: false,
      }}
      dateFormatter="string"
    />
  );
};
```

### 示例 3: 复杂表单（联动、验证）

```tsx
import {
  ProForm,
  ProFormText,
  ProFormSelect,
  ProFormRadio,
  ProFormDependency,
  ProFormTextArea,
  ProFormDateTimePicker,
} from '@ant-design/pro-components';

export default () => {
  return (
    <ProForm
      onFinish={async (values) => {
        console.log(values);
        message.success('提交成功');
        return true;
      }}
      grid={true}
      rowProps={{ gutter: [16, 16] }}
    >
      <ProFormRadio.Group
        name="type"
        label="用户类型"
        options={[
          { label: '个人', value: 'personal' },
          { label: '企业', value: 'company' },
        ]}
        colProps={{ span: 24 }}
        rules={[{ required: true }]}
      />

      <ProFormDependency name={['type']}>
        {({ type }) => {
          if (type === 'company') {
            return (
              <>
                <ProFormText
                  name="companyName"
                  label="公司名称"
                  colProps={{ span: 12 }}
                  rules={[{ required: true }]}
                />
                <ProFormText
                  name="taxNumber"
                  label="税号"
                  colProps={{ span: 12 }}
                  rules={[{ required: true }]}
                />
              </>
            );
          }
          return (
            <>
              <ProFormText
                name="firstName"
                label="姓"
                colProps={{ span: 12 }}
                rules={[{ required: true }]}
              />
              <ProFormText
                name="lastName"
                label="名"
                colProps={{ span: 12 }}
                rules={[{ required: true }]}
              />
            </>
          );
        }}
      </ProFormDependency>

      <ProFormText
        name="email"
        label="邮箱"
        colProps={{ span: 12 }}
        rules={[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '邮箱格式不正确' },
        ]}
      />

      <ProFormText.Password
        name="password"
        label="密码"
        colProps={{ span: 12 }}
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6位' },
        ]}
      />

      <ProFormDependency name={['password']}>
        {({ password }) => {
          return (
            <ProFormText.Password
              name="confirmPassword"
              label="确认密码"
              colProps={{ span: 12 }}
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                {
                  validator: (_, value) => {
                    if (value !== password) {
                      return Promise.reject('两次输入的密码不一致');
                    }
                    return Promise.resolve();
                  },
                },
              ]}
            />
          );
        }}
      </ProFormDependency>

      <ProFormSelect
        name="country"
        label="国家"
        colProps={{ span: 12 }}
        options={[
          { label: '中国', value: 'CN' },
          { label: '美国', value: 'US' },
        ]}
        rules={[{ required: true }]}
      />

      <ProFormDependency name={['country']}>
        {({ country }) => {
          return (
            <ProFormSelect
              name="city"
              label="城市"
              colProps={{ span: 12 }}
              request={async () => {
                if (country === 'CN') {
                  return [
                    { label: '北京', value: 'beijing' },
                    { label: '上海', value: 'shanghai' },
                  ];
                }
                return [
                  { label: '纽约', value: 'newyork' },
                  { label: '洛杉矶', value: 'losangeles' },
                ];
              }}
              rules={[{ required: true }]}
            />
          );
        }}
      </ProFormDependency>

      <ProFormDateTimePicker
        name="birthday"
        label="生日"
        colProps={{ span: 12 }}
      />

      <ProFormSelect
        name="interests"
        label="兴趣爱好"
        colProps={{ span: 12 }}
        fieldProps={{
          mode: 'multiple',
        }}
        options={[
          { label: '阅读', value: 'reading' },
          { label: '运动', value: 'sports' },
          { label: '音乐', value: 'music' },
          { label: '旅行', value: 'travel' },
        ]}
      />

      <ProFormTextArea
        name="bio"
        label="个人简介"
        colProps={{ span: 24 }}
        fieldProps={{
          rows: 4,
          showCount: true,
          maxLength: 200,
        }}
      />
    </ProForm>
  );
};
```

### 示例 4: 布局系统（菜单、权限）

```tsx
import { ProLayout, PageContainer } from '@ant-design/pro-components';
import { useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';

export default () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [pathname, setPathname] = useState(location.pathname);

  const menuData = [
    {
      path: '/',
      name: '首页',
      icon: <HomeOutlined />,
    },
    {
      path: '/users',
      name: '用户管理',
      icon: <UserOutlined />,
      access: 'canUser',
      children: [
        {
          path: '/users/list',
          name: '用户列表',
        },
        {
          path: '/users/create',
          name: '新建用户',
        },
      ],
    },
    {
      path: '/settings',
      name: '系统设置',
      icon: <SettingOutlined />,
      children: [
        {
          path: '/settings/profile',
          name: '个人资料',
        },
        {
          path: '/settings/security',
          name: '安全设置',
        },
      ],
    },
  ];

  return (
    <ProLayout
      route={{
        path: '/',
        routes: menuData,
      }}
      location={{
        pathname,
      }}
      menuItemRender={(menuItemProps, defaultDom) => {
        return (
          <div
            onClick={() => {
              setPathname(menuItemProps.path || '/');
              navigate(menuItemProps.path || '/');
            }}
          >
            {defaultDom}
          </div>
        );
      }}
      breadcrumbRender={(routers = []) => {
        return [
          {
            path: '/',
            breadcrumbName: '首页',
          },
          ...routers,
        ];
      }}
      itemRender={(route, params, routes, paths) => {
        const last = routes.indexOf(route) === routes.length - 1;
        return last ? (
          <span>{route.breadcrumbName}</span>
        ) : (
          <Link to={paths.join('/')}>{route.breadcrumbName}</Link>
        );
      }}
      menuFooterRender={(props) => {
        return (
          <div
            style={{
              textAlign: 'center',
              padding: 16,
              color: 'rgba(255, 255, 255, 0.65)',
            }}
          >
            <div>Version 1.0.0</div>
          </div>
        );
      }}
      avatarProps={{
        src: 'https://gw.alipayobjects.com/zos/antfincdn/XAosXuNZyF/BiazfanxmamNRoxxVxka.png',
        title: 'Admin User',
        size: 'small',
      }}
      actionsRender={() => [
        <Button key="notification" icon={<NotificationOutlined />} />,
        <Dropdown key="user" menu={{ items: userMenuItems }}>
          <Avatar icon={<UserOutlined />} />
        </Dropdown>,
      ]}
      menuHeaderRender={(logo, title) => (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {logo}
          {title}
        </div>
      )}
      headerTitleRender={(logo, title, props) => {
        return <div>{title}</div>;
      }}
      navTheme="dark"
      headerTheme="dark"
      primaryColor="#1890ff"
      layout="side"
      contentWidth="Fluid"
      fixedHeader={false}
      fixSiderbar={true}
    >
      <PageContainer title="页面标题">
        <YourContent />
      </PageContainer>
    </ProLayout>
  );
};
```

### 示例 5: 网格列表

```tsx
import { ProList, ProCard } from '@ant-design/pro-components';
import { Avatar, Tag, Button } from 'antd';

export default () => {
  const [dataSource, setDataSource] = useState([
    {
      id: 1,
      title: '卡片标题1',
      description: '这是卡片描述内容',
      image: 'https://via.placeholder.com/300x200',
      category: '分类A',
      status: '进行中',
      author: '张三',
      views: 1234,
      likes: 56,
    },
    // ... more data
  ]);

  return (
    <ProList
      grid={{ gutter: 16, column: 3 }}
      dataSource={dataSource}
      renderItem={(item) => ({
        title: item.title,
        subTitle: item.description,
        actions: [
          <Button key="edit" type="link">
            编辑
          </Button>,
          <Button key="delete" type="link" danger>
            删除
          </Button>,
        ],
        avatar: (
          <Avatar src={item.image} size={120} shape="square" />
        ),
        content: (
          <ProCard
            hoverable
            style={{ height: '100%' }}
            bodyStyle={{
              padding: 24,
            }}
          >
            <div
              style={{
                marginBottom: 16,
                display: 'flex',
                gap: 8,
              }}
            >
              <Tag color="blue">{item.category}</Tag>
              <Tag color="green">{item.status}</Tag>
            </div>

            <div style={{ marginBottom: 16 }}>
              <p>{item.description}</p>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                color: 'rgba(0, 0, 0, 0.45)',
              }}
            >
              <span>
                <EyeOutlined /> {item.views}
              </span>
              <span>
                <LikeOutlined /> {item.likes}
              </span>
              <span>
                <UserOutlined /> {item.author}
              </span>
            </div>
          </ProCard>
        ),
      })}
      pagination={{
        defaultPageSize: 9,
        showSizeChanger: true,
      }}
      headerTitle="卡片列表"
    />
  );
};
```

### 示例 6: 数据转换和错误处理

```tsx
import { ProTable } from '@ant-design/pro-components';
import { message } from 'antd';

type ApiResponse = {
  code: number;
  message: string;
  data: {
    list: TableItem[];
    total: number;
  };
};

const transformRequestParams = (params: any) => {
  const { current, pageSize, ...rest } = params;
  return {
    page: current,
    page_size: pageSize,
    ...rest,
  };
};

const transformResponse = (response: ApiResponse) => {
  return {
    data: response.data.list,
    success: response.code === 200,
    total: response.data.total,
  };
};

export default () => {
  return (
    <ProTable
      columns={columns}
      request={async (params, sort, filter) => {
        try {
          // 1. 转换请求参数
          const requestParams = transformRequestParams({
            ...params,
            sort,
            filter,
          });

          // 2. 发送请求
          const response = await fetch('/api/list', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestParams),
          });

          // 3. 解析响应
          const data: ApiResponse = await response.json();

          // 4. 错误处理
          if (data.code !== 200) {
            message.error(data.message || '请求失败');
            return {
              data: [],
              success: false,
              total: 0,
            };
          }

          // 5. 转换响应数据
          return transformResponse(data);
        } catch (error) {
          // 6. 异常处理
          console.error('请求异常:', error);
          message.error('网络错误,请稍后重试');
          return {
            data: [],
            success: false,
            total: 0,
          };
        }
      }}
      rowKey="id"
      pagination={{
        defaultPageSize: 10,
      }}
      onError={(error) => {
        console.error('表格错误:', error);
        message.error('加载失败');
      }}
      onLoad={(data) => {
        console.log('数据加载完成:', data);
      }}
    />
  );
};
```

---

## 最佳实践

### 1. ProTable 使用规范

**✅ 推荐**: 使用 request 模式,让 ProTable 管理加载状态

```tsx
<ProTable
  request={async (params) => {
    const msg = await fetchData(params);
    return {
      data: msg.data,
      success: true,
      total: msg.total,
    };
  }}
/>
```

**❌ 避免**: 手动管理 loading 和 dataSource

```tsx
// 不推荐
const [loading, setLoading] = useState(false);
const [dataSource, setDataSource] = useState([]);

useEffect(() => {
  setLoading(true);
  fetchData().then((data) => {
    setDataSource(data);
    setLoading(false);
  });
}, []);
```

### 2. 列配置规范

**✅ 推荐**: 使用 valueType 简化配置

```tsx
{
  title: '状态',
  dataIndex: 'status',
  valueType: 'select',
  valueEnum: {
    open: { text: '开启', status: 'Success' },
    closed: { text: '关闭', status: 'Default' },
  },
}
```

**❌ 避免**: 手动编写 render

```tsx
{
  title: '状态',
  dataIndex: 'status',
  render: (status) => {
    return status === 'open' ? (
      <Tag color="success">开启</Tag>
    ) : (
      <Tag>关闭</Tag>
    );
  },
}
```

### 3. 表单联动

**✅ 推荐**: 使用 ProFormDependency 实现联动

```tsx
<ProFormDependency name={['type']}>
  {({ type }) => {
    return type === 'company' ? (
      <ProFormText name="companyName" label="公司名称" />
    ) : null;
  }}
</ProFormDependency>
```

**❌ 避免**: 使用 useEffect + 手动控制显示隐藏

```tsx
useEffect(() => {
  if (type === 'company') {
    setShowCompanyField(true);
  }
}, [type]);
```

### 4. 权限控制

**✅ 推荐**: 在路由配置中使用 access 字段

```tsx
{
  path: '/admin',
  name: '管理员',
  access: 'canAdmin',
}
```

**❌ 避免**: 在组件内部手动判断权限

```tsx
if (hasPermission('canAdmin')) {
  // 渲染内容
}
```

### 5. 性能优化

**✅ 推荐**: 使用虚拟列表处理大数据

```tsx
<ProList
  dataSource={largeData}
  pagination={{
    defaultPageSize: 20,
  }}
/>
```

**❌ 避免**: 一次性渲染大量数据

```tsx
<ProList
  dataSource={largeData}
  pagination={false}
/>
```

---

## 常见问题

### Q: ProTable 的 request 什么时候被调用?

A: 在以下情况会调用:
1. 组件首次挂载
2. 分页、排序、筛选变化
3. 调用 `actionRef.current?.reload()`
4. 调用 `actionRef.current?.reloadAndRest()`

### Q: 如何手动触发表格刷新?

A: 使用 `actionRef`:

```tsx
const actionRef = useRef<ActionType>();

<ProTable actionRef={actionRef} {...props} />

// 手动刷新
actionRef.current?.reload();

// 刷新并重置页码
actionRef.current?.reloadAndRest();
```

### Q: ProForm 如何获取表单实例?

A: 使用 `formRef`:

```tsx
const formRef = useRef<ProFormInstance>();

<ProForm formRef={formRef} {...props} />

// 获取表单值
const values = formRef.current?.getFieldsValue();

// 设置表单值
formRef.current?.setFieldsValue({ name: 'value' });

// 重置表单
formRef.current?.resetFields();
```

### Q: ProLayout 如何动态改变主题?

A: 使用 `props` 传递主题配置:

```tsx
const [theme, setTheme] = useState('light');

<ProLayout
  navTheme={theme}
  headerTheme={theme}
  {...props}
/>

// 切换主题
setTheme('dark');
```

### Q: ProList 如何实现无限滚动?

A: 结合 `pagination` 和 `onLoadMore`:

```tsx
<ProList
  pagination={false}
  onLoadMore={async () => {
    const moreData = await fetchMoreData();
    setDataSource([...dataSource, ...moreData]);
  }}
/>
```

### Q: ProTable 如何实现前端分页?

A: 使用 `dataSource` + `pagination`:

```tsx
<ProTable
  dataSource={allData}
  pagination={{
    pageSize: 10,
    onChange: (page, pageSize) => {
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      setCurrentData(allData.slice(start, end));
    },
  }}
/>
```

### Q: 如何自定义 ProTable 的搜索表单?

A: 使用 `search` 配置:

```tsx
<ProTable
  search={{
    span: 6,
    defaultCollapsed: false,
    optionRender: ({ searchText, resetText }, { form }) => [
      <Button key="search" type="primary" onClick={() => form?.submit()}>
        {searchText}
      </Button>,
      <Button key="reset" onClick={() => form?.resetFields()}>
        {resetText}
      </Button>,
    ],
  }}
/>
```

### Q: ProForm 如何实现动态字段?

A: 使用 `ProFormList`:

```tsx
<ProFormList
  name="users"
  creatorButtonProps={{
    position: 'top',
    creatorButtonText: '添加用户',
  }}
>
  {(f, index, action) => (
    <ProFormText name={[index, 'name']} label="姓名" />
  )}
</ProFormList>
```

---

## 参考资源

- [ProComponents 官方文档](https://procomponents.ant.design/)
- [ProTable API](https://procomponents.ant.design/components/table)
- [ProForm API](https://procomponents.ant.design/components/form)
- [ProLayout API](https://procomponents.ant.design/components/layout)
- [ProList API](https://procomponents.ant.design/components/list)
- [Ant Design 官方文档](https://ant.design/index-cn)

---

## 版本要求

- **@ant-design/pro-components**: >= 2.0.0
- **@ant-design/pro-table**: >= 3.0.0
- **Ant Design**: >= 5.0.0
- **React**: >= 17.0.0

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
