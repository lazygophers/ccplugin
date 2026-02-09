---
name: antd-theme-skills
description: Ant Design 主题定制完整指南 - Token 系统、CSS-in-JS、动态主题、深色模式、主题切换
---

# Ant Design 主题定制完整指南

## 概述

Ant Design 5.x 引入了全新的 CSS-in-JS 主题系统，基于 Design Token 实现了强大的主题定制能力。与 v4 版本使用的 Less 变量不同，v5 采用运行时动态主题机制，无需重新编译即可切换主题，同时支持深色模式、紧凑模式等多种主题变体。

**核心特性**:
- **CSS-in-JS**: 运行时动态主题，无需重新编译
- **动态切换**: 无需刷新页面即可切换主题
- **深色模式**: 内置 darkAlgorithm 支持深色主题
- **紧凑模式**: 高密度信息展示的 compactAlgorithm
- **Token 系统**: 三层 Token 架构 (Seed → Map → Alias)
- **持久化**: LocalStorage 集成，主题状态保存
- **组件级定制**: ConfigProvider 嵌套实现局部主题

---

## 核心特性

### 1. CSS-in-JS 动态主题

Ant Design 5 使用 CSS-in-JS 技术，在浏览器运行时动态生成样式，支持实时主题切换而无需重新编译。

**优势**:
- 无需构建工具配置
- 运行时动态修改主题
- 支持多主题并存
- 组件级主题定制

### 2. 深色模式 (Dark Mode)

内置 `darkAlgorithm` 主题算法，一键切换深色主题。

**适用场景**:
- 低光环境使用
- 减少眼睛疲劳
- 节省设备电量 (OLED 屏幕)
- 专业设计工具

### 3. 紧凑模式 (Compact Mode)

内置 `compactAlgorithm` 算法，减少组件间距和尺寸，适合高密度信息展示。

**适用场景**:
- 数据密集型应用
- 小屏幕设备
- 监控面板
- 后台管理系统

### 4. Token 系统

三层 Token 架构提供细粒度的主题控制:

- **Seed Token**: 基础设计令牌 (颜色、字体、尺寸等)
- **Map Token**: 派生令牌 (从 Seed Token 计算得出)
- **Alias Token**: 别名令牌 (组件使用的语义化令牌)

### 5. 主题持久化

通过 LocalStorage 保存用户主题偏好，刷新页面后自动恢复。

### 6. 响应式主题

自动跟随系统主题设置，支持 `prefers-color-scheme` 媒体查询。

---

## Token 系统详解

### Token 层级架构

Ant Design 的 Design Token 分为三个层级:

```
Seed Token (基础令牌)
    ↓
Map Token (映射令牌)
    ↓
Alias Token (别名令牌)
    ↓
Component Token (组件令牌)
```

### Seed Token (种子令牌)

Seed Token 是最基础的设计令牌，定义原始的设计值。

**常用 Seed Token**:

```typescript
const seedToken = {
  // 品牌色
  colorPrimary: '#1677ff',        // 主色
  colorSuccess: '#52c41a',        // 成功色
  colorWarning: '#faad14',        // 警告色
  colorError: '#ff4d4f',          // 错误色
  colorInfo: '#1677ff',           // 信息色

  // 中性色
  colorBgBase: '#ffffff',         // 背景基准色
  colorTextBase: '#000000',       // 文本基准色
  colorBorder: '#d9d9d9',         // 边框色

  // 圆角
  borderRadius: 6,                // 圆角

  // 阴影
  boxShadow: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',

  // 字体
  fontSize: 14,                   // 基础字号
  lineHeight: 1.5714,             // 行高
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
};
```

### Map Token (映射令牌)

Map Token 从 Seed Token 派生，定义具体的颜色映射。

**常用 Map Token**:

```typescript
const mapToken = {
  // 背景色
  colorBgContainer: '#ffffff',
  colorBgElevated: '#ffffff',
  colorBgLayout: '#f5f5f5',
  colorBgSpotlight: 'rgba(0, 0, 0, 0.85)',

  // 文本色
  colorText: 'rgba(0, 0, 0, 0.88)',
  colorTextSecondary: 'rgba(0, 0, 0, 0.65)',
  colorTextTertiary: 'rgba(0, 0, 0, 0.45)',
  colorTextQuaternary: 'rgba(0, 0, 0, 0.25)',

  // 边框色
  colorBorderSecondary: '#f0f0f0',

  // 填充色
  colorFillSecondary: 'rgba(0, 0, 0, 0.06)',
  colorFillTertiary: 'rgba(0, 0, 0, 0.04)',
  colorFillQuaternary: 'rgba(0, 0, 0, 0.02)',
};
```

### Alias Token (别名令牌)

Alias Token 是语义化的令牌别名，供组件直接使用。

**常用 Alias Token**:

```typescript
const aliasToken = {
  // 组件背景
  colorBgContainer: mapToken.colorBgContainer,
  colorBgElevated: mapToken.colorBgElevated,
  colorBgLayout: mapToken.colorBgLayout,

  // 组件文本
  colorText: mapToken.colorText,
  colorTextSecondary: mapToken.colorTextSecondary,
  colorTextTertiary: mapToken.colorTextTertiary,

  // 组件边框
  colorBorder: mapToken.colorBorder,
  colorBorderSecondary: mapToken.colorBorderSecondary,
};
```

### Token 优先级

Token 的覆盖优先级从高到低:

1. **组件 Token**: 特定组件的 Token
2. **ConfigProvider Token**: 通过 ConfigProvider 配置的 Token
3. **全局主题 Token**: 全局主题配置的 Token
4. **默认 Token**: Ant Design 默认的 Token

---

## 基础主题配置

### 示例 1: 修改主色

最简单的主题定制是修改主色 (Primary Color)。

```typescript
import React from 'react';
import { ConfigProvider, Button, Card, Space } from 'antd';

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#722ed1', // 修改主色为紫色
        },
      }}
    >
      <Card title="紫色主题示例">
        <Space>
          <Button type="primary">主按钮</Button>
          <Button>默认按钮</Button>
          <Button type="dashed">虚线按钮</Button>
          <Button type="link">链接按钮</Button>
        </Space>
      </Card>
    </ConfigProvider>
  );
};

export default App;
```

**效果**:
- 所有使用 `type="primary"` 的组件都会使用紫色
- 包括按钮、链接、选中状态等
- 其他颜色 (Success、Warning、Error) 保持默认

### 示例 2: 完整主题配置

配置多个主题 Token，创建完整的品牌主题。

```typescript
import React from 'react';
import { ConfigProvider, Button, Input, Card, Form, Space, Typography } from 'antd';

const { Title } = Typography;

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 品牌色
          colorPrimary: '#1890ff',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorInfo: '#1677ff',

          // 字体
          fontSize: 15,
          fontSizeHeading1: 38,
          fontSizeHeading2: 30,
          fontSizeHeading3: 24,
          fontSizeHeading4: 20,
          fontSizeHeading5: 16,

          // 圆角
          borderRadius: 8,
          borderRadiusLG: 12,
          borderRadiusSM: 6,

          // 间距
          marginXS: 8,
          marginSM: 12,
          margin: 16,
          marginMD: 20,
          marginLG: 24,
          marginXL: 32,

          // 阴影
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
          boxShadowLG: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
        },
        components: {
          Button: {
            borderRadius: 6,
            controlHeight: 38,
            controlHeightLG: 46,
            controlHeightSM: 30,
          },
          Input: {
            borderRadius: 6,
            controlHeight: 38,
            controlHeightLG: 46,
            controlHeightSM: 30,
            paddingContentHorizontal: 12,
          },
          Card: {
            borderRadiusLG: 12,
          },
        },
      }}
    >
      <div style={{ padding: 24 }}>
        <Title level={2}>完整主题配置</Title>
        <Card>
          <Form layout="vertical">
            <Form.Item label="用户名">
              <Input placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item label="密码">
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" size="large">
                  提交
                </Button>
                <Button size="large">取消</Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </ConfigProvider>
  );
};

export default App;
```

**关键配置说明**:
- `token`: 全局 Token 配置
- `components`: 组件级 Token 配置
- 优先级: 组件 Token > 全局 Token

### 示例 3: 组件级主题定制

为特定组件定制样式，而不影响全局主题。

```typescript
import React from 'react';
import { ConfigProvider, Button, Card, Space, DatePicker, Select } from 'antd';

const App: React.FC = () => {
  return (
    <Space direction="vertical" size="large" style={{ display: 'flex' }}>
      {/* 全局主题: 蓝色 */}
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1677ff',
          },
        }}
      >
        <Card title="蓝色主题 (默认)">
          <Space>
            <Button type="primary">主要按钮</Button>
            <Button>次要按钮</Button>
            <DatePicker />
            <Select placeholder="选择选项" style={{ width: 120 }} />
          </Space>
        </Card>
      </ConfigProvider>

      {/* 局部主题: 绿色 */}
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#52c41a',
          },
          components: {
            Button: {
              colorPrimary: '#00b96b',
              algorithm: true, // 启用算法
            },
          },
        }}
      >
        <Card title="绿色主题 (局部)">
          <Space>
            <Button type="primary">主要按钮</Button>
            <Button>次要按钮</Button>
          </Space>
        </Card>
      </ConfigProvider>

      {/* 局部主题: 紫色 */}
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#722ed1',
          },
        }}
      >
        <Card title="紫色主题 (局部)">
          <Space>
            <Button type="primary">主要按钮</Button>
            <Button>次要按钮</Button>
          </Space>
        </Card>
      </ConfigProvider>
    </Space>
  );
};

export default App;
```

**应用场景**:
- 不同模块使用不同主题
- 特殊页面突出显示
- A/B 测试不同主题

---

## 深色模式实现

### 示例 4: 深色模式自动跟随系统

使用 `darkAlgorithm` 实现深色模式，自动跟随系统主题设置。

```typescript
import React, { useEffect, useState } from 'react';
import { ConfigProvider, theme, Button, Card, Layout, Typography, Space } from 'antd';
import { BulbOutlined, BulbFilled } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

interface ThemeConfig {
  algorithm: typeof theme.defaultAlgorithm | typeof theme.darkAlgorithm;
  token: {
    colorPrimary: string;
    borderRadius?: number;
  };
}

const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 检测系统主题偏好
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // 初始化主题
    setIsDarkMode(mediaQuery.matches);

    // 监听系统主题变化
    const handleChange = (e: MediaQueryListEvent) => {
      setIsDarkMode(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  // 主题配置
  const themeConfig: ThemeConfig = {
    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 8,
    },
  };

  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isDarkMode ? '#141414' : '#001529',
          padding: '0 24px',
        }}>
          <Title level={3} style={{ color: '#fff', margin: 0 }}>
            {isDarkMode ? '🌙 深色模式' : '☀️ 浅色模式'}
          </Title>
          <Button
            type="primary"
            icon={isDarkMode ? <BulbFilled /> : <BulbOutlined />}
            onClick={() => setIsDarkMode(!isDarkMode)}
          >
            {isDarkMode ? '切换到浅色' : '切换到深色'}
          </Button>
        </Header>
        <Content style={{ padding: '24px' }}>
          <Space direction="vertical" size="large" style={{ display: 'flex' }}>
            <Card>
              <Title level={4}>当前主题状态</Title>
              <Text>
                系统主题偏好: {window.matchMedia('(prefers-color-scheme: dark)').matches ? '深色' : '浅色'}
              </Text>
              <br />
              <Text>
                应用主题: {isDarkMode ? '深色模式' : '浅色模式'}
              </Text>
            </Card>

            <Card title="组件示例">
              <Space>
                <Button type="primary">主要按钮</Button>
                <Button>默认按钮</Button>
                <Button type="dashed">虚线按钮</Button>
                <Button type="link">链接按钮</Button>
              </Space>
            </Card>

            <Card title="表单组件">
              <Space direction="vertical" style={{ display: 'flex' }}>
                <Button type="primary" block>
                  区块按钮
                </Button>
                <Button danger>危险按钮</Button>
              </Space>
            </Card>
          </Space>
        </Content>
      </Layout>
    </ConfigProvider>
  );
};

export default App;
```

**实现要点**:
- 使用 `window.matchMedia('(prefers-color-scheme: dark)')` 检测系统主题
- 监听 `change` 事件自动跟随系统主题切换
- 通过 `theme.darkAlgorithm` 启用深色算法
- 深色模式下自动调整所有组件颜色

### 深色模式算法说明

Ant Design 提供三种内置算法:

1. **defaultAlgorithm**: 默认浅色主题算法
2. **darkAlgorithm**: 深色主题算法
3. **compactAlgorithm**: 紧凑模式算法

**组合使用**:

```typescript
import { theme } from 'antd';

// 深色 + 紧凑
const themeConfig = {
  algorithm: [theme.darkAlgorithm, theme.compactAlgorithm],
};

// 仅紧凑
const themeConfig = {
  algorithm: theme.compactAlgorithm,
};

// 默认
const themeConfig = {
  algorithm: theme.defaultAlgorithm,
};
```

---

## 动态主题切换

### 示例 5: 多主题系统 (预设主题 + 自定义)

实现完整的主题切换系统，支持预设主题和自定义主题。

```typescript
import React, { useState, useEffect } from 'react';
import { ConfigProvider, theme, Button, Card, Radio, Space, Typography, ColorPicker, message } from 'antd';
import { BgColorsOutlined, CheckOutlined } from '@ant-design/icons';
import type { ThemeConfig } from 'antd';
import type { Color } from 'antd/es/color-picker';

const { Title, Text } = Typography;

// 预设主题
const presetThemes = {
  default: {
    name: '默认蓝色',
    colorPrimary: '#1677ff',
  },
  green: {
    name: '清新绿色',
    colorPrimary: '#52c41a',
  },
  purple: {
    name: '优雅紫色',
    colorPrimary: '#722ed1',
  },
  pink: {
    name: '活力粉色',
    colorPrimary: '#eb2f96',
  },
  orange: {
    name: '温暖橙色',
    colorPrimary: '#fa8c16',
  },
  cyan: {
    name: '科技青色',
    colorPrimary: '#13c2c2',
  },
};

// LocalStorage 键
const THEME_KEY = 'antd-theme-preference';
const DARK_MODE_KEY = 'antd-dark-mode';

const App: React.FC = () => {
  const [currentTheme, setCurrentTheme] = useState<string>('default');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [customColor, setCustomColor] = useState<string>('#1677ff');

  // 从 LocalStorage 加载主题偏好
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_KEY);
    const savedDarkMode = localStorage.getItem(DARK_MODE_KEY);

    if (savedTheme) {
      setCurrentTheme(savedTheme);
    }

    if (savedDarkMode) {
      setIsDarkMode(savedDarkMode === 'true');
    }
  }, []);

  // 保存主题偏好到 LocalStorage
  const saveThemePreference = (themeValue: string, darkMode: boolean) => {
    localStorage.setItem(THEME_KEY, themeValue);
    localStorage.setItem(DARK_MODE_KEY, String(darkMode));
  };

  // 切换预设主题
  const handlePresetThemeChange = (themeValue: string) => {
    setCurrentTheme(themeValue);
    saveThemePreference(themeValue, isDarkMode);
    message.success(`已切换到 ${presetThemes[themeValue as keyof typeof presetThemes].name}`);
  };

  // 切换深色模式
  const toggleDarkMode = () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    saveThemePreference(currentTheme, newDarkMode);
    message.success(newDarkMode ? '已开启深色模式' : '已关闭深色模式');
  };

  // 自定义颜色
  const handleCustomColorChange = (_: Color, hex: string) => {
    setCustomColor(hex);
    setCurrentTheme('custom');
    saveThemePreference('custom', isDarkMode);
    message.success(`已应用自定义颜色: ${hex}`);
  };

  // 获取当前主题配置
  const getThemeConfig = (): ThemeConfig => {
    const colorPrimary = currentTheme === 'custom'
      ? customColor
      : presetThemes[currentTheme as keyof typeof presetThemes]?.colorPrimary || '#1677ff';

    return {
      algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
      token: {
        colorPrimary,
        borderRadius: 8,
      },
      components: {
        Button: {
          borderRadius: 6,
        },
        Input: {
          borderRadius: 6,
        },
        Card: {
          borderRadiusLG: 12,
        },
      },
    };
  };

  return (
    <ConfigProvider theme={getThemeConfig()}>
      <div style={{
        padding: '24px',
        minHeight: '100vh',
        background: isDarkMode ? '#000000' : '#f0f2f5',
      }}>
        <Space direction="vertical" size="large" style={{ display: 'flex' }}>
          {/* 主题选择器 */}
          <Card>
            <Space direction="vertical" size="middle" style={{ display: 'flex', width: '100%' }}>
              <Title level={4}>
                <BgColorsOutlined /> 主题选择器
              </Title>

              {/* 预设主题 */}
              <div>
                <Text strong>预设主题:</Text>
                <div style={{ marginTop: 12 }}>
                  <Radio.Group
                    value={currentTheme}
                    onChange={(e) => handlePresetThemeChange(e.target.value)}
                    optionType="button"
                    buttonStyle="solid"
                  >
                    {Object.entries(presetThemes).map(([key, { name, colorPrimary }]) => (
                      <Radio.Button
                        key={key}
                        value={key}
                        style={{
                          backgroundColor: currentTheme === key ? colorPrimary : undefined,
                          borderColor: colorPrimary,
                          color: currentTheme === key ? '#fff' : undefined,
                        }}
                      >
                        {currentTheme === key && <CheckOutlined />}
                        {' '}
                        {name}
                      </Radio.Button>
                    ))}
                  </Radio.Group>
                </div>
              </div>

              {/* 自定义颜色 */}
              <div>
                <Text strong>自定义颜色:</Text>
                <div style={{ marginTop: 12 }}>
                  <ColorPicker
                    value={customColor}
                    onChange={handleCustomColorChange}
                    showText
                    format="hex"
                  />
                  {currentTheme === 'custom' && (
                    <Text type="secondary" style={{ marginLeft: 12 }}>
                      (当前使用自定义颜色)
                    </Text>
                  )}
                </div>
              </div>

              {/* 深色模式切换 */}
              <div>
                <Text strong>主题模式:</Text>
                <div style={{ marginTop: 12 }}>
                  <Button
                    type={isDarkMode ? 'primary' : 'default'}
                    onClick={toggleDarkMode}
                    icon={isDarkMode ? '🌙' : '☀️'}
                  >
                    {isDarkMode ? '深色模式' : '浅色模式'}
                  </Button>
                  <Text type="secondary" style={{ marginLeft: 12 }}>
                    {isDarkMode ? '(当前为深色主题)' : '(当前为浅色主题)'}
                  </Text>
                </div>
              </div>
            </Space>
          </Card>

          {/* 预览区域 */}
          <Card title="组件预览">
            <Space direction="vertical" size="middle" style={{ display: 'flex' }}>
              <Space>
                <Button type="primary">主要按钮</Button>
                <Button>默认按钮</Button>
                <Button type="dashed">虚线按钮</Button>
                <Button type="link">链接按钮</Button>
                <Button danger>危险按钮</Button>
              </Space>

              <Space>
                <Button type="primary" size="large">
                  大号按钮
                </Button>
                <Button size="large">大号按钮</Button>
                <Button type="primary" size="small">
                  小号按钮
                </Button>
                <Button size="small">小号按钮</Button>
              </Space>

              <Space>
                <Button type="primary" icon={<CheckOutlined />}>
                  带图标
                </Button>
                <Button type="primary" loading>
                  加载中
                </Button>
                <Button type="primary" disabled>
                  禁用状态
                </Button>
              </Space>
            </Space>
          </Card>

          {/* 当前主题信息 */}
          <Card title="当前主题配置">
            <Space direction="vertical" style={{ display: 'flex' }}>
              <Text>
                <strong>主题名称:</strong> {currentTheme === 'custom' ? '自定义' : presetThemes[currentTheme as keyof typeof presetThemes]?.name}
              </Text>
              <Text>
                <strong>主色调:</strong> {currentTheme === 'custom' ? customColor : presetThemes[currentTheme as keyof typeof presetThemes]?.colorPrimary}
              </Text>
              <Text>
                <strong>主题模式:</strong> {isDarkMode ? '深色模式' : '浅色模式'}
              </Text>
            </Space>
          </Card>
        </Space>
      </div>
    </ConfigProvider>
  );
};

export default App;
```

**功能特性**:
- 6 种预设主题可选
- 自定义颜色选择器
- 深色/浅色模式切换
- LocalStorage 持久化
- 实时预览组件效果
- 主题配置信息展示

---

## 紧凑模式实现

### 示例 6: 紧凑模式实现

使用 `compactAlgorithm` 减少组件间距和尺寸，实现高密度信息展示。

```typescript
import React, { useState } from 'react';
import { ConfigProvider, theme, Button, Table, Card, Space, Typography, Switch, Tag } from 'antd';

const { Title, Text } = Typography;

interface DataType {
  key: number;
  name: string;
  age: number;
  address: string;
  tags: string[];
}

const columns = [
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    render: (text: string) => <a>{text}</a>,
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
  {
    title: '标签',
    key: 'tags',
    dataIndex: 'tags',
    render: (tags: string[]) => (
      <>
        {tags.map((tag) => {
          let color = tag.length > 5 ? 'geekblue' : 'green';
          if (tag === 'loser') {
            color = 'volcano';
          }
          return (
            <Tag color={color} key={tag}>
              {tag.toUpperCase()}
            </Tag>
          );
        })}
      </>
    ),
  },
  {
    title: '操作',
    key: 'action',
    render: (_: any, record: DataType) => (
      <Space size="small">
        <Button type="link" size={record.compact ? 'small' : 'middle'}>
          编辑
        </Button>
        <Button type="link" size={record.compact ? 'small' : 'middle'}>
          删除
        </Button>
      </Space>
    ),
  },
];

const data: DataType[] = [
  {
    key: 1,
    name: '张三',
    age: 32,
    address: '北京市朝阳区',
    tags: ['developer', 'nice'],
  },
  {
    key: 2,
    name: '李四',
    age: 42,
    address: '上海市浦东新区',
    tags: ['loser'],
  },
  {
    key: 3,
    name: '王五',
    age: 28,
    address: '广州市天河区',
    tags: ['cool', 'teacher'],
  },
];

const App: React.FC = () => {
  const [isCompact, setIsCompact] = useState(false);

  const themeConfig = {
    algorithm: isCompact
      ? [theme.defaultAlgorithm, theme.compactAlgorithm]
      : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
    },
  };

  return (
    <ConfigProvider theme={themeConfig}>
      <div style={{ padding: '24px' }}>
        <Space direction="vertical" size="large" style={{ display: 'flex' }}>
          {/* 控制面板 */}
          <Card>
            <Space>
              <Text strong>紧凑模式:</Text>
              <Switch
                checked={isCompact}
                onChange={setIsCompact}
                checkedChildren="开启"
                unCheckedChildren="关闭"
              />
              {isCompact && (
                <Tag color="blue">已启用紧凑模式</Tag>
              )}
            </Space>
          </Card>

          {/* 按钮示例 */}
          <Card title="按钮组件">
            <Space direction="vertical" style={{ display: 'flex' }}>
              <Text>普通按钮:</Text>
              <Space>
                <Button type="primary">主要按钮</Button>
                <Button>默认按钮</Button>
                <Button type="dashed">虚线按钮</Button>
                <Button type="link">链接按钮</Button>
              </Space>

              <Text>不同尺寸:</Text>
              <Space>
                <Button type="primary" size="large">
                  大号按钮
                </Button>
                <Button type="primary">
                  中号按钮
                </Button>
                <Button type="primary" size="small">
                  小号按钮
                </Button>
              </Space>

              <Text>区块按钮:</Text>
              <Button type="primary" block>
                区块按钮
              </Button>
            </Space>
          </Card>

          {/* 表格示例 */}
          <Card title="数据表格">
            <Table
              columns={columns}
              dataSource={data}
              size={isCompact ? 'small' : 'middle'}
              pagination={{
                pageSize: isCompact ? 10 : 5,
                size: isCompact ? 'small' : 'default',
              }}
            />
          </Card>

          {/* 表单示例 */}
          <Card title="表单组件">
            <Space direction="vertical" style={{ display: 'flex' }}>
              <Space>
                <Button type="primary" size={isCompact ? 'small' : 'middle'}>
                  提交
                </Button>
                <Button size={isCompact ? 'small' : 'middle'}>
                  取消
                </Button>
                <Button danger size={isCompact ? 'small' : 'middle'}>
                  删除
                </Button>
              </Space>
            </Space>
          </Card>
        </Space>
      </div>
    </ConfigProvider>
  );
};

export default App;
```

**紧凑模式效果**:
- 组件高度减小
- 间距缩小
- 表格行高减小
- 字号略微减小
- 适合数据密集型应用

---

## Next.js SSR 主题处理

### 示例 7: Next.js SSR 主题配置

在 Next.js 中使用 Ant Design 主题，需要处理 SSR 环境和客户端状态同步。

**文件结构**:
```
app/
├── layout.tsx       # 根布局
├── page.tsx         # 主页面
├── theme-provider.tsx  # 主题上下文
└── globals.css      # 全局样式
```

**theme-provider.tsx**:
```typescript
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import type { ThemeConfig } from 'antd';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);

    // 从 LocalStorage 读取主题偏好
    const savedTheme = localStorage.getItem('antd-dark-mode');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'true');
    } else {
      // 检测系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDark);
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('antd-dark-mode', String(newMode));
  };

  const themeConfig: ThemeConfig = {
    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 8,
    },
  };

  // 避免服务端渲染不匹配
  if (!isClient) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleDarkMode }}>
      <ConfigProvider theme={themeConfig}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};
```

**app/layout.tsx**:
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from './theme-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Next.js + Ant Design 主题示例',
  description: 'Ant Design 5 主题定制示例',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
```

**app/page.tsx**:
```typescript
'use client';

import React from 'react';
import { Button, Card, Space, Typography, Layout } from 'antd';
import { useTheme } from './theme-provider';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const { isDarkMode, toggleDarkMode } = useTheme();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isDarkMode ? '#141414' : '#001529',
          padding: '0 24px',
        }}
      >
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          Next.js + Ant Design 主题示例
        </Title>
        <Button
          type="primary"
          onClick={toggleDarkMode}
        >
          {isDarkMode ? '🌙 切换到浅色' : '☀️ 切换到深色'}
        </Button>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Space direction="vertical" size="large" style={{ display: 'flex' }}>
          <Card>
            <Title level={4}>当前主题</Title>
            <Text>{isDarkMode ? '🌙 深色模式' : '☀️ 浅色模式'}</Text>
          </Card>

          <Card title="按钮示例">
            <Space>
              <Button type="primary">主要按钮</Button>
              <Button>默认按钮</Button>
              <Button type="dashed">虚线按钮</Button>
              <Button type="link">链接按钮</Button>
            </Space>
          </Card>
        </Space>
      </Content>
    </Layout>
  );
}
```

**app/globals.css**:
```css
/* 避免服务端渲染不匹配 */
:root {
  --antd-prefix: ant;
}
```

**SSR 注意事项**:
1. 使用 `'use client'` 标记客户端组件
2. 在 `useEffect` 中读取 LocalStorage
3. 使用 `isClient` 状态避免水合不匹配
4. 主题状态通过 Context 传递
5. 避免在服务端调用浏览器 API

---

## 最佳实践

### 1. 主题组织

**推荐方式**: 创建统一的主题配置文件。

**themes/index.ts**:
```typescript
import { theme } from 'antd';
import type { ThemeConfig } from 'antd';

export const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    borderRadius: 8,
  },
};

export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#1677ff',
    colorBgBase: '#141414',
  },
};

export const compactTheme: ThemeConfig = {
  algorithm: theme.compactAlgorithm,
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
  },
};
```

**使用**:
```typescript
import { lightTheme, darkTheme } from './themes';

<ConfigProvider theme={isDarkMode ? darkTheme : lightTheme}>
  <App />
</ConfigProvider>
```

### 2. 组件 Token 定制

针对特定组件定制样式:

```typescript
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: '#722ed1',
        algorithm: true,
      },
      Input: {
        colorBorder: '#d9d9d9',
        borderRadius: 6,
      },
      Table: {
        headerBg: '#fafafa',
        headerColor: 'rgba(0, 0, 0, 0.88)',
      },
    },
  }}
>
  <App />
</ConfigProvider>
```

### 3. 主题切换性能优化

**避免频繁切换**:
```typescript
import { debounce } from 'lodash';

const debouncedToggleTheme = debounce(() => {
  toggleDarkMode();
}, 300);
```

**使用 CSS 变量** (高级用法):
```typescript
// 通过 CSS 变量控制主题
const themeConfig = {
  token: {
    colorPrimary: 'var(--primary-color)',
  },
};
```

### 4. 主题持久化

**使用 LocalStorage**:
```typescript
// 保存主题偏好
localStorage.setItem('theme', JSON.stringify({
  mode: 'dark',
  primaryColor: '#1677ff',
}));

// 读取主题偏好
const savedTheme = JSON.parse(localStorage.getItem('theme') || '{}');
```

**URL 参数控制** (用于演示):
```typescript
const urlParams = new URLSearchParams(window.location.search);
const themeMode = urlParams.get('theme') || 'light';
```

### 5. 主题测试

**测试不同主题**:
```typescript
import { render } from '@testing-library/react';
import { ConfigProvider } from 'antd';

const renderWithTheme = (component: React.ReactNode, theme: ThemeConfig) => {
  return render(
    <ConfigProvider theme={theme}>
      {component}
    </ConfigProvider>
  );
};

test('按钮在深色模式下正确渲染', () => {
  const { container } = renderWithTheme(
    <Button type="primary">点击</Button>,
    { algorithm: theme.darkAlgorithm }
  );

  expect(container.querySelector('.ant-btn-primary')).toBeInTheDocument();
});
```

---

## 常见问题

### Q1: 如何迁移从 Ant Design v4 到 v5?

**A**: v5 使用 CSS-in-JS，不再需要 Less 配置。

**v4 方式** (已废弃):
```typescript
// ❌ v4 方式，v5 中不再支持
import less from 'less';

const lessVars = {
  '@primary-color': '#1677ff',
};
```

**v5 方式**:
```typescript
// ✅ v5 方式
import { ConfigProvider } from 'antd';

<ConfigProvider theme={{ token: { colorPrimary: '#1677ff' } }}>
  <App />
</ConfigProvider>
```

### Q2: 主题切换时页面闪烁如何解决?

**A**: 使用 `useEffect` 和 `isClient` 状态避免水合不匹配。

```typescript
const [isClient, setIsClient] = useState(false);

useEffect(() => {
  setIsClient(true);
}, []);

if (!isClient) {
  return null; // 或返回加载状态
}
```

### Q3: 如何实现多主题并存?

**A**: 使用嵌套的 `ConfigProvider`。

```typescript
<ConfigProvider theme={{ token: { colorPrimary: '#1677ff' } }}>
  <App>
    <ConfigProvider theme={{ token: { colorPrimary: '#52c41a' } }}>
      <SpecialSection />
    </ConfigProvider>
  </App>
</ConfigProvider>
```

### Q4: 如何自定义特定组件的 Token?

**A**: 使用 `components` 配置。

```typescript
<ConfigProvider
  theme={{
    components: {
      Button: {
        colorPrimary: '#722ed1',
        algorithm: true,
      },
    },
  }}
>
  <App />
</ConfigProvider>
```

### Q5: 深色模式下如何保持可读性?

**A**: 使用 `darkAlgorithm` 确保对比度符合 WCAG 标准。

```typescript
const themeConfig = {
  algorithm: theme.darkAlgorithm, // 自动计算对比度
  token: {
    colorBgBase: '#141414',
  },
};
```

### Q6: 如何实现主题切换动画?

**A**: 使用 CSS transition。

```css
* {
  transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}
```

---

## 参考资源

### 官方文档
- [Ant Design 主题定制 - 英文](https://ant.design/docs/react/customize-theme)
- [Ant Design 主题定制 - 中文](https://ant.design/docs/react/customize-theme-cn)
- [Ant Design 深色模式规范](https://ant.design/docs/spec/dark/)
- [Ant Design Theme Editor](https://ant.design/theme-editor)

### 技术文章
- [Ant Design meets CSS Variables](https://ant.design/docs/blog/css-var-plan)
- [主题拓展 - ConfigProvider Style](https://ant.design/docs/blog/config-provider-style-cn)
- [How To Toggle Dark Theme With Ant Design 5.0](https://betterprogramming.pub/how-to-toggle-dark-theme-with-ant-design-5-0-eb68552f62b8)

### 社区资源
- [ant-design-style - 业务级 CSS-in-JS 方案](https://ant-design.github.io/antd-style/zh-CN/guide/)
- [Ant Design Token System RFC](https://github.com/ant-design/ant-design/discussions/36884)

---

## 总结

Ant Design 5 的主题系统基于 CSS-in-JS 和 Design Token，提供了强大的主题定制能力:

**核心优势**:
- 运行时动态主题，无需重新编译
- 内置深色模式和紧凑模式
- 三层 Token 架构 (Seed → Map → Alias)
- 组件级主题定制
- LocalStorage 持久化支持
- 自动跟随系统主题

**适用场景**:
- 品牌主题定制
- 多租户系统
- 深色模式应用
- 高密度数据展示
- 主题切换演示
- A/B 主题测试

**最佳实践**:
- 使用统一的主题配置文件
- 合理使用组件 Token 定制
- 实现 LocalStorage 持久化
- 避免频繁主题切换影响性能
- 测试不同主题下的组件表现

**版本要求**:
- Ant Design >= 5.0.0
- React >= 16.14.0 (推荐 18.x)
- Next.js >= 13 (如果使用 SSR)

---

**最后更新**: 2026-02-10
**Ant Design 版本**: 5.x
**维护者**: ccplugin-market
