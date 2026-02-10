---
name: antd-data-display-skills
description: Ant Design 数据展示组件完整指南 - List、Card、Descriptions、Tree、Tabs、Tag、Badge
---

# antd-data-display-skills - Ant Design 数据展示组件完整指南

## 概述

Ant Design 数据展示组件是一套用于展示各类数据的 UI 组件集合，涵盖列表、卡片、树形控件、标签页等常见场景。这些组件专注于数据的清晰呈现、良好的交互体验和灵活的定制能力，是构建企业级后台管理系统不可或缺的基础组件。

数据展示组件的核心价值在于：
- **信息层次清晰** - 通过合理的视觉层次和排版，帮助用户快速理解数据结构
- **交互体验流畅** - 提供丰富的交互模式（加载更多、分页、搜索、展开等）
- **性能优化** - 支持虚拟滚动、懒加载等优化策略，轻松处理大规模数据
- **响应式设计** - 自动适配不同屏幕尺寸，确保移动端和桌面端都有良好体验

## 核心特性

- **统一的 API 设计** - 所有展示组件遵循相同的设计模式（dataSource、render、pagination）
- **性能优化** - 内置虚拟滚动、懒加载、按需渲染等性能优化机制
- **灵活定制** - 支持自定义渲染函数、插槽、样式主题等
- **类型安全** - 完整的 TypeScript 类型定义和类型推导
- **无障碍访问** - 符合 WCAG 2.1 标准，支持键盘导航和屏幕阅读器
- **国际化** - 内置多语言支持，易于扩展

## 组件分类

### 1. 列表类组件
- **List** - 基础列表组件（支持分页、加载更多、虚拟滚动）
- **InfiniteScroll** - 无限滚动列表（基于 rc-virtual-list）

### 2. 卡片类组件
- **Card** - 卡片容器（支持边框、加载状态、网格布局）
- **Descriptions** - 描述列表（展示键值对数据）

### 3. 树形组件
- **Tree** - 树形控件（支持异步加载、拖拽、搜索）
- **TreeSelect** - 树形选择器（在输入组件文档中）

### 4. 标签页组件
- **Tabs** - 标签页（支持图标、增减、路由集成）

### 5. 标记组件
- **Tag** - 标签（彩色标签、热门标签、动态增减）
- **Badge** - 徽标（独立徽标、状态点、动态计数）

---

## List 列表组件

### 基础列表

List 是最常用的列表展示组件，支持静态和动态数据源。

**核心属性：**

```typescript
interface ListProps<T = any> {
  dataSource: T[];                    // 数据源
  renderItem: (item: T, index: number) => ReactNode; // 渲染函数
  bordered?: boolean;                 // 是否显示边框
  split?: boolean;                    // 是否显示分割线
  header?: ReactNode;                 // 列表头部
  footer?: ReactNode;                 // 列表底部
  pagination?: PaginationProps | false; // 分页配置
  loading?: boolean;                  // 加载状态
  locale?: ListLocale;                // 国际化配置
  grid?: ColumnProps;                 // 网格布局（Grid 格式）
  size?: 'default' | 'small' | 'large'; // 列表尺寸
}
```

**示例 1：基础列表（静态数据）**

```tsx
import React from 'react';
import { List, Typography, Avatar, Space } from 'antd';
import type { ListItemProps } from 'antd';

const { Text } = Typography;

interface DataType {
  id: number;
  title: string;
  description: string;
  avatar: string;
}

const data: DataType[] = [
  {
    id: 1,
    title: 'Ant Design Title 1',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=1',
  },
  {
    id: 2,
    title: 'Ant Design Title 2',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=2',
  },
  {
    id: 3,
    title: 'Ant Design Title 3',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=3',
  },
  {
    id: 4,
    title: 'Ant Design Title 4',
    description: 'Ant Design, a design language for background applications.',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=4',
  },
];

const BasicList: React.FC = () => {
  return (
    <List
      header={<div>Header</div>}
      footer={<div>Footer</div>}
      bordered
      dataSource={data}
      renderItem={(item) => (
        <List.Item>
          <List.Item.Meta
            avatar={<Avatar src={item.avatar} />}
            title={<a href="#">{item.title}</a>}
            description={item.description}
          />
        </List.Item>
      )}
    />
  );
};

export default BasicList;
```

### 加载更多列表

通过 `loadMore` 属性实现"加载更多"功能，适合数据量较大的场景。

**示例 2：加载更多列表（分页加载）**

```tsx
import React, { useState, useEffect } from 'react';
import { List, Button, Spin, message } from 'antd';
import type { ListItemProps } from 'antd';

interface DataType {
  id: number;
  name: string;
  age: number;
  address: string;
}

const LoadMoreList: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DataType[]>([]);
  const [list, setList] = useState<DataType[]>([]);
  const [page, setPage] = useState(1);

  // 模拟加载数据
  const fetchData = (pageNum: number): Promise<DataType[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newData: DataType[] = Array.from({ length: 10 }).map((_, index) => ({
          id: (pageNum - 1) * 10 + index + 1,
          name: `Ant Design ${page}`,
          age: (pageNum - 1) * 10 + index + 18,
          address: `New York No. ${index + 1} Lake Park`,
        }));
        resolve(newData);
      }, 1000);
    });
  };

  const onLoadMore = async () => {
    setLoading(true);
    try {
      const newData = await fetchData(page + 1);
      setPage(page + 1);
      setData([...data, ...newData]);
      setList([...data, ...newData]);
      window.dispatchEvent(new Event('resize'));
    } catch (error) {
      message.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(1).then((initialData) => {
      setData(initialData);
      setList(initialData);
    });
  }, []);

  const loadMore = !loading ? (
    <div
      style={{
        textAlign: 'center',
        marginTop: 12,
        height: 32,
        lineHeight: '32px',
      }}
    >
      <Button onClick={onLoadMore}>loading more</Button>
    </div>
  ) : null;

  return (
    <List
      loading={loading}
      itemLayout="horizontal"
      loadMore={loadMore}
      dataSource={data}
      renderItem={(item) => (
        <List.Item
          actions={[<a key="list-loadmore-edit">edit</a>, <a key="list-loadmore-more">more</a>]}
        >
          <List.Item.Meta
            avatar={<div style={{ width: 50, height: 50, background: '#f0f0f0' }} />}
            title={<a href="#">{item.name}</a>}
            description="Ant Design, a design language for background applications"
          />
          <div>Content</div>
        </List.Item>
      )}
    />
  );
};

export default LoadMoreList;
```

### 竖排列表

通过 `itemLayout="vertical"` 创建竖排布局的列表。

**示例 3：竖排列表（文章列表）**

```tsx
import React from 'react';
import { List, Tag, Space } from 'antd';
import { LikeOutlined, MessageOutlined, StarOutlined } from '@ant-design/icons';

interface DataType {
  href: string;
  title: string;
  avatar: string;
  description: string;
  content: string;
}

const IconText = ({ icon, text }: { icon: React.FC; text: string }) => (
  <Space>
    {React.createElement(icon)}
    {text}
  </Space>
);

const VerticalList: React.FC = () => {
  const listData: DataType[] = Array.from({ length: 23 }).map((_, i) => ({
    href: 'https://ant.design',
    title: `ant design part ${i}`,
    avatar: `https://xsgames.co/randomusers/avatar.php?u=${i}`,
    description:
      'Ant Design, a design language for background applications, is refined by Ant UED Team.',
    content:
      'We supply a series of design principles, practical patterns and high quality design resources (Sketch and Axure), to help people create their product prototypes beautifully and efficiently.',
  }));

  return (
    <List
      itemLayout="vertical"
      size="large"
      pagination={{
        onChange: (page) => {
          console.log(page);
        },
        pageSize: 3,
      }}
      dataSource={listData}
      footer={
        <div>
          <b>ant design</b> footer part
        </div>
      }
      renderItem={(item) => (
        <List.Item
          key={item.title}
          actions={[
            <IconText icon={StarOutlined} text="156" key="list-vertical-star-o" />,
            <IconText icon={LikeOutlined} text="156" key="list-vertical-like-o" />,
            <IconText icon={MessageOutlined} text="2" key="list-vertical-message" />,
          ]}
          extra={
            <img
              width={272}
              alt="logo"
              src="https://gw.alipayobjects.com/zos/rmsportal/mTLRUmTwZbMnBNEvggFs.png"
            />
          }
        >
          <List.Item.Meta
            avatar={<Avatar src={item.avatar} />}
            title={<a href={item.href}>{item.title}</a>}
            description={item.description}
          />
          {item.content}
        </List.Item>
      )}
    />
  );
};

export default VerticalList;
```

### 简单列表

通过 `split` 属性控制是否显示分割线，`bordered` 控制边框。

**示例 4：简单列表（无分割线）**

```tsx
import React from 'react';
import { List, Typography } from 'antd';

const { Paragraph } = Typography;

const data = [
  'Racing car sprays burning fuel into crowd.',
  'Japanese princess to wed commoner.',
  'Australian walks 100km after outback crash.',
  'Man charged over missing wedding girl.',
  'Los Angeles battles huge wildfires.',
];

const SimpleList: React.FC = () => {
  return (
    <>
      <Paragraph>Split: true (default)</Paragraph>
      <List
        header={<div>Header</div>}
        footer={<div>Footer</div>}
        bordered
        dataSource={data}
        renderItem={(item) => <List.Item>{item}</List.Item>}
      />

      <Paragraph>Split: false</Paragraph>
      <List
        bordered
        split={false}
        dataSource={data}
        renderItem={(item) => <List.Item>{item}</List.Item>}
      />
    </>
  );
};

export default SimpleList;
```

### 响应式列表

通过 `grid` 属性实现响应式网格布局。

**示例 5：响应式网格列表**

```tsx
import React from 'react';
import { List, Card } from 'antd';

const data = [
  {
    title: 'Title 1',
  },
  {
    title: 'Title 2',
  },
  {
    title: 'Title 3',
  },
  {
    title: 'Title 4',
  },
  {
    title: 'Title 5',
  },
  {
    title: 'Title 6',
  },
];

const GridList: React.FC = () => {
  return (
    <List
      grid={{
        gutter: 16,
        xs: 1,
        sm: 2,
        md: 4,
        lg: 4,
        xl: 6,
        xxl: 3,
      }}
      dataSource={data}
      renderItem={(item) => (
        <List.Item>
          <Card title={item.title}>Card content</Card>
        </List.Item>
      )}
    />
  );
};

export default GridList;
```

### 列表性能优化

对于大数据量列表，使用虚拟滚动提升性能。

**示例 6：虚拟滚动列表（处理 10000+ 数据）**

```tsx
import React, { useState, useRef, useEffect } from 'react';
import { List, Avatar, Button, Space, message } from 'antd';
import { RocketPro } from '@ant-design/icons';

interface DataType {
  id: number;
  email: string;
  name: {
    first: string;
    last: string;
  };
  picture: {
    large: string;
  };
}

const VirtualScrollList: React.FC = () => {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);

  // 模拟获取 10000 条数据
  const fetchLargeData = (): Promise<DataType[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const largeData: DataType[] = Array.from({ length: 10000 }).map((_, index) => ({
          id: index,
          email: `user${index}@example.com`,
          name: {
            first: `First${index}`,
            last: `Last${index}`,
          },
          picture: {
            large: `https://i.pravatar.cc/150?img=${index % 70}`,
          },
        }));
        resolve(largeData);
      }, 500);
    });
  };

  useEffect(() => {
    setLoading(true);
    fetchLargeData().then((result) => {
      setData(result);
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ height: 400, overflow: 'auto' }}>
      <List
        dataSource={data}
        renderItem={(item) => (
          <List.Item key={item.id}>
            <List.Item.Meta
              avatar={<Avatar src={item.picture.large} />}
              title={<a href="#">{item.name.first} {item.name.last}</a>}
              description={item.email}
            />
          </List.Item>
        )}
      />
    </div>
  );
};

export default VirtualScrollList;
```

---

## Card 卡片组件

### 基础卡片

Card 是通用的卡片容器组件，支持标题、额外操作、封面图等功能。

**核心属性：**

```typescript
interface CardProps {
  title?: ReactNode;                  // 卡片标题
  extra?: ReactNode;                  // 标题右侧操作区
  bordered?: boolean;                 // 是否有边框
  hoverable?: boolean;                // 鼠标悬停时浮起
  loading?: boolean;                  // 加载中状态
  cover?: ReactNode;                  // 卡片封面
  actions?: ReactNode[];              // 卡片操作组
  bodyStyle?: CSSProperties;          // 内容区域自定义样式
  headStyle?: CSSProperties;          // 标题区域自定义样式
  size?: 'default' | 'small';         // 卡片尺寸
  type?: 'inner';                     // 卡片类型（可内嵌）
  children?: ReactNode;               // 卡片内容
}
```

**示例 7：基础卡片（多种样式）**

```tsx
import React from 'react';
import { Card, Row, Col } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';

const BasicCard: React.FC = () => {
  return (
    <Row gutter={16}>
      <Col span={8}>
        <Card title="Default size card" extra={<a href="#">More</a>} style={{ width: 300 }}>
          <p>Card content</p>
          <p>Card content</p>
          <p>Card content</p>
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small" title="Small size card" extra={<a href="#">More</a>} style={{ width: 300 }}>
          <p>Card content</p>
          <p>Card content</p>
          <p>Card content</p>
        </Card>
      </Col>
      <Col span={8}>
        <Card
          title="With hoverable"
          extra={<a href="#">More</a>}
          hoverable
          style={{ width: 300 }}
        >
          <p>Card content</p>
          <p>Card content</p>
          <p>Card content</p>
        </Card>
      </Col>
    </Row>
  );
};

export default BasicCard;
```

### 边框卡片

通过 `bordered` 属性控制边框显示。

**示例 8：无边框卡片**

```tsx
import React from 'react';
import { Card, Radio, Space } from 'antd';
import type { CardProps } from 'antd';

const BorderCard: React.FC = () => {
  const [bordered, setBordered] = React.useState<CardProps['bordered']>(true);

  return (
    <Space direction="vertical" size={16}>
      <Radio.Group value={bordered} onChange={(e) => setBordered(e.target.value)}>
        <Radio value={true}>Bordered</Radio>
        <Radio value={false}>Borderless</Radio>
      </Radio.Group>

      <Card title="Card" bordered={bordered} style={{ width: 300 }}>
        <p>Card content</p>
        <p>Card content</p>
        <p>Card content</p>
      </Card>
    </Space>
  );
};

export default BorderCard;
```

### 简单卡片

只有内容区域的简单卡片，不带标题和边框。

**示例 9：简单卡片（无边框、无标题）**

```tsx
import React from 'react';
import { Card, Divider } from 'antd';

const SimpleCard: React.FC = () => {
  return (
    <div style={{ background: '#ECECEC', padding: '30px' }}>
      <Card title="Card title" bordered={false} style={{ width: 300 }}>
        <p style={{ fontSize: 14, color: 'rgba(0, 0, 0, 0.85)', marginBottom: 16, fontWeight: 500 }}>
          Card content
        </p>
        <p>Card content</p>
        <p>Card content</p>
      </Card>
    </div>
  );
};

export default SimpleCard;
```

### 灵活的卡片内容

Card 内容区域支持任意 React 组件。

**示例 10：灵活内容卡片**

```tsx
import React from 'react';
import { Card, Avatar, Space, Typography, Button, Divider } from 'antd';
import { UserOutlined, EditOutlined, EllipsisOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

const FlexibleCard: React.FC = () => {
  const cardTitle = (
    <Space>
      <Avatar size={32} icon={<UserOutlined />} />
      <Text strong>User Profile</Text>
    </Space>
  );

  const cardActions = [
    <EditOutlined key="edit" />,
    <EllipsisOutlined key="ellipsis" />,
  ];

  return (
    <Card
      title={cardTitle}
      actions={cardActions}
      style={{ width: 400 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Text type="secondary">Name</Text>
          <Paragraph style={{ marginBottom: 0 }}>John Doe</Paragraph>
        </div>
        <Divider style={{ margin: '12px 0' }} />
        <div>
          <Text type="secondary">Email</Text>
          <Paragraph style={{ marginBottom: 0 }}>john.doe@example.com</Paragraph>
        </div>
        <Divider style={{ margin: '12px 0' }} />
        <div>
          <Text type="secondary">Location</Text>
          <Paragraph style={{ marginBottom: 0 }}>New York, USA</Paragraph>
        </div>
      </Space>
    </Card>
  );
};

export default FlexibleCard;
```

### 内部卡片

通过 `type="inner"` 创建内部嵌套卡片。

**示例 11：内部卡片（嵌套卡片）**

```tsx
import React from 'react';
import { Card, Radio, Space } from 'antd';

const InnerCard: React.FC = () => {
  return (
    <div style={{ background: '#ECECEC', padding: '30px' }}>
      <Card title="Card Title">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Card type="inner" title="Inner Card title" extra={<a href="#">More</a>}>
            Inner Card content
          </Card>
          <Card type="inner" title="Inner Card title 2" extra={<a href="#">More</a>}>
            Inner Card content 2
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default InnerCard;
```

### 网格卡片

使用 Grid 栅格系统创建卡片网格布局。

**示例 12：网格卡片布局**

```tsx
import React from 'react';
import { Card, Col, Row, Avatar, Space, Typography, Button } from 'antd';
import { EditOutlined, EllipsisOutlined, SettingOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface CardData {
  title: string;
  description: string;
  avatar: string;
}

const cardData: CardData[] = [
  {
    title: 'Card 1',
    description: 'This is the description of card 1',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=1',
  },
  {
    title: 'Card 2',
    description: 'This is the description of card 2',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=2',
  },
  {
    title: 'Card 3',
    description: 'This is the description of card 3',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=3',
  },
  {
    title: 'Card 4',
    description: 'This is the description of card 4',
    avatar: 'https://xsgames.co/randomusers/avatar.php?u=4',
  },
];

const GridCard: React.FC = () => {
  return (
    <div style={{ background: '#ECECEC', padding: '30px' }}>
      <Row gutter={16}>
        {cardData.map((item, index) => (
          <Col span={8} key={index}>
            <Card
              hoverable
              style={{ marginBottom: 16 }}
              cover={<img alt="example" src={`https://picsum.photos/300/200?random=${index}`} />}
              actions={[
                <SettingOutlined key="setting" />,
                <EditOutlined key="edit" />,
                <EllipsisOutlined key="ellipsis" />,
              ]}
            >
              <Card.Meta
                avatar={<Avatar src={item.avatar} />}
                title={item.title}
                description={item.description}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default GridCard;
```

### 加载中卡片

使用 `loading` 属性显示加载状态。

**示例 13：加载中卡片**

```tsx
import React, { useState } from 'react';
import { Card, Button, Space } from 'antd';

const LoadingCard: React.FC = () => {
  const [loading, setLoading] = useState(true);

  const handleLoad = () => {
    setLoading(!loading);
  };

  return (
    <Space direction="vertical">
      <Card
        loading={loading}
        title="Card title"
        style={{ width: 300 }}
      >
        Whatever content
      </Card>

      <Button onClick={handleLoad} type="primary">
        Toggle loading
      </Button>
    </Space>
  );
};

export default LoadingCard;
```

---

## Descriptions 描述列表

### 基础描述列表

Descriptions 用于展示只读的键值对数据，适合展示详细信息、配置信息等场景。

**核心属性：**

```typescript
interface DescriptionsProps {
  title?: ReactNode;                  // 标题
  bordered?: boolean;                 // 是否显示边框
  column?: number | { xs: number; sm: number; md: number; lg: number; xl: number; xxl: number }; // 列数
  size?: 'default' | 'middle' | 'small'; // 尺寸
  layout?: 'horizontal' | 'vertical'; // 布局方式
  colon?: boolean;                    // 是否显示冒号
  items?:DescriptionsItemType[];      // 数据项（5.x 推荐方式）
  children?: ReactNode;               // 数据项（4.x 方式）
}
```

**示例 14：基础描述列表**

```tsx
import React from 'react';
import { Descriptions, Button } from 'antd';

const BasicDescriptions: React.FC = () => {
  return (
    <Descriptions title="User Info">
      <Descriptions.Item label="UserName">Zhou Maomao</Descriptions.Item>
      <Descriptions.Item label="Telephone">18100000000</Descriptions.Item>
      <Descriptions.Item label="Live">Hangzhou, Zhejiang</Descriptions.Item>
      <Descriptions.Item label="Remark">empty</Descriptions.Item>
      <Descriptions.Item label="Address">
        No. 18, Wantang Road, Xihu District, Hangzhou, Zhejiang, China
      </Descriptions.Item>
    </Descriptions>
  );
};

export default BasicDescriptions;
```

### 响应式描述列表

通过 `column` 属性实现响应式列数。

**示例 15：响应式描述列表**

```tsx
import React from 'react';
import { Descriptions } from 'antd';

const ResponsiveDescriptions: React.FC = () => {
  return (
    <Descriptions
      title="Responsive Descriptions"
      bordered
      column={{ xxl: 4, xl: 3, lg: 3, md: 3, sm: 2, xs: 1 }}
    >
      <Descriptions.Item label="Product">Cloud Database</Descriptions.Item>
      <Descriptions.Item label="Billing">Prepaid</Descriptions.Item>
      <Descriptions.Item label="Time">18:00:00</Descriptions.Item>
      <Descriptions.Item label="Amount">$80.00</Descriptions.Item>
      <Descriptions.Item label="Discount">$20.00</Descriptions.Item>
      <Descriptions.Item label="Official">$60.00</Descriptions.Item>
      <Descriptions.Item label="Config Info">
        Data disk type: MongoDB
        <br />
        Database version: 3.4
        <br />
        Package: dds.mongo.mid
        <br />
        Storage space: 10 GB
        <br />
        Replication factor: 3
        <br />
        Region: East China 1
        <br />
      </Descriptions.Item>
    </Descriptions>
  );
};

export default ResponsiveDescriptions;
```

### 带边框的描述列表

通过 `bordered` 属性显示边框。

**示例 16：带边框描述列表**

```tsx
import React from 'react';
import { Descriptions, Badge } from 'antd';

const BorderedDescriptions: React.FC = () => {
  return (
    <Descriptions title="User Info" bordered>
      <Descriptions.Item label="Product">Cloud Database</Descriptions.Item>
      <Descriptions.Item label="Billing">Prepaid</Descriptions.Item>
      <Descriptions.Item label="Time">18:00:00</Descriptions.Item>
      <Descriptions.Item label="Amount">$80.00</Descriptions.Item>
      <Descriptions.Item label="Discount">$20.00</Descriptions.Item>
      <Descriptions.Item label="Official">$60.00</Descriptions.Item>
      <Descriptions.Item label="Status">
        <Badge status="processing" text="Running" />
      </Descriptions.Item>
      <Descriptions.Item label="Negotiated">
        YES
      </Descriptions.Item>
      <Descriptions.Item
        label="Config Info"
        span={2}
      >
        Data disk type: MongoDB
        <br />
        Database version: 3.4
        <br />
        Package: dds.mongo.mid
        <br />
        Storage space: 10 GB
        <br />
        Replication factor: 3
        <br />
        Region: East China 1
      </Descriptions.Item>
    </Descriptions>
  );
};

export default BorderedDescriptions;
```

---

## Tree 树形控件

### 基础树形控件

Tree 用于展示树形结构数据，支持展开/收起、选中、右键菜单等交互。

**核心属性：**

```typescript
interface TreeProps {
  treeData: DataNode[];               // 数据源
  checkedKeys?: Key[] | { checked: Key[]; halfChecked: Key[] }; // 选中的节点
  defaultCheckedKeys?: Key[];         // 默认选中的节点
  expandedKeys?: Key[];               // 展开的节点
  defaultExpandedKeys?: Key[];        // 默认展开的节点
  selectedKeys?: Key[];               // 选中的节点
  defaultSelectedKeys?: Key[];        // 默认选中的节点
  checkable?: boolean;                // 显示复选框
  selectable?: boolean;               // 是否可选中
  disabled?: boolean;                 // 禁用树
  multiple?: boolean;                 // 支持多选
  checkStrictly?: boolean;            // 父子节点选中状态不再关联
  draggable?: boolean;                // 是否可拖拽
  blockNode?: boolean;                // 是否节点占据一行
  showLine?: boolean | { showLeafIcon: boolean }; // 是否显示连接线
  icon?: (node: DataNode) => ReactNode; // 自定义图标
  switcherIcon?: ReactNode;           // 自定义展开/收起图标
  loadData?: (node: DataNode) => Promise<void>; // 异步加载数据
  onCheck?: (checkedKeys: Key[] | { checked: Key[]; halfChecked: Key[] }, info: any) => void; // 选中回调
  onSelect?: (selectedKeys: Key[], info: any) => void; // 选择回调
  onExpand?: (expandedKeys: Key[], info: any) => void; // 展开回调
  onDrop?: (info: any) => void;       // 拖拽放下回调
}
```

**示例 17：基础树形控件**

```tsx
import React, { useState } from 'react';
import { Tree } from 'antd';
import type { DataNode, TreeProps } from 'antd';

const treeData: DataNode[] = [
  {
    title: 'Parent 1',
    key: '1',
    children: [
      {
        title: 'Parent 1-0',
        key: '1-0',
        children: [
          {
            title: 'Leaf',
            key: '1-0-0',
          },
          {
            title: 'Leaf',
            key: '1-0-1',
          },
        ],
      },
      {
        title: 'Parent 1-1',
        key: '1-1',
        children: [
          {
            title: 'Leaf',
            key: '1-1-0',
          },
        ],
      },
    ],
  },
  {
    title: 'Parent 2',
    key: '2',
    children: [
      {
        title: 'Leaf',
        key: '2-0',
      },
    ],
  },
];

const BasicTree: React.FC = () => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>(['0-0-0', '0-0-1']);
  const [checkedKeys, setCheckedKeys] = useState<React.Key[]>(['0-0-0']);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [autoExpandParent, setAutoExpandParent] = useState<boolean>(true);

  const onExpand: TreeProps['onExpand'] = (expandedKeysValue) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  };

  const onCheck: TreeProps['onCheck'] = (checkedKeysValue) => {
    setCheckedKeys(checkedKeysValue as React.Key[]);
  };

  const onSelect: TreeProps['onSelect'] = (selectedKeysValue, info) => {
    setSelectedKeys(selectedKeysValue);
  };

  return (
    <Tree
      checkable
      onExpand={onExpand}
      expandedKeys={expandedKeys}
      autoExpandParent={autoExpandParent}
      onCheck={onCheck}
      checkedKeys={checkedKeys}
      onSelect={onSelect}
      selectedKeys={selectedKeys}
      treeData={treeData}
    />
  );
};

export default BasicTree;
```

### 异步加载树

通过 `loadData` 实现懒加载树节点。

**示例 18：异步加载树（懒加载）**

```tsx
import React, { useState } from 'react';
import { Tree, Spin } from 'antd';
import type { DataNode, EventDataNode } from 'antd';

const AsyncTree: React.FC = () => {
  const [treeData, setTreeData] = useState<DataNode[]>([
    {
      title: 'Expand to load',
      key: '0',
    },
    {
      title: 'Expand to load',
      key: '1',
    },
    {
      title: 'Tree Node',
      key: '2',
      isLeaf: true,
    },
  ]);

  const onLoadData = ({ key, children }: any) =>
    new Promise<void>((resolve) => {
      if (children) {
        resolve();
        return;
      }

      setTimeout(() => {
        setTreeData((origin) => {
          return updateTreeData(origin, key, [
            {
              title: 'Child Node',
              key: `${key}-0`,
            },
            {
              title: 'Child Node',
              key: `${key}-1`,
            },
          ]);
        });

        resolve();
      }, 1000);
    });

  const updateTreeData = (list: DataNode[], key: React.Key, children: DataNode[]): DataNode[] =>
    list.map((node) => {
      if (node.key === key) {
        return {
          ...node,
          children,
        };
      }
      if (node.children) {
        return {
          ...node,
          children: updateTreeData(node.children, key, children),
        };
      }
      return node;
    });

  return (
    <Tree
      loadData={onLoadData}
      treeData={treeData}
    />
  );
};

export default AsyncTree;
```

### 可搜索树

通过 `Tree.findAll` 或 `filterTreeData` 实现搜索功能。

**示例 19：可搜索树（高亮匹配）**

```tsx
import React, { useState, useMemo } from 'react';
import { Tree, Input } from 'antd';
import type { DataNode } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const { Search } = Input;

const x = 3;
const y = 2;
const z = 1;
const defaultData: DataNode[] = [];

const generateData = (
  _level: number,
  _preKey: React.Key | null,
  _tns: DataNode[],
) => {
  const preKey = _preKey || '0';
  const tns = _tns || defaultData;

  const children = [];
  for (let i = 0; i < x; i++) {
    const key = `${preKey}-${i}`;
    tns.push({ title: key, key });
    if (i < y) {
      children.push(key);
    }
  }

  if (_level < 0) {
    return tns;
  }

  const level = _level - 1;
  children.forEach((key, index) => {
    tns[index].children = [];
    return generateData(level, key, tns[index].children);
  });

  return tns;
};

generateData(z);

const SearchableTree: React.FC = () => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  const dataList: { key: React.Key; title: string; parent: string }[] = [];
  const generateList = (data: DataNode[], parent: string = '') => {
    data.forEach((node) => {
      const { key, title } = node;
      dataList.push({ key, title: title as string, parent });
      if (node.children) {
        generateList(node.children, key as string);
      }
    });
  };

  generateList(defaultData);

  const getParentKey = (key: React.Key, tree: DataNode[]): React.Key => {
    let parentKey;
    for (let i = 0; i < tree.length; i++) {
      const node = tree[i];
      if (node.children) {
        if (node.children.some((item) => item.key === key)) {
          parentKey = node.key;
        } else if (getParentKey(key, node.children)) {
          parentKey = getParentKey(key, node.children);
        }
      }
    }
    return parentKey!;
  };

  const onExpand = (newExpandedKeys: React.Key[]) => {
    setExpandedKeys(newExpandedKeys);
    setAutoExpandParent(false);
  };

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const newExpandedKeys = dataList
      .map((item) => {
        if (item.title.indexOf(value) > -1) {
          return getParentKey(item.key, defaultData);
        }
        return null;
      })
      .filter((item, i, self): item is React.Key => !!(item && self.indexOf(item) === i));

    setExpandedKeys(newExpandedKeys as React.Key[]);
    setSearchValue(value);
    setAutoExpandParent(true);
  };

  const treeData = useMemo(() => {
    const loop = (data: DataNode[]): DataNode[] =>
      data.map((item) => {
        const strTitle = item.title as string;
        const index = strTitle.indexOf(searchValue);
        const beforeStr = strTitle.substring(0, index);
        const afterStr = strTitle.slice(index + searchValue.length);
        const title =
          index > -1 ? (
            <span>
              {beforeStr}
              <span className="site-tree-search-value">{searchValue}</span>
              {afterStr}
            </span>
          ) : (
            <span>{strTitle}</span>
          );

        if (item.children) {
          return { title, key: item.key, children: loop(item.children) };
        }

        return {
          title,
          key: item.key,
        };
      });

    return loop(defaultData);
  }, [searchValue]);

  return (
    <div>
      <Search
        style={{ marginBottom: 8 }}
        placeholder="Search"
        onChange={onChange}
        prefix={<SearchOutlined />}
      />
      <Tree
        onExpand={onExpand}
        expandedKeys={expandedKeys}
        autoExpandParent={autoExpandParent}
        treeData={treeData}
      />
    </div>
  );
};

export default SearchableTree;
```

### 树节点拖拽

通过 `draggable` 和 `onDrop` 实现拖拽排序。

**示例 20：可拖拽树（拖拽排序）**

```tsx
import React, { useState } from 'react';
import { Tree } from 'antd';
import type { DataNode, TreeProps } from 'antd';

const treeData: DataNode[] = [
  {
    title: 'Parent 1',
    key: '1',
    children: [
      {
        title: 'Parent 1-0',
        key: '1-0',
        children: [
          {
            title: 'Leaf',
            key: '1-0-0',
          },
          {
            title: 'Leaf',
            key: '1-0-1',
          },
        ],
      },
      {
        title: 'Parent 1-1',
        key: '1-1',
        children: [
          {
            title: 'Leaf',
            key: '1-1-0',
          },
        ],
      },
    ],
  },
  {
    title: 'Parent 2',
    key: '2',
  },
];

const DraggableTree: React.FC = () => {
  const [gData, setGData] = useState(treeData);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>(['1-0', '1-0-0', '1-0-1', '1-1']);

  const onDrop: TreeProps['onDrop'] = (info) => {
    const dropKey = info.node.key;
    const dragKey = info.dragNode.key;
    const dropPos = info.node.pos.split('-');
    const dropPosition = info.dropPosition - Number(dropPos[dropPos.length - 1]);

    const loop = (
      data: DataNode[],
      key: React.Key,
      callback: (node: DataNode, i: number, data: DataNode[]) => void,
    ) => {
      data.forEach((item, index, arr) => {
        if (item.key === key) {
          callback(item, index, arr);
        }
        if (item.children) {
          loop(item.children, key, callback);
        }
      });
    };

    const data = [...gData];

    let dragObj: DataNode;

    loop(data, dragKey, (item, index, arr) => {
      arr.splice(index, 1);
      dragObj = item;
    });

    if (!info.dropToGap) {
      loop(data, dropKey, (item) => {
        item.children = item.children || [];
        item.children.unshift(dragObj);
      });
    } else if (
      (info.node.props.children as any)?.length > 0 &&
      (info.node.props.children as any)[0].key === dragKey &&
      dropPosition === 1
    ) {
      loop(data, dropKey, (item) => {
        item.children = item.children || [];
        item.children.unshift(dragObj);
      });
    } else {
      let ar: DataNode[] = [];
      let i;
      loop(data, dropKey, (_item, index, arr) => {
        ar = arr;
        i = index;
      });
      if (dropPosition === -1) {
        ar.splice(i!, 0, dragObj!);
      } else {
        ar.splice(i! + 1, 0, dragObj!);
      }
    }

    setGData(data);
  };

  return (
    <Tree
      className="draggable-tree"
      defaultExpandedKeys={expandedKeys}
      draggable
      blockNode
      onDrop={onDrop}
      treeData={gData}
    />
  );
};

export default DraggableTree;
```

---

## Tabs 标签页组件

### 基础标签页

Tabs 用于组织内容并节省空间，提供平级的区域展示。

**核心属性：**

```typescript
interface TabsProps {
  type?: 'line' | 'card' | 'editable-card'; // 标签页类型
  activeKey?: string;                       // 当前激活的 key
  defaultActiveKey?: string;                // 默认激活的 key
  hideAdd?: boolean;                        // 隐藏添加按钮
  tabPosition?: 'left' | 'right' | 'top' | 'bottom'; // 位置
  animated?: boolean | { inkBar: boolean; tabPane: boolean }; // 动画
  tabBarExtraContent?: ReactNode | { left?: ReactNode; right?: ReactNode }; // tab bar 额外内容
  size?: 'large' | 'middle' | 'small';     // 尺寸  }
```

**示例 21：基础标签页**

```tsx
import React from 'react';
import { Tabs } from 'antd';

const BasicTabs: React.FC = () => {
  const items = [
    {
      key: '1',
      label: 'Tab 1',
      children: 'Content of Tab Pane 1',
    },
    {
      key: '2',
      label: 'Tab 2',
      children: 'Content of Tab Pane 2',
    },
    {
      key: '3',
      label: 'Tab 3',
      children: 'Content of Tab Pane 3',
    },
  ];

  return <Tabs defaultActiveKey="1" items={items} />;
};

export default BasicTabs;
```

### 图标标签页

在标签上添加图标。

**示例 22：图标标签页**

```tsx
import React from 'react';
import { Tabs } from 'antd';
import { AppleOutlined, AndroidOutlined } from '@ant-design/icons';

const IconTabs: React.FC = () => {
  const items = [
    {
      key: '1',
      label: (
        <span>
          <AppleOutlined />
          Tab 1
        </span>
      ),
      children: 'Tab 1',
    },
    {
      key: '2',
      label: (
        <span>
          <AndroidOutlined />
          Tab 2
        </span>
      ),
      children: 'Tab 2',
    },
  ];

  return <Tabs defaultActiveKey="2" items={items} />;
};

export default IconTabs;
```

### 增减标签页

通过 `type="editable-card"` 实现可添加和关闭的标签页。

**示例 23：动态增减标签页**

```tsx
import React, { useState } from 'react';
import { Tabs, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const AddRemoveTabs: React.FC = () => {
  const [items, setItems] = useState([
    {
      key: '1',
      label: 'Tab 1',
      children: 'Content of Tab Pane 1',
    },
    {
      key: '2',
      label: 'Tab 2',
      children: 'Content of Tab Pane 2',
    },
    {
      key: '3',
      label: 'Tab 3',
      children: 'Content of Tab Pane 3',
    },
  ]);
  const [activeKey, setActiveKey] = useState('1');
  const [currentIndex, setCurrentIndex] = useState(3);

  const remove = (targetKey: string) => {
    const newItems = items.filter((item) => item.key !== targetKey);
    if (newItems.length && activeKey === targetKey) {
      const newActiveKey = newItems.length ? newItems[0].key : '';
      setActiveKey(newActiveKey);
    }
    setItems(newItems);
  };

  const onEdit = (targetKey: string, action: 'add' | 'remove') => {
    if (action === 'add') {
      const newKey = `newTab${currentIndex + 1}`;
      const newItems = [
        ...items,
        {
          key: newKey,
          label: `New Tab ${currentIndex + 1}`,
          children: `Content of new Tab ${currentIndex + 1}`,
        },
      ];
      setCurrentIndex(currentIndex + 1);
      setItems(newItems);
      setActiveKey(newKey);
    } else {
      remove(targetKey);
    }
  };

  return (
    <Tabs
      type="editable-card"
      onChange={setActiveKey}
      activeKey={activeKey}
      onEdit={onEdit}
      items={items}
    />
  );
};

export default AddRemoveTabs;
```

### 卡片式标签页

通过 `type="card"` 创建卡片式标签页。

**示例 24：卡片式标签页**

```tsx
import React from 'react';
import { Tabs } from 'antd';

const CardTabs: React.FC = () => {
  const items = [
    {
      key: '1',
      label: 'Tab 1',
      children: 'Content of Tab Pane 1',
    },
    {
      key: '2',
      label: 'Tab 2',
      children: 'Content of Tab Pane 2',
    },
    {
      key: '3',
      label: 'Tab 3',
      children: 'Content of Tab Pane 3',
    },
  ];

  return <Tabs defaultActiveKey="1" type="card" items={items} />;
};

export default CardTabs;
```

### 位置和大小

通过 `tabPosition` 和 `size` 属性控制标签页位置和大小。

**示例 25：不同位置和大小的标签页**

```tsx
import React, { useState } from 'react';
import { Tabs, Radio, Space } from 'antd';

const PositionSizeTabs: React.FC = () => {
  const [position, setPosition] = useState<'left' | 'right' | 'top' | 'bottom'>('left');
  const [size, setSize] = useState<'small' | 'middle' | 'large'>('small');

  const items = [
    {
      key: '1',
      label: 'Tab 1',
      children: 'Content of Tab Pane 1',
    },
    {
      key: '2',
      label: 'Tab 2',
      children: 'Content of Tab Pane 2',
    },
    {
      key: '3',
      label: 'Tab 3',
      children: 'Content of Tab Pane 3',
    },
  ];

  return (
    <Space direction="vertical" size="large">
      <Radio.Group
        value={position}
        onChange={(e) => setPosition(e.target.value)}
        style={{ marginBottom: 8 }}
      >
        <Radio.Button value="top">Top</Radio.Button>
        <Radio.Button value="bottom">Bottom</Radio.Button>
        <Radio.Button value="left">Left</Radio.Button>
        <Radio.Button value="right">Right</Radio.Button>
      </Radio.Group>

      <Radio.Group
        value={size}
        onChange={(e) => setSize(e.target.value)}
        style={{ marginBottom: 8 }}
      >
        <Radio.Button value="small">Small</Radio.Button>
        <Radio.Button value="middle">Middle</Radio.Button>
        <Radio.Button value="large">Large</Radio.Button>
      </Radio.Group>

      <Tabs
        tabPosition={position}
        size={size}
        items={items}
      />
    </Space>
  );
};

export default PositionSizeTabs;
```

---

## Tag 标签组件

### 基础标签

Tag 用于展示标签和分类信息。

**核心属性：**

```typescript
interface TagProps {
  closable?: boolean;                  // 是否可关闭
  closeIcon?: ReactNode;               // 自定义关闭图标
  color?: string | PresetColorType;    // 颜色
  icon?: ReactNode;                    // 图标
  visible?: boolean;                   // 是否显示
  onClose?: (e: React.MouseEvent<HTMLElement>) => void; // 关闭回调
  style?: React.CSSProperties;         // 自定义样式
  className?: string;                  // 自定义类名
}
```

**示例 26：基础标签**

```tsx
import React, { useState } from 'react';
import { Tag, Space, Divider } from 'antd';
import { CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';

const BasicTag: React.FC = () => {
  const log = (e: React.MouseEvent<HTMLElement>) => {
    console.log(e);
  };

  const preventDefault = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();
    console.log('Clicked! But prevent default.');
  };

  return (
    <Space direction="vertical" size="middle">
      <Space size="middle">
        <Tag>Tag 1</Tag>
        <Tag>
          <a href="https://github.com/ant-design/ant-design/issues/1862">Link</a>
        </Tag>
        <Tag closable onClose={log}>
          Tag 2
        </Tag>
        <Tag closable onClose={preventDefault}>
          Prevent Default
        </Tag>
      </Space>

      <Divider />

      <Space size="middle">
        <Tag color="magenta">magenta</Tag>
        <Tag color="red">red</Tag>
        <Tag color="volcano">volcano</Tag>
        <Tag color="orange">orange</Tag>
        <Tag color="gold">gold</Tag>
        <Tag color="lime">lime</Tag>
        <Tag color="green">green</Tag>
        <Tag color="cyan">cyan</Tag>
        <Tag color="blue">blue</Tag>
        <Tag color="geekblue">geekblue</Tag>
        <Tag color="purple">purple</Tag>
      </Space>
    </Space>
  );
};

export default BasicTag;
```

### 彩色标签

通过 `color` 属性设置不同颜色。

**示例 27：预设颜色和自定义颜色标签**

```tsx
import React from 'react';
import { Tag, Space, Divider } from 'antd';

const ColorTag: React.FC = () => {
  const presetColors = [
    'magenta',
    'red',
    'volcano',
    'orange',
    'gold',
    'lime',
    'green',
    'cyan',
    'blue',
    'geekblue',
    'purple',
  ] as const;

  const customColors = [
    '#f50',
    '#2db7f5',
    '#87d068',
    '#108ee9',
  ];

  return (
    <Space direction="vertical" size="middle">
      <div>
        <Divider orientation="left">Preset Colors</Divider>
        <Space size="middle">
          {presetColors.map((color) => (
            <Tag key={color} color={color}>
              {color}
            </Tag>
          ))}
        </Space>
      </div>

      <div>
        <Divider orientation="left">Custom Colors</Divider>
        <Space size="middle">
          {customColors.map((color) => (
            <Tag key={color} color={color}>
              {color}
            </Tag>
          ))}
        </Space>
      </div>
    </Space>
  );
};

export default ColorTag;
```

### 热门标签

通过不同颜色和状态展示标签热度。

**示例 28：热门标签（动态添加）**

```tsx
import React, { useState } from 'react';
import { Tag, Space, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const HotTag: React.FC = () => {
  const [tags, setTags] = useState([
    'Movies',
    'Books',
    'Music',
    'Sports',
  ]);
  const [inputVisible, setInputVisible] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [editInputIndex, setEditInputIndex] = useState(-1);
  const [editInputValue, setEditInputValue] = useState('');

  const handleClose = (removedTag: string) => {
    const newTags = tags.filter((tag) => tag !== removedTag);
    setTags(newTags);
  };

  const showInput = () => {
    setInputVisible(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleInputConfirm = () => {
    if (inputValue && tags.indexOf(inputValue) === -1) {
      setTags([...tags, inputValue]);
    }
    setInputVisible(false);
    setInputValue('');
  };

  const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditInputValue(e.target.value);
  };

  const handleEditInputConfirm = () => {
    const newTags = [...tags];
    newTags[editInputIndex] = editInputValue;
    setTags(newTags);
    setEditInputIndex(-1);
    setEditInputValue('');
  };

  return (
    <Space size="middle" wrap>
      {tags.map((tag, index) => {
        if (editInputIndex === index) {
          return (
            <input
              key={tag}
              size="small"
              className="tag-input"
              value={editInputValue}
              onChange={handleEditInputChange}
              onBlur={handleEditInputConfirm}
              onPressEnter={handleEditInputConfirm}
            />
          );
        }

        const isLongTag = tag.length > 20;

        const tagElem = (
          <Tag
            key={tag}
            closable={index !== 0}
            onClose={() => handleClose(tag)}
          >
            {isLongTag ? `${tag.slice(0, 20)}...` : tag}
          </Tag>
        );

        return isLongTag ? (
          <span key={tag} title={tag}>
            {tagElem}
          </span>
        ) : (
          tagElem
        );
      })}
      {inputVisible && (
        <input
          type="text"
          size="small"
          className="tag-input"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputConfirm}
          onPressEnter={handleInputConfirm}
        />
      )}
      {!inputVisible && (
        <Tag className="site-tag-plus" onClick={showInput}>
          <PlusOutlined /> New Tag
        </Tag>
      )}
    </Space>
  );
};

export default HotTag;
```

### 动态添加删除

完整的状态管理示例，支持动态添加和编辑标签。

**示例 29：完整标签管理系统**

```tsx
import React, { useState, useRef, useEffect } from 'react';
import { Tag, Space, Input, Button, message } from 'antd';
import { PlusOutlined, CloseOutlined } from '@ant-design/icons';

interface TagManagerProps {
  initialTags?: string[];
  maxTags?: number;
  onChange?: (tags: string[]) => void;
}

const TagManager: React.FC<TagManagerProps> = ({
  initialTags = [],
  maxTags = 10,
  onChange,
}) => {
  const [tags, setTags] = useState<string[]>(initialTags);
  const [inputVisible, setInputVisible] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<Input>(null);

  useEffect(() => {
    if (inputVisible) {
      inputRef.current?.focus();
    }
  }, [inputVisible]);

  const handleClose = (removedTag: string) => {
    const newTags = tags.filter((tag) => tag !== removedTag);
    setTags(newTags);
    onChange?.(newTags);
  };

  const showInput = () => {
    if (tags.length >= maxTags) {
      message.warning(`Maximum ${maxTags} tags allowed`);
      return;
    }
    setInputVisible(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleInputConfirm = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !tags.includes(trimmedValue)) {
      if (tags.length >= maxTags) {
        message.warning(`Maximum ${maxTags} tags allowed`);
        setInputVisible(false);
        setInputValue('');
        return;
      }
      const newTags = [...tags, trimmedValue];
      setTags(newTags);
      onChange?.(newTags);
    } else if (tags.includes(trimmedValue)) {
      message.warning('Tag already exists');
    }
    setInputVisible(false);
    setInputValue('');
  };

  const handleInputBlur = () => {
    handleInputConfirm();
  };

  return (
    <Space size="middle" wrap>
      <Space size="small" wrap>
        {tags.map((tag) => (
          <Tag
            key={tag}
            closable
            onClose={(e) => {
              e.preventDefault();
              handleClose(tag);
            }}
            closeIcon={<CloseOutlined style={{ fontSize: 10 }} />}
          >
            {tag}
          </Tag>
        ))}
      </Space>
      {inputVisible ? (
        <Input
          ref={inputRef}
          type="text"
          size="small"
          style={{ width: 78 }}
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onPressEnter={handleInputConfirm}
          placeholder="Add tag"
        />
      ) : (
        <Tag
          onClick={showInput}
          style={{ borderStyle: 'dashed', cursor: 'pointer' }}
        >
          <PlusOutlined /> Add Tag
        </Tag>
      )}
      <span style={{ color: '#999' }}>{tags.length}/{maxTags}</span>
    </Space>
  );
};

export default TagManager;
```

### 控制标签颜色

根据业务逻辑动态设置标签颜色。

**示例 30：状态标签（根据值设置颜色）**

```tsx
import React from 'react';
import { Tag, Space } from 'antd';
import { CheckCircleOutlined, SyncOutlined, CloseCircleOutlined } from '@ant-design/icons';

type Status = 'success' | 'processing' | 'error' | 'warning' | 'default';

interface StatusConfig {
  color: string;
  icon: React.ReactNode;
  text: string;
}

const statusConfigMap: Record<Status, StatusConfig> = {
  success: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: 'Success',
  },
  processing: {
    color: 'processing',
    icon: <SyncOutlined spin />,
    text: 'Processing',
  },
  error: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    text: 'Error',
  },
  warning: {
    color: 'warning',
    icon: <CloseCircleOutlined />,
    text: 'Warning',
  },
  default: {
    color: 'default',
    icon: null,
    text: 'Default',
  },
};

interface StatusTagProps {
  status: Status;
  text?: string;
}

const StatusTag: React.FC<StatusTagProps> = ({ status, text }) => {
  const config = statusConfigMap[status];

  return (
    <Tag
      color={config.color}
      icon={config.icon}
    >
      {text || config.text}
    </Tag>
  );
};

const ControlledColorTag: React.FC = () => {
  return (
    <Space direction="vertical" size="middle">
      <Space>
        <StatusTag status="success" />
        <StatusTag status="processing" />
        <StatusTag status="error" />
        <StatusTag status="warning" />
        <StatusTag status="default" />
      </Space>

      <Space>
        <StatusTag status="success" text="Completed" />
        <StatusTag status="processing" text="In Progress" />
        <StatusTag status="error" text="Failed" />
        <StatusTag status="warning" text="Warning" />
        <StatusTag status="default" text="Unknown" />
      </Space>
    </Space>
  );
};

export default ControlledColorTag;
```

---

## Badge 徽标组件

### 基础徽标

Badge 用于显示通知数量或状态标记。

**核心属性：**

```typescript
interface BadgeProps {
  count?: ReactNode;                   // 显示的数字
  color?: string;                      // 颜色
  dot?: boolean;                       // 是否显示为小红点
  offset?: [number, number];           // 设置徽标的偏移量 [x, y]
  overflowCount?: number;              // 数字封顶值
  showZero?: boolean;                  // 当数字为 0 时，是否显示 Badge
  size?: 'default' | 'small';          // 大小
  status?: 'success' | 'processing' | 'default' | 'error' | 'warning'; // 状态点
  text?: ReactNode;                    // 在 status 为文本时展示
  title?: string;                      // 鼠标悬停显示的文本
}
```

**示例 31：基础徽标**

```tsx
import React from 'react';
import { Badge, Button, Space, Typography } from 'antd';

const { Text } = Typography;

const BasicBadge: React.FC = () => {
  return (
    <Space direction="vertical" size="large">
      <Space>
        <Badge count={5}>
          <Button>Default</Button>
        </Badge>
        <Badge count={0} showZero>
          <Button>Zero</Button>
        </Badge>
        <Badge count={<span className="head-example"></span>}>
          <Button>Custom</Button>
        </Badge>
      </Space>

      <Space>
        <Badge dot>
          <Button>Dot only</Button>
        </Badge>
        <Badge count={0} dot>
          <Button>Dot with zero</Button>
        </Badge>
      </Space>

      <Space>
        <Badge count={99}>
          <Button>Max</Button>
        </Badge>
        <Badge count={100}>
          <Button>Max +</Button>
        </Badge>
        <Badge count={1000} overflowCount={999}>
          <Button>Custom Overflow</Button>
        </Badge>
      </Space>
    </Space>
  );
};

export default BasicBadge;
```

### 独立徽标

不包裹任何元素的独立 Badge。

**示例 32：独立徽标（无包裹元素）**

```tsx
import React from 'react';
import { Badge, Space } from 'antd';

const StandaloneBadge: React.FC = () => {
  return (
    <Space direction="vertical" size="large">
      <Space>
        <Badge count={25} />
        <Badge count={100} overflowCount={99} />
        <Badge count={1000} overflowCount={999} />
      </Space>
    </Space>
  );
};

export default StandaloneBadge;
```

### 状态点

通过 `status` 属性显示不同颜色的状态点。

**示例 33：状态点徽标**

```tsx
import React from 'react';
import { Badge, Space, Card, Descriptions, Divider } from 'antd';

const StatusDotBadge: React.FC = () => {
  return (
    <Space direction="vertical" size="large">
      <Space>
        <Badge status="success" text="Success" />
        <Badge status="error" text="Error" />
        <Badge status="default" text="Default" />
        <Badge status="processing" text="Processing" />
        <Badge status="warning" text="Warning" />
      </Space>

      <Divider />

      <Card title="Status Points">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Badge status="success" />
            <span>Success status</span>
          </Space>
          <Space>
            <Badge status="error" />
            <span>Error status</span>
          </Space>
          <Space>
            <Badge status="default" />
            <span>Default status</span>
          </Space>
          <Space>
            <Badge status="processing" />
            <span>Processing status</span>
          </Space>
          <Space>
            <Badge status="warning" />
            <span>Warning status</span>
          </Space>
        </Space>
      </Card>
    </Space>
  );
};

export default StatusDotBadge;
```

### 动态徽标

动态更新数字的 Badge。

**示例 34：动态徽标（通知系统）**

```tsx
import React, { useState, useEffect } from 'react';
import { Badge, Button, Space, Dropdown, message, Tooltip } from 'antd';
import { BellOutlined, CheckOutlined, ClearOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';

interface Notification {
  id: number;
  title: string;
  content: string;
  read: boolean;
}

const DynamicBadge: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([
    { id: 1, title: 'New Message', content: 'You have a new message', read: false },
    { id: 2, title: 'Update Available', content: 'A new version is available', read: false },
    { id: 3, title: 'Reminder', content: 'Meeting in 30 minutes', read: false },
  ]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    message.success('All notifications marked as read');
  };

  const clearAll = () => {
    setNotifications([]);
    message.success('All notifications cleared');
  };

  const notificationMenuItems: MenuProps['items'] = [
    {
      key: 'notifications',
      label: (
        <div style={{ width: 300, maxHeight: 400, overflow: 'auto' }}>
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {notifications.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                No notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  style={{
                    padding: '8px 12px',
                    background: notification.read ? 'transparent' : '#f0f0f0',
                    borderRadius: 4,
                  }}
                >
                  <div style={{ fontWeight: notification.read ? 'normal' : 'bold' }}>
                    {notification.title}
                  </div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    {notification.content}
                  </div>
                </div>
              ))
            )}
          </Space>
        </div>
      ),
    },
    {
      type: 'divider',
    },
    {
      key: 'mark-read',
      label: 'Mark all as read',
      icon: <CheckOutlined />,
      onClick: markAllAsRead,
      disabled: unreadCount === 0,
    },
    {
      key: 'clear',
      label: 'Clear all',
      icon: <ClearOutlined />,
      onClick: clearAll,
      disabled: notifications.length === 0,
    },
  ];

  return (
    <Space>
      <Dropdown menu={{ items: notificationMenuItems }} trigger={['click']}>
        <Badge count={unreadCount} overflowCount={99} offset={[-5, 5]}>
          <Tooltip title="Notifications">
            <Button type="text" icon={<BellOutlined />} />
          </Tooltip>
        </Badge>
      </Dropdown>

      <Button
        size="small"
        onClick={() => {
          const newNotification: Notification = {
            id: Date.now(),
            title: 'New Notification',
            content: `New notification at ${new Date().toLocaleTimeString()}`,
            read: false,
          };
          setNotifications((prev) => [...prev, newNotification]);
          message.info('New notification added');
        }}
      >
        Add Notification
      </Button>
    </Space>
  );
};

export default DynamicBadge;
```

---

## 最佳实践

### ✅ 推荐做法

1. **大数据量场景使用虚拟滚动**
   - ✅ 使用 `List` 组件的虚拟滚动或 rc-virtual-list
   - ✅ 分页加载数据，避免一次性加载全部

2. **合理使用响应式布局**
   - ✅ 使用 `List` 的 `grid` 属性实现响应式列表
   - ✅ 使用 `Descriptions` 的 `column` 属性适配不同屏幕

3. **性能优化**
   - ✅ 使用 `React.memo` 优化列表项渲染
   - ✅ 复杂列表项使用虚拟滚动
   - ✅ 图片懒加载

4. **无障碍访问**
   - ✅ 为交互元素提供 `aria-label`
   - ✅ 确保键盘导航可用
   - ✅ 状态变化提供足够反馈

### ❌ 避免的做法

1. **避免在循环中创建复杂组件**
   ```tsx
   // ❌ 错误：每次渲染都创建新的函数
   <List
     dataSource={data}
     renderItem={(item) => (
       <List.Item
         onClick={() => handleClick(item)} // 每次渲染创建新函数
       >
         {item.name}
       </List.Item>
     )}
   />

   // ✅ 正确：使用 useCallback 缓存函数
   const handleClick = useCallback((item) => {
     console.log(item);
   }, []);

   <List
     dataSource={data}
     renderItem={(item) => (
       <List.Item
         onClick={() => handleClick(item)}
       >
         {item.name}
       </List.Item>
     )}
   />
   ```

2. **避免滥用内联样式**
   ```tsx
   // ❌ 错误：大量内联样式
   <Card style={{ width: 300, marginBottom: 16, background: '#fff', borderRadius: 8 }}>
     {content}
   </Card>

   // ✅ 正确：使用 className 和 CSS
   <Card className="my-card">
     {content}
   </Card>
   ```

3. **避免在渲染中进行复杂计算**
   ```tsx
   // ❌ 错误：每次渲染都进行复杂计算
   const List = () => {
     const data = heavyComputation(rawData); // 复杂计算
     return <div>{data.map(...)}</div>;
   };

   // ✅ 正确：使用 useMemo 缓存结果
   const List = () => {
     const data = useMemo(() => heavyComputation(rawData), [rawData]);
     return <div>{data.map(...)}</div>;
   };
   ```

4. **避免过深的组件嵌套**
   ```tsx
   // ❌ 错误：过深的嵌套影响性能
   <Card>
     <List>
       <List.Item>
         <Descriptions>
           <Descriptions.Item>
             <Tree>...</Tree>
           </Descriptions.Item>
         </Descriptions>
       </List.Item>
     </List>
   </Card>

   // ✅ 正确：扁平化组件结构
   <Card>
     <CustomList data={data} />
   </Card>
   ```

---

## 常见问题

### Q1: List 组件如何实现无限滚动？

**A**: 使用 `loadMore` 属性配合滚动事件：

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { List, Spin } from 'antd';

const InfiniteScrollList: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    setLoading(true);
    // 模拟 API 调用
    const newData = await fetchData();
    setData([...data, ...newData]);
    setLoading(false);
    setHasMore(newData.length > 0);
  };

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container || loading) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    if (scrollHeight - scrollTop - clientHeight < 100 && hasMore) {
      loadData();
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      style={{ height: 400, overflow: 'auto' }}
    >
      <List dataSource={data} renderItem={(item) => <List.Item>{item.name}</List.Item>} />
      {loading && <Spin />}
    </div>
  );
};
```

### Q2: Card 如何实现响应式布局？

**A**: 使用 Grid 栅格系统：

```tsx
<Row gutter={[16, 16]}>
  <Col xs={24} sm={12} md={8} lg={6}>
    <Card>Content</Card>
  </Col>
  <Col xs={24} sm={12} md={8} lg={6}>
    <Card>Content</Card>
  </Col>
</Row>
```

### Q3: Tree 组件如何获取选中节点的完整路径？

**A**: 递归查找父节点：

```tsx
const findNodePath = (tree: DataNode[], key: string, path: string[] = []): string[] => {
  for (const node of tree) {
    const currentPath = [...path, node.key as string];
    if (node.key === key) {
      return currentPath;
    }
    if (node.children) {
      const childPath = findNodePath(node.children, key, currentPath);
      if (childPath.length > 0) {
        return childPath;
      }
    }
  }
  return [];
};
```

### Q4: Tabs 如何集成路由？

**A**: 使用 `activeKey` 和 `onChange` 配合路由：

```tsx
import { Tabs } from 'antd';
import { useRouter, usePathname } from 'next/navigation';

const RouteTabs: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();

  const items = [
    { key: '/tab1', label: 'Tab 1', children: 'Content 1' },
    { key: '/tab2', label: 'Tab 2', children: 'Content 2' },
  ];

  const handleTabChange = (key: string) => {
    router.push(key);
  };

  return (
    <Tabs
      activeKey={pathname}
      onChange={handleTabChange}
      items={items}
    />
  );
};
```

### Q5: Tag 组件如何限制最大数量？

**A**: 显示前 N 个，多余的折叠：

```tsx
const MAX_VISIBLE = 3;

const LimitedTags: React.FC<{ tags: string[] }> = ({ tags }) => {
  const visibleTags = tags.slice(0, MAX_VISIBLE);
  const remainingCount = tags.length - MAX_VISIBLE;

  return (
    <Space size="small">
      {visibleTags.map((tag) => (
        <Tag key={tag}>{tag}</Tag>
      ))}
      {remainingCount > 0 && <Tag>+{remainingCount}</Tag>}
    </Space>
  );
};
```

### Q6: Badge 如何自定义样式？

**A**: 使用 `style` 和 `className`：

```tsx
<Badge
  count={5}
  style={{
    backgroundColor: '#52c41a',
    boxShadow: '0 0 0 1px #d9d9d9 inset',
  }}
>
  <Button>Custom Style</Button>
</Badge>
```

### Q7: 如何实现可编辑的 Tree？

**A**: 在节点数据中添加编辑状态，使用 Modal 或 Input 编辑：

```tsx
const [treeData, setTreeData] = useState<DataNode[]>(initialData);
const [editingKey, setEditingKey] = useState<string | null>(null);

const handleEdit = (key: string) => {
  setEditingKey(key);
};

const handleSave = (key: string, newTitle: string) => {
  const updateTree = (nodes: DataNode[]): DataNode[] => {
    return nodes.map((node) => {
      if (node.key === key) {
        return { ...node, title: newTitle };
      }
      if (node.children) {
        return { ...node, children: updateTree(node.children) };
      }
      return node;
    });
  };

  setTreeData(updateTree(treeData));
  setEditingKey(null);
};
```

### Q8: List 如何实现虚拟滚动？

**A**: 使用 `rc-virtual-list`：

```tsx
import VirtualList from 'rc-virtual-list';

const VirtualScrollList: React.FC = () => {
  const [data, setData] = useState<any[]>([]);

  return (
    <div style={{ height: 400 }}>
      <VirtualList
        data={data}
        height={400}
        itemHeight={47}
        itemKey="id"
      >
        {(item) => (
          <List.Item key={item.id}>
            {item.name}
          </List.Item>
        )}
      </VirtualList>
    </div>
  );
};
```

---

## 参考资源

### 官方文档
- [Ant Design - List](https://ant.design/components/list-cn/)
- [Ant Design - Card](https://ant.design/components/card-cn/)
- [Ant Design - Descriptions](https://ant.design/components/descriptions-cn/)
- [Ant Design - Tree](https://ant.design/components/tree-cn/)
- [Ant Design - Tabs](https://ant.design/components/tabs-cn/)
- [Ant Design - Tag](https://ant.design/components/tag-cn/)
- [Ant Design - Badge](https://ant.design/components/badge-cn/)

### 相关文档
- [antd-data-display-skills](../antd-data-display-skills/SKILL.md) - 数据展示完整指南
- [antd-table-skills](../antd-table-skills/SKILL.md) - 表格高级用法
- [antd-form-skills](../antd-form-skills/SKILL.md) - 表单集成

### 扩展阅读
- [React 虚拟滚动最佳实践](https://react.dev/learn/render-and-commit#conditional-rendering)
- [性能优化指南](../antd-performance-skills/SKILL.md)
- [无障碍访问指南](../antd-accessibility-skills/SKILL.md)

---

**维护者**: Claude Code & LazyGophers Community
**最后更新**: 2026-02-10
