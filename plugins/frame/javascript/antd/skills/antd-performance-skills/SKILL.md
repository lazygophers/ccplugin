---
name: antd-performance-skills
description: Ant Design 性能优化完整指南 - 虚拟滚动、懒加载、渲染优化、包体积优化
---

# antd-performance: Ant Design 性能优化完整指南

Ant Design 性能优化是提升大型应用用户体验的关键，通过虚拟滚动、懒加载、渲染优化、包体积优化等技术，显著降低内存占用和渲染时间，提升页面响应速度。

---

## 概述

### 性能优化的重要性

在现代 Web 应用中，性能优化直接影响用户体验和业务指标：

- **首屏加载时间**: 影响用户留存率和 SEO 排名
- **交互响应速度**: 影响用户操作流畅度和满意度
- **内存占用**: 影响长时间使用的稳定性
- **网络传输**: 影响加载速度和流量消耗

### 常见性能问题

1. **大数据渲染**: Table/List 组件渲染成千上万条数据导致卡顿
2. **重复渲染**: 不必要的组件重渲染导致性能浪费
3. **包体积过大**: 未按需加载导致初始加载缓慢
4. **内存泄漏**: 未清理的定时器、事件监听器导致内存占用持续增长
5. **图片资源**: 大图未压缩、未懒加载导致页面加载缓慢

---

## 核心特性

- **虚拟滚动** - 只渲染可视区域内的元素，支持 10万+ 数据流畅滚动
- **组件懒加载** - 按需加载组件，减少初始包体积
- **渲染优化** - 使用 React.memo、useMemo、useCallback 减少重复渲染
- **按需导入** - 只导入使用的组件，减少包体积 60%+
- **大数据分页** - 分批加载数据，降低单次渲染压力
- **图片懒加载** - 使用 Lazyload 组件延迟加载图片
- **性能监控** - 使用 React Profiler 和 Performance API 监控性能
- **代码分割** - 使用 React.lazy 和 Suspense 分割代码

---

## 虚拟滚动

### Table 虚拟滚动

`Table` 组件支持虚拟滚动，只需设置 `scroll` 属性：

```tsx
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface DataType {
  key: string;
  name: string;
  age: number;
  address: string;
}

// 生成 10万 条测试数据
const dataSource: DataType[] = Array.from({ length: 100000 }, (_, i) => ({
  key: `key-${i}`,
  name: `User ${i}`,
  age: Math.floor(Math.random() * 50) + 18,
  address: `Address ${i}`,
}));

const columns: ColumnsType<DataType> = [
  { title: 'Name', dataIndex: 'name', width: 150 },
  { title: 'Age', dataIndex: 'age', width: 100 },
  { title: 'Address', dataIndex: 'address', width: 300 },
];

function VirtualTable() {
  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      scroll={{ y: 400 }} // 启用虚拟滚动的关键
      pagination={false} // 大数据场景建议关闭分页
      bordered
    />
  );
}
```

**关键属性**:
- `scroll.y`: 设置表格高度，启用垂直虚拟滚动
- `scroll.x`: 设置表格宽度，启用水平虚拟滚动
- `pagination={false}`: 大数据场景建议关闭分页，使用虚拟滚动替代

### Table 高级虚拟滚动配置

```tsx
import { Table } from 'antd';

function AdvancedVirtualTable() {
  return (
    <Table
      columns={columns}
      dataSource={dataSource}

      // 1. 虚拟滚动配置
      scroll={{
        x: 1200,        // 水平滚动宽度
        y: 500,         // 垂直滚动高度
      }}

      // 2. 性能优化配置
      pagination={false}           // 关闭分页
      bordered={true}              // 显示边框
      size="small"                 // 紧凑模式
      rowKey={(record) => record.key} // 指定唯一 key

      // 3. 渲染优化
      rowHeight={55}               // 固定行高（提升性能）
      components={{
        body: {
          row: ({ children, ...props }) => (
            <tr {...props}>{children}</tr>
          ),
          cell: ({ children, ...props }) => (
            <td {...props}>{children}</td>
          ),
        },
      }}

      // 4. 交互优化
      onRow={(record) => ({
        onMouseEnter: () => console.log('Hover:', record.key),
      })}
    />
  );
}
```

### List 虚拟滚动

`List` 组件支持虚拟滚动，用于渲染大量数据列表：

```tsx
import { List } from 'antd';

interface ListItem {
  id: number;
  title: string;
  description: string;
}

// 生成 5万 条测试数据
const data: ListItem[] = Array.from({ length: 50000 }, (_, i) => ({
  id: i,
  title: `Ant Design Title ${i}`,
  description: `Ant Design, a design language for background applications, is refined by Ant UED Team.`,
}));

function VirtualList() {
  return (
    <List
      dataSource={data}
      renderItem={(item) => (
        <List.Item key={item.id}>
          <List.Item.Meta
            title={item.title}
            description={item.description}
          />
        </List.Item>
      )}
      // 启用虚拟滚动
      split={true}
      bordered={true}
      style={{
        height: 400,        // 固定高度
        overflow: 'auto',   // 启用滚动
      }}
    />
  );
}
```

### 使用 rc-virtual-list 高级虚拟滚动

Ant Design 内部使用 `rc-virtual-list` 实现虚拟滚动，也可以直接使用：

```tsx
import VirtualList from 'rc-virtual-list';
import type { ReactNode } from 'react';

interface ItemData {
  id: number;
  value: ReactNode;
}

const containerHeight = 400;
const itemHeight = 50;

// 生成 10万 条数据
const data: ItemData[] = Array.from({ length: 100000 }, (_, i) => ({
  id: i,
  value: `Item ${i}`,
}));

function CustomVirtualList() {
  return (
    <div>
      <VirtualList
        data={data}
        height={containerHeight}
        itemHeight={itemHeight}
        itemKey="id"
        fullWidth={true}

        // 自定义渲染
        renderItem={(item) => (
          <div
            key={item.id}
            style={{
              height: itemHeight,
              display: 'flex',
              alignItems: 'center',
              padding: '0 16px',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            {item.value}
          </div>
        )}
      />
    </div>
  );
}
```

### 虚拟滚动最佳实践

**✅ 推荐**:

```tsx
// 1. 固定行高提升性能
<Table
  scroll={{ y: 400 }}
  rowHeight={55} // 固定行高
/>

// 2. 使用唯一的 rowKey
<Table
  rowKey="id" // 或 rowKey={(record) => record.uniqueId}
/>

// 3. 避免复杂的列渲染
const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    render: (name) => <span>{name}</span>, // 简单渲染
  },
];
```

**❌ 避免**:

```tsx
// 1. 不要在 render 中使用复杂计算
const columns = [
  {
    title: 'Complex',
    render: (record) => {
      const complex = heavyCalculation(record); // ❌ 每次渲染都计算
      return <div>{complex}</div>;
    },
  },
];

// 2. 不要频繁更新 dataSource
const [data, setData] = useState([]);
useEffect(() => {
  // ❌ 每秒更新整个列表
  const timer = setInterval(() => {
    setData(largeData);
  }, 1000);
  return () => clearInterval(timer);
}, []);

// 3. 不要动态改变行高
<Table
  rowHeight={(record) => record.size} // ❌ 动态行高降低性能
/>
```

---

## 懒加载技术

### 路由级懒加载

使用 `React.lazy` 和 `Suspense` 实现路由懒加载：

```tsx
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

// 懒加载页面组件
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Users = lazy(() => import('./pages/Users'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Spin size="large" />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/users" element={<Users />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

### 组件级懒加载

懒加载大型组件：

```tsx
import { lazy, Suspense, useState } from 'react';
import { Button } from 'antd';

// 懒加载重型组件
const HeavyChart = lazy(() => import('./components/HeavyChart'));
const RichTextEditor = lazy(() => import('./components/RichTextEditor'));

function LazyComponentExample() {
  const [showChart, setShowChart] = useState(false);

  return (
    <div>
      <Button onClick={() => setShowChart(true)}>
        Load Chart
      </Button>

      {showChart && (
        <Suspense fallback={<div>Loading chart...</div>}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

### 图片懒加载

使用 `Image.PreviewGroup` 的懒加载功能：

```tsx
import { Image } from 'antd';

function LazyImageGallery() {
  const images = [
    'https://example.com/image1.jpg',
    'https://example.com/image2.jpg',
    'https://example.com/image3.jpg',
    // ... more images
  ];

  return (
    <Image.PreviewGroup>
      <div style={{ display: 'flex', gap: 16 }}>
        {images.map((src, index) => (
          <Image
            key={index}
            src={src}
            width={200}
            height={200}
            style={{ objectFit: 'cover' }}

            // 懒加载配置
            loading="lazy"
            placeholder={<div style={{ width: 200, height: 200, background: '#f0f0f0' }} />}
          />
        ))}
      </div>
    </Image.PreviewGroup>
  );
}
```

### Tab 懒加载

`Tabs` 组件内容懒加载：

```tsx
import { Tabs } from 'antd';
import type { TabsProps } from 'antd';

function LazyTabs() {
  const items: TabsProps['items'] = [
    {
      key: '1',
      label: 'Tab 1',
      children: <div>Content 1 (loaded immediately)</div>,
    },
    {
      key: '2',
      label: 'Tab 2',
      // 懒加载 Tab 2 的内容
      children: (
        <LazyWrapper>
          <HeavyContent />
        </LazyWrapper>
      ),
    },
    {
      key: '3',
      label: 'Tab 3',
      children: (
        <LazyWrapper>
          <AnotherHeavyContent />
        </LazyWrapper>
      ),
    },
  ];

  return <Tabs defaultActiveKey="1" items={items} />;
}

// 懒加载包装组件
function LazyWrapper({ children }: { children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // 延迟加载
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  if (!isVisible) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
```

### Modal 懒加载

Modal 内容懒加载：

```tsx
import { Modal, Button } from 'antd';
import { useState, lazy, Suspense } from 'react';

const HeavyForm = lazy(() => import('./HeavyForm'));

function LazyModal() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const showModal = () => setIsModalOpen(true);
  const handleCancel = () => setIsModalOpen(false);

  return (
    <>
      <Button type="primary" onClick={showModal}>
        Open Modal
      </Button>

      <Modal
        title="Lazy Loaded Modal"
        open={isModalOpen}
        onCancel={handleCancel}
        footer={null}
        width={800}
      >
        <Suspense fallback={<div>Loading form...</div>}>
          <HeavyForm onSubmit={handleCancel} />
        </Suspense>
      </Modal>
    </>
  );
}
```

---

## 渲染优化

### React.memo 优化组件

使用 `React.memo` 避免不必要的重渲染：

```tsx
import { memo } from 'react';
import { Card, Progress } from 'antd';

interface ExpensiveComponentProps {
  title: string;
  progress: number;
  // 其他频繁变化的 prop
  timestamp: number;
}

// ❌ 未优化：每次父组件渲染都会重渲染
function ExpensiveComponent({ title, progress, timestamp }: ExpensiveComponentProps) {
  console.log('ExpensiveComponent rendered');

  // 模拟昂贵计算
  const calculatedValue = useMemo(() => {
    return heavyCalculation(progress);
  }, [progress]);

  return (
    <Card title={title}>
      <Progress percent={progress} />
      <p>Calculated: {calculatedValue}</p>
      <p>Timestamp: {timestamp}</p>
    </Card>
  );
}

// ✅ 优化后：只在 props 变化时重渲染
const MemoizedExpensiveComponent = memo(function ExpensiveComponent({
  title,
  progress,
  timestamp,
}: ExpensiveComponentProps) {
  console.log('MemoizedExpensiveComponent rendered');

  const calculatedValue = useMemo(() => {
    return heavyCalculation(progress);
  }, [progress]);

  return (
    <Card title={title}>
      <Progress percent={progress} />
      <p>Calculated: {calculatedValue}</p>
      <p>Timestamp: {timestamp}</p>
    </Card>
  );
}, (prevProps, nextProps) => {
  // 自定义比较函数
  return (
    prevProps.title === nextProps.title &&
    prevProps.progress === nextProps.progress &&
    prevProps.timestamp === nextProps.timestamp
  );
});

// 使用示例
function ParentComponent() {
  const [timestamp, setTimestamp] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimestamp(Date.now());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div>
      {/* 未优化的组件会每秒渲染一次 */}
      <ExpensiveComponent
        title="Not Optimized"
        progress={75}
        timestamp={timestamp}
      />

      {/* 优化的组件只在 progress 变化时渲染 */}
      <MemoizedExpensiveComponent
        title="Optimized"
        progress={75}
        timestamp={timestamp}
      />
    </div>
  );
}
```

### useMemo 优化计算

使用 `useMemo` 缓存昂贵的计算结果：

```tsx
import { useMemo } from 'react';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface DataType {
  id: number;
  name: string;
  value: number;
}

// 昂贵的计算函数
function heavyCalculation(data: DataType[]) {
  console.log('Performing heavy calculation...');
  return data.map(item => ({
    ...item,
    calculated: item.value * 2 + Math.sqrt(item.value),
  }));
}

function TableWithMemo() {
  const [data, setData] = useState<DataType[]>([
    { id: 1, name: 'Item 1', value: 10 },
    { id: 2, name: 'Item 2', value: 20 },
    { id: 3, name: 'Item 3', value: 30 },
    // ... more data
  ]);

  const [filter, setFilter] = useState('');

  // ❌ 未优化：每次组件渲染都重新计算
  const calculatedDataBad = heavyCalculation(data);

  // ✅ 优化后：只在 data 变化时计算
  const calculatedData = useMemo(() => {
    return heavyCalculation(data);
  }, [data]);

  // ✅ 结合过滤使用 useMemo
  const filteredData = useMemo(() => {
    return calculatedData.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [calculatedData, filter]);

  const columns: ColumnsType<DataType> = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Value', dataIndex: 'value' },
    { title: 'Calculated', dataIndex: 'calculated' },
  ];

  return (
    <div>
      <Input
        placeholder="Filter by name"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{ marginBottom: 16 }}
      />

      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey="id"
      />
    </div>
  );
}
```

### useCallback 优化函数

使用 `useCallback` 缓存函数引用：

```tsx
import { useCallback } from 'react';
import { Button, List } from 'antd';

interface Item {
  id: number;
  name: string;
}

function ListWithCallback() {
  const [items, setItems] = useState<Item[]>([
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
    { id: 3, name: 'Item 3' },
  ]);

  const [count, setCount] = useState(0);

  // ❌ 未优化：每次渲染创建新函数
  const handleClickBad = (id: number) => {
    console.log('Clicked item:', id);
  };

  // ✅ 优化后：函数引用保持稳定
  const handleClick = useCallback((id: number) => {
    console.log('Clicked item:', id);
  }, []); // 空依赖数组，函数永不变化

  // ✅ 依赖其他状态
  const handleDelete = useCallback((id: number) => {
    setItems(prevItems => prevItems.filter(item => item.id !== id));
  }, []); // 依赖 []

  // ✅ 依赖外部值
  const handleLog = useCallback((id: number) => {
    console.log('Current count:', count);
    console.log('Clicked item:', id);
  }, [count]); // 依赖 count，count 变化时重新创建

  return (
    <div>
      <div>Count: {count}</div>
      <Button onClick={() => setCount(count + 1)}>
        Increment Count
      </Button>

      <List
        dataSource={items}
        renderItem={(item) => (
          <List.Item
            key={item.id}
            onClick={() => handleClick(item.id)}
          >
            {item.name}
            <Button
              size="small"
              danger
              onClick={() => handleDelete(item.id)}
            >
              Delete
            </Button>
          </List.Item>
        )}
      />
    </div>
  );
}
```

### 优化 Table 渲染

优化 Table 列渲染性能：

```tsx
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { memo } from 'react';

interface DataType {
  key: string;
  name: string;
  age: number;
  address: string;
}

// ✅ 使用 memo 优化单元格渲染组件
const NameCell = memo(({ value }: { value: string }) => {
  console.log('NameCell rendered');
  return <span style={{ fontWeight: 'bold' }}>{value}</span>;
});

const AgeCell = memo(({ value }: { value: number }) => {
  console.log('AgeCell rendered');
  return <span>{value} years old</span>;
});

function OptimizedTable() {
  const dataSource: DataType[] = [
    { key: '1', name: 'John Brown', age: 32, address: 'New York No. 1 Lake Park' },
    { key: '2', name: 'Jim Green', age: 42, address: 'London No. 1 Lake Park' },
    { key: '3', name: 'Joe Black', age: 28, address: 'Sydney No. 1 Lake Park' },
  ];

  const columns: ColumnsType<DataType> = [
    {
      title: 'Name',
      dataIndex: 'name',
      // ✅ 使用 memo 优化的组件
      render: (value: string) => <NameCell value={value} />,
    },
    {
      title: 'Age',
      dataIndex: 'age',
      render: (value: number) => <AgeCell value={value} />,
    },
    {
      title: 'Address',
      dataIndex: 'address',
      // ❌ 避免：内联函数
      // render: (value) => <div style={{ color: 'red' }}>{value}</div>
    },
  ];

  return <Table dataSource={dataSource} columns={columns} />;
}
```

---

## 包体积优化

### 按需导入

Ant Design 5.x 默认支持按需导入，无需额外配置：

```tsx
// ✅ 推荐：按需导入
import { Button, Table, Form } from 'antd';

// ❌ 避免：导入整个库
// import * as antd from 'antd';
// const { Button, Table, Form } = antd;
```

### Tree Shaking 配置

确保打包工具支持 Tree Shaking：

**webpack.config.js**:
```javascript
module.exports = {
  mode: 'production',
  optimization: {
    usedExports: true,
    sideEffects: false,
  },
};
```

**package.json**:
```json
{
  "sideEffects": false
}
```

### 图标按需导入

Ant Design 5.x 图标需要单独安装和导入：

```bash
npm install @ant-design/icons
```

```tsx
// ✅ 推荐：按需导入图标
import { UserOutlined, SearchOutlined } from '@ant-design/icons';

<Button icon={<UserOutlined />}>User</Button>
<Input suffix={<SearchOutlined />} />

// ❌ 避免：导入所有图标
// import * as Icons from '@ant-design/icons';
```

### Moment.js 替换

Ant Design 5.x 已将 DatePicker 依赖从 Moment.js 替换为 dayjs，减少包体积：

```tsx
// ✅ 使用 dayjs（默认）
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import 'dayjs/locale/zh-cn';

dayjs.extend(customParseFormat);
dayjs.locale('zh-cn');

<DatePicker defaultValue={dayjs('2023-01-01')} />
```

### 移除未使用的语言包

只导入需要的语言包：

```tsx
// ✅ 推荐：只导入需要的语言
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

// ❌ 避免：导入所有语言
// import * as locales from 'antd/locale';
```

---

## 大数据优化

### 分页加载

使用分页减少单次渲染数据量：

```tsx
import { Table } from 'antd';
import type { PaginationProps } from 'antd';

interface DataType {
  key: string;
  name: string;
  age: number;
}

function PaginatedTable() {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 模拟 API 请求
  const fetchData = async (page: number, pageSize: number) => {
    setLoading(true);
    try {
      // 实际项目中替换为真实 API
      const response = await fetch(`/api/data?page=${page}&size=${pageSize}`);
      const result = await response.json();

      setData(result.data);
      setPagination({
        current: page,
        pageSize: pageSize,
        total: result.total,
      });
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchData(pagination.current, pagination.pageSize);
  }, []);

  // 处理分页变化
  const handleTableChange: PaginationProps['onChange'] = (page, pageSize) => {
    fetchData(page, pageSize);
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
      pagination={{
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: pagination.total,
        onChange: handleTableChange,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `Total ${total} items`,
      }}
    />
  );
}
```

### 无限滚动

结合虚拟滚动和无限滚动加载更多数据：

```tsx
import { useState, useRef, useCallback } from 'react';
import { List, Spin } from 'antd';

interface Item {
  id: number;
  name: string;
  description: string;
}

function InfiniteScrollList() {
  const [data, setData] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  // 加载数据
  const loadData = async (pageNum: number) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/items?page=${pageNum}&size=20`);
      const newItems = await response.json();

      setData(prev => [...prev, ...newItems]);
      setHasMore(newItems.length > 0);
      setPage(pageNum);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadData(1);
  }, []);

  // 滚动到底部加载更多
  const handleScroll = useCallback(() => {
    const scrollTop = window.scrollY;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;

    if (scrollTop + clientHeight >= scrollHeight - 100 && !loading && hasMore) {
      loadData(page + 1);
    }
  }, [loading, hasMore, page]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return (
    <List
      dataSource={data}
      renderItem={(item) => (
        <List.Item key={item.id}>
          <List.Item.Meta
            title={item.name}
            description={item.description}
          />
        </List.Item>
      )}
    />
  );
}
```

### 后端搜索和过滤

避免在前端过滤大数据集：

```tsx
import { Input, Table } from 'antd';
import { useState, useEffect } from 'react';
import { debounce } from 'lodash';

function ServerSideFilter() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 防抖搜索
  const debouncedSearch = useMemo(
    () =>
      debounce((value: string) => {
        fetchData(value);
      }, 500),
    []
  );

  // 获取数据
  const fetchData = async (search: string = '') => {
    setLoading(true);
    try {
      const response = await fetch(`/api/data?search=${encodeURIComponent(search)}`);
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchData();
  }, []);

  // 搜索输入变化
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchText(value);
    debouncedSearch(value);
  };

  return (
    <div>
      <Input.Search
        placeholder="Search..."
        value={searchText}
        onChange={handleSearchChange}
        style={{ marginBottom: 16 }}
        loading={loading}
      />

      <Table
        dataSource={data}
        columns={columns}
        loading={loading}
        rowKey="id"
      />
    </div>
  );
}
```

---

## 性能监控

### React Profiler

使用 React DevTools Profiler 监控组件渲染性能：

```tsx
import { Profiler } from 'react';
import { Table } from 'antd';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  console.log('Profiler:', {
    id,
    phase,
    actualDuration,
    baseDuration,
    startTime,
    commitTime,
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

### Performance API

使用浏览器 Performance API 监控加载性能：

```tsx
import { useEffect } from 'react';

function PerformanceMonitor() {
  useEffect(() => {
    // 监控首次内容绘制（FCP）
    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
    console.log('First Contentful Paint:', fcp?.startTime);

    // 监控最大内容绘制（LCP）
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('Largest Contentful Paint:', lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // 监控累积布局偏移（CLS）
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
          console.log('Cumulative Layout Shift:', clsValue);
        }
      }
    }).observe({ entryTypes: ['layout-shift'] });
  }, []);

  return <div>Monitoring performance...</div>;
}
```

### Antd 组件性能监控

监控 Ant Design 组件的渲染性能：

```tsx
import { useMutationEffect } from './hooks/useMutationEffect';

function ComponentPerformanceMonitor() {
  const [renderCount, setRenderCount] = useState(0);
  const renderTime = useRef<number[]>([]);

  useEffect(() => {
    const startTime = performance.now();
    setRenderCount(prev => prev + 1);

    return () => {
      const endTime = performance.now();
      renderTime.current.push(endTime - startTime);

      console.log(`Render ${renderCount}: ${endTime - startTime}ms`);
    };
  });

  // 监控 Table 渲染性能
  const tableRef = useRef<any>(null);

  useEffect(() => {
    if (tableRef.current) {
      const tableNode = tableRef.current?.nativeElement;
      if (tableNode) {
        console.log('Table DOM nodes:', tableNode.querySelectorAll('*').length);
      }
    }
  }, [data]);

  return (
    <div>
      <p>Render count: {renderCount}</p>
      <p>Avg render time: {average(renderTime.current).toFixed(2)}ms</p>
      <Table ref={tableRef} dataSource={data} columns={columns} />
    </div>
  );
}
```

---

## 最佳实践

### 渲染优化对比

**✅ 推荐**:

```tsx
// 1. 使用 memo 优化子组件
const ExpensiveRow = memo(({ data }: { data: DataType }) => {
  return <tr>{/* 复杂渲染 */}</tr>;
});

// 2. 使用 useMemo 缓存计算
const sortedData = useMemo(() => {
  return data.sort((a, b) => a.value - b.value);
}, [data]);

// 3. 使用 useCallback 缓存函数
const handleClick = useCallback((id: string) => {
  // 处理点击
}, [dependency]);

// 4. 虚拟滚动大数据
<Table scroll={{ y: 400 }} dataSource={largeData} />

// 5. 按需导入组件
import { Button, Table } from 'antd';
```

**❌ 避免**:

```tsx
// 1. 避免在 render 中创建新对象/数组
const items = data.map(item => ({ value: item })); // ❌ 每次渲染创建新对象

// 2. 避免在 render 中进行昂贵计算
const sorted = data.sort((a, b) => {
  return complexCalculation(a, b); // ❌ 每次渲染都计算
});

// 3. 避免不必要的匿名函数
<Button onClick={() => console.log('click')}>Click</Button> // ❌

// 4. 避免导入整个库
import * as antd from 'antd'; // ❌

// 5. 避免一次性渲染大数据
{data.map(item => <div key={item.id}>{item.name}</div>)} // ❌ 10000+ items
```

### Table 性能优化对比

**✅ 推荐**:

```tsx
<Table
  // 使用唯一且稳定的 key
  rowKey="id"

  // 启用虚拟滚动
  scroll={{ y: 400 }}

  // 固定列宽
  columns={[
    { title: 'Name', dataIndex: 'name', width: 200 },
    { title: 'Age', dataIndex: 'age', width: 100 },
  ]}

  // 简化单元格渲染
  columns={[
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status) => <Tag>{status}</Tag>,
    },
  ]}

  // 使用 memo 优化自定义渲染组件
  components={{
    body: {
      row: memo(RowComponent),
      cell: memo(CellComponent),
    },
  }}
/>
```

**❌ 避免**:

```tsx
<Table
  // ❌ 使用 index 作为 key
  rowKey={(record, index) => index}

  // ❌ 不使用虚拟滚动
  // {largeData.map(...)}

  // ❌ 动态列宽
  columns={[
    { title: 'Name', dataIndex: 'name' }, // 宽度自动计算
  ]}

  // ❌ 复杂的单元格渲染
  columns={[
    {
      title: 'Complex',
      render: (record) => {
        const value1 = heavyCalculation(record.field1);
        const value2 = heavyCalculation(record.field2);
        return <div>{value1} - {value2}</div>;
      },
    },
  ]}
/>
```

### 数据加载优化对比

**✅ 推荐**:

```tsx
// 1. 分页加载
<Table
  pagination={{
    pageSize: 20,
    total: 10000,
    onChange: (page) => fetchData(page),
  }}
/>

// 2. 防抖搜索
<Input
  onChange={debounce((e) => {
    fetchData(e.target.value);
  }, 500)}
/>

// 3. 后端过滤
// API: /api/data?filter=keyword

// 4. 懒加载图片
<Image loading="lazy" src={url} />
```

**❌ 避免**:

```tsx
// 1. 一次性加载所有数据
const [allData, setAllData] = useState(largeDataset); // ❌

// 2. 实时搜索
<Input
  onChange={(e) => {
    // ❌ 每次输入都请求
    fetchData(e.target.value);
  }}
/>

// 3. 前端过滤大数据
const filtered = allData.filter(item =>
  item.name.includes(searchText)
); // ❌

// 4. 立即加载所有图片
{images.map(img => <img src={img.url} />)} // ❌
```

---

## 常见问题

### Q: 什么时候应该使用虚拟滚动？

A: 虚拟滚动适用于以下场景：
- 数据量超过 1000 条
- 所有数据项高度相同或可预测
- 需要流畅的滚动体验
- 不需要一次性渲染所有数据

对于少量数据（< 100 条），使用普通渲染即可。

### Q: React.memo 为什么没有提升性能？

A: 可能的原因：
1. props 每次都在变化（检查是否使用了内联函数/对象）
2. 比较函数实现错误
3. 子组件本身很简单，memo 的开销大于优化收益

**解决方案**:
```tsx
// ✅ 使用稳定的 props
const handleClick = useCallback(() => {}, []);

// ✅ 使用 useMemo 缓存对象
const style = useMemo(() => ({ color: 'red' }), []);

// ✅ 简单组件不需要 memo
function SimpleComponent({ text }) {
  return <div>{text}</div>;
}
```

### Q: Table 渲染 10000 条数据很慢怎么办？

A: 采用以下优化策略：
1. **启用虚拟滚动**: `scroll={{ y: 400 }}`
2. **使用分页**: `pagination={{ pageSize: 50 }}`
3. **后端分页**: 只加载当前页数据
4. **简化列渲染**: 使用 memo 优化的组件
5. **固定列宽**: 避免动态计算宽度

```tsx
<Table
  scroll={{ y: 400 }}
  pagination={{ pageSize: 50 }}
  rowKey="id"
  columns={optimizedColumns}
/>
```

### Q: 如何检测性能瓶颈？

A: 使用以下工具和方法：
1. **React DevTools Profiler**: 查看组件渲染时间和次数
2. **Chrome DevTools Performance**: 记录运行时性能
3. **Lighthouse**: 评估整体性能指标
4. **自定义监控**: 使用 Performance API 记录关键指标

```tsx
// 自定义性能监控
useEffect(() => {
  const start = performance.now();

  return () => {
    const end = performance.now();
    console.log(`Render time: ${end - start}ms`);
  };
});
```

### Q: Ant Design 包体积太大如何优化？

A: 采用以下优化策略：
1. **按需导入**: 只导入使用的组件
2. **Tree Shaking**: 确保打包工具支持
3. **图标按需导入**: 只导入使用的图标
4. **代码分割**: 使用 React.lazy 和 Suspense
5. **Gzip 压缩**: 服务器启用 Gzip

```tsx
// ✅ 按需导入
import { Button, Table } from 'antd';

// ✅ 图标按需导入
import { UserOutlined } from '@ant-design/icons';

// ✅ 代码分割
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

### Q: useMemo 和 useCallback 什么时候使用？

A: 使用场景：
- **useMemo**: 缓存昂贵的计算结果
  ```tsx
  const sorted = useMemo(() => data.sort(...), [data]);
  ```

- **useCallback**: 缓存传递给子组件的函数
  ```tsx
  const handleClick = useCallback(() => {}, []);
  ```

**注意**: 不要过度使用，只在有明显性能问题时使用。

### Q: 虚拟滚动会导致滚动条闪烁吗？

A: 可能的原因和解决方案：
1. **动态行高**: 使用固定行高
   ```tsx
   <Table rowHeight={55} scroll={{ y: 400 }} />
   ```

2. **异步加载**: 使用 loading 状态
   ```tsx
   <Table loading={isLoading} dataSource={data} />
   ```

3. **列宽未固定**: 设置列宽
   ```tsx
   columns={[{ title: 'Name', width: 200 }]}
   ```

### Q: 如何优化表单的性能？

A: 表单性能优化策略：
1. **使用 Form.useWatch** 替代 Form.onValuesChange
   ```tsx
   const name = Form.useWatch('name', form);
   ```

2. **拆分大表单**: 使用多个子表单
   ```tsx
   <Form.Item name="username"><Input /></Form.Item>
   <Form.Item name="email"><Input /></Form.Item>
   ```

3. **防抖验证**: 延迟触发验证
   ```tsx
   const validateDebounced = debounce(validate, 300);
   ```

4. **使用 shouldUpdate**: 精确控制更新
   ```tsx
   <Form.Item shouldUpdate={(prev, curr) => prev.a !== curr.a}>
     {/* 只在 a 变化时重新渲染 */}
   </Form.Item>
   ```

---

## 参考资源

- [Ant Design 性能优化官方文档](https://ant.design/docs/react/performance-cn)
- [React 性能优化官方文档](https://react.dev/learn/render-and-commit)
- [rc-virtual-list GitHub](https://github.com/react-component/virtual-list)
- [Web Vitals](https://web.dev/vitals/)
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- @ant-design/icons >= 5.0.0

---

## 相关模块

- [antd-config-skills](../antd-config-skills): 配置系统和主题优化
- [antd-table-skills](../antd-table-skills): Table 组件深入优化
- [antd-form-skills](../antd-form-skills): Form 表单性能优化
- [antd-nextjs-skills](../antd-nextjs-skills): Next.js 集成优化

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
