---
name: antd-chart-skills
description: Ant Design 图表集成完整指南 - @ant-design/charts、折线图、柱状图、饼图、配置项、交互
---

# Ant Design Charts 完整集成指南

## Overview

`@ant-design/charts` 是基于 Ant Design 设计语言和 G2Plot 封装的 React 图表库，提供了一系列开箱即用的高质量图表组件。该库完美融合了 Ant Design 的设计理念和 G2Plot 的强大能力，为开发者提供了一套完整的可视化解决方案。

## 核心特性

- **设计语言统一**: 遵循 Ant Design 设计规范，与 antd 组件完美融合
- **开箱即用**: 提供合理的默认配置和最佳实践
- **响应式设计**: 自动适配容器尺寸变化
- **丰富的图表类型**: 支持 20+ 种图表类型
- **高性能渲染**: 基于 Canvas/G 渲染，支持大数据量可视化
- **交互能力**: 内置丰富的交互功能（缩放、刷选、联动等）
- **无障碍支持**: 完善的键盘导航和屏幕阅读器支持
- **TypeScript 支持**: 完整的类型定义

## 安装与配置

### 1. 安装依赖

```bash
# 使用 npm
npm install @ant-design/charts --save

# 使用 yarn
yarn add @ant-design/charts

# 使用 pnpm
pnpm add @ant-design/charts
```

### 2. 基本导入

```typescript
// 导入单个图表组件
import { Line, Column, Pie, Area, Scatter, Bar } from '@ant-design/charts';

// 导入所有图表组件
import * as Charts from '@ant-design/charts';

// 导入类型定义
import type {
  LineConfig,
  ColumnConfig,
  PieConfig,
  DataItem,
} from '@ant-design/charts';
```

### 3. 依赖版本要求

```json
{
  "dependencies": {
    "@ant-design/charts": "^2.0.0",
    "react": ">=16.9.0",
    "antd": ">=5.0.0"
  }
}
```

## 图表类型总览

### 折线图系列

| 图表类型 | 组件名 | 适用场景 |
|---------|--------|----------|
| 折线图 | `Line` | 趋势分析、时间序列数据 |
| 面积图 | `Area` | 显示累积趋势、突出总量 |
| 多折线图 | `Line` (多系列) | 多维度对比 |
| 阶梯折线图 | `Line` (stepType) | 阶段性变化数据 |

### 柱状图系列

| 图表类型 | 组件名 | 适用场景 |
|---------|--------|----------|
| 柱状图 | `Column` | 分类数据对比 |
| 条形图 | `Bar` | 长标签名分类数据 |
| 堆叠柱状图 | `Column` (stack) | 组成部分分析 |
| 分组柱状图 | `Column` (group) | 多维度对比 |
| 百分比堆叠图 | `Column` (stack+normalized) | 占比分析 |

### 饼图系列

| 图表类型 | 组件名 | 适用场景 |
|---------|--------|----------|
| 饼图 | `Pie` | 占比分析、部分与整体关系 |
| 环形图 | `Pie` (innerRadius) | 中心信息展示 |
| 玫瑰图 | `Rose` | 分类数据大小对比 |
| 饼图对比 | `Pie` (多系列) | 多维度占比对比 |

### 散点图与气泡图

| 图表类型 | 组件名 | 适用场景 |
|---------|--------|----------|
| 散点图 | `Scatter` | 相关性分析、分布分析 |
| 气泡图 | `Scatter` (size字段) | 三维数据展示 |
| 四象限图 | `Scatter` (参考线) | 数据分类分析 |

### 其他图表类型

| 图表类型 | 组件名 | 适用场景 |
|---------|--------|----------|
| 双轴图 | `DualAxes` | 多度量对比 |
| 混合图表 | `Mix` | 多图表类型组合 |
| 仪表盘 | `Gauge` | KPI 指标展示 |
| 漏斗图 | `Funnel` | 转化率分析 |
| 水波图 | `Liquid` | 进度/占比展示 |
| 热力图 | `Heatmap` | 二维数据分布 |
| 箱线图 | `Box` | 统计分布分析 |
| 直方图 | `Histogram` | 频率分布 |

## 折线图 (Line)

### 基础折线图

```typescript
import React from 'react';
import { Line } from '@ant-design/charts';
import type { LineConfig } from '@ant-design/charts';

const data = [
  { year: '2018', value: 300 },
  { year: '2019', value: 450 },
  { year: '2020', value: 400 },
  { year: '2021', value: 550 },
  { year: '2022', value: 600 },
  { year: '2023', value: 750 },
];

const BasicLine: React.FC = () => {
  const config: LineConfig = {
    data,
    xField: 'year',
    yField: 'value',
    width: 800,
    height: 400,
    autoFit: true,
    point: {
      size: 5,
      shape: 'circle',
    },
    smooth: true,
  };

  return <Line {...config} />;
};

export default BasicLine;
```

### 多折线图

```typescript
import React from 'react';
import { Line } from '@ant-design/charts';

const data = [
  { date: '2023-01', type: 'Sales', value: 350 },
  { date: '2023-01', type: 'Profit', value: 120 },
  { date: '2023-02', type: 'Sales', value: 420 },
  { date: '2023-02', type: 'Profit', value: 150 },
  { date: '2023-03', type: 'Sales', value: 380 },
  { date: '2023-03', type: 'Profit', value: 135 },
  { date: '2023-04', type: 'Sales', value: 500 },
  { date: '2023-04', type: 'Profit', value: 180 },
  { date: '2023-05', type: 'Sales', value: 470 },
  { date: '2023-05', type: 'Profit', value: 165 },
];

const MultiLineChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    yAxis: {
      label: {
        formatter: (v: string) => `$${v}k`,
      },
    },
    legend: {
      position: 'top',
    },
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  return <Line {...config} />;
};

export default MultiLineChart;
```

### 面积图

```typescript
import React from 'react';
import { Area } from '@ant-design/charts';

const data = [
  { date: '2023-01', value: 300 },
  { date: '2023-02', value: 450 },
  { date: '2023-03', value: 400 },
  { date: '2023-04', value: 550 },
  { date: '2023-05', value: 600 },
  { date: '2023-06', value: 700 },
];

const AreaChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    smooth: true,
    areaStyle: {
      fillOpacity: 0.6,
    },
    point: {
      size: 3,
    },
  };

  return <Area {...config} />;
};

export default AreaChart;
```

### 阶梯折线图

```typescript
import React from 'react';
import { Line } from '@ant-design/charts';

const StepLineChart: React.FC = () => {
  const data = [
    { stage: 'Start', value: 0 },
    { stage: 'Design', value: 20 },
    { stage: 'Development', value: 20 },
    { stage: 'Testing', value: 60 },
    { stage: 'Deploy', value: 60 },
    { stage: 'Complete', value: 100 },
  ];

  const config = {
    data,
    xField: 'stage',
    yField: 'value',
    stepType: 'vh', // 'vh' | 'hv' | 'hvh'
    lineStyle: {
      lineWidth: 3,
    },
  };

  return <Line {...config} />;
};

export default StepLineChart;
```

## 柱状图 (Column)

### 基础柱状图

```typescript
import React from 'react';
import { Column } from '@ant-design/charts';

const data = [
  { category: 'Electronics', value: 450 },
  { category: 'Clothing', value: 320 },
  { category: 'Books', value: 280 },
  { category: 'Food', value: 390 },
  { category: 'Toys', value: 210 },
];

const BasicColumn: React.FC = () => {
  const config = {
    data,
    xField: 'category',
    yField: 'value',
    label: {
      position: 'top' as const,
      style: {
        fill: '#000',
        opacity: 0.6,
      },
    },
    meta: {
      category: {
        alias: 'Category',
      },
      value: {
        alias: 'Sales ($)',
      },
    },
  };

  return <Column {...config} />;
};

export default BasicColumn;
```

### 堆叠柱状图

```typescript
import React from 'react';
import { Column } from '@ant-design/charts';

const data = [
  { month: 'Jan', type: 'Online', value: 350 },
  { month: 'Jan', type: 'Retail', value: 220 },
  { month: 'Feb', type: 'Online', value: 420 },
  { month: 'Feb', type: 'Retail', value: 280 },
  { month: 'Mar', type: 'Online', value: 380 },
  { month: 'Mar', type: 'Retail', value: 250 },
];

const StackedColumn: React.FC = () => {
  const config = {
    data,
    xField: 'month',
    yField: 'value',
    seriesField: 'type',
    isStack: true,
    label: {
      position: 'middle' as const,
      style: {
        fill: '#FFF',
      },
    },
  };

  return <Column {...config} />;
};

export default StackedColumn;
```

### 分组柱状图

```typescript
import React from 'react';
import { Column } from '@ant-design/charts';

const data = [
  { quarter: 'Q1', product: 'A', sales: 350 },
  { quarter: 'Q1', product: 'B', sales: 280 },
  { quarter: 'Q2', product: 'A', sales: 420 },
  { quarter: 'Q2', product: 'B', sales: 350 },
  { quarter: 'Q3', product: 'A', sales: 380 },
  { quarter: 'Q3', product: 'B', sales: 310 },
  { quarter: 'Q4', product: 'A', sales: 520 },
  { quarter: 'Q4', product: 'B', sales: 420 },
];

const GroupedColumn: React.FC = () => {
  const config = {
    data,
    xField: 'quarter',
    yField: 'sales',
    seriesField: 'product',
    groupField: 'quarter',
    label: {
      position: 'top' as const,
    },
  };

  return <Column {...config} />;
};

export default GroupedColumn;
```

### 条形图 (横向柱状图)

```typescript
import React from 'react';
import { Bar } from '@ant-design/charts';

const data = [
  { product: 'Product A', value: 450 },
  { product: 'Product B', value: 320 },
  { product: 'Product C', value: 550 },
  { product: 'Product D', value: 280 },
  { product: 'Product E', value: 410 },
];

const BarChart: React.FC = () => {
  const config = {
    data,
    xField: 'value',
    yField: 'product',
    seriesField: 'product',
    label: {
      position: 'right' as const,
      offset: 4,
    },
  };

  return <Bar {...config} />;
};

export default BarChart;
```

## 饼图 (Pie)

### 基础饼图

```typescript
import React from 'react';
import { Pie } from '@ant-design/charts';

const data = [
  { type: 'Electronics', value: 450 },
  { type: 'Clothing', value: 320 },
  { type: 'Books', value: 280 },
  { type: 'Food', value: 390 },
  { type: 'Toys', value: 210 },
];

const BasicPie: React.FC = () => {
  const config = {
    data,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer' as const,
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'element-active',
      },
      {
        type: 'element-selected',
      },
    ],
  };

  return <Pie {...config} />;
};

export default BasicPie;
```

### 环形图

```typescript
import React from 'react';
import { Pie } from '@ant-design/charts';

const DonutChart: React.FC = () => {
  const data = [
    { category: 'Completed', value: 65 },
    { category: 'In Progress', value: 25 },
    { category: 'Pending', value: 10 },
  ];

  const config = {
    data,
    angleField: 'value',
    colorField: 'category',
    innerRadius: 0.6,
    label: {
      type: 'inner' as const,
      offset: '-50%',
      content: '{value}',
      style: {
        fontSize: 20,
        textAlign: 'center' as const,
      },
    },
    legend: {
      position: 'bottom' as const,
    },
    statistic: {
      title: {
        offsetY: -8,
        content: 'Total Tasks',
        style: {
          fontSize: '14px',
        },
      },
      content: {
        offsetY: 4,
        style: {
          fontSize: '24px',
        },
        content: '100',
      },
    },
  };

  return <Pie {...config} />;
};

export default DonutChart;
```

### 玫瑰图

```typescript
import React from 'react';
import { Rose } from '@ant-design/charts';

const RoseChart: React.FC = () => {
  const data = [
    { category: 'A', value: 450 },
    { category: 'B', value: 320 },
    { category: 'C', value: 280 },
    { category: 'D', value: 390 },
    { category: 'E', value: 210 },
    { category: 'F', value: 360 },
    { category: 'G', value: 290 },
  ];

  const config = {
    data,
    xField: 'category',
    yField: 'value',
    seriesField: 'category',
    radius: 0.9,
    label: {
      offset: -15,
    },
  };

  return <Rose {...config} />;
};

export default RoseChart;
```

## 散点图 (Scatter)

### 基础散点图

```typescript
import React from 'react';
import { Scatter } from '@ant-design/charts';

const data = [
  { x: 10, y: 20, category: 'A' },
  { x: 30, y: 40, category: 'B' },
  { x: 50, y: 35, category: 'A' },
  { x: 70, y: 60, category: 'B' },
  { x: 90, y: 80, category: 'A' },
];

const BasicScatter: React.FC = () => {
  const config = {
    data,
    xField: 'x',
    yField: 'y',
    colorField: 'category',
    size: 5,
    shape: 'circle',
    xAxis: {
      title: {
        text: 'X Axis',
      },
    },
    yAxis: {
      title: {
        text: 'Y Axis',
      },
    },
  };

  return <Scatter {...config} />;
};

export default BasicScatter;
```

### 气泡图

```typescript
import React from 'react';
import { Scatter } from '@ant-design/charts';

const BubbleChart: React.FC = () => {
  const data = [
    { x: 10, y: 20, size: 10, category: 'A' },
    { x: 30, y: 40, size: 20, category: 'B' },
    { x: 50, y: 35, size: 15, category: 'A' },
    { x: 70, y: 60, size: 25, category: 'B' },
    { x: 90, y: 80, size: 18, category: 'A' },
    { x: 60, y: 50, size: 22, category: 'C' },
  ];

  const config = {
    data,
    xField: 'x',
    yField: 'y',
    sizeField: 'size',
    colorField: 'category',
    size: [5, 20],
    shape: 'circle',
    xAxis: {
      title: {
        text: 'X Axis',
      },
    },
    yAxis: {
      title: {
        text: 'Y Axis',
      },
    },
    tooltip: {
      fields: ['x', 'y', 'size', 'category'],
    },
  };

  return <Scatter {...config} />;
};

export default BubbleChart;
```

## 高级图表

### 双轴图

```typescript
import React from 'react';
import { DualAxes } from '@ant-design/charts';

const DualAxesChart: React.FC = () => {
  const data = [
    { month: 'Jan', revenue: 350, orders: 120 },
    { month: 'Feb', revenue: 420, orders: 150 },
    { month: 'Mar', revenue: 380, orders: 135 },
    { month: 'Apr', revenue: 500, orders: 180 },
    { month: 'May', revenue: 470, orders: 165 },
  ];

  const config = {
    data: [data, data],
    xField: 'month',
    yField: ['revenue', 'orders'],
    geometryOptions: [
      {
        geometry: 'line',
        color: '#5B8FF9',
        lineStyle: {
          lineWidth: 3,
        },
        point: {
          size: 5,
        },
      },
      {
        geometry: 'column',
        color: '#5AD8A6',
        columnWidthRatio: 0.4,
      },
    ],
    yAxis: {
      revenue: {
        min: 0,
        max: 600,
        label: {
          formatter: (v: string) => `$${v}k`,
        },
      },
      orders: {
        min: 0,
        max: 200,
      },
    },
  };

  return <DualAxes {...config} />;
};

export default DualAxesChart;
```

### 仪表盘

```typescript
import React from 'react';
import { Gauge } from '@ant-design/charts';

const GaugeChart: React.FC = () => {
  const data = [
    { value: 75 },
  ];

  const config = {
    data,
    valueField: 'value',
    title: {
      visible: true,
      text: 'Performance',
    },
    range: {
      width: 30,
      color: '#30BF78',
    },
    indicator: {
      pointer: {
        style: {
          stroke: '#30BF78',
        },
      },
      pin: {
        style: {
          stroke: '#30BF78',
        },
      },
    },
    statistic: {
      content: {
        style: {
          fontSize: '36px',
          fontWeight: 'bold',
        },
        content: '75%',
      },
    },
  };

  return <Gauge {...config} />;
};

export default GaugeChart;
```

### 漏斗图

```typescript
import React from 'react';
import { Funnel } from '@ant-design/charts';

const FunnelChart: React.FC = () => {
  const data = [
    { stage: 'Visit', value: 10000 },
    { stage: 'View Product', value: 6000 },
    { stage: 'Add to Cart', value: 3000 },
    { stage: 'Checkout', value: 2000 },
    { stage: 'Purchase', value: 1500 },
  ];

  const config = {
    data,
    xField: 'stage',
    yField: 'value',
    legend: {
      position: 'bottom' as const,
    },
    label: {
      formatter: (datum: any) => {
        const percent = ((datum.value / 10000) * 100).toFixed(2);
        return `${datum.stage}: ${datum.value} (${percent}%)`;
      },
    },
  };

  return <Funnel {...config} />;
};

export default FunnelChart;
```

## 图表配置

### 通用配置项

```typescript
interface CommonConfig {
  // 数据配置
  data: Record<string, any>[];
  xField: string;
  yField: string;
  seriesField?: string;

  // 尺寸配置
  width?: number;
  height?: number;
  autoFit?: boolean; // 默认 true，自动适配容器

  // 标题配置
  title?: {
    visible?: boolean;
    text?: string;
    style?: React.CSSProperties;
  };

  // 描述配置
  description?: {
    visible?: boolean;
    text?: string;
    style?: React.CSSProperties;
  };

  // 图例配置
  legend?: {
    position?: 'top' | 'bottom' | 'left' | 'right';
    offsetX?: number;
    offsetY?: number;
    layout?: 'horizontal' | 'vertical';
  };

  // 坐标轴配置
  xAxis?: AxisConfig;
  yAxis?: AxisConfig;

  // 提示框配置
  tooltip?: TooltipConfig;

  // 标签配置
  label?: LabelConfig;

  // 主题配置
  theme?: 'default' | 'dark';

  // 动画配置
  animation?: AnimationConfig;

  // 交互配置
  interactions?: InteractionConfig[];

  // 样式配置
  style?: React.CSSProperties;
  className?: string;
}
```

### 坐标轴配置

```typescript
interface AxisConfig {
  title?: {
    text?: string;
    offset?: number;
    style?: React.CSSProperties;
  };
  label?: {
    formatter?: (value: any, index: number) => string;
    style?: React.CSSProperties;
    rotate?: number;
    offset?: number;
  };
  line?: {
    style?: React.CSSProperties;
  };
  tickLine?: {
    style?: React.CSSProperties;
    length?: number;
  };
  grid?: {
    visible?: boolean;
    style?: React.CSSProperties;
    line?: {
      style?: React.CSSProperties;
    };
  };
  min?: number;
  max?: number;
  range?: [number, number];
}
```

### Tooltip 配置

```typescript
interface TooltipConfig {
  visible?: boolean;
  fields?: string[];
  formatter?: (datum: any, data?: any[]) => {
    name?: string;
    value?: any;
  };
  showMarkers?: boolean;
  showContent?: boolean;
  offset?: number;
  enterable?: boolean;
  domStyles?: {
    'g2-tooltip'?: React.CSSProperties;
    'g2-tooltip-title'?: React.CSSProperties;
    'g2-tooltip-list'?: React.CSSProperties;
  };
}
```

### Label 配置

```typescript
interface LabelConfig {
  visible?: boolean;
  type?: 'inner' | 'outer';
  position?: 'top' | 'bottom' | 'left' | 'right' | 'middle';
  offset?: number;
  offsetX?: number;
  offsetY?: number;
  rotate?: number;
  style?: React.CSSProperties;
  formatter?: (text: string, item: any, index: number) => string;
  content?: string; // 模板字符串，如 '{name} {value}'
}
```

### 交互配置

```typescript
type InteractionType =
  | 'tooltip' // 提示框
  | 'legend-active' // 图例激活
  | 'legend-filter' // 图例筛选
  | 'element-active' // 元素激活
  | 'element-selected' // 元素选中
  | 'element-highlight' // 元素高亮
  | 'brush' // 刷选
  | 'zoom' // 缩放
  | 'pan' // 平移
  | 'sibling-filter'; // 联动筛选

interface InteractionConfig {
  type: InteractionType;
  enable?: boolean;
}
```

## 交互功能

### Tooltip 自定义

```typescript
const CustomTooltipChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    tooltip: {
      fields: ['date', 'value', 'category'],
      formatter: (datum: any) => {
        return {
          name: datum.category,
          value: `$${datum.value.toLocaleString()}`,
        };
      },
      domStyles: {
        'g2-tooltip': {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderRadius: '4px',
          padding: '8px',
        },
        'g2-tooltip-title': {
          color: '#fff',
          fontWeight: 'bold',
        },
      },
    },
  };

  return <Line {...config} />;
};
```

### 图例筛选

```typescript
const LegendFilterChart: React.FC = () => {
  const config = {
    data: multiSeriesData,
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    legend: {
      position: 'top',
    },
    interactions: [
      {
        type: 'legend-active',
        enable: true,
      },
      {
        type: 'legend-filter',
        enable: true,
      },
    ],
  };

  return <Line {...config} />;
};
```

### 元素选中

```typescript
const ElementSelectChart: React.FC = () => {
  const config = {
    data,
    xField: 'category',
    yField: 'value',
    interactions: [
      {
        type: 'element-active',
      },
      {
        type: 'element-selected',
        enable: true,
      },
    ],
    state: {
      selected: {
        style: {
          stroke: '#000',
          lineWidth: 2,
        },
      },
      active: {
        style: {
          opacity: 0.8,
        },
      },
    },
  };

  return <Column {...config} />;
};
```

### 缩放和平移

```typescript
const ZoomPanChart: React.FC = () => {
  const config = {
    data: largeDataset,
    xField: 'date',
    yField: 'value',
    interactions: [
      {
        type: 'zoom',
        enable: true,
      },
      {
        type: 'pan',
        enable: true,
      },
    ],
    scrollbar: {
      type: 'vertical' as const,
    },
  };

  return <Line {...config} />;
};
```

## 主题配置

### 内置主题

```typescript
import React from 'react';
import { Line } from '@ant-design/charts';

const ThemedChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    theme: 'default', // 或 'dark'
  };

  return <Line {...config} />;
};

// 使用 Ant Design 主题
const AntDesignThemedChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    theme: {
      colors10: [
        '#5B8FF9',
        '#5AD8A6',
        '#5D7092',
        '#F6BD16',
        '#E86452',
        '#6DC8EC',
        '#945FB9',
        '#FF9845',
        '#1E9493',
        '#FF99C3',
      ],
    },
  };

  return <Line {...config} />;
};
```

### 自定义主题

```typescript
const CustomThemeChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    theme: {
      colors10: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'],
      geometries: {
        point: {
          circle: {
            style: {
              fill: '#4ECDC4',
              stroke: '#45B7D1',
              lineWidth: 2,
            },
          },
        },
      },
    },
  };

  return <Line {...config} />;
};
```

## 数据处理

### 数据转换

```typescript
import React, { useMemo } from 'react';
import { Line } from '@ant-design/charts';

const DataTransformChart: React.FC = () => {
  // 原始数据
  const rawData = [
    { date: '2023-01-01', sales: 100, cost: 60 },
    { date: '2023-01-02', sales: 120, cost: 70 },
    { date: '2023-01-03', sales: 110, cost: 65 },
  ];

  // 数据转换
  const transformedData = useMemo(() => {
    return rawData.map(item => ({
      ...item,
      date: new Date(item.date).toLocaleDateString(),
      profit: item.sales - item.cost,
      profitMargin: ((item.sales - item.cost) / item.sales * 100).toFixed(2),
    }));
  }, [rawData]);

  const config = {
    data: transformedData,
    xField: 'date',
    yField: 'profit',
    smooth: true,
  };

  return <Line {...config} />;
};
```

### 数据聚合

```typescript
import React, { useMemo } from 'react';
import { Column } from '@ant-design/charts';

const AggregatedChart: React.FC = () => {
  const rawData = [
    { date: '2023-01', category: 'A', value: 100 },
    { date: '2023-01', category: 'B', value: 150 },
    { date: '2023-01', category: 'C', value: 120 },
    { date: '2023-02', category: 'A', value: 110 },
    { date: '2023-02', category: 'B', value: 160 },
    { date: '2023-02', category: 'C', value: 130 },
  ];

  // 按月聚合
  const aggregatedData = useMemo(() => {
    const map = new Map();

    rawData.forEach(item => {
      const existing = map.get(item.date);
      if (existing) {
        existing.value += item.value;
      } else {
        map.set(item.date, {
          date: item.date,
          value: item.value,
        });
      }
    });

    return Array.from(map.values());
  }, [rawData]);

  const config = {
    data: aggregatedData,
    xField: 'date',
    yField: 'value',
  };

  return <Column {...config} />;
};
```

## 性能优化

### 大数据量优化

```typescript
import React, { useMemo } from 'react';
import { Line } from '@ant-design/charts';

const LargeDataChart: React.FC = () => {
  // 生成大量数据
  const largeData = useMemo(() => {
    const data = [];
    for (let i = 0; i < 10000; i++) {
      data.push({
        index: i,
        value: Math.random() * 1000,
      });
    }
    return data;
  }, []);

  const config = {
    data: largeData,
    xField: 'index',
    yField: 'value',
    // 性能优化配置
    animation: false, // 禁用动画
    renderer: 'canvas', // 使用 Canvas 渲染
    tooltip: {
      showMarkers: false, // 禁用标记点
    },
    point: {
      size: 0, // 隐藏数据点
    },
  };

  return <Line {...config} />;
};
```

### 懒加载与虚拟滚动

```typescript
import React, { useState, useEffect } from 'react';
import { Line } from '@ant-design/charts';

const LazyLoadChart: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = async (page: number) => {
    setLoading(true);
    // 模拟异步数据加载
    const response = await fetch(`/api/data?page=${page}`);
    const newData = await response.json();
    setData(prev => [...prev, ...newData]);
    setLoading(false);
  };

  useEffect(() => {
    loadData(1);
  }, []);

  const config = {
    data,
    xField: 'date',
    yField: 'value',
    animation: false,
  };

  return (
    <div>
      <Line {...config} />
      <button onClick={() => loadData(Math.ceil(data.length / 100) + 1)} disabled={loading}>
        {loading ? 'Loading...' : 'Load More'}
      </button>
    </div>
  );
};
```

## 组合与联动

### 图表联动

```typescript
import React, { useState } from 'react';
import { Line, Column } from '@ant-design/charts';

const LinkedCharts: React.FC = () => {
  const [filterState, setFilterState] = useState<Record<string, any>>({});

  const handleChartClick = (info: any) => {
    setFilterState({
      category: info.data.category,
    });
  };

  const lineConfig = {
    data,
    xField: 'date',
    yField: 'value',
    seriesField: 'category',
    interactions: [
      {
        type: 'element-selected',
      },
    ],
    onReady: (chart: any) => {
      chart.on('element:click', handleChartClick);
    },
  };

  const columnConfig = {
    data: data.filter(d => !filterState.category || d.category === filterState.category),
    xField: 'date',
    yField: 'value',
  };

  return (
    <div>
      <Line {...lineConfig} />
      <Column {...columnConfig} />
    </div>
  );
};
```

### 图表组合

```typescript
import React from 'react';
import { Line, Column, Pie } from '@ant-design/charts';
import { Card, Row, Col } from 'antd';

const Dashboard: React.FC = () => {
  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title="Revenue Trend">
          <Line {...lineConfig} />
        </Card>
      </Col>
      <Col span={12}>
        <Card title="Sales by Category">
          <Column {...columnConfig} />
        </Card>
      </Col>
      <Col span={12}>
        <Card title="Market Share">
          <Pie {...pieConfig} />
        </Card>
      </Col>
    </Row>
  );
};
```

## 响应式设计

### 自适应容器

```typescript
import React from 'react';
import { Line } from '@ant-design/charts';

const ResponsiveChart: React.FC = () => {
  const config = {
    data,
    xField: 'date',
    yField: 'value',
    autoFit: true, // 自动适配容器尺寸
    width: undefined, // 不设置固定宽度
    height: 400,
  };

  return (
    <div style={{ width: '100%' }}>
      <Line {...config} />
    </div>
  );
};
```

### 响应式配置

```typescript
import React, { useEffect, useState } from 'react';
import { Line } from '@ant-design/charts';

const ResponsiveConfigChart: React.FC = () => {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    const updateConfig = () => {
      const width = window.innerWidth;
      const isMobile = width < 768;

      setConfig({
        data,
        xField: 'date',
        yField: 'value',
        legend: {
          position: isMobile ? 'bottom' : 'top',
        },
        label: {
          visible: !isMobile, // 移动端隐藏标签
        },
        height: isMobile ? 300 : 400,
      });
    };

    updateConfig();
    window.addEventListener('resize', updateConfig);
    return () => window.removeEventListener('resize', updateConfig);
  }, []);

  return <Line {...config} />;
};
```

## 完整示例

### 示例 1: 销售分析仪表板

```typescript
import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { Line, Column, Pie, DualAxes } from '@ant-design/charts';

const SalesDashboard: React.FC = () => {
  // 模拟数据
  const revenueData = [
    { month: 'Jan', value: 35000 },
    { month: 'Feb', value: 42000 },
    { month: 'Mar', value: 38000 },
    { month: 'Apr', value: 50000 },
    { month: 'May', value: 47000 },
    { month: 'Jun', value: 55000 },
  ];

  const categoryData = [
    { category: 'Electronics', value: 45000 },
    { category: 'Clothing', value: 32000 },
    { category: 'Books', value: 28000 },
    { category: 'Food', value: 39000 },
    { category: 'Toys', value: 21000 },
  ];

  const trendData = [
    { month: 'Jan', revenue: 35000, orders: 1200 },
    { month: 'Feb', revenue: 42000, orders: 1500 },
    { month: 'Mar', revenue: 38000, orders: 1350 },
    { month: 'Apr', revenue: 50000, orders: 1800 },
    { month: 'May', revenue: 47000, orders: 1650 },
    { month: 'Jun', revenue: 55000, orders: 2000 },
  ];

  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Statistic title="Total Revenue" value={267000} prefix="$" />
        </Col>
        <Col span={6}>
          <Statistic title="Total Orders" value={9500} />
        </Col>
        <Col span={6}>
          <Statistic title="Avg Order Value" value={28.1} prefix="$" />
        </Col>
        <Col span={6}>
          <Statistic title="Growth Rate" value={12.5} suffix="%" />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Revenue Trend">
            <DualAxes
              data={[trendData, trendData]}
              xField="month"
              yField={['revenue', 'orders']}
              geometryOptions={[
                { geometry: 'line', color: '#5B8FF9' },
                { geometry: 'column', color: '#5AD8A6' },
              ]}
              yAxis={{
                revenue: {
                  label: {
                    formatter: (v: string) => `$${v}k`,
                  },
                },
              }}
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Monthly Revenue">
            <Line
              data={revenueData}
              xField="month"
              yField="value"
              smooth
              point={{ size: 5 }}
              areaStyle={{ fillOpacity: 0.2 }}
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Sales by Category">
            <Column
              data={categoryData}
              xField="category"
              yField="value"
              label={{ position: 'top' }}
              meta={{
                value: {
                  formatter: (v: string) => `$${v.toLocaleString()}`,
                },
              }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SalesDashboard;
```

### 示例 2: 实时数据监控

```typescript
import React, { useState, useEffect } from 'react';
import { Card, Spin } from 'antd';
import { Line, Gauge } from '@ant-design/charts';

interface MetricData {
  timestamp: string;
  value: number;
}

const RealTimeMonitor: React.FC = () => {
  const [data, setData] = useState<MetricData[]>([]);
  const [currentValue, setCurrentValue] = useState(0);
  const [loading, setLoading] = useState(false);

  // 模拟实时数据更新
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      // 模拟 API 调用
      const newValue = Math.random() * 100;
      const timestamp = new Date().toLocaleTimeString();

      setData(prev => {
        const newData = [...prev, { timestamp, value: newValue }];
        // 只保留最近 20 条数据
        return newData.slice(-20);
      });
      setCurrentValue(newValue);
      setLoading(false);
    };

    // 初始加载
    fetchData();

    // 定时刷新
    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  const lineConfig = {
    data,
    xField: 'timestamp',
    yField: 'value',
    smooth: true,
    animation: false,
    height: 300,
  };

  const gaugeConfig = {
    data: [{ value: currentValue }],
    valueField: 'value',
    range: {
      color: currentValue > 80 ? '#F4664A' : currentValue > 50 ? '#FAAD14' : '#30BF78',
    },
    indicator: {
      pointer: {
        style: {
          stroke: currentValue > 80 ? '#F4664A' : currentValue > 50 ? '#FAAD14' : '#30BF78',
        },
      },
    },
    statistic: {
      content: {
        content: `${currentValue.toFixed(2)}%`,
        style: {
          fontSize: '24px',
          fontWeight: 'bold',
        },
      },
    },
  };

  return (
    <Row gutter={16}>
      <Col span={18}>
        <Card title="Real-time Trend" extra={<Spin spinning={loading} />}>
          <Line {...lineConfig} />
        </Card>
      </Col>
      <Col span={6}>
        <Card title="Current Value">
          <Gauge {...gaugeConfig} />
        </Card>
      </Col>
    </Row>
  );
};

export default RealTimeMonitor;
```

### 示例 3: 交互式数据探索

```typescript
import React, { useState } from 'react';
import { Card, Select, DatePicker, Space } from 'antd';
import { Line, Column, Pie } from '@ant-design/charts';

const { RangePicker } = DatePicker;

const DataExplorer: React.FC = () => {
  const [dateRange, setDateRange] = useState<any>(null);
  const [category, setCategory] = useState<string>('all');
  const [chartType, setChartType] = useState<'line' | 'column' | 'pie'>('line');

  // 模拟数据
  const allData = [
    { date: '2023-01', category: 'A', value: 350 },
    { date: '2023-02', category: 'A', value: 420 },
    { date: '2023-03', category: 'A', value: 380 },
    { date: '2023-01', category: 'B', value: 280 },
    { date: '2023-02', category: 'B', value: 320 },
    { date: '2023-03', category: 'B', value: 290 },
  ];

  // 数据过滤
  const filteredData = allData.filter(item => {
    const categoryMatch = category === 'all' || item.category === category;
    // 日期过滤逻辑
    return categoryMatch;
  });

  const config = {
    data: filteredData,
    xField: 'date',
    yField: 'value',
    seriesField: 'category',
    smooth: true,
    legend: {
      position: 'top',
    },
  };

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return <Line {...config} />;
      case 'column':
        return <Column {...config} />;
      case 'pie':
        return <Pie
          data={filteredData}
          angleField="value"
          colorField="category"
        />;
      default:
        return <Line {...config} />;
    }
  };

  return (
    <Card
      title="Data Explorer"
      extra={
        <Space>
          <RangePicker onChange={(dates) => setDateRange(dates)} />
          <Select
            value={category}
            onChange={setCategory}
            style={{ width: 120 }}
          >
            <Select.Option value="all">All Categories</Select.Option>
            <Select.Option value="A">Category A</Select.Option>
            <Select.Option value="B">Category B</Select.Option>
          </Select>
          <Select
            value={chartType}
            onChange={setChartType as any}
            style={{ width: 100 }}
          >
            <Select.Option value="line">Line</Select.Option>
            <Select.Option value="column">Column</Select.Option>
            <Select.Option value="pie">Pie</Select.Option>
          </Select>
        </Space>
      }
    >
      {renderChart()}
    </Card>
  );
};

export default DataExplorer;
```

## 最佳实践

### 1. 数据准备

✅ **推荐**:
```typescript
// 规范化数据格式
const normalizedData = rawData.map(item => ({
  date: new Date(item.timestamp).toISOString(),
  value: Number(item.amount),
  category: String(item.type),
}));

// 数据验证
const isValidData = (data: any[]) => {
  return data.every(item =>
    item.date &&
    typeof item.value === 'number' &&
    !isNaN(item.value)
  );
};
```

❌ **避免**:
```typescript
// 直接使用未处理的数据
<Line data={rawData} ... />

// 不进行数据验证
<Line data={unvalidatedData} ... />
```

### 2. 性能优化

✅ **推荐**:
```typescript
// 大数据量禁用动画
const config = {
  animation: data.length > 1000 ? false : true,
  // 或完全禁用
  animation: false,
};

// 使用 Canvas 渲染
const config = {
  renderer: 'canvas',
};

// 数据采样
const sampledData = useMemo(() => {
  if (data.length > 1000) {
    return data.filter((_, index) => index % 10 === 0);
  }
  return data;
}, [data]);
```

❌ **避免**:
```typescript
// 大数据量启用动画
const config = {
  animation: true, // 数据量 > 10000 时会卡顿
};

// 不做任何优化
<Line data={hugeDataset} ... />
```

### 3. 响应式设计

✅ **推荐**:
```typescript
// 自动适配容器
const config = {
  autoFit: true,
  // 不设置固定宽高
  // width: 800, ❌
};

// 响应式配置
const getConfig = (width: number) => ({
  legend: {
    position: width < 768 ? 'bottom' : 'top',
  },
  label: {
    visible: width >= 768,
  },
});
```

❌ **避免**:
```typescript
// 固定尺寸不适应
const config = {
  width: 800,
  height: 400,
  autoFit: false, // ❌
};

// 移动端体验差
const config = {
  legend: { position: 'top' }, // 移动端占用过多空间
};
```

### 4. 无障碍支持

✅ **推荐**:
```typescript
// 添加描述性标题
const config = {
  title: {
    visible: true,
    text: 'Monthly Revenue Trend',
  },
  description: {
    visible: true,
    text: 'Shows revenue growth from Jan to Jun 2023',
  },
};

// 键盘导航
<Line
  {...config}
  tabIndex={0}
  role="img"
  aria-label="Line chart showing revenue trend"
/>
```

❌ **避免**:
```typescript
// 无标题和描述
const config = {
  title: { visible: false }, // ❌
  description: { visible: false }, // ❌
};

// 无 ARIA 属性
<Line {...config} /> // ❌ 屏幕阅读器无法理解
```

### 5. 错误处理

✅ **推荐**:
```typescript
const ChartWithErrorHandling: React.FC = () => {
  const [error, setError] = useState<string | null>(null);

  try {
    if (!data || data.length === 0) {
      return <Empty description="No data available" />;
    }

    return <Line {...config} />;
  } catch (err) {
    return (
      <Alert
        type="error"
        message="Chart Error"
        description={error || 'Failed to render chart'}
      />
    );
  }
};
```

❌ **避免**:
```typescript
// 不处理空数据
<Line data={[]} ... /> // ❌ 显示空白

// 不处理异常
const BadChart = () => <Line {...invalidConfig} />; // ❌ 白屏
```

## 常见问题 Q&A

### Q1: 如何导出图表为图片?

**A**:
```typescript
import React, { useRef } from 'react';
import { Line } from '@ant-design/charts';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

const ExportableChart: React.FC = () => {
  const chartRef = useRef<any>();

  const exportChart = () => {
    const chart = chartRef.current?.getChart();
    if (chart) {
      const link = document.createElement('a');
      link.download = 'chart.png';
      link.href = chart.toDataURL();
      link.click();
    }
  };

  return (
    <div>
      <Line {...config} chartRef={chartRef} />
      <Button icon={<DownloadOutlined />} onClick={exportChart}>
        Export PNG
      </Button>
    </div>
  );
};
```

### Q2: 如何实现图表的动态更新?

**A**:
```typescript
import React, { useState, useEffect } from 'react';
import { Line } from '@ant-design/charts';

const DynamicChart: React.FC = () => {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      // 模拟数据更新
      setData(prev => {
        const newData = {
          time: new Date().toLocaleTimeString(),
          value: Math.random() * 100,
        };
        return [...prev.slice(-19), newData]; // 保留最近 20 条
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const config = {
    data,
    xField: 'time',
    yField: 'value',
    animation: false, // 动态更新建议禁用动画
  };

  return <Line {...config} />;
};
```

### Q3: 如何自定义图表颜色?

**A**:
```typescript
const CustomColorChart: React.FC = () => {
  const config = {
    data: multiSeriesData,
    xField: 'date',
    yField: 'value',
    seriesField: 'category',
    // 方式 1: 使用主题颜色
    color: ['#FF6B6B', '#4ECDC4', '#45B7D1'],

    // 方式 2: 使用颜色映射函数
    color: ({ category }) => {
      const colorMap: Record<string, string> = {
        A: '#FF6B6B',
        B: '#4ECDC4',
        C: '#45B7D1',
      };
      return colorMap[category] || '#999';
    },
  };

  return <Line {...config} />;
};
```

### Q4: 如何实现图表的数据筛选?

**A**:
```typescript
const FilterableChart: React.FC = () => {
  const [filters, setFilters] = useState<Record<string, any>>({});

  const filteredData = useMemo(() => {
    return data.filter(item => {
      return Object.entries(filters).every(([key, value]) => {
        return value === 'all' || item[key] === value;
      });
    });
  }, [data, filters]);

  const handleLegendClick = (info: any) => {
    setFilters(prev => ({
      ...prev,
      category: info.item.value,
    }));
  };

  const config = {
    data: filteredData,
    xField: 'date',
    yField: 'value',
    seriesField: 'category',
    interactions: [
      {
        type: 'legend-filter',
        enable: true,
      },
    ],
  };

  return <Line {...config} />;
};
```

### Q5: 如何处理大数据量图表的性能问题?

**A**:
```typescript
const HighPerformanceChart: React.FC = () => {
  // 策略 1: 数据采样
  const sampledData = useMemo(() => {
    if (data.length > 5000) {
      return data.filter((_, index) => index % Math.ceil(data.length / 5000) === 0);
    }
    return data;
  }, [data]);

  // 策略 2: 禁用动画和高开销交互
  const config = {
    data: sampledData,
    animation: false,
    point: { size: 0 },
    tooltip: { showMarkers: false },
    renderer: 'canvas', // 使用 Canvas 而非 SVG
  };

  return <Line {...config} />;
};
```

### Q6: 如何实现图表间的联动?

**A**:
```typescript
import React, { useState } from 'react';
import { Line, Column } from '@ant-design/charts';

const LinkedCharts: React.FC = () => {
  const [linkData, setLinkData] = useState<any>(null);

  const handleLineClick = (info: any) => {
    setLinkData({
      date: info.data.date,
    });
  };

  const lineConfig = {
    data,
    xField: 'date',
    yField: 'value',
    onReady: (chart: any) => {
      chart.on('element:click', handleLineClick);
    },
  };

  const columnConfig = {
    data: data.filter(d => !linkData || d.date === linkData.date),
    xField: 'date',
    yField: 'value',
  };

  return (
    <div>
      <Line {...lineConfig} />
      <Column {...columnConfig} />
    </div>
  );
};
```

### Q7: 如何实现图表的主题切换?

**A**:
```typescript
import React, { useState } from 'react';
import { Line } from '@ant-design/charts';
import { Switch } from 'antd';

const ThemedChart: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  const config = {
    data,
    xField: 'date',
    yField: 'value',
    theme: isDark ? 'dark' : 'default',
    // 或自定义主题
    theme: isDark ? darkTheme : lightTheme,
  };

  return (
    <div>
      <Switch
        checked={isDark}
        onChange={setIsDark}
        checkedChildren="Dark"
        unCheckedChildren="Light"
      />
      <Line {...config} />
    </div>
  );
};
```

### Q8: 如何处理空数据和错误状态?

**A**:
```typescript
import { Empty, Alert, Spin } from 'antd';

const RobustChart: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    fetchData()
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Spin />;
  }

  if (error) {
    return (
      <Alert
        type="error"
        message="Failed to load data"
        description={error}
      />
    );
  }

  if (!data || data.length === 0) {
    return <Empty description="No data available" />;
  }

  return <Line {...config} />;
};
```

## TypeScript 类型定义

### 基础类型

```typescript
import type {
  // 图表配置类型
  LineConfig,
  ColumnConfig,
  PieConfig,
  AreaConfig,
  ScatterConfig,
  DualAxesConfig,
  GaugeConfig,

  // 数据类型
  DataItem,

  // 事件类型
  ChartEvent,
  ChartRef,

  // 其他类型
  TooltipCfg,
  LegendCfg,
  AxisCfg,
  LabelCfg,
} from '@ant-design/charts';
```

### 自定义类型

```typescript
interface ChartData {
  date: string;
  value: number;
  category?: string;
}

interface SalesData extends ChartData {
  revenue: number;
  cost: number;
  profit: number;
}

const MyChart: React.FC<{ data: SalesData[] }> = ({ data }) => {
  const config: LineConfig = {
    data,
    xField: 'date',
    yField: 'revenue',
  };

  return <Line {...config} />;
};
```

## 总结

`@ant-design/charts` 提供了一套功能完整、设计精美的 React 图表解决方案：

**核心优势**:
- 与 Ant Design 设计语言完美融合
- 开箱即用的合理默认配置
- 丰富的图表类型和交互能力
- 完善的 TypeScript 支持
- 高性能的渲染引擎
- 优秀的响应式和无障碍支持

**最佳实践**:
- 合理选择图表类型（数据特征 → 图表类型）
- 做好数据预处理和验证
- 大数据量场景进行性能优化
- 实现良好的响应式和交互体验
- 添加完善的错误处理和加载状态
- 遵循无障碍标准

**适用场景**:
- 数据可视化仪表板
- 实时数据监控
- 数据分析和探索
- 业务报表系统
- 科学研究可视化
