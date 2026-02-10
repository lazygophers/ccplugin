---
name: antd-table-skills
description: Ant Design 表格组件完整指南 - 虚拟滚动、分页、排序、筛选、编辑、树形表格、性能优化（深入版）
---

# Ant Design Table 完整指南

Table 是 Ant Design 中最重要的数据展示组件,用于展示大量结构化的数据,并支持排序、搜索、分页、自定义操作等复杂行为。

## 版本要求

- **Ant Design**: 5.9.0+（虚拟滚动需要 5.9.0+）
- **React**: 18.0+
- **TypeScript**: 5.2+（推荐）

## 核心特性

- ✅ **虚拟滚动**: 支持 10000+ 行数据流畅渲染
- ✅ **灵活配置**: 支持本地/远程数据源、排序、筛选、分页
- ✅ **可编辑**: 行编辑、单元格编辑、批量编辑
- ✅ **树形数据**: 支持树形结构展示和懒加载
- ✅ **固定列**: 左右固定列、固定表头
- ✅ **响应式**: 自适应不同屏幕尺寸
- ✅ **无障碍**: 完整的键盘导航和屏幕阅读器支持

---

## 1. Table 基础

### 1.1 完整 API 文档

#### Table Props

| 参数 | 说明 | 类型 | 默认值 | 版本 |
| --- | --- | --- | --- | --- |
| `bordered` | 是否展示外边框和列边框 | `boolean` | `false` | - |
| `columns` | 表格列的配置描述 | `ColumnsType[]` | - | - |
| `dataSource` | 数据数组 | `object[]` | - | - |
| `pagination` | 分页器配置 | `object \| false` | - | - |
| `rowKey` | 表格行 key 的取值 | `string \| function` | `'key'` | - |
| `rowSelection` | 行选择配置 | `object` | - | - |
| `scroll` | 表格滚动配置 | `{ x?: number, y?: number }` | - | - |
| `loading` | 页面是否加载中 | `boolean \| SpinProps` | `false` | - |
| `size` | 表格大小 | `'large' \| 'middle' \| 'small'` | `'large'` | - |
| `tableLayout` | 表格元素的 table-layout 属性 | `'auto' \| 'fixed'` | `'auto'` | - |
| `title` | 表格标题 | `function(data)` | - | - |
| `footer` | 表格尾部 | `function(data)` | - | - |
| `expandable` | 展开行配置 | `object` | - | - |
| `summary` | 总结栏 | `function(data)` | - | - |
| `virtual` | 是否启用虚拟滚动 | `boolean` | `false` | 5.9.0 |
| `sticky` | 设置粘性头部和滚动条 | `boolean \| object` | - | 4.6.0 |
| `onChange` | 分页、排序、筛选变化时触发 | `function` | - | - |
| `onRow` | 设置行属性 | `function(record)` | - | - |
| `onHeaderRow` | 设置头部行属性 | `function(columns)` | - | - |

#### Column Props

| 参数 | 说明 | 类型 | 默认值 | 版本 |
| --- | --- | --- | --- | --- |
| `title` | 列标题 | `ReactNode \| function` | - | - |
| `dataIndex` | 列数据在数据项中对应的路径 | `string \| string[]` | - | - |
| `key` | React 需要的 key | `string` | - | - |
| `render` | 生成复杂数据的渲染函数 | `function(value, record, index)` | - | - |
| `align` | 列的对齐方式 | `'left' \| 'right' \| 'center'` | `'left'` | - |
| `width` | 列宽度 | `string \| number` | - | - |
| `fixed` | 列是否固定 | `boolean \| 'left' \| 'right'` | - | - |
| `sorter` | 排序函数 | `function \| boolean \| { multiple: number }` | - | - |
| `filters` | 表头的筛选菜单项 | `object[]` | - | - |
| `onFilter` | 本地筛选函数 | `function` | - | - |
| `filterMultiple` | 是否多选 | `boolean` | `true` | - |
| `filterMode` | 筛选菜单 UI | `'menu' \| 'tree'` | `'menu'` | 4.17.0 |
| `ellipsis` | 超过宽度自动省略 | `boolean \| { showTitle?: boolean }` | `false` | - |
| `colSpan` | 表头列合并 | `number` | - | - |
| `className` | 列样式类名 | `string` | - | - |
| `onCell` | 设置单元格属性 | `function(record)` | - | - |
| `onHeaderCell` | 设置头部单元格属性 | `function(column)` | - | - |

### 1.2 基础示例

```tsx
import React from 'react';
import { Table } from 'antd';
import type { TableProps } from 'antd';

interface DataType {
  key: string;
  name: string;
  age: number;
  address: string;
}

const dataSource: DataType[] = [
  {
    key: '1',
    name: '胡彦斌',
    age: 32,
    address: '西湖区湖底公园1号',
  },
  {
    key: '2',
    name: '胡彦祖',
    age: 42,
    address: '西湖区湖底公园1号',
  },
];

const columns: TableProps<DataType>['columns'] = [
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '年龄',
    dataIndex: 'age',
    key: 'age',
  },
  {
    title: '住址',
    dataIndex: 'address',
    key: 'address',
  },
];

const BasicTable: React.FC = () => {
  return <Table<DataType> dataSource={dataSource} columns={columns} />;
};

export default BasicTable;
```

### 1.3 数据源管理

#### 本地数据源

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';

const LocalDataSourceTable: React.FC = () => {
  const [data] = useState([
    { key: '1', name: 'John', age: 32 },
    { key: '2', name: 'Jim', age: 42 },
  ]);

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  return <Table dataSource={data} columns={columns} />;
};
```

#### 远程数据源

```tsx
import React, { useState, useEffect } from 'react';
import { Table } from 'antd';
import type { TablePaginationConfig } from 'antd';
import type { FilterValue, SorterResult } from 'antd/es/table/interface';

interface TableParams {
  pagination?: TablePaginationConfig;
  filters?: Record<string, FilterValue | null>;
  sorter?: SorterResult<any> | SorterResult<any>[];
}

const RemoteDataTable: React.FC = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tableParams, setTableParams] = useState<TableParams>({
    pagination: {
      current: 1,
      pageSize: 10,
    },
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/data');
      const result = await response.json();

      setData(result.data);
      setTableParams({
        ...tableParams,
        pagination: {
          ...tableParams.pagination,
          total: result.total,
        },
      });
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [tableParams.pagination?.current, tableParams.pagination?.pageSize]);

  const handleTableChange: TableProps['onChange'] = (
    pagination,
    filters,
    sorter
  ) => {
    setTableParams({
      pagination,
      filters,
      sorter,
    });
  };

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      loading={loading}
      onChange={handleTableChange}
      pagination={tableParams.pagination}
    />
  );
};
```

### 1.4 列配置完整说明

```tsx
const columns = [
  {
    // 基础配置
    title: '姓名',
    dataIndex: 'name', // 支持 'user.name' 嵌套路径
    key: 'name',

    // 渲染配置
    render: (value: any, record: any, index: number) => {
      return <a href="#">{value}</a>;
    },

    // 样式配置
    align: 'center',
    width: 100,
    className: 'custom-column',
    fixed: 'left', // 'left' | 'right' | true

    // 排序配置
    sorter: (a: any, b: any) => a.name.localeCompare(b.name),
    sortOrder: 'ascend', // 'ascend' | 'descend' | null
    sortDirections: ['ascend', 'descend'],

    // 筛选配置
    filters: [
      { text: 'London', value: 'London' },
      { text: 'New York', value: 'New York' },
    ],
    onFilter: (value: any, record: any) => record.address.includes(value),
    filteredValue: ['London'], // 受控模式

    // 省略配置
    ellipsis: true,
    ellipsis: { showTitle: false },

    // 自定义配置
    onCell: (record: any) => ({
      style: { background: record.age > 30 ? '#f0f0f0' : '' },
      onClick: () => console.log(record),
    }),

    onHeaderCell: (column: any) => ({
      style: { background: '#fafafa' },
    }),
  },
];
```

---

## 2. 虚拟滚动 ⭐⭐⭐

虚拟滚动是 Table 组件最重要的性能优化特性,可以流畅渲染 10000+ 行数据。

### 2.1 基础虚拟滚动

**核心要点:**
- 必须设置 `virtual={true}`
- `scroll.x` 和 `scroll.y` 必须设置为数字类型
- `scroll.y` 必须是固定高度值

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface DataType {
  key: string;
  name: string;
  age: number;
  address: string;
}

const VirtualTable: React.FC = () => {
  // 生成 10000 条数据
  const data = useMemo(() => {
    const dataSource: DataType[] = [];
    for (let i = 0; i < 10000; i++) {
      dataSource.push({
        key: `${i}`,
        name: `User ${i}`,
        age: Math.floor(Math.random() * 100),
        address: `Address ${i}`,
      });
    }
    return dataSource;
  }, []);

  const columns: ColumnsType<DataType> = [
    {
      title: 'Name',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: 'Age',
      dataIndex: 'age',
      width: 100,
      sorter: (a, b) => a.age - b.age,
    },
    {
      title: 'Address',
      dataIndex: 'address',
      width: 200,
    },
  ];

  return (
    <Table<DataType>
      virtual
      columns={columns}
      dataSource={data}
      scroll={{ x: 1200, y: 500 }}
      pagination={false}
    />
  );
};

export default VirtualTable;
```

### 2.2 可变高度虚拟滚动

当单元格高度不一致时,需要特殊处理:

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const VariableHeightTable: React.FC = () => {
  const data = useMemo(() => {
    return Array.from({ length: 10000 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      description: 'A'.repeat(Math.floor(Math.random() * 200)), // 随机长度文本
    }));
  }, []);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      width: 300,
      // 可变高度内容
      render: (text: string) => (
        <div style={{ whiteSpace: 'pre-wrap' }}>{text}</div>
      ),
    },
  ];

  return (
    <Table
      virtual
      columns={columns}
      dataSource={data}
      scroll={{ x: 600, y: 500 }}
      pagination={false}
      // 关键配置:设置预估行高
      // @ts-ignore
      listItemHeight={60} // 预估每行 60px
    />
  );
};
```

### 2.3 横向 + 纵向虚拟滚动

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const BothDirectionVirtualTable: React.FC = () => {
  const data = useMemo(() => {
    return Array.from({ length: 10000 }, (_, i) => ({
      key: `${i}`,
      ...Object.fromEntries(
        Array.from({ length: 50 }, (_, j) => [
          `column${j}`,
          `Data ${i}-${j}`,
        ])
      ),
    }));
  }, []);

  const columns = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => ({
      title: `Column ${i}`,
      dataIndex: `column${i}`,
      width: 150,
      fixed: i < 2 ? 'left' : i > 47 ? 'right' : undefined,
    }));
  }, []);

  return (
    <Table
      virtual
      columns={columns}
      dataSource={data}
      scroll={{ x: 7500, y: 600 }}
      pagination={false}
    />
  );
};
```

### 2.4 虚拟滚动与展开行的兼容性

```tsx
import React, { useMemo, useState } from 'react';
import { Table } from 'antd';

interface ExpandedDataType {
  key: string;
  name: string;
  age: number;
  address: string;
  description: string;
}

const VirtualExpandTable: React.FC = () => {
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([]);

  const data = useMemo(() => {
    return Array.from({ length: 5000 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      age: Math.floor(Math.random() * 100),
      address: `Address ${i}`,
      description: `Detailed description for user ${i}`.repeat(10),
    }));
  }, []);

  const columns = [
    { title: 'Name', dataIndex: 'name', width: 150 },
    { title: 'Age', dataIndex: 'age', width: 100 },
    { title: 'Address', dataIndex: 'address', width: 200 },
  ];

  const expandedRowRender = (record: ExpandedDataType) => {
    return (
      <div style={{ padding: '16px' }}>
        <p><strong>Description:</strong></p>
        <p>{record.description}</p>
      </div>
    );
  };

  return (
    <Table<ExpandedDataType>
      virtual
      columns={columns}
      dataSource={data}
      expandable={{
        expandedRowRender,
        expandedRowKeys,
        onExpandedRowsChange: (keys) => setExpandedRowKeys(keys),
      }}
      scroll={{ x: 800, y: 500 }}
      pagination={false}
    />
  );
};
```

### 2.5 虚拟滚动性能优化和注意事项

#### 关键优化点

1. **固定行高**: 如果可能,尽量保持行高一致
2. **简化渲染**: render 函数中避免复杂计算
3. **避免内联函数**: 使用 useMemo 缓存 columns
4. **减少固定列**: 固定列会影响性能

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const OptimizedVirtualTable: React.FC = () => {
  const data = useMemo(() => {
    return Array.from({ length: 10000 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      age: i,
    }));
  }, []);

  // ✅ 使用 useMemo 缓存 columns
  const columns = useMemo(() => [
    {
      title: 'Name',
      dataIndex: 'name',
      width: 150,
      // ✅ 使用 useCallback 或外置函数
      render: (name: string) => <span>{name}</span>,
    },
    {
      title: 'Age',
      dataIndex: 'age',
      width: 100,
      // ✅ 简单渲染逻辑
      render: (age: number) => age,
    },
  ], []);

  return (
    <Table
      virtual
      columns={columns}
      dataSource={data}
      scroll={{ x: 400, y: 500 }}
      pagination={false}
      // ✅ 禁用不必要的功能
      rowHoverable={false}
    />
  );
};
```

#### 常见问题解决

**问题 1: 虚拟滚动与自定义 components 冲突**

```tsx
// ❌ 错误: 直接使用自定义 body.row
const components = {
  body: {
    row: ({ children, ...props }) => (
      <tr {...props}>{children}</tr>
    ),
  },
};

// ✅ 正确: 使用 forwardRef
import React from 'react';

const CustomRow = React.forwardRef<HTMLTableRowElement, any>(
  (props, ref) => {
    return <tr {...props} ref={ref} />;
  }
);

const components = {
  body: {
    row: CustomRow,
  },
};
```

**问题 2: 虚拟滚动下动态高度不准确**

```tsx
// ✅ 设置预估行高
<Table
  virtual
  scroll={{ x: 1200, y: 500 }}
  // @ts-ignore
  listItemHeight={60} // 预估每行 60px
/>
```

### 2.6 虚拟滚动 vs 无限滚动对比

| 特性 | 虚拟滚动 | 无限滚动 (Pagination) |
| --- | --- | --- |
| 数据量 | 10000+ 行 | 任意 (分页加载) |
| 内存占用 | 固定 (只渲染可见区) | 线性增长 |
| 滚动体验 | 流畅 | 需要加载等待 |
| 实现复杂度 | 简单 (virtual={true}) | 中等 (需监听滚动) |
| 适用场景 | 已加载全部数据 | 远程分页数据 |

**虚拟滚动推荐场景:**
- 数据已在内存中 (如导出数据、本地处理)
- 需要快速滚动浏览
- 数据量 5000+ 行

**无限滚动推荐场景:**
- 数据需要远程加载
- 数据持续增长 (如社交媒体)
- 需要按需加载减少网络请求

---

## 3. 高级功能

### 3.1 排序

#### 本地排序

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';
import type { SorterResult } from 'antd/es/table/interface';

interface DataType {
  key: string;
  name: string;
  age: number;
}

const LocalSortTable: React.FC = () => {
  const [data, setData] = useState<DataType[]>([
    { key: '1', name: 'John', age: 32 },
    { key: '2', name: 'Jim', age: 42 },
    { key: '3', name: 'Joe', age: 28 },
  ]);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      sorter: (a: DataType, b: DataType) => a.name.localeCompare(b.name),
    },
    {
      title: 'Age',
      dataIndex: 'age',
      sorter: (a: DataType, b: DataType) => a.age - b.age,
      defaultSortOrder: 'descend' as const,
    },
  ];

  const onChange = (
    pagination: any,
    filters: any,
    sorter: SorterResult<DataType> | SorterResult<DataType>[]
  ) => {
    console.log('Sorter:', sorter);
  };

  return (
    <Table
      columns={columns}
      dataSource={data}
      onChange={onChange}
    />
  );
};
```

#### 远程排序

```tsx
import React, { useState, useEffect } from 'react';
import { Table } from 'antd';
import type { TableProps } from 'antd';

const RemoteSortTable: React.FC = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sortField, setSortField] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<string>('');

  const fetchData = async (field?: string, order?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (field && order) {
        params.append('sortField', field);
        params.append('sortOrder', order);
      }

      const response = await fetch(`/api/data?${params}`);
      const result = await response.json();
      setData(result.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      // 远程排序:设置为 true
      sorter: true,
      sortOrder: sortField === 'name' ? (sortOrder === 'asc' ? 'ascend' : 'descend') : null,
    },
    {
      title: 'Age',
      dataIndex: 'age',
      sorter: true,
      sortOrder: sortField === 'age' ? (sortOrder === 'asc' ? 'ascend' : 'descend') : null,
    },
  ];

  const handleChange: TableProps['onChange'] = (pagination, filters, sorter) => {
    const sorterResult = sorter as SorterResult<any>;
    setSortField(sorterResult.field);
    setSortOrder(sorterResult.order === 'ascend' ? 'asc' : 'descend');
    fetchData(sorterResult.field, sorterResult.order);
  };

  return (
    <Table
      columns={columns}
      dataSource={data}
      loading={loading}
      onChange={handleChange}
    />
  );
};
```

#### 多列排序

```tsx
import React from 'react';
import { Table } from 'antd';

const MultiSortTable: React.FC = () => {
  const data = [
    { key: '1', name: 'John', age: 32, score: 90 },
    { key: '2', name: 'Jim', age: 42, score: 85 },
    { key: '3', name: 'Joe', age: 28, score: 90 },
  ];

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Age',
      dataIndex: 'age',
      // 设置排序优先级
      sorter: {
        compare: (a: any, b: any) => a.age - b.age,
        multiple: 1, // 优先级 1
      },
    },
    {
      title: 'Score',
      dataIndex: 'score',
      sorter: {
        compare: (a: any, b: any) => a.score - b.score,
        multiple: 2, // 优先级 2
      },
    },
  ];

  return <Table columns={columns} dataSource={data} />;
};
```

#### 自定义排序函数

```tsx
const columns = [
  {
    title: 'Version',
    dataIndex: 'version',
    // 自定义版本号排序
    sorter: (a: any, b: any) => {
      const parseVersion = (v: string) => v.split('.').map(Number);
      const aParts = parseVersion(a.version);
      const bParts = parseVersion(b.version);

      for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
        const aPart = aParts[i] || 0;
        const bPart = bParts[i] || 0;
        if (aPart !== bPart) return aPart - bPart;
      }
      return 0;
    },
  },
  {
    title: 'Date',
    dataIndex: 'date',
    // 日期排序
    sorter: (a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  },
  {
    title: 'Price',
    dataIndex: 'price',
    // 价格排序 (处理货币符号)
    sorter: (a: any, b: any) => {
      const priceA = parseFloat(a.price.replace(/[^0-9.-]+/g, ''));
      const priceB = parseFloat(b.price.replace(/[^0-9.-]+/g, ''));
      return priceA - priceB;
    },
  },
];
```

### 3.2 筛选

#### 本地筛选

```tsx
import React from 'react';
import { Table } from 'antd';

const LocalFilterTable: React.FC = () => {
  const data = [
    { key: '1', name: 'John', age: 32, address: 'London' },
    { key: '2', name: 'Jim', age: 42, address: 'New York' },
    { key: '3', name: 'Joe', age: 28, address: 'London' },
  ];

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Age',
      dataIndex: 'age',
    },
    {
      title: 'Address',
      dataIndex: 'address',
      filters: [
        { text: 'London', value: 'London' },
        { text: 'New York', value: 'New York' },
      ],
      onFilter: (value: any, record: any) => record.address.includes(value),
      filteredValue: null, // 受控模式
    },
  ];

  return <Table columns={columns} dataSource={data} />;
};
```

#### 远程筛选

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';
import type { FilterValue } from 'antd/es/table/interface';

const RemoteFilterTable: React.FC = () => {
  const [filters, setFilters] = useState<Record<string, FilterValue | null>>({});

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Address',
      dataIndex: 'address',
      filters: [
        { text: 'London', value: 'London' },
        { text: 'New York', value: 'New York' },
      ],
      // 远程筛选:受控模式
      filteredValue: filters.address || null,
    },
  ];

  const handleChange = (pagination: any, filters: any) => {
    setFilters(filters);
    // 发起远程请求
    fetchData(filters);
  };

  return <Table columns={columns} dataSource={[]} onChange={handleChange} />;
};
```

#### 自定义筛选菜单

```tsx
import React, { useRef, useState } from 'react';
import { Table, Input, Button, Space } from 'antd';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import { SearchOutlined } from '@ant-design/icons';

const CustomFilterTable: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const searchInput = useRef<any>(null);

  const handleSearch = (
    selectedKeys: React.Key[],
    confirm: FilterDropdownProps['confirm'],
    dataIndex: string
  ) => {
    confirm();
    setSearchText(selectedKeys[0] as string);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters: () => void) => {
    clearFilters();
    setSearchText('');
  };

  const getColumnSearchProps = (dataIndex: string) => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <Input
          ref={searchInput}
          placeholder={`Search ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
          style={{ marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            Search
          </Button>
          <Button
            onClick={() => handleReset(clearFilters!)}
            size="small"
            style={{ width: 90 }}
          >
            Reset
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <SearchOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
    ),
    onFilter: (value: any, record: any) =>
      record[dataIndex]
        .toString()
        .toLowerCase()
        .includes((value as string).toLowerCase()),
  });

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      ...getColumnSearchProps('name'),
    },
    {
      title: 'Age',
      dataIndex: 'age',
      key: 'age',
    },
  ];

  return <Table columns={columns} dataSource={[]} />;
};
```

### 3.3 固定列

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const FixedColumnTable: React.FC = () => {
  const data = useMemo(() => {
    return Array.from({ length: 100 }, (_, i) => ({
      key: `${i}`,
      ...Object.fromEntries(
        Array.from({ length: 20 }, (_, j) => [`column${j}`, `Data ${i}-${j}`])
      ),
    }));
  }, []);

  const columns = useMemo(() => {
    return [
      // 左固定列
      {
        title: 'Left Fixed 1',
        dataIndex: 'column0',
        fixed: 'left',
        width: 150,
      },
      {
        title: 'Left Fixed 2',
        dataIndex: 'column1',
        fixed: 'left',
        width: 150,
      },
      // 中间滚动列
      ...Array.from({ length: 16 }, (_, i) => ({
        title: `Column ${i + 2}`,
        dataIndex: `column${i + 2}`,
        width: 150,
      })),
      // 右固定列
      {
        title: 'Right Fixed 1',
        dataIndex: 'column18',
        fixed: 'right',
        width: 150,
      },
      {
        title: 'Right Fixed 2',
        dataIndex: 'column19',
        fixed: 'right',
        width: 150,
      },
    ];
  }, []);

  return (
    <Table
      columns={columns}
      dataSource={data}
      scroll={{ x: 3000, y: 500 }}
      // 关键:建议设置 scroll.x 为固定值
      // 非固定列宽度之和不要超过 scroll.x
    />
  );
};
```

**固定列注意事项:**
1. 必须指定固定列的 `width`
2. 建议设置 `scroll.x` 为固定值
3. 非固定列宽度之和不要超过 `scroll.x`
4. 固定列通过 sticky 实现,IE 11 会降级为横向滚动
5. 避免过多固定列 (影响性能)

### 3.4 固定表头

```tsx
import React from 'react';
import { Table } from 'antd';

const FixedHeaderTable: React.FC = () => {
  const data = Array.from({ length: 100 }, (_, i) => ({
    key: `${i}`,
    name: `User ${i}`,
    age: i,
    address: `Address ${i}`,
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name', width: 150 },
    { title: 'Age', dataIndex: 'age', width: 100 },
    { title: 'Address', dataIndex: 'address', width: 200 },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      scroll={{ y: 400 }} // 设置纵向滚动
      pagination={false}
    />
  );
};
```

#### 随页面滚动的固定表头

```tsx
import React from 'react';
import { Table } from 'antd';

const StickyTable: React.FC = () => {
  return (
    <Table
      columns={columns}
      dataSource={data}
      sticky={{ offsetHeader: 64 }} // 表头距离顶部 64px
      scroll={{ y: 400 }}
    />
  );
};
```

---

## 4. 可编辑表格 ⭐

### 4.1 行编辑模式

```tsx
import React, { useState, createContext, useContext } from 'react';
import { Table, Form, Input, Button, Popconfirm } from 'antd';
import type { FormInstance } from 'antd/es/form';

const EditableContext = createContext<FormInstance<any> | null>(null);

interface EditableRowProps {
  index: number;
}

const EditableRow: React.FC<EditableRowProps> = ({ index, ...props }) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} component={false}>
      <EditableContext.Provider value={form}>
        <tr {...props} />
      </EditableContext.Provider>
    </Form>
  );
};

interface EditableCellProps {
  title: React.ReactNode;
  editable: boolean;
  children: React.ReactNode;
  dataIndex: string;
  record: any;
  handleSave: (record: any) => void;
}

const EditableCell: React.FC<EditableCellProps> = ({
  title,
  editable,
  children,
  dataIndex,
  record,
  handleSave,
  ...rest
}) => {
  const [editing, setEditing] = useState(false);
  const form = useContext(EditableContext)!;

  const toggleEdit = () => {
    setEditing(!editing);
    form.setFieldsValue({ [dataIndex]: record[dataIndex] });
  };

  const save = async () => {
    try {
      const values = await form.validateFields();
      toggleEdit();
      handleSave({ ...record, ...values });
    } catch (err) {
      console.log('Save failed:', err);
    }
  };

  let childNode = children;

  if (editable) {
    childNode = editing ? (
      <Form.Item
        style={{ margin: 0 }}
        name={dataIndex}
        rules={[
          {
            required: true,
            message: `${title} is required.`,
          },
        ]}
      >
        <Input onPressEnter={save} onBlur={save} />
      </Form.Item>
    ) : (
      <div
        className="editable-cell-value-wrap"
        style={{ paddingRight: 24 }}
        onClick={toggleEdit}
      >
        {children}
      </div>
    );
  }

  return <td {...rest}>{childNode}</td>;
};

const EditableTable: React.FC = () => {
  const [dataSource, setDataSource] = useState([
    {
      key: '0',
      name: 'Edward King 0',
      age: '32',
      address: 'London, Park Lane no. 0',
    },
    {
      key: '1',
      name: 'Edward King 1',
      age: '32',
      address: 'London, Park Lane no. 1',
    },
  ]);

  const [count, setCount] = useState(2);

  const handleDelete = (key: string) => {
    const newData = dataSource.filter((item) => item.key !== key);
    setDataSource(newData);
  };

  const defaultColumns: any[] = [
    {
      title: 'name',
      dataIndex: 'name',
      width: '30%',
      editable: true,
    },
    {
      title: 'age',
      dataIndex: 'age',
    },
    {
      title: 'address',
      dataIndex: 'address',
    },
    {
      title: 'operation',
      dataIndex: 'operation',
      render: (_: any, record: any) =>
        dataSource.length >= 1 ? (
          <Popconfirm
            title="Sure to delete?"
            onConfirm={() => handleDelete(record.key)}
          >
            <a>Delete</a>
          </Popconfirm>
        ) : null,
    },
  ];

  const handleSave = (row: any) => {
    const newData = [...dataSource];
    const index = newData.findIndex((item) => row.key === item.key);
    const item = newData[index];
    newData.splice(index, 1, {
      ...item,
      ...row,
    });
    setDataSource(newData);
  };

  const columns = defaultColumns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record: any) => ({
        record,
        editable: col.editable,
        dataIndex: col.dataIndex,
        title: col.title,
        handleSave,
      }),
    };
  });

  const onAdd = () => {
    const newData = {
      key: `${count}`,
      name: `Edward King ${count}`,
      age: '32',
      address: `London, Park Lane no. ${count}`,
    };
    setDataSource([...dataSource, newData]);
    setCount(count + 1);
  };

  return (
    <div>
      <Button
        onClick={onAdd}
        type="primary"
        style={{ marginBottom: 16 }}
      >
        Add a row
      </Button>
      <Table
        components={{
          body: {
            row: EditableRow,
            cell: EditableCell,
          },
        }}
        rowClassName={() => 'editable-row'}
        bordered
        dataSource={dataSource}
        columns={columns}
      />
    </div>
  );
};

export default EditableTable;
```

### 4.2 单元格编辑

```tsx
import React, { useState } from 'react';
import { Table, Input, InputNumber, Popconfirm, Form } from 'antd';

interface EditableCellProps extends React.HTMLAttributes<HTMLElement> {
  editing: boolean;
  dataIndex: string;
  title: any;
  inputType: 'number' | 'text';
  record: any;
  index: number;
  children: React.ReactNode;
}

const EditableCell: React.FC<EditableCellProps> = ({
  editing,
  dataIndex,
  title,
  inputType,
  record,
  index,
  children,
  ...restProps
}) => {
  const inputNode = inputType === 'number' ? <InputNumber /> : <Input />;

  return (
    <td {...restProps}>
      {editing ? (
        <Form.Item
          name={dataIndex}
          style={{ margin: 0 }}
          rules={[
            {
              required: true,
              message: `Please Input ${title}!`,
            },
          ]}
        >
          {inputNode}
        </Form.Item>
      ) : (
        children
      )}
    </td>
  );
};

const CellEditableTable: React.FC = () => {
  const [form] = Form.useForm();
  const [data, setData] = useState([
    {
      key: '0',
      name: 'Edward King 0',
      age: '32',
      address: 'London, Park Lane no. 0',
    },
  ]);
  const [editingKey, setEditingKey] = useState('');

  const isEditing = (record: any) => record.key === editingKey;

  const edit = (record: any) => {
    form.setFieldsValue({
      name: '',
      age: '',
      address: '',
      ...record,
    });
    setEditingKey(record.key);
  };

  const cancel = () => {
    setEditingKey('');
  };

  const save = async (key: React.Key) => {
    try {
      const row = await form.validateFields();
      const newData = [...data];
      const index = newData.findIndex((item) => key === item.key);

      if (index > -1) {
        const item = newData[index];
        newData.splice(index, 1, {
          ...item,
          ...row,
        });
        setData(newData);
        setEditingKey('');
      } else {
        newData.push(row);
        setData(newData);
        setEditingKey('');
      }
    } catch (errInfo) {
      console.log('Validate Failed:', errInfo);
    }
  };

  const columns = [
    {
      title: 'name',
      dataIndex: 'name',
      width: '25%',
      editable: true,
    },
    {
      title: 'age',
      dataIndex: 'age',
      width: '15%',
      editable: true,
    },
    {
      title: 'address',
      dataIndex: 'address',
      width: '40%',
      editable: true,
    },
    {
      title: 'operation',
      dataIndex: 'operation',
      render: (_: any, record: any) => {
        const editable = isEditing(record);
        return editable ? (
          <span>
            <a
              onClick={() => save(record.key)}
              style={{ marginRight: 8 }}
            >
              Save
            </a>
            <Popconfirm title="Sure to cancel?" onConfirm={cancel}>
              <a>Cancel</a>
            </Popconfirm>
          </span>
        ) : (
          <a disabled={editingKey !== ''} onClick={() => edit(record)}>
            Edit
          </a>
        );
      },
    },
  ];

  const mergedColumns = columns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record: any) => ({
        record,
        inputType: col.dataIndex === 'age' ? 'number' : 'text',
        dataIndex: col.dataIndex,
        title: col.title,
        editing: isEditing(record),
      }),
    };
  });

  return (
    <Form form={form} component={false}>
      <Table
        components={{
          body: {
            cell: EditableCell,
          },
        }}
        bordered
        dataSource={data}
        columns={mergedColumns}
        rowClassName="editable-row"
      />
    </Form>
  );
};
```

### 4.3 批量编辑

```tsx
import React, { useState } from 'react';
import { Table, Checkbox, Button, Space } from 'antd';

const BatchEditTable: React.FC = () => {
  const [data, setData] = useState(
    Array.from({ length: 10 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      age: i,
      status: 'active',
    }))
  );

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [editing, setEditing] = useState(false);
  const [tempData, setTempData] = useState(data);

  const handleBatchEdit = () => {
    if (selectedRowKeys.length === 0) {
      return;
    }
    setEditing(true);
  };

  const handleSave = () => {
    setData(tempData);
    setEditing(false);
  };

  const handleCancel = () => {
    setTempData(data);
    setEditing(false);
  };

  const updateField = (key: string, field: string, value: any) => {
    const newData = tempData.map((item) => {
      if (selectedRowKeys.includes(item.key)) {
        return { ...item, [field]: value };
      }
      return item;
    });
    setTempData(newData);
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string) => (editing ? <input value={text} /> : text),
    },
    {
      title: 'Age',
      dataIndex: 'age',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status: string) =>
        editing ? (
          <select
            value={status}
            onChange={(e) => updateField('', 'status', e.target.value)}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        ) : (
          status
        ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          onClick={handleBatchEdit}
          disabled={selectedRowKeys.length === 0 || editing}
        >
          Batch Edit
        </Button>
        {editing && (
          <>
            <Button onClick={handleSave}>Save</Button>
            <Button onClick={handleCancel}>Cancel</Button>
          </>
        )}
      </Space>
      <Table
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
        }}
        columns={columns}
        dataSource={editing ? tempData : data}
      />
    </div>
  );
};
```

### 4.4 编辑验证

```tsx
import React, { useState } from 'react';
import { Table, Form, Input, message } from 'antd';

const ValidationTable: React.FC = () => {
  const [form] = Form.useForm();
  const [data, setData] = useState([
    { key: '1', name: 'John', email: 'john@example.com' },
  ]);

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateEmail = (email: string) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleSave = (key: string, field: string, value: any) => {
    const newErrors = { ...errors };

    if (field === 'email' && !validateEmail(value)) {
      newErrors[`${key}-${field}`] = 'Invalid email format';
      setErrors(newErrors);
      return;
    }

    if (field === 'name' && value.length < 3) {
      newErrors[`${key}-${field}`] = 'Name must be at least 3 characters';
      setErrors(newErrors);
      return;
    }

    delete newErrors[`${key}-${field}`];
    setErrors(newErrors);

    const newData = data.map((item) =>
      item.key === key ? { ...item, [field]: value } : item
    );
    setData(newData);
    message.success('Saved successfully');
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string, record: any) => (
        <Form.Item
          validateStatus={errors[`${record.key}-name`] ? 'error' : ''}
          help={errors[`${record.key}-name`]}
          style={{ margin: 0 }}
        >
          <Input
            defaultValue={text}
            onBlur={(e) =>
              handleSave(record.key, 'name', e.target.value)
            }
          />
        </Form.Item>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      render: (text: string, record: any) => (
        <Form.Item
          validateStatus={errors[`${record.key}-email`] ? 'error' : ''}
          help={errors[`${record.key}-email`]}
          style={{ margin: 0 }}
        >
          <Input
            defaultValue={text}
            onBlur={(e) =>
              handleSave(record.key, 'email', e.target.value)
            }
          />
        </Form.Item>
      ),
    },
  ];

  return <Table columns={columns} dataSource={data} pagination={false} />;
};
```

### 4.5 编辑性能优化

```tsx
import React, { useState, useMemo, useCallback } from 'react';
import { Table, Form, Input } from 'antd';

// ✅ 使用 React.memo 优化单元格组件
const MemoEditableCell = React.memo<{
  value: string;
  onSave: (value: string) => void;
}>(({ value, onSave }) => {
  const [editing, setEditing] = useState(false);

  return editing ? (
    <Input
      defaultValue={value}
      autoFocus
      onBlur={(e) => {
        onSave(e.target.value);
        setEditing(false);
      }}
      onPressEnter={(e) => {
        onSave((e.target as HTMLInputElement).value);
        setEditing(false);
      }}
    />
  ) : (
    <span onClick={() => setEditing(true)}>{value}</span>
  );
});

const OptimizedEditableTable: React.FC = () => {
  const [data, setData] = useState(
    Array.from({ length: 1000 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      age: i,
    }))
  );

  // ✅ 使用 useCallback 缓存保存函数
  const handleSave = useCallback((key: string, field: string, value: any) => {
    setData((prevData) =>
      prevData.map((item) =>
        item.key === key ? { ...item, [field]: value } : item
      )
    );
  }, []);

  // ✅ 使用 useMemo 缓存 columns
  const columns = useMemo(() => [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string, record: any) => (
        <MemoEditableCell
          value={text}
          onSave={(value) => handleSave(record.key, 'name', value)}
        />
      ),
    },
    {
      title: 'Age',
      dataIndex: 'age',
    },
  ], [handleSave]);

  return (
    <Table
      columns={columns}
      dataSource={data}
      // ✅ 性能优化配置
      rowHoverable={false}
      pagination={{ pageSize: 50 }}
    />
  );
};
```

---

## 5. 树形表格 ⭐

### 5.1 树形数据结构

```tsx
import React from 'react';
import { Table } from 'antd';

interface TreeNode {
  key: string;
  name: string;
  age: number;
  children?: TreeNode[];
}

const TreeTable: React.FC = () => {
  const data: TreeNode[] = [
    {
      key: '1',
      name: 'John Brown',
      age: 32,
      children: [
        {
          key: '1-1',
          name: 'John Brown Jr.',
          age: 12,
        },
        {
          key: '1-2',
          name: 'Jim Green',
          age: 42,
          children: [
            {
              key: '1-2-1',
              name: 'Jim Green Jr.',
              age: 22,
            },
          ],
        },
      ],
    },
    {
      key: '2',
      name: 'Joe Black',
      age: 32,
    },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
  ];

  // ✅ 树形表格配置
  return (
    <Table<TreeNode>
      columns={columns}
      dataSource={data}
      // 默认展开所有行
      defaultExpandAllRows
      // 默认展开指定行
      // defaultExpandedRowKeys={['1']}
      // 层级缩进宽度
      indentSize={20}
      pagination={false}
    />
  );
};
```

### 5.2 展开行

```tsx
import React, { useState } from 'react';
import { Table, Descriptions } from 'antd';

const ExpandableTable: React.FC = () => {
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([]);

  const data = [
    {
      key: '1',
      name: 'John Brown',
      age: 32,
      address: 'New York No. 1 Lake Park',
      description: 'My name is John Brown, I am 32 years old.',
    },
    {
      key: '2',
      name: 'Jim Green',
      age: 42,
      address: 'London No. 1 Lake Park',
      description: 'My name is Jim Green, I am 42 years old.',
    },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
    { title: 'Address', dataIndex: 'address' },
  ];

  const expandedRowRender = (record: any) => (
    <Descriptions title="User Info" bordered>
      <Descriptions.Item label="Full Name">{record.name}</Descriptions.Item>
      <Descriptions.Item label="Age">{record.age}</Descriptions.Item>
      <Descriptions.Item label="Address">{record.address}</Descriptions.Item>
      <Descriptions.Item label="Description" span={3}>
        {record.description}
      </Descriptions.Item>
    </Descriptions>
  );

  return (
    <Table
      columns={columns}
      expandable={{
        expandedRowRender,
        expandedRowKeys,
        onExpandedRowsChange: (keys) => setExpandedRowKeys(keys),
        // 点击行展开
        expandRowByClick: true,
      }}
      dataSource={data}
    />
  );
};
```

### 5.3 懒加载

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';

interface LazyNode {
  key: string;
  name: string;
  age?: number;
  isLeaf?: boolean;
  children?: LazyNode[];
}

const LazyLoadTreeTable: React.FC = () => {
  const [data, setData] = useState<LazyNode[]>([
    {
      key: '1',
      name: 'Parent 1',
      isLeaf: false,
    },
    {
      key: '2',
      name: 'Parent 2',
      isLeaf: false,
    },
  ]);

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
  ];

  // ✅ 懒加载子节点
  const onExpand = async (expanded: boolean, record: LazyNode) => {
    if (expanded && !record.children) {
      // 模拟异步加载
      const loadChildren = async (key: string) => {
        return new Promise<LazyNode[]>((resolve) => {
          setTimeout(() => {
            resolve([
              { key: `${key}-1`, name: `Child ${key}-1`, age: 10 },
              { key: `${key}-2`, name: `Child ${key}-2`, age: 20 },
            ]);
          }, 1000);
        });
      };

      const children = await loadChildren(record.key);

      setData((prevData) => {
        const updateNode = (nodes: LazyNode[]): LazyNode[] => {
          return nodes.map((node) => {
            if (node.key === record.key) {
              return { ...node, children };
            }
            if (node.children) {
              return { ...node, children: updateNode(node.children) };
            }
            return node;
          });
        };
        return updateNode(prevData);
      });
    }
  };

  return (
    <Table
      columns={columns}
      dataSource={data}
      pagination={false}
      expandable={{
        onExpand,
        childrenColumnName: 'children',
      }}
    />
  );
};
```

### 5.4 多级展开

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';

const MultiLevelTable: React.FC = () => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>(['1', '1-1']);

  const data = [
    {
      key: '1',
      name: 'Level 1-1',
      children: [
        {
          key: '1-1',
          name: 'Level 2-1',
          children: [
            { key: '1-1-1', name: 'Level 3-1' },
            { key: '1-1-2', name: 'Level 3-2' },
          ],
        },
        {
          key: '1-2',
          name: 'Level 2-2',
        },
      ],
    },
    {
      key: '2',
      name: 'Level 1-2',
      children: [
        { key: '2-1', name: 'Level 2-3' },
      ],
    },
  ];

  const columns = [{ title: 'Name', dataIndex: 'name', key: 'name' }];

  return (
    <Table
      columns={columns}
      dataSource={data}
      pagination={false}
      expandable={{
        defaultExpandAllRows: false,
        defaultExpandedRowKeys: ['1'],
        expandedRowKeys: expandedKeys,
        onExpandedRowsChange: setExpandedKeys,
      }}
    />
  );
};
```

### 5.5 树形 + 虚拟滚动

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const VirtualTreeTable: React.FC = () => {
  const data = useMemo(() => {
    const generateTree = (level: number, maxLevel: number): any[] => {
      if (level > maxLevel) return [];
      const count = level === 1 ? 100 : 10;
      return Array.from({ length: count }, (_, i) => ({
        key: `${level}-${i}`,
        name: `Node ${level}-${i}`,
        children: generateTree(level + 1, maxLevel),
      }));
    };
    return generateTree(1, 3);
  }, []);

  const columns = [
    { title: 'Name', dataIndex: 'name', width: 300 },
    { title: 'Key', dataIndex: 'key', width: 150 },
  ];

  return (
    <Table
      virtual
      columns={columns}
      dataSource={data}
      scroll={{ x: 600, y: 500 }}
      pagination={false}
      expandable={{
        defaultExpandAllRows: true,
        indentSize: 20,
      }}
    />
  );
};
```

---

## 6. 选择与操作

### 6.1 行选择

```tsx
import React, { useState } from 'react';
import { Table, Button } from 'antd';

const RowSelectionTable: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const data = Array.from({ length: 10 }, (_, i) => ({
    key: `${i}`,
    name: `User ${i}`,
    age: i,
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  const hasSelected = selectedRowKeys.length > 0;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          onClick={() => console.log('Selected:', selectedRowKeys)}
          disabled={!hasSelected}
        >
          {hasSelected ? `Selected ${selectedRowKeys.length} items` : 'Select Items'}
        </Button>
      </div>
      <Table
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
          type: 'checkbox',
        }}
        columns={columns}
        dataSource={data}
      />
    </div>
  );
};
```

### 6.2 跨页选择

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';

const CrossPageSelectionTable: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const data = Array.from({ length: 100 }, (_, i) => ({
    key: `${i}`,
    name: `User ${i}`,
    age: i,
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  return (
    <Table
      rowSelection={{
        selectedRowKeys,
        onChange: (keys) => setSelectedRowKeys(keys),
        preserveSelectedRowKeys: true,
        getCheckboxProps: (record: any) => ({
          disabled: record.name === 'User 0',
        }),
      }}
      columns={columns}
      dataSource={data}
      pagination={{ pageSize: 10 }}
    />
  );
};
```

### 6.3 批量操作

```tsx
import React, { useState } from 'react';
import { Table, Button, Space, Popconfirm, message } from 'antd';

const BatchOperationTable: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [data, setData] = useState(
    Array.from({ length: 10 }, (_, i) => ({
      key: `${i}`,
      name: `User ${i}`,
      status: 'active',
    }))
  );

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Status', dataIndex: 'status' },
    {
      title: 'Action',
      render: (_: any, record: any) => (
        <a onClick={() => handleDelete([record.key])}>Delete</a>
      ),
    },
  ];

  const handleDelete = (keys: React.Key[]) => {
    setData(data.filter((item) => !keys.includes(item.key)));
    setSelectedRowKeys([]);
    message.success(`Deleted ${keys.length} items`);
  };

  const handleBatchDelete = () => {
    handleDelete(selectedRowKeys);
  };

  const handleBatchExport = () => {
    const selectedData = data.filter((item) =>
      selectedRowKeys.includes(item.key)
    );
    console.log('Export:', selectedData);
    message.success(`Exported ${selectedData.length} items`);
  };

  const handleBatchUpdate = () => {
    const newData = data.map((item) =>
      selectedRowKeys.includes(item.key)
        ? { ...item, status: 'inactive' }
        : item
    );
    setData(newData);
    message.success(`Updated ${selectedRowKeys.length} items`);
  };

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          danger
          disabled={selectedRowKeys.length === 0}
          onClick={handleBatchDelete}
        >
          Batch Delete
        </Button>
        <Button
          disabled={selectedRowKeys.length === 0}
          onClick={handleBatchExport}
        >
          Batch Export
        </Button>
        <Button
          disabled={selectedRowKeys.length === 0}
          onClick={handleBatchUpdate}
        >
          Batch Update
        </Button>
      </Space>
      <Table
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        columns={columns}
        dataSource={data}
      />
    </div>
  );
};
```

### 6.4 自定义行选择

```tsx
import React, { useState } from 'react';
import { Table } from 'antd';

const CustomSelectionTable: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const data = Array.from({ length: 10 }, (_, i) => ({
    key: `${i}`,
    name: `User ${i}`,
    age: i,
  }));

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  return (
    <Table
      rowSelection={{
        selectedRowKeys,
        onChange: setSelectedRowKeys,
        renderCell: (checked, record, index, originNode) => (
          <div title={record.name}>
            {originNode}
          </div>
        ),
        columnTitle: 'Select',
        columnWidth: 50,
        fixed: true,
        selections: [
          Table.SELECTION_ALL,
          Table.SELECTION_INVERT,
          Table.SELECTION_NONE,
          {
            key: 'odd',
            text: 'Select Odd Row',
            onSelect: (changableRowKeys) => {
              let newSelectedRowKeys = [];
              newSelectedRowKeys = changableRowKeys.filter((_, index) => {
                return index % 2 === 0;
              });
              setSelectedRowKeys(newSelectedRowKeys);
            },
          },
        ],
      }}
      columns={columns}
      dataSource={data}
    />
  );
};
```

---

## 7. 性能优化 ⭐⭐⭐

### 7.1 大数据渲染优化

**关键优化策略:**

1. **虚拟滚动** - 最有效的优化方案
2. **分页** - 减少单页数据量
3. **延迟加载** - 按需加载数据
4. **简化渲染** - 优化 render 函数

### 7.2 复杂列渲染优化

```tsx
// ❌ 错误:每次渲染都创建新函数
const BadExample = () => {
  const columns = [
    {
      title: 'Name',
      render: (value: any, record: any) => (
        <div>
          <span>{record.name}</span>
          <button onClick={() => console.log(record)}>Click</button>
        </div>
      ),
    },
  ];
  return <Table columns={columns} dataSource={[]} />;
};

// ✅ 正确:使用 useMemo 缓存
const GoodExample = () => {
  const columns = useMemo(() => [
    {
      title: 'Name',
      render: (value: any, record: any) => (
        <div>
          <span>{record.name}</span>
          <button onClick={() => handleClick(record)}>Click</button>
        </div>
      ),
    },
  ], []);

  const handleClick = (record: any) => {
    console.log(record);
  };

  return <Table columns={columns} dataSource={[]} />;
};
```

### 7.3 columns memo 优化

```tsx
import React, { useMemo } from 'react';
import { Table } from 'antd';

const ColumnsMemoTable = () => {
  const [filters, setFilters] = useState({});

  // ✅ 使用 useMemo 缓存 columns
  const columns = useMemo(() => [
    {
      title: 'Name',
      dataIndex: 'name',
      shouldCellUpdate: (record: any, prevRecord: any) => {
        return record.name !== prevRecord.name;
      },
    },
  ], []);

  return <Table columns={columns} dataSource={data} />;
};
```

---

## 8. 高级特性

### 8.1 自定义单元格渲染

```tsx
import React from 'react';
import { Table, Tag, Progress, Avatar } from 'antd';

const CustomCellTable = () => {
  const data = [
    {
      key: '1',
      name: 'John Brown',
      status: 'active',
      progress: 75,
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John',
    },
  ];

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string, record: any) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar src={record.avatar} style={{ marginRight: 8 }} />
          <span>{text}</span>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : 'red';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
  ];

  return <Table columns={columns} dataSource={data} />;
};
```

### 8.2 总结行

```tsx
import React from 'react';
import { Table } from 'antd';

const SummaryTable = () => {
  const data = [
    { key: '1', name: 'John', income: 1000, expense: 500 },
    { key: '2', name: 'Jim', income: 1500, expense: 800 },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Income', dataIndex: 'income' },
    { title: 'Expense', dataIndex: 'expense' },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      summary={(pageData) => {
        const totalIncome = pageData.reduce((sum, record) => sum + record.income, 0);
        const totalExpense = pageData.reduce((sum, record) => sum + record.expense, 0);

        return (
          <Table.Summary fixed>
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={2}>
                <strong>Total</strong>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={1}>
                <strong>{totalIncome}</strong>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={2}>
                <strong>{totalExpense}</strong>
              </Table.Summary.Cell>
            </Table.Summary.Row>
          </Table.Summary>
        );
      }}
    />
  );
};
```

---

## 9. 最佳实践

### 9.1 始终指定 rowKey

```tsx
// ❌ 错误:没有指定 rowKey
<Table dataSource={data} columns={columns} />

// ✅ 正确:指定 rowKey
<Table rowKey="id" dataSource={data} columns={columns} />
```

### 9.2 使用 TypeScript 类型安全

```tsx
import React from 'react';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface User {
  id: string;
  name: string;
  age: number;
}

const TypedTable: React.FC = () => {
  const columns: ColumnsType<User> = [
    {
      title: 'Name',
      dataIndex: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
  ];

  return <Table<User> columns={columns} dataSource={data} />;
};
```

### 9.3 优化 columns 定义

```tsx
// ✅ 使用 useMemo 缓存 columns
const GoodExample = () => {
  const columns = useMemo(() => [
    {
      title: 'Name',
      render: () => <ComplexComponent />,
    },
  ], []);

  return <Table columns={columns} />;
};
```

---

## 10. 参考资源

### 官方文档
- [Ant Design Table 组件](https://ant.design/components/table-cn/)
- [Ant Design Table 虚拟滚动文档](https://ant.design/docs/blog/virtual-table-cn/)
- [Ant Design ProComponents ProTable](https://procomponents.ant.design/components/table)

### 性能优化文章
- [Table Performance Optimization Discussion](https://github.com/ant-design/ant-design/discussions/44120)
- [5 Ways to Improve Table Performance](https://betterprogramming.pub/5-ways-to-improve-table-performance-87e40c5d659b)
- [Ant Design Bundle Size Optimization](https://dev.to/anaselbahrawy/ant-design-bundle-size-optimization-the-tree-shaking-approach-every-react-developer-should-know-2l5a)

### 社区资源
- [Table performance optimization (GitHub Discussion)](https://github.com/ant-design/ant-design/discussions/44120)
- [React Table Row Selection with Server-Side Pagination](https://codesandbox.io/s/react-table-row-selection-with-server-side-pagination-ygv0s)

### 常见问题
- [Table FAQ](https://ant.design/components/table-cn/#FAQ)
- [GitHub Issues: ant-design](https://github.com/ant-design/ant-design/issues?q=is%3Aissue+table)

---

## 总结

Ant Design Table 是一个功能强大的表格组件,掌握以下关键点可以帮助你构建高性能的企业级表格应用:

### 核心要点

1. **性能优化**
   - ✅ 使用虚拟滚动处理大数据 (10000+ 行)
   - ✅ 使用 useMemo 缓存 columns
   - ✅ 使用 useCallback 缓存事件处理函数
   - ✅ 合理使用分页

2. **数据管理**
   - ✅ 始终指定 rowKey
   - ✅ 使用 TypeScript 类型安全
   - ✅ 合理选择本地/远程数据源

3. **高级功能**
   - ✅ 掌握可编辑表格
   - ✅ 掌握树形表格
   - ✅ 掌握虚拟滚动

4. **最佳实践**
   - ✅ 提取 columns 为常量
   - ✅ 使用 React.memo 优化渲染
   - ✅ 合理使用 key 和 rowKey

### 性能对比

| 场景 | 推荐方案 | 数据量 | 性能 |
| --- | --- | --- | --- |
| 少量数据 | 普通 Table | < 100 | ⭐⭐⭐⭐⭐ |
| 中等数据 | 分页 Table | 100-1000 | ⭐⭐⭐⭐ |
| 大量数据 | 虚拟滚动 Table | 1000-10000 | ⭐⭐⭐⭐⭐ |
| 超大数据 | 远程分页 | 10000+ | ⭐⭐⭐⭐ |

记住:选择合适的方案比盲目优化更重要!

---

**版本**: 1.0.0
**最后更新**: 2025-02-10
**维护者**: CCPlugin Team
