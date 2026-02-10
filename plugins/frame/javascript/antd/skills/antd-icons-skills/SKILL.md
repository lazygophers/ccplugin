---
name: antd-icons-skills
description: Ant Design 图标系统完整指南 - @ant-design/icons、自定义图标、图标加载优化
---

# antd-icons: Ant Design 图标系统完整指南

Ant Design 图标系统是一套高质量的 React 图标组件库，提供 200+ 个开箱即用的图标组件，支持自定义图标、按需加载、主题定制等功能，适用于各类 Web 应用场景。

---

## 概述

### 图标系统

Ant Design 图标系统基于 `@ant-design/icons` 包，提供：

- **200+ 官方图标** - 涵盖方向性、建议性、编辑、数据、品牌等多个类别
- **React 组件化** - 直接作为 React 组件使用，无需额外配置
- **Tree Shaking 支持** - 按需加载，自动移除未使用的图标
- **主题适配** - 自动跟随 Ant Design 主题（主色、尺寸等）
- **TypeScript 支持** - 完整的类型定义

### 图标库

```
@ant-design/icons
├── 图标分类
│   ├── 方向性图标（Directional Icons）
│   ├── 建议性图标（Suggestion Icons）
│   ├── 编辑类图标（Editor Icons）
│   ├── 数据类图标（Data Icons）
│   ├── 品牌和标识（Brand & Logos）
│   └── 通用图标（General Icons）
│
├── 使用方式
│   ├── 直接引入图标组件
│   ├── Icons API 动态加载
│   └── 自定义图标
│
└── 优化策略
    ├── 按需加载（Tree Shaking）
    ├── 图标懒加载
    └── 图标合并（IconFont）
```

---

## 核心特性

- **开箱即用** - 200+ 高质量图标，直接引入使用
- **Tree Shaking** - 自动按需加载，只打包使用的图标
- **主题继承** - 自动继承 ConfigProvider 的主题配置
- **多种尺寸** - 支持预设尺寸和自定义尺寸
- **颜色定制** - 支持主题色和自定义颜色
- **旋转翻转** - 支持图标旋转和镜像翻转
- **自定义图标** - 支持 SVG、IconFont、自定义 React 组件
- **加载优化** - Icons API 动态加载，减少初始包体积

---

## 基础使用

### 引入方式

#### 方式 1: 直接引入图标组件（推荐）

```tsx
import { HomeOutlined, UserOutlined, SettingOutlined } from '@ant-design/icons';

function BasicIcons() {
  return (
    <div>
      <HomeOutlined />
      <UserOutlined />
      <SettingOutlined />
    </div>
  );
}
```

#### 方式 2: 从子路径引入（兼容旧版）

```tsx
import HomeOutlined from '@ant-design/icons/HomeOutlined';

function BasicIcon() {
  return <HomeOutlined />;
}
```

#### 方式 3: Icons API 动态加载（适用于动态场景）

```tsx
import * as Icons from '@ant-design/icons';

function DynamicIcon({ iconName }: { iconName: string }) {
  const IconComponent = Icons[iconName];

  if (!IconComponent) {
    return <span>Icon not found</span>;
  }

  return <IconComponent />;
}

// 使用
<DynamicIcon iconName="HomeOutlined" />
<DynamicIcon iconName="UserOutlined" />
```

### 基础图标

#### Outlined 图标（轮廓风格）

```tsx
import {
  HomeOutlined,
  UserOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

function OutlinedIcons() {
  return (
    <div>
      <HomeOutlined /> {/* 首页 */}
      <UserOutlined /> {/* 用户 */}
      <SettingOutlined /> {/* 设置 */}
      <InfoCircleOutlined /> {/* 信息 */}
      <CheckCircleOutlined /> {/* 成功 */}
      <CloseCircleOutlined /> {/* 失败 */}
      <ExclamationCircleOutlined /> {/* 警告 */}
    </div>
  );
}
```

#### Filled 图标（实心风格）

```tsx
import {
  HomeFilled,
  StarFilled,
  LikeFilled,
  CheckCircleFilled,
  CloseCircleFilled,
} from '@ant-design/icons';

function FilledIcons() {
  return (
    <div>
      <HomeFilled /> {/* 首页（实心） */}
      <StarFilled /> {/* 星标（实心） */}
      <LikeFilled /> {/* 点赞（实心） */}
      <CheckCircleFilled /> {/* 成功（实心） */}
      <CloseCircleFilled /> {/* 失败（实心） */}
    </div>
  );
}
```

#### TwoTone 图标（双色风格）

```tsx
import {
  HeartTwoTone,
  MehTwoTone,
  SmileTwoTone,
} from '@ant-design/icons';

function TwoToneIcons() {
  return (
    <div>
      <HeartTwoTone twoToneColor="#eb2f96" /> {/* 爱心（双色） */}
      <MehTwoTone twoToneColor="#faad14" /> {/* 中性（双色） */}
      <SmileTwoTone twoToneColor="#52c41a" /> {/* 微笑（双色） */}
    </div>
  );
}
```

### 图标尺寸

#### 预设尺寸

```tsx
import { SearchOutlined } from '@ant-design/icons';

function IconSizes() {
  return (
    <div>
      <SearchOutlined style={{ fontSize: 12 }} /> {/* 小图标 */}
      <SearchOutlined style={{ fontSize: 14 }} /> {/* 默认 */}
      <SearchOutlined style={{ fontSize: 16 }} /> {/* 中等 */}
      <SearchOutlined style={{ fontSize: 20 }} /> {/* 大图标 */}
      <SearchOutlined style={{ fontSize: 24 }} /> {/* 超大 */}
    </div>
  );
}
```

#### 配合组件尺寸

```tsx
import { Button, Input, SearchOutlined } from '@ant-design/icons';

function ComponentSizes() {
  return (
    <div>
      <Button size="small" icon={<SearchOutlined />}>
        Small
      </Button>
      <Button size="middle" icon={<SearchOutlined />}>
        Middle
      </Button>
      <Button size="large" icon={<SearchOutlined />}>
        Large
      </Button>

      <Input size="small" prefix={<SearchOutlined />} />
      <Input size="middle" prefix={<SearchOutlined />} />
      <Input size="large" prefix={<SearchOutlined />} />
    </div>
  );
}
```

### 图标颜色

#### 主题色

```tsx
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';

function ThemeColors() {
  return (
    <div>
      <CheckCircleOutlined style={{ color: '#52c41a' }} /> {/* 成功色 */}
      <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> {/* 错误色 */}
      <WarningOutlined style={{ color: '#faad14' }} /> {/* 警告色 */}
      <InfoCircleOutlined style={{ color: '#1677ff' }} /> {/* 信息色 */}
    </div>
  );
}
```

#### 自定义颜色

```tsx
import { HeartOutlined } from '@ant-design/icons';

function CustomColors() {
  return (
    <div>
      <HeartOutlined style={{ color: '#ff0000' }} /> {/* 红色 */}
      <HeartOutlined style={{ color: '#00ff00' }} /> {/* 绿色 */}
      <HeartOutlined style={{ color: '#0000ff' }} /> {/* 蓝色 */}
      <HeartOutlined style={{ color: 'rgba(0, 0, 0, 0.45)' }} /> {/* 半透明 */}
    </div>
  );
}
```

#### CSS 变量颜色

```tsx
import { CheckCircleOutlined } from '@ant-design/icons';

function CSSVariableColor() {
  return (
    <CheckCircleOutlined
      style={{
        color: 'var(--ant-color-success)',
      }}
    />
  );
}
```

### 图标旋转和翻转

#### 旋转

```tsx
import { LoadingOutlined, SyncOutlined } from '@ant-design/icons';

function RotatedIcons() {
  return (
    <div>
      {/* 静态旋转 */}
      <SyncOutlined rotate={90} /> {/* 顺时针 90 度 */}
      <SyncOutlined rotate={180} /> {/* 顺时针 180 度 */}
      <SyncOutlined rotate={270} /> {/* 顺时针 270 度 */}

      {/* 动态旋转（加载动画） */}
      <LoadingOutlined spin style={{ fontSize: 24 }} />
    </div>
  );
}
```

#### 翻转

```tsx
import { ArrowLeftOutlined } from '@ant-design/icons';

function FlippedIcons() {
  return (
    <div>
      <ArrowLeftOutlined /> {/* 原始 */}
      <ArrowLeftOutlined flip="horizontal" /> {/* 水平翻转 */}
      <ArrowLeftOutlined flip="vertical" /> {/* 垂直翻转 */}
      <ArrowLeftOutlined flip="both" /> {/* 双向翻转 */}
    </div>
  );
}
```

---

## 按需加载

### 为什么按需加载

Ant Design 图标库默认支持 Tree Shaking，但需要正确的引入方式：

**❌ 错误方式（全量引入）**：
```tsx
import * as Icons from '@ant-design/icons';

// 这会打包所有图标（即使只使用一个）
function BadExample() {
  return <Icons.HomeOutlined />;
}
```

**✅ 正确方式（按需引入）**：
```tsx
import { HomeOutlined } from '@ant-design/icons';

// 只打包使用的图标
function GoodExample() {
  return <HomeOutlined />;
}
```

### 配置方法

#### Vite 配置

```tsx
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // 启用 Tree Shaking
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
});
```

#### Webpack 配置

```js
// webpack.config.js
module.exports = {
  // ...
  optimization: {
    usedExports: true, // 启用 Tree Shaking
    sideEffects: false, // 标记包无副作用
  },
};
```

#### Next.js 配置

```js
// next.config.js
module.exports = {
  webpack: (config) => {
    // 启用 Tree Shaking
    config.optimization = {
      ...config.optimization,
      usedExports: true,
      sideEffects: false,
    };
    return config;
  },
};
```

### 包体积对比

#### 全量引入（不推荐）

```tsx
// 打包体积分析
import * as Icons from '@ant-design/icons';

// 包体积: ~1.2MB（未压缩）~300KB（gzip）
```

#### 按需引入（推荐）

```tsx
// 只引入使用的图标
import { HomeOutlined, UserOutlined } from '@ant-design/icons';

// 包体积: ~5KB（未压缩）~2KB（gzip）
```

**对比结果**：
- 全量引入：1.2MB（200+ 图标）
- 按需引入：5KB（2 个图标）
- 减少：99.6%

---

## 图标分类

### 方向性图标（Directional Icons）

用于表示方向、导航、位置等：

```tsx
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  UpOutlined,
  DownOutlined,
  LeftOutlined,
  RightOutlined,
  VerticalAlignTopOutlined,
  VerticalAlignBottomOutlined,
} from '@ant-design/icons';

function DirectionalIcons() {
  return (
    <div>
      <ArrowUpOutlined /> {/* 向上箭头 */}
      <ArrowDownOutlined /> {/* 向下箭头 */}
      <ArrowLeftOutlined /> {/* 向左箭头 */}
      <ArrowRightOutlined /> {/* 向右箭头 */}
      <UpOutlined /> {/* 向上 */}
      <DownOutlined /> {/* 向下 */}
      <LeftOutlined /> {/* 向左 */}
      <RightOutlined /> {/* 向右 */}
      <VerticalAlignTopOutlined /> {/* 顶部对齐 */}
      <VerticalAlignBottomOutlined /> {/* 底部对齐 */}
    </div>
  );
}
```

### 建议性图标（Suggestion Icons）

用于提示、引导用户操作：

```tsx
import {
  CheckCircleOutlined,
  CheckCircleFilled,
  CloseCircleOutlined,
  CloseCircleFilled,
  ExclamationCircleOutlined,
  ExclamationCircleFilled,
  InfoCircleOutlined,
  InfoCircleFilled,
  WarningOutlined,
  WarningFilled,
} from '@ant-design/icons';

function SuggestionIcons() {
  return (
    <div>
      <CheckCircleOutlined style={{ color: '#52c41a' }} /> {/* 成功（轮廓） */}
      <CheckCircleFilled style={{ color: '#52c41a' }} /> {/* 成功（实心） */}

      <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> {/* 失败（轮廓） */}
      <CloseCircleFilled style={{ color: '#ff4d4f' }} /> {/* 失败（实心） */}

      <ExclamationCircleOutlined style={{ color: '#faad14' }} /> {/* 警告（轮廓） */}
      <ExclamationCircleFilled style={{ color: '#faad14' }} /> {/* 警告（实心） */}

      <InfoCircleOutlined style={{ color: '#1677ff' }} /> {/* 信息（轮廓） */}
      <InfoCircleFilled style={{ color: '#1677ff' }} /> {/* 信息（实心） */}
    </div>
  );
}
```

### 编辑类图标（Editor Icons）

用于编辑、删除、保存等操作：

```tsx
import {
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CopyOutlined,
  ScissorOutlined,
  SnippetsOutlined,
  FormOutlined,
  HighlightOutlined,
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
} from '@ant-design/icons';

function EditorIcons() {
  return (
    <div>
      <EditOutlined /> {/* 编辑 */}
      <DeleteOutlined /> {/* 删除 */}
      <SaveOutlined /> {/* 保存 */}
      <CopyOutlined /> {/* 复制 */}
      <ScissorOutlined /> {/* 剪切 */}
      <SnippetsOutlined /> {/* 代码片段 */}
      <FormOutlined /> {/* 表单 */}
      <HighlightOutlined /> {/* 高亮 */}
      <BoldOutlined /> {/* 粗体 */}
      <ItalicOutlined /> {/* 斜体 */}
      <UnderlineOutlined /> {/* 下划线 */}
    </div>
  );
}
```

### 数据类图标（Data Icons）

用于数据展示、文件、媒体等：

```tsx
import {
  FileOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileMarkdownOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FilePptOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons';

function DataIcons() {
  return (
    <div>
      <FileOutlined /> {/* 文件 */}
      <FileTextOutlined /> {/* 文本文件 */}
      <FilePdfOutlined /> {/* PDF 文件 */}
      <FileImageOutlined /> {/* 图片文件 */}
      <FileMarkdownOutlined /> {/* Markdown 文件 */}
      <FileExcelOutlined /> {/* Excel 文件 */}
      <FileWordOutlined /> {/* Word 文件 */}
      <FilePptOutlined /> {/* PPT 文件 */}

      <FolderOutlined /> {/* 文件夹 */}
      <FolderOpenOutlined /> {/* 打开文件夹 */}

      <DatabaseOutlined /> {/* 数据库 */}
      <CloudUploadOutlined /> {/* 上传 */}
      <CloudDownloadOutlined /> {/* 下载 */}
    </div>
  );
}
```

### 品牌和标识（Brand & Logos）

用于第三方平台、社交媒体等：

```tsx
import {
  GithubOutlined,
  WechatOutlined,
  AlipayOutlined,
  TaobaoOutlined,
  DingdingOutlined,
  WeiboOutlined,
  TwitterOutlined,
  FacebookOutlined,
  GoogleOutlined,
  AppleOutlined,
  AndroidOutlined,
  WindowsOutlined,
} from '@ant-design/icons';

function BrandIcons() {
  return (
    <div>
      <GithubOutlined /> {/* GitHub */}
      <WechatOutlined /> {/* 微信 */}
      <AlipayOutlined /> {/* 支付宝 */}
      <TaobaoOutlined /> {/* 淘宝 */}
      <DingdingOutlined /> {/* 钉钉 */}
      <WeiboOutlined /> {/* 微博 */}
      <TwitterOutlined /> {/* Twitter */}
      <FacebookOutlined /> {/* Facebook */}
      <GoogleOutlined /> {/* Google */}
      <AppleOutlined /> {/* Apple */}
      <AndroidOutlined /> {/* Android */}
      <WindowsOutlined /> {/* Windows */}
    </div>
  );
}
```

---

## 自定义图标

### SVG 图标

#### 方式 1: 使用 Icon 组件（推荐）

```tsx
import { Icon } from '@ant-design/icons';

const HeartSvg = () => (
  <svg width="1em" height="1em" fill="currentColor" viewBox="0 0 1024 1024">
    <path d="M923 283.6c-13.4-31.1-32.6-58.9-56.9-82.8-24.3-23.8-52.5-42.4-84-55.5-31.5-13-65.3-19.6-99.4-19.6-39.6 0-77.1 9.3-111.2 27.5-29.4 15.7-54.8 38.1-74.6 65.8-19.8-27.7-45.2-50.1-74.6-65.8-34.1-18.2-71.6-27.5-111.2-27.5-34.1 0-67.9 6.6-99.4 19.6-31.5 13-59.7 31.7-84 55.5-24.3 23.9-43.5 51.7-56.9 82.8-13.6 31.5-20.6 65.6-20.6 100.9 0 33.3 6.8 66.4 20.3 97.9 13.4 31.1 32.5 58.9 56.8 82.8 24.3 23.8 52.5 42.4 84 55.5 31.5 13 65.3 19.6 99.4 19.6 39.6 0 77.1-9.3 111.2-27.5 29.4-15.7 54.8-38.1 74.6-65.8 19.8 27.7 45.2 50.1 74.6 65.8 34.1 18.2 71.6 27.5 111.2 27.5 34.1 0 67.9-6.6 99.4-19.6 31.5-13 59.7-31.7 84-55.5 24.3-23.9 43.5-51.7 56.9-82.8 13.6-31.5 20.6-65.6 20.6-100.9 0-35.3-7-69.4-20.6-100.9zM512 760.6c-20.8 0-41.1-4.1-60.2-12.2-18.7-8-35.4-19.6-49.4-34.3-14.1-14.7-25.2-31.9-32.8-50.9-7.7-19.1-11.7-39.6-11.7-60.4s4-41.3 11.7-60.4c7.7-19 18.7-36.2 32.8-50.9 14-14.7 30.7-26.3 49.4-34.3 19.1-8.1 39.4-12.2 60.2-12.2s41.1 4.1 60.2 12.2c18.7 8 35.4 19.6 49.4 34.3 14.1 14.7 25.2 31.9 32.8 50.9 7.7 19.1 11.7 39.6 11.7 60.4s-4 41.3-11.7 60.4c-7.7 19-18.7 36.2-32.8 50.9-14 14.7-30.7 26.3-49.4 34.3-19.1 8.1-39.4 12.2-60.2 12.2z" />
  </svg>
);

const HeartIcon = (props) => <Icon component={HeartSvg} {...props} />;

function CustomSVGIcon() {
  return <HeartIcon style={{ color: '#ff4d4f', fontSize: 32 }} />;
}
```

#### 方式 2: 直接使用 SVG（简单场景）

```tsx
function SimpleSVGIcon() {
  return (
    <svg
      width="1em"
      height="1em"
      fill="currentColor"
      viewBox="0 0 1024 1024"
      style={{ fontSize: 24, color: '#1890ff' }}
    >
      <path d="M923 283.6c-13.4-31.1-32.6-58.9-56.9-82.8-24.3-23.8-52.5-42.4-84-55.5-31.5-13-65.3-19.6-99.4-19.6-39.6 0-77.1 9.3-111.2 27.5-29.4 15.7-54.8 38.1-74.6 65.8-19.8-27.7-45.2-50.1-74.6-65.8-34.1-18.2-71.6-27.5-111.2-27.5-34.1 0-67.9 6.6-99.4 19.6-31.5 13-59.7 31.7-84 55.5-24.3 23.9-43.5 51.7-56.9 82.8-13.6 31.5-20.6 65.6-20.6 100.9 0 33.3 6.8 66.4 20.3 97.9 13.4 31.1 32.5 58.9 56.8 82.8 24.3 23.8 52.5 42.4 84 55.5 31.5 13 65.3 19.6 99.4 19.6 39.6 0 77.1-9.3 111.2-27.5 29.4-15.7 54.8-38.1 74.6-65.8 19.8 27.7 45.2 50.1 74.6 65.8 34.1 18.2 71.6 27.5 111.2 27.5 34.1 0 67.9-6.6 99.4-19.6 31.5-13 59.7-31.7 84-55.5 24.3-23.9 43.5-51.7 56.9-82.8 13.6-31.5 20.6-65.6 20.6-100.9 0-35.3-7-69.4-20.6-100.9z" />
    </svg>
  );
}
```

#### 方式 3: 使用 createFromIconfontCN（IconFont）

```tsx
import { createFromIconfontCN } from '@ant-design/icons';

const IconFont = createFromIconfontCN({
  scriptUrl: '//at.alicdn.com/t/font_8d5l8fzk5b87iudi.js',
});

function IconFontExample() {
  return (
    <div>
      <IconFont type="icon-example" />
      <IconFont type="icon-test" style={{ fontSize: 32, color: '#52c41a' }} />
    </div>
  );
}
```

### IconFont 图标

#### 使用在线 IconFont

```tsx
import { createFromIconfontCN } from '@ant-design/icons';

const IconFont = createFromIconfontCN({
  scriptUrl: [
    '//at.alicdn.com/t/font_1788044_0dwu3guebvr.js', // 图标库 1
    '//at.alicdn.com/t/font_1788045_0dwu3guebvr.js', // 图标库 2
  ],
});

function MultipleIconFont() {
  return (
    <div>
      <IconFont type="icon-tuichu" />
      <IconFont type="icon-facebook" />
      <IconFont type="icon-twitter" />
    </div>
  );
}
```

#### 使用本地 IconFont

```tsx
import { createFromIconfontCN } from '@ant-design/icons';

const LocalIconFont = createFromIconfontCN({
  scriptUrl: '/icons/iconfont.js', // 本地文件路径
});

function LocalIconFontExample() {
  return <LocalIconFont type="icon-custom" />;
}
```

### 自定义 React 图标组件

```tsx
import { Icon } from '@ant-design/icons';

interface CustomIconProps {
  size?: number;
  color?: string;
  rotate?: number;
}

const CustomIcon = ({ size = 24, color = '#1890ff', rotate = 0 }: CustomIconProps) => {
  const SvgComponent = () => (
    <svg
      width="1em"
      height="1em"
      fill="currentColor"
      viewBox="0 0 1024 1024"
      style={{ fontSize: size, color, transform: `rotate(${rotate}deg)` }}
    >
      <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" />
    </svg>
  );

  return <Icon component={SvgComponent} />;
};

function CustomReactIcon() {
  return (
    <div>
      <CustomIcon size={16} color="#ff4d4f" />
      <CustomIcon size={24} color="#52c41a" />
      <CustomIcon size={32} color="#1677ff" rotate={45} />
    </div>
  );
}
```

---

## 图标配合组件使用

### Button 图标

```tsx
import { Button } from 'antd';
import {
  SearchOutlined,
  DownloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';

function ButtonIcons() {
  return (
    <div>
      {/* 图标 + 文本 */}
      <Button type="primary" icon={<SearchOutlined />}>
        搜索
      </Button>

      {/* 仅图标 */}
      <Button icon={<DownloadOutlined />} />

      {/* 加载状态 */}
      <Button type="primary" loading>
        加载中
      </Button>

      {/* 不同类型的按钮 */}
      <Button type="primary" icon={<PlusOutlined />}>
        新建
      </Button>
      <Button icon={<EditOutlined />}>编辑</Button>
      <Button danger icon={<DeleteOutlined />}>
        删除
      </Button>
    </div>
  );
}
```

### Menu 图标

```tsx
import { Menu } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  SettingOutlined,
  FileOutlined,
  TeamOutlined,
} from '@ant-design/icons';

const { SubMenu } = Menu;

function MenuIcons() {
  return (
    <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']}>
      <Menu.Item key="1" icon={<HomeOutlined />}>
        首页
      </Menu.Item>

      <Menu.Item key="2" icon={<UserOutlined />}>
        用户管理
      </Menu.Item>

      <SubMenu key="sub1" icon={<FileOutlined />} title="文件管理">
        <Menu.Item key="3">文件列表</Menu.Item>
        <Menu.Item key="4">上传文件</Menu.Item>
      </SubMenu>

      <Menu.Item key="5" icon={<TeamOutlined />}>
        团队管理
      </Menu.Item>

      <Menu.Item key="6" icon={<SettingOutlined />}>
        系统设置
      </Menu.Item>
    </Menu>
  );
}
```

### Tabs 图标

```tsx
import { Tabs } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons';

function TabsIcons() {
  const items = [
    {
      key: '1',
      label: (
        <span>
          <HomeOutlined />
          首页
        </span>
      ),
      children: '首页内容',
    },
    {
      key: '2',
      label: (
        <span>
          <UserOutlined />
          用户
        </span>
      ),
      children: '用户内容',
    },
    {
      key: '3',
      label: (
        <span>
          <SettingOutlined />
          设置
        </span>
      ),
      children: '设置内容',
    },
  ];

  return <Tabs defaultActiveKey="1" items={items} />;
}
```

### Form 图标

```tsx
import { Form, Input, Button } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
} from '@ant-design/icons';

function FormIcons() {
  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <Form
      name="register"
      onFinish={onFinish}
      style={{ maxWidth: 400 }}
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入用户名!' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="用户名" />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱!' },
          { type: 'email', message: '邮箱格式不正确!' },
        ]}
      >
        <Input prefix={<MailOutlined />} placeholder="邮箱" />
      </Form.Item>

      <Form.Item
        name="phone"
        rules={[{ required: true, message: '请输入手机号!' }]}
      >
        <Input prefix={<PhoneOutlined />} placeholder="手机号" />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码!' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="密码" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          注册
        </Button>
      </Form.Item>
    </Form>
  );
}
```

### Breadcrumb 图标

```tsx
import { Breadcrumb } from 'antd';
import { HomeOutlined, UserOutlined } from '@ant-design/icons';

function BreadcrumbIcons() {
  return (
    <Breadcrumb>
      <Breadcrumb.Item href="">
        <HomeOutlined />
        <span>首页</span>
      </Breadcrumb.Item>
      <Breadcrumb.Item href="">
        <UserOutlined />
        <span>用户管理</span>
      </Breadcrumb.Item>
      <Breadcrumb.Item>用户列表</Breadcrumb.Item>
    </Breadcrumb>
  );
}
```

### Card 图标

```tsx
import { Card, Avatar } from 'antd';
import {
  SettingOutlined,
  EllipsisOutlined,
  EditOutlined,
} from '@ant-design/icons';

const { Meta } = Card;

function CardIcons() {
  return (
    <Card
      style={{ width: 300 }}
      cover={
        <img
          alt="example"
          src="https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png"
        />
      }
      actions={[
        <SettingOutlined key="setting" />,
        <EditOutlined key="edit" />,
        <EllipsisOutlined key="ellipsis" />,
      ]}
    >
      <Meta
        avatar={<Avatar src="https://api.dicebear.com/7.x/miniavs/svg?seed=3" />}
        title="Card title"
        description="This is the description"
      />
    </Card>
  );
}
```

---

## 性能优化

### Tree Shaking

#### 确保正确的构建配置

```tsx
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // 将 @ant-design/icons 单独打包
          if (id.includes('@ant-design/icons')) {
            return 'antd-icons';
          }
        },
      },
    },
  },
});
```

#### 分析打包体积

```bash
# 使用 vite-plugin-inspect 分析
npm install --save-dev vite-plugin-inspect

# vite.config.ts
import inspect from 'vite-plugin-inspect';

export default defineConfig({
  plugins: [inspect()],
});
```

### 图标懒加载

#### React.lazy 动态加载

```tsx
import { lazy, Suspense } from 'react';

const LazyHomeOutlined = lazy(() =>
  import('@ant-design/icons/HomeOutlined').then((module) => ({
    default: module.HomeOutlined,
  }))
);

function LazyIconExample() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyHomeOutlined />
    </Suspense>
  );
}
```

#### 动态 import

```tsx
function DynamicIconLoader({ iconName }: { iconName: string }) {
  const [IconComponent, setIconComponent] = useState<React.ComponentType | null>(null);

  useEffect(() => {
    import(`@ant-design/icons/${iconName}`)
      .then((module) => {
        setIconComponent(() => module.default);
      })
      .catch((error) => {
        console.error('Failed to load icon:', error);
      });
  }, [iconName]);

  if (!IconComponent) {
    return <span>Loading...</span>;
  }

  return <IconComponent />;
}

// 使用
<DynamicIconLoader iconName="HomeOutlined" />
```

### 图标合并（IconFont）

#### 批量导出自定义图标

```tsx
import { createFromIconfontCN } from '@ant-design/icons';

const IconFont = createFromIconfontCN({
  scriptUrl: '//at.alicdn.com/t/font_8d5l8fzk5b87iudi.js',
});

function BatchIconExample() {
  return (
    <div>
      <IconFont type="icon-home" />
      <IconFont type="icon-user" />
      <IconFont type="icon-setting" />
      {/* 所有图标打包成一个字体文件 */}
    </div>
  );
}
```

---

## 最佳实践

### 1. 图标引入

**✅ 推荐**：直接引入使用的图标组件

```tsx
import { HomeOutlined, UserOutlined } from '@ant-design/icons';
```

**❌ 避免**：全量引入所有图标

```tsx
import * as Icons from '@ant-design/icons';
```

### 2. 图标尺寸

**✅ 推荐**：使用预设尺寸

```tsx
<HomeOutlined style={{ fontSize: 14 }} />
<HomeOutlined style={{ fontSize: 16 }} />
<HomeOutlined style={{ fontSize: 24 }} />
```

**❌ 避免**：使用不规范的尺寸

```tsx
<HomeOutlined style={{ fontSize: 13 }} /> {/* 不规范 */}
```

### 3. 图标颜色

**✅ 推荐**：使用主题色或语义化颜色

```tsx
<CheckCircleOutlined style={{ color: '#52c41a' }} /> {/* 成功 */}
<CloseCircleOutlined style={{ color: '#ff4d4f' }} /> {/* 错误 */}
<WarningOutlined style={{ color: '#faad14' }} /> {/* 警告 */}
```

**❌ 避免**：硬编码颜色值

```tsx
<CheckCircleOutlined style={{ color: 'rgb(82, 196, 26)' }} /> {/* 不推荐 */}
```

### 4. 图标样式

**✅ 推荐**：使用 className 或 style 对象

```tsx
<HomeOutlined className="my-icon" />
<HomeOutlined style={{ fontSize: 24, color: '#1890ff' }} />
```

**❌ 避免**：内联样式过长

```tsx
<HomeOutlined style={{ fontSize: 24, color: '#1890ff', marginLeft: 8, marginRight: 8, marginTop: 4, marginBottom: 4 }} /> {/* 不推荐 */}
```

### 5. 图标性能

**✅ 推荐**：按需加载，避免全量引入

```tsx
import { HomeOutlined } from '@ant-design/icons';
```

**❌ 避免**：全量引入导致包体积过大

```tsx
import * as Icons from '@ant-design/icons';
```

### 6. 自定义图标

**✅ 推荐**：使用 Icon 组件包装 SVG

```tsx
const CustomIcon = (props) => (
  <Icon component={CustomSvg} {...props} />
);
```

**❌ 避免**：直接使用 img 标签

```tsx
<img src="/icon.svg" alt="icon" /> {/* 不推荐 */}
```

---

## 常见问题

### Q1: 如何按需加载图标?

**A**: 直接引入使用的图标组件即可：

```tsx
import { HomeOutlined, UserOutlined } from '@ant-design/icons';
```

不要使用 `import * as Icons from '@ant-design/icons'`，这会打包所有图标。

### Q2: 如何自定义图标颜色和尺寸?

**A**: 通过 `style` 属性设置：

```tsx
<HomeOutlined
  style={{
    fontSize: 32,    // 尺寸
    color: '#ff4d4f', // 颜色
  }}
/>
```

### Q3: 如何使用 IconFont 图标?

**A**: 使用 `createFromIconfontCN` 创建 IconFont 组件：

```tsx
import { createFromIconfontCN } from '@ant-design/icons';

const IconFont = createFromIconfontCN({
  scriptUrl: '//at.alicdn.com/t/font_8d5l8fzk5b87iudi.js',
});

function App() {
  return <IconFont type="icon-example" />;
}
```

### Q4: 图标旋转和翻转怎么做?

**A**: 使用 `rotate` 和 `flip` 属性：

```tsx
<SyncOutlined rotate={90} /> {/* 旋转 90 度 */}
<ArrowLeftOutlined flip="horizontal" /> {/* 水平翻转 */}
```

### Q5: 如何动态加载图标?

**A**: 使用动态 import 或 Icons API：

```tsx
// 方式 1: 动态 import
const DynamicIcon = lazy(() => import('@ant-design/icons/HomeOutlined'));

// 方式 2: Icons API
import * as Icons from '@ant-design/icons';
const IconComponent = Icons[iconName];
```

### Q6: 图标不显示怎么办?

**A**: 检查以下几点：
1. 确认正确引入了图标组件
2. 检查是否有 CSS 覆盖了图标样式
3. 确认浏览器控制台是否有错误信息
4. 检查是否正确设置了颜色（白色图标在白色背景上看不见）

### Q7: 如何减少图标包体积?

**A**:
1. 使用按需加载（只引入使用的图标）
2. 使用 IconFont 合并多个自定义图标
3. 启用 Tree Shaking 和代码压缩

### Q8: 图标可以用于其他框架吗?

**A**: `@ant-design/icons` 是 React 组件库，仅适用于 React。如果要用于其他框架，可以：
1. 导出 SVG 源文件
2. 使用 IconFont（跨框架兼容）
3. 使用其他框架的图标库

### Q9: 如何使用自定义 SVG 图标?

**A**: 使用 `Icon` 组件包装 SVG：

```tsx
import { Icon } from '@ant-design/icons';

const CustomSvg = () => (
  <svg viewBox="0 0 1024 1024">
    <path d="..." />
  </svg>
);

const CustomIcon = (props) => <Icon component={CustomSvg} {...props} />;
```

### Q10: 图标支持动画吗?

**A**: 支持。使用 `spin` 属性实现旋转动画：

```tsx
<LoadingOutlined spin /> {/* 自动旋转 */}
```

也可以通过 CSS 自定义动画：

```tsx
<SyncOutlined className="custom-spin" />
```

```css
.custom-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

## 参考资源

- [Ant Design 图标官方文档](https://ant.design/components/icon-cn/)
- [@ant-design/icons GitHub](https://github.com/ant-design/ant-design-icons/tree/master/packages/icons-react)
- [IconFont 图标库](https://www.iconfont.cn/)
- [Ant Design 图标列表](https://ant.design/icons/)

---

## 版本要求

- @ant-design/icons >= 5.0.0
- React >= 16.9.0
- Ant Design >= 5.0.0（用于主题集成）

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
