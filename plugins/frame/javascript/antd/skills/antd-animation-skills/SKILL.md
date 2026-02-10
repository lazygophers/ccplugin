---
name: antd-animation-skills
description: Ant Design 动画系统完整指南 - Motion 动画、过渡效果、自定义动画、性能优化
---

# antd-animation: Ant Design 动画系统完整指南

Ant Design 动画系统基于 CSS transitions、CSS animations 和 Motion 高级动画机制，提供流畅的 UI 交互体验。本文档全面介绍 Ant Design 5.x 的动画系统，包括基础动画、Motion API、自定义动画、性能优化等。

---

## 概述

### 核心功能

- **CSS Transitions** - 基于 CSS 的过渡效果（颜色、尺寸、位置等）
- **CSS Animations** - 关键帧动画，支持复杂动画序列
- **Motion 高级动画** - Ant Design 5.x 内置动画系统
- **组件内置动画** - 各组件自带的进入/退出/状态切换动画
- **自定义动画** - 支持完全自定义的动画配置
- **性能优化** - GPU 加速、动画节流、减少重绘
- **可配置性** - 通过 ConfigProvider 全局配置动画参数

### 动画分类

```
Ant Design 动画系统
├── CSS Transitions          # CSS 过渡效果
│   ├── 状态变化过渡
│   ├── 悬停效果
│   └── 焦点效果
├── CSS Animations           # CSS 关键帧动画
│   ├── 进入动画
│   ├── 退出动画
│   └── 循环动画
├── Motion 动画              # 高级动画系统
│   ├── 组件级动画
│   ├── 列表动画
│   └── 页面切换动画
└── 自定义动画               # 完全自定义
    ├── @keyframes
    ├── Motion Config
    └── 第三方动画库集成
```

### 动画性能原则

- **优先使用 CSS 动画** - CSS 动画由浏览器优化，性能优于 JavaScript 动画
- **GPU 加速** - 使用 `transform` 和 `opacity` 触发硬件加速
- **避免动画布局属性** - 避免动画 `width`、`height`、`left`、`top` 等属性
- **使用 will-change** - 提前告知浏览器哪些属性会动画
- **减少重绘和回流** - 动画期间避免修改 DOM 结构

---

## CSS Transitions

### 1. 基础过渡效果

CSS transitions 是最简单的动画形式，用于平滑过渡元素状态变化：

```tsx
import { Button } from 'antd';

function TransitionExample() {
  return (
    <Button
      style={{
        transition: 'all 0.3s ease-in-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      Hover Me
    </Button>
  );
}
```

### 2. Transition 属性详解

```tsx
function TransitionProperties() {
  return (
    <Button
      style={{
        // 1. transition-property: 指定要动画的属性
        transitionProperty: 'all', // 'none' | 'all' | 属性列表

        // 2. transition-duration: 动画持续时间
        transitionDuration: '0.3s', // 秒或毫秒 (300ms)

        // 3. transition-timing-function: 动画缓动函数
        transitionTimingFunction: 'ease-in-out', // 'linear' | 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'cubic-bezier(...)'

        // 4. transition-delay: 动画延迟
        transitionDelay: '0s', // 秒或毫秒

        // 简写形式
        transition: 'all 0.3s ease-in-out 0s',
      }}
    >
      Animated Button
    </Button>
  );
}
```

### 3. 颜色过渡

```tsx
import { Button, Card } from 'antd';

function ColorTransition() {
  return (
    <div>
      {/* 背景色过渡 */}
      <Button
        style={{
          backgroundColor: '#1890ff',
          color: '#fff',
          transition: 'background-color 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#40a9ff';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#1890ff';
        }}
      >
        Background Color Transition
      </Button>

      {/* 边框色过渡 */}
      <Card
        style={{
          border: '2px solid #d9d9d9',
          transition: 'border-color 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = '#1890ff';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = '#d9d9d9';
        }}
      >
        Border Color Transition
      </Card>
    </div>
  );
}
```

### 4. 尺寸和位置过渡

```tsx
function SizePositionTransition() {
  return (
    <div>
      {/* 尺寸过渡 */}
      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          transition: 'transform 0.3s ease',
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.2)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
        }}
      >
        Scale Animation
      </div>

      {/* 位置过渡 */}
      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#52c41a',
          transition: 'transform 0.3s ease',
          cursor: 'pointer',
          marginTop: 16,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateX(20px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateX(0)';
        }}
      >
        Translate Animation
      </div>
    </div>
  );
}
```

### 5. 透明度过渡

```tsx
function OpacityTransition() {
  const [visible, setVisible] = useState(true);

  return (
    <div>
      <Button onClick={() => setVisible(!visible)}>
        Toggle Visibility
      </Button>

      <div
        style={{
          opacity: visible ? 1 : 0,
          transition: 'opacity 0.3s ease-in-out',
          marginTop: 16,
          padding: 24,
          backgroundColor: '#f0f0f0',
        }}
      >
        This content fades in and out smoothly
      </div>
    </div>
  );
}
```

### 6. 阴影过渡

```tsx
import { Card } from 'antd';

function ShadowTransition() {
  return (
    <Card
      style={{
        transition: 'box-shadow 0.3s ease',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.2)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
      }}
    >
      Hover me to see shadow animation
    </Card>
  );
}
```

### 7. 缓动函数详解

```tsx
function EasingFunctions() {
  const easings = [
    { name: 'linear', value: 'linear' },
    { name: 'ease', value: 'ease' },
    { name: 'ease-in', value: 'ease-in' },
    { name: 'ease-out', value: 'ease-out' },
    { name: 'ease-in-out', value: 'ease-in-out' },
    { name: 'cubic-bezier', value: 'cubic-bezier(0.68, -0.55, 0.27, 1.55)' },
  ];

  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      {easings.map((easing) => (
        <Button
          key={easing.name}
          style={{
            transition: `transform 1s ${easing.value}`,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateX(100px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateX(0)';
          }}
        >
          {easing.name}
        </Button>
      ))}
    </div>
  );
}
```

---

## CSS Animations

### 1. 基础关键帧动画

CSS animations 使用 `@keyframes` 定义关键帧，实现复杂动画序列：

```tsx
// styles.css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

// 使用动画
function KeyframeAnimation() {
  return (
    <div>
      {/* 淡入动画 */}
      <div
        style={{
          animation: 'fadeIn 1s ease-in',
        }}
      >
        Fade In Content
      </div>

      {/* 滑入动画 */}
      <div
        style={{
          animation: 'slideIn 0.5s ease-out',
        }}
      >
        Slide In Content
      </div>

      {/* 弹跳动画 */}
      <div
        style={{
          animation: 'bounce 1s infinite',
        }}
      >
        Bouncing Element
      </div>
    </div>
  );
}
```

### 2. Animation 属性详解

```tsx
function AnimationProperties() {
  return (
    <div
      style={{
        // 1. animation-name: 动画名称
        animationName: 'fadeIn',

        // 2. animation-duration: 动画持续时间
        animationDuration: '1s',

        // 3. animation-timing-function: 缓动函数
        animationTimingFunction: 'ease-in-out',

        // 4. animation-delay: 动画延迟
        animationDelay: '0.5s',

        // 5. animation-iteration-count: 动画迭代次数
        animationIterationCount: 'infinite', // 数字或 'infinite'

        // 6. animation-direction: 动画方向
        animationDirection: 'alternate', // 'normal' | 'reverse' | 'alternate' | 'alternate-reverse'

        // 7. animation-fill-mode: 动画填充模式
        animationFillMode: 'forwards', // 'none' | 'forwards' | 'backwards' | 'both'

        // 8. animation-play-state: 动画播放状态
        animationPlayState: 'running', // 'running' | 'paused'

        // 简写形式
        animation: 'fadeIn 1s ease-in-out 0.5s infinite alternate forwards',
      }}
    >
      Animated Element
    </div>
  );
}
```

### 3. 复杂关键帧动画

```tsx
// styles.css
@keyframes complexAnimation {
  0% {
    opacity: 0;
    transform: scale(0.5) rotate(0deg);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2) rotate(180deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(360deg);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.7);
  }
  70% {
    transform: scale(1.1);
    box-shadow: 0 0 0 10px rgba(24, 144, 255, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0);
  }
}

function ComplexKeyframes() {
  return (
    <div>
      {/* 复杂组合动画 */}
      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          animation: 'complexAnimation 2s ease-in-out forwards',
        }}
      >
        Complex Animation
      </div>

      {/* 脉冲效果 */}
      <Button
        type="primary"
        style={{
          animation: 'pulse 2s infinite',
          marginTop: 16,
        }}
      >
        Pulse Button
      </Button>
    </div>
  );
}
```

### 4. 多阶段动画

```tsx
// styles.css
@keyframes multiStage {
  0% {
    transform: translateX(0) scale(1);
    opacity: 0;
  }
  25% {
    transform: translateX(50px) scale(1.1);
    opacity: 0.5;
  }
  50% {
    transform: translateX(100px) scale(1);
    opacity: 1;
  }
  75% {
    transform: translateX(150px) scale(0.9);
    opacity: 0.5;
  }
  100% {
    transform: translateX(200px) scale(1);
    opacity: 0;
  }
}

function MultiStageAnimation() {
  return (
    <div
      style={{
        width: 50,
        height: 50,
        backgroundColor: '#52c41a',
        animation: 'multiStage 4s ease-in-out infinite',
      }}
    />
  );
}
```

### 5. 动态控制动画

```tsx
function DynamicAnimationControl() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [scale, setScale] = useState(1);

  return (
    <div>
      <Button onClick={() => setIsPlaying(!isPlaying)}>
        {isPlaying ? 'Pause' : 'Play'}
      </Button>

      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          marginTop: 16,
          animation: 'bounce 1s infinite',
          animationPlayState: isPlaying ? 'running' : 'paused',
          transform: `scale(${scale})`,
        }}
      />

      <Slider
        min={0.5}
        max={2}
        step={0.1}
        value={scale}
        onChange={setScale}
        style={{ marginTop: 16 }}
      />
    </div>
  );
}
```

---

## Motion 高级动画

### 1. Motion 组件基础

Ant Design 5.x 提供内置的 Motion 动画组件：

```tsx
import { Button, Card } from 'antd';

function MotionBasic() {
  return (
    <div>
      {/* 淡入动画 */}
      <Button
        style={{
          animation: 'antd-fade-in 0.3s ease-in-out',
        }}
      >
        Fade In
      </Button>

      {/* 缩放动画 */}
      <Card
        style={{
          animation: 'antd-zoom-in 0.3s ease-out',
        }}
      >
        Zoom In Card
      </Card>
    </div>
  );
}
```

### 2. 列表动画

```tsx
import { List, Button } from 'antd';

function ListAnimation() {
  const [items, setItems] = useState([
    { id: 1, title: 'Item 1' },
    { id: 2, title: 'Item 2' },
    { id: 3, title: 'Item 3' },
  ]);

  const addItem = () => {
    const newId = items.length + 1;
    setItems([...items, { id: newId, title: `Item ${newId}` }]);
  };

  return (
    <div>
      <Button onClick={addItem} style={{ marginBottom: 16 }}>
        Add Item
      </Button>

      <List
        dataSource={items}
        renderItem={(item, index) => (
          <List.Item
            key={item.id}
            style={{
              animation: 'antd-fade-in 0.3s ease-in-out',
              animationDelay: `${index * 0.1}s`,
            }}
          >
            {item.title}
          </List.Item>
        )}
      />
    </div>
  );
}
```

### 3. 页面切换动画

```tsx
import { useState } from 'react';
import { Button, Card } from 'antd';

function PageTransition() {
  const [page, setPage] = useState(1);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button onClick={() => setPage(1)}>Page 1</Button>
        <Button onClick={() => setPage(2)} style={{ marginLeft: 8 }}>
          Page 2
        </Button>
        <Button onClick={() => setPage(3)} style={{ marginLeft: 8 }}>
          Page 3
        </Button>
      </div>

      <div
        key={page}
        style={{
          animation: 'antd-fade-in 0.3s ease-in-out',
        }}
      >
        <Card>
          <h2>Page {page}</h2>
          <p>This is page {page} content with transition animation.</p>
        </Card>
      </div>
    </div>
  );
}
```

### 4. Modal 动画

```tsx
import { Modal, Button } from 'antd';

function ModalAnimation() {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <Button onClick={() => setVisible(true)}>Open Modal</Button>

      <Modal
        title="Animated Modal"
        open={visible}
        onOk={() => setVisible(false)}
        onCancel={() => setVisible(false)}
        // Ant Design Modal 自带动画，无需额外配置
        // 可通过 transitionName 自定义动画
        transitionName="ant-fade"
        maskTransitionName="ant-fade"
      >
        <p>This modal has built-in animation effects.</p>
      </Modal>
    </div>
  );
}
```

### 5. Drawer 动画

```tsx
import { Drawer, Button } from 'antd';

function DrawerAnimation() {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <Button onClick={() => setVisible(true)}>Open Drawer</Button>

      <Drawer
        title="Animated Drawer"
        placement="right"
        open={visible}
        onClose={() => setVisible(false)}
        // Drawer 自带滑动动画
        // placement: 'left' | 'right' | 'top' | 'bottom'
      >
        <p>This drawer has built-in slide animation.</p>
      </Drawer>
    </div>
  );
}
```

### 6. Collapse 动画

```tsx
import { Collapse } from 'antd';

const { Panel } = Collapse;

function CollapseAnimation() {
  return (
    <Collapse
      // Collapse 自带折叠动画
      accordion
    >
      <Panel header="Panel 1" key="1">
        <p>Content 1 with smooth collapse animation</p>
      </Panel>
      <Panel header="Panel 2" key="2">
        <p>Content 2 with smooth collapse animation</p>
      </Panel>
      <Panel header="Panel 3" key="3">
        <p>Content 3 with smooth collapse animation</p>
      </Panel>
    </Collapse>
  );
}
```

### 7. Tabs 动画

```tsx
import { Tabs } from 'antd';

function TabsAnimation() {
  return (
    <Tabs
      defaultActiveKey="1"
      // Tab 切换动画
      animated={{
        inkBar: true,
        tabPane: true,
      }}
      items={[
        { key: '1', label: 'Tab 1', children: 'Content 1' },
        { key: '2', label: 'Tab 2', children: 'Content 2' },
        { key: '3', label: 'Tab 3', children: 'Content 3' },
      ]}
    />
  );
}
```

---

## 内置组件动画

### 1. Button 动画

```tsx
function ButtonAnimations() {
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      {/* 悬停效果 */}
      <Button
        style={{
          transition: 'all 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.05)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
        }}
      >
        Hover Scale
      </Button>

      {/* 点击波纹效果 - Button 内置 */}
      <Button type="primary">Click Ripple (Built-in)</Button>

      {/* 加载动画 - Button 内置 */}
      <Button loading>Loading State</Button>

      {/* 禁用过渡 */}
      <Button disabled style={{ transition: 'all 0.3s' }}>
        Disabled Transition
      </Button>
    </div>
  );
}
```

### 2. Input 动画

```tsx
import { Input } from 'antd';

function InputAnimations() {
  const [focused, setFocused] = useState(false);

  return (
    <div>
      <Input
        placeholder="Focus to see animation"
        style={{
          transition: 'all 0.3s ease',
          borderColor: focused ? '#1890ff' : '#d9d9d9',
          boxShadow: focused ? '0 0 0 2px rgba(24, 144, 255, 0.2)' : 'none',
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      />

      <Input.Password
        placeholder="Password with animation"
        style={{ marginTop: 16 }}
      />
    </div>
  );
}
```

### 3. Card 动画

```tsx
import { Card } from 'antd';

function CardAnimations() {
  return (
    <Card
      hoverable
      style={{
        transition: 'all 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-5px)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
      }}
    >
      <p>Hover me to see lift animation</p>
    </Card>
  );
}
```

### 4. Dropdown 动画

```tsx
import { Dropdown, Button } from 'antd';

function DropdownAnimation() {
  const items = [
    { key: '1', label: 'Item 1' },
    { key: '2', label: 'Item 2' },
    { key: '3', label: 'Item 3' },
  ];

  return (
    <Dropdown
      menu={{ items }}
      // Dropdown 自带弹出动画
      trigger={['click']}
    >
      <Button>Click to see dropdown animation</Button>
    </Dropdown>
  );
}
```

### 5. Tooltip 动画

```tsx
import { Tooltip, Button } from 'antd';

function TooltipAnimation() {
  return (
    <Tooltip title="This tooltip has fade animation">
      <Button>Hover me</Button>
    </Tooltip>
  );
}
```

### 6. Popover 动画

```tsx
import { Popover, Button } from 'antd';

function PopoverAnimation() {
  return (
    <Popover
      content="This popover has fade and scale animation"
      trigger="hover"
    >
      <Button>Hover me</Button>
    </Popover>
  );
}
```

### 7. Progress 动画

```tsx
import { Progress, Button } from 'antd';

function ProgressAnimation() {
  const [percent, setPercent] = useState(0);

  const increase = () => {
    setPercent((prev) => (prev >= 100 ? 0 : prev + 10));
  };

  return (
    <div>
      <Progress
        percent={percent}
        // Progress 自带进度条动画
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
      />
      <Button onClick={increase} style={{ marginTop: 16 }}>
        Increase
      </Button>
    </div>
  );
}
```

### 8. Spin 动画

```tsx
import { Spin, Button } from 'antd';

function SpinAnimation() {
  const [loading, setLoading] = useState(false);

  const toggleLoading = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 3000);
  };

  return (
    <div>
      <Spin spinning={loading}>
        <div style={{ padding: 24, border: '1px solid #f0f0f0' }}>
          <p>Content with spinner</p>
        </div>
      </Spin>

      <Button onClick={toggleLoading} style={{ marginTop: 16 }}>
        Toggle Loading
      </Button>
    </div>
  );
}
```

---

## 全局动画配置

### 1. ConfigProvider 动画配置

```tsx
import { ConfigProvider, Button, Card } from 'antd';

function GlobalAnimationConfig() {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 全局动画持续时间
          motionDurationSlow: '0.3s',    // 慢速动画
          motionDurationBase: '0.2s',    // 基础动画
          motionDurationFast: '0.1s',    // 快速动画

          // 动画缓动函数
          motionEaseInOutCirc: 'cubic-bezier(0.78, 0.14, 0.15, 0.86)',
          motionEaseOut: 'cubic-bezier(0.215, 0.61, 0.355, 1)',
          motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
          motionEaseOutBack: 'cubic-bezier(0.12, 0.4, 0.29, 1.46)',
          motionEaseInBack: 'cubic-bezier(0.6, -0.28, 0.735, 0.045)',
          motionEaseInQuint: 'cubic-bezier(0.755, 0.045, 0.855, 0.06)',
          motionEaseOutQuint: 'cubic-bezier(0.23, 1, 0.32, 1)',
        },
      }}
    >
      <div>
        <Button type="primary">Animated Button</Button>
        <Card style={{ marginTop: 16 }}>
          Animated Card
        </Card>
      </div>
    </ConfigProvider>
  );
}
```

### 2. 组件级动画覆盖

```tsx
function ComponentAnimationOverride() {
  return (
    <ConfigProvider
      theme={{
        token: {
          motionDurationSlow: '0.5s', // 全局慢速动画
        },
        components: {
          Button: {
            motionDurationSlow: '0.1s', // Button 使用快速动画
          },
          Card: {
            motionDurationSlow: '0.8s', // Card 使用更慢动画
          },
        },
      }}
    >
      <div>
        <Button type="primary">Fast Animation Button</Button>
        <Card style={{ marginTop: 16 }}>
          Slow Animation Card
        </Card>
      </div>
    </ConfigProvider>
  );
}
```

### 3. 禁用动画

```tsx
function DisableAnimations() {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 设置极短的动画时间，实质上禁用动画
          motionDurationSlow: '0s',
          motionDurationBase: '0s',
          motionDurationFast: '0s',
        },
      }}
    >
      <div>
        <Button type="primary">No Animation Button</Button>
        <Card style={{ marginTop: 16 }}>
          No Animation Card
        </Card>
      </div>
    </ConfigProvider>
  );
}
```

---

## 自定义动画

### 1. 自定义 Keyframes

```tsx
// 自定义动画样式
const customStyles = `
  @keyframes slideInFromLeft {
    from {
      transform: translateX(-100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideInFromRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes fadeInScale {
    from {
      opacity: 0;
      transform: scale(0.8);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes rotateIn {
    from {
      transform: rotate(-180deg) scale(0);
      opacity: 0;
    }
    to {
      transform: rotate(0) scale(1);
      opacity: 1;
    }
  }
`;

function CustomKeyframes() {
  useEffect(() => {
    // 注入自定义动画样式
    const styleSheet = document.createElement('style');
    styleSheet.textContent = customStyles;
    document.head.appendChild(styleSheet);

    return () => {
      document.head.removeChild(styleSheet);
    };
  }, []);

  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          animation: 'slideInFromLeft 0.5s ease-out',
        }}
      >
        From Left
      </div>

      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#52c41a',
          animation: 'slideInFromRight 0.5s ease-out',
        }}
      >
        From Right
      </div>

      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#faad14',
          animation: 'fadeInScale 0.5s ease-out',
        }}
      >
        Fade Scale
      </div>

      <div
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#ff4d4f',
          animation: 'rotateIn 0.7s ease-out',
        }}
      >
        Rotate In
      </div>
    </div>
  );
}
```

### 2. 自定义动画 Hook

```tsx
function useAnimation(
  animationName: string,
  duration: number = 300,
  delay: number = 0
) {
  const [isAnimating, setIsAnimating] = useState(false);

  const start = useCallback(() => {
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), duration + delay);
  }, [duration, delay]);

  const style = useMemo(() => ({
    animation: `${animationName} ${duration}ms ease-in-out ${delay}ms`,
  }), [animationName, duration, delay]);

  return { isAnimating, start, style };
}

function CustomAnimationHook() {
  const fadeIn = useAnimation('fadeIn', 500);
  const slideIn = useAnimation('slideIn', 500);

  return (
    <div>
      <Button onClick={fadeIn.start}>Fade In</Button>
      <Button onClick={slideIn.start} style={{ marginLeft: 8 }}>
        Slide In
      </Button>

      <div
        key={fadeIn.isAnimating ? 'fade' : 'static'}
        style={{
          ...fadeIn.style,
          padding: 24,
          backgroundColor: '#f0f0f0',
          marginTop: 16,
        }}
      >
        Animated Content
      </div>
    </div>
  );
}
```

### 3. 条件动画

```tsx
function ConditionalAnimation() {
  const [visible, setVisible] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (visible) {
      setMounted(true);
    } else {
      // 延迟卸载，等待退出动画完成
      const timer = setTimeout(() => setMounted(false), 300);
      return () => clearTimeout(timer);
    }
  }, [visible]);

  return (
    <div>
      <Button onClick={() => setVisible(!visible)}>
        {visible ? 'Hide' : 'Show'}
      </Button>

      {mounted && (
        <div
          style={{
            padding: 24,
            backgroundColor: '#1890ff',
            color: '#fff',
            marginTop: 16,
            transition: 'all 0.3s ease-in-out',
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(-20px)',
          }}
        >
          Conditionally Animated Content
        </div>
      )}
    </div>
  );
}
```

### 4. 交错动画

```tsx
function StaggeredAnimation() {
  const [items] = useState([
    { id: 1, text: 'Item 1' },
    { id: 2, text: 'Item 2' },
    { id: 3, text: 'Item 3' },
    { id: 4, text: 'Item 4' },
    { id: 5, text: 'Item 5' },
  ]);

  const [visible, setVisible] = useState(false);

  return (
    <div>
      <Button onClick={() => setVisible(!visible)}>
        Toggle Staggered Animation
      </Button>

      <div style={{ marginTop: 16 }}>
        {items.map((item, index) => (
          <div
            key={item.id}
            style={{
              padding: 16,
              margin: 8,
              backgroundColor: '#1890ff',
              color: '#fff',
              transition: 'all 0.3s ease-in-out',
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateX(0)' : 'translateX(-50px)',
              transitionDelay: `${index * 0.1}s`,
            }}
          >
            {item.text}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 5. 动画序列

```tsx
function AnimationSequence() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step < 3) {
      const timer = setTimeout(() => setStep(step + 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [step]);

  const reset = () => setStep(0);

  return (
    <div>
      <Button onClick={reset}>Restart Sequence</Button>

      <div style={{ marginTop: 16, display: 'flex', gap: 16 }}>
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            style={{
              width: 60,
              height: 60,
              backgroundColor: step > index ? '#52c41a' : '#d9d9d9',
              transition: 'all 0.5s ease-in-out',
              transform: step === index ? 'scale(1.2)' : 'scale(1)',
            }}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## 性能优化

### 1. GPU 加速

```tsx
function GPUAcceleration() {
  return (
    <div>
      {/* ✅ 使用 transform 和 opacity - GPU 加速 */}
      <div
        style={{
          transform: 'translateX(100px)',  // GPU 加速
          opacity: 0.5,                     // GPU 加速
          transition: 'all 0.3s ease',
        }}
      >
        Optimized Animation
      </div>

      {/* ❌ 避免动画布局属性 - CPU 渲染，性能差 */}
      <div
        style={{
          left: '100px',    // 触发回流
          width: '200px',   // 触发重绘
          height: '100px',  // 触发重绘
          transition: 'all 0.3s ease',
        }}
      >
        Unoptimized Animation
      </div>
    </div>
  );
}
```

### 2. will-change 优化

```tsx
function WillChangeOptimization() {
  return (
    <div
      style={{
        // 提前告知浏览器哪些属性会动画，浏览器会提前优化
        willChange: 'transform, opacity',
        transition: 'transform 0.3s ease, opacity 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.1)';
        e.currentTarget.style.opacity = '0.8';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.opacity = '1';
      }}
    >
      Optimized with will-change
    </div>
  );
}
```

### 3. 动画节流

```tsx
import { throttle } from 'lodash';

function ThrottledAnimation() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = throttle((e: MouseEvent) => {
    setPosition({
      x: e.clientX,
      y: e.clientY,
    });
  }, 16); // 限制为 60fps

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  return (
    <div
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: 20,
        height: 20,
        backgroundColor: '#1890ff',
        borderRadius: '50%',
        transition: 'transform 0.1s linear',
        pointerEvents: 'none',
      }}
    />
  );
}
```

### 4. 减少重绘

```tsx
function ReduceRepaints() {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <Button onClick={() => setVisible(!visible)}>Toggle</Button>

      {/* ✅ 使用 visibility - 不触发重绘 */}
      <div
        style={{
          visibility: visible ? 'visible' : 'hidden',
          transition: 'opacity 0.3s ease',
          opacity: visible ? 1 : 0,
        }}
      >
        Optimized - No Repaint
      </div>

      {/* ❌ 使用 display - 触发重绘 */}
      <div
        style={{
          display: visible ? 'block' : 'none',
        }}
      >
        Unoptimized - Triggers Repaint
      </div>
    </div>
  );
}
```

### 5. React.memo 优化

```tsx
const AnimatedCard = React.memo(function AnimatedCard({ title }: { title: string }) {
  return (
    <Card
      style={{
        transition: 'transform 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      {title}
    </Card>
  );
});

function MemoOptimization() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <Button onClick={() => setCount(count + 1)}>
        Count: {count}
      </Button>

      {/* Card不会因为 count 变化而重新渲染 */}
      <AnimatedCard title="Optimized Card" />
    </div>
  );
}
```

### 6. 动画合成层

```tsx
function CompositeLayer() {
  return (
    <div
      style={{
        // 创建新的合成层，独立渲染
        transform: 'translateZ(0)',
        transition: 'transform 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateZ(0) scale(1.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateZ(0) scale(1)';
      }}
    >
      Composite Layer Animation
    </div>
  );
}
```

---

## 第三方动画库集成

### 1. Framer Motion 集成

```bash
npm install framer-motion
```

```tsx
import { motion } from 'framer-motion';

function FramerMotionExample() {
  return (
    <div>
      {/* 基础动画 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{ width: 100, height: 100, backgroundColor: '#1890ff' }}
      />

      {/* 悬停动画 */}
      <motion.div
        whileHover={{ scale: 1.2 }}
        whileTap={{ scale: 0.8 }}
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#52c41a',
          margin: 16,
        }}
      />

      {/* 拖拽动画 */}
      <motion.div
        drag
        dragConstraints={{ left: 0, right: 300, top: 0, bottom: 300 }}
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#faad14',
          margin: 16,
        }}
      />
    </div>
  );
}
```

### 2. React Spring 集成

```bash
npm install react-spring
```

```tsx
import { useSpring, animated } from '@react-spring/web';

function ReactSpringExample() {
  const [props, set] = useSpring(() => ({
    x: 0,
    opacity: 1,
  }));

  return (
    <div>
      <Button onClick={() => set({ x: 100, opacity: 0.5 })}>
        Animate
      </Button>

      <animated.div
        style={{
          transform: props.x.to((x) => `translateX(${x}px)`),
          opacity: props.opacity,
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          marginTop: 16,
        }}
      />
    </div>
  );
}
```

### 3. GSAP 集成

```bash
npm install gsap
```

```tsx
import { gsap } from 'gsap';
import { useRef, useEffect } from 'react';

function GSAPExample() {
  const boxRef = useRef<HTMLDivElement>(null);

  const animate = () => {
    gsap.to(boxRef.current, {
      x: 100,
      rotation: 360,
      duration: 1,
      ease: 'power2.inOut',
    });
  };

  return (
    <div>
      <Button onClick={animate}>Animate with GSAP</Button>

      <div
        ref={boxRef}
        style={{
          width: 100,
          height: 100,
          backgroundColor: '#1890ff',
          marginTop: 16,
        }}
      />
    </div>
  );
}
```

### 4. Auto Animate 集成

```bash
npm install @formkit/auto-animate
```

```tsx
import { useAutoAnimate } from '@formkit/auto-animate/react';

function AutoAnimateExample() {
  const [parent] = useAutoAnimate();
  const [items, setItems] = useState([1, 2, 3]);

  const addItem = () => {
    setItems([...items, items.length + 1]);
  };

  return (
    <div>
      <Button onClick={addItem}>Add Item</Button>

      <ul ref={parent} style={{ marginTop: 16 }}>
        {items.map((item) => (
          <li key={item} style={{ padding: 8 }}>
            Item {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 完整示例

### 示例 1: 产品卡片动画

```tsx
import { Card, Tag, Button, Space } from 'antd';

const { Meta } = Card;

function ProductCard() {
  return (
    <Card
      hoverable
      style={{
        width: 300,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      cover={
        <img
          alt="example"
          src="https://gw.alipayobjects.com/zos/rmsportal/JiqGstjfoqJOJcCH.png"
          style={{
            transition: 'transform 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
        />
      }
      actions={[
        <Button type="primary">Add to Cart</Button>,
        <Button>View Details</Button>,
      ]}
    >
      <Meta
        title="Product Name"
        description={
          <Space>
            <Tag color="red">New</Tag>
            <Tag color="green">In Stock</Tag>
          </Space>
        }
      />
      <div
        style={{
          marginTop: 16,
          fontSize: 20,
          fontWeight: 'bold',
          color: '#1890ff',
          transition: 'color 0.3s ease',
        }}
      >
        $99.99
      </div>
    </Card>
  );
}
```

### 示例 2: 列表项动画

```tsx
import { List, Button, Avatar } from 'antd';

function AnimatedList() {
  const [data, setData] = useState([
    { id: 1, name: 'John Doe', email: 'john@example.com' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com' },
  ]);

  const addItem = () => {
    const newId = data.length + 1;
    const newItem = {
      id: newId,
      name: `User ${newId}`,
      email: `user${newId}@example.com`,
    };
    setData([...data, newItem]);
  };

  return (
    <div>
      <Button onClick={addItem} style={{ marginBottom: 16 }}>
        Add User
      </Button>

      <List
        dataSource={data}
        renderItem={(item, index) => (
          <List.Item
            key={item.id}
            style={{
              animation: 'fadeInUp 0.3s ease-out',
              animationDelay: `${index * 0.05}s`,
              animationFillMode: 'both',
            }}
          >
            <List.Item.Meta
              avatar={<Avatar>{item.name[0]}</Avatar>}
              title={item.name}
              description={item.email}
            />
          </List.Item>
        )}
      />
    </div>
  );
}

// 添加样式
const styles = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
```

### 示例 3: 页面切换动画

```tsx
import { useState, useEffect } from 'react';
import { Layout, Menu, Button } from 'antd';

const { Content, Sider } = Layout;

function PageTransition() {
  const [currentPage, setCurrentPage] = useState('home');
  const [animating, setAnimating] = useState(false);

  const changePage = (page: string) => {
    if (page === currentPage || animating) return;

    setAnimating(true);

    // 退出动画
    setTimeout(() => {
      setCurrentPage(page);

      // 进入动画
      setTimeout(() => {
        setAnimating(false);
      }, 50);
    }, 300);
  };

  const pages = {
    home: {
      title: 'Home Page',
      content: 'Welcome to the home page',
    },
    about: {
      title: 'About Page',
      content: 'Learn more about us',
    },
    contact: {
      title: 'Contact Page',
      content: 'Get in touch with us',
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} style={{ background: '#fff' }}>
        <Menu
          mode="inline"
          selectedKeys={[currentPage]}
          onClick={({ key }) => changePage(key)}
          items={[
            { key: 'home', label: 'Home' },
            { key: 'about', label: 'About' },
            { key: 'contact', label: 'Contact' },
          ]}
        />
      </Sider>

      <Layout style={{ padding: '24px' }}>
        <Content
          style={{
            background: '#fff',
            padding: 24,
            margin: 0,
            minHeight: 280,
          }}
        >
          <div
            key={currentPage}
            style={{
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              opacity: animating ? 0 : 1,
              transform: animating ? 'translateX(-20px)' : 'translateX(0)',
            }}
          >
            <h1>{pages[currentPage].title}</h1>
            <p>{pages[currentPage].content}</p>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
```

### 示例 4: 加载动画序列

```tsx
import { useState, useEffect } from 'react';
import { Card, Spin, Button } from 'antd';

function LoadingSequence() {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  const steps = [
    { text: 'Initializing...', duration: 1000 },
    { text: 'Loading data...', duration: 1500 },
    { text: 'Processing...', duration: 1200 },
    { text: 'Completing...', duration: 800 },
  ];

  const startLoading = () => {
    setLoading(true);
    setStep(0);

    let currentStep = 0;

    const runStep = () => {
      if (currentStep < steps.length) {
        setStep(currentStep);
        setTimeout(() => {
          currentStep++;
          runStep();
        }, steps[currentStep].duration);
      } else {
        setLoading(false);
        setStep(0);
      }
    };

    runStep();
  };

  return (
    <Card style={{ width: 400 }}>
      <Spin spinning={loading} tip={steps[step]?.text || 'Loading...'}>
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p>Click the button to start the loading sequence</p>
          <Button onClick={startLoading}>Start Loading</Button>
        </div>
      </Spin>
    </Card>
  );
}
```

### 示例 5: 交互式动画控制面板

```tsx
import { useState } from 'react';
import { Card, Slider, Select, Button, Space, ColorPicker } from 'antd';

function AnimationControlPanel() {
  const [duration, setDuration] = useState(300);
  const [easing, setEasing] = useState('ease-in-out');
  const [delay, setDelay] = useState(0);
  const [color, setColor] = useState('#1890ff');
  const [isAnimating, setIsAnimating] = useState(false);

  const easingOptions = [
    { label: 'Linear', value: 'linear' },
    { label: 'Ease', value: 'ease' },
    { label: 'Ease In', value: 'ease-in' },
    { label: 'Ease Out', value: 'ease-out' },
    { label: 'Ease In Out', value: 'ease-in-out' },
  ];

  const animate = () => {
    if (isAnimating) return;

    setIsAnimating(true);

    const element = document.getElementById('animated-box');
    if (element) {
      element.style.transition = `all ${duration}ms ${easing} ${delay}ms`;
      element.style.transform = 'translateX(200px) rotate(360deg) scale(1.2)';
      element.style.backgroundColor = color;
      element.style.borderRadius = '50%';

      setTimeout(() => {
        element.style.transform = 'translateX(0) rotate(0deg) scale(1)';
        element.style.backgroundColor = '#1890ff';
        element.style.borderRadius = '4px';

        setTimeout(() => {
          setIsAnimating(false);
        }, duration + delay);
      }, duration + delay);
    }
  };

  return (
    <Card title="Animation Control Panel" style={{ width: 500 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Duration */}
        <div>
          <div style={{ marginBottom: 8 }}>
            Duration: {duration}ms
          </div>
          <Slider
            min={100}
            max={2000}
            step={100}
            value={duration}
            onChange={setDuration}
          />
        </div>

        {/* Easing */}
        <div>
          <div style={{ marginBottom: 8 }}>Easing Function:</div>
          <Select
            style={{ width: '100%' }}
            value={easing}
            onChange={setEasing}
            options={easingOptions}
          />
        </div>

        {/* Delay */}
        <div>
          <div style={{ marginBottom: 8 }}>
            Delay: {delay}ms
          </div>
          <Slider
            min={0}
            max={1000}
            step={100}
            value={delay}
            onChange={setDelay}
          />
        </div>

        {/* Color */}
        <div>
          <div style={{ marginBottom: 8 }}>Color:</div>
          <ColorPicker
            value={color}
            onChange={(color) => setColor(color.toHexString())}
            showText
          />
        </div>

        {/* Animated Box */}
        <div
          id="animated-box"
          style={{
            width: 100,
            height: 100,
            backgroundColor: '#1890ff',
            transition: `all ${duration}ms ${easing} ${delay}ms`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
          }}
        >
          Animated
        </div>

        {/* Control Buttons */}
        <Button
          type="primary"
          onClick={animate}
          loading={isAnimating}
          block
        >
          Animate
        </Button>
      </Space>
    </Card>
  );
}
```

---

## 最佳实践

### 1. 动画性能

**✅ 推荐**：使用 GPU 加速属性

```tsx
// GPU 加速 - 高性能
<div
  style={{
    transform: 'translateX(100px)',  // ✅ GPU 加速
    opacity: 0.5,                     // ✅ GPU 加速
    transition: 'all 0.3s ease',
  }}
/>
```

**❌ 避免**：动画布局属性

```tsx
// CPU 渲染 - 低性能
<div
  style={{
    left: '100px',    // ❌ 触发回流
    width: '200px',   // ❌ 触发重绘
    height: '100px',  // ❌ 触发重绘
    transition: 'all 0.3s ease',
  }}
/>
```

### 2. 动画持续时间

**✅ 推荐**：合理设置动画时间

```tsx
// 快速交互
<Button style={{ transition: 'all 0.1s' }}>Quick</Button>

// 标准交互
<Card style={{ transition: 'all 0.3s' }}>Standard</Card>

// 慢速动画
<Modal transitionName="ant-fade 0.5s">Slow</Modal>
```

**❌ 避免**：过长的动画时间

```tsx
// ❌ 用户体验差
<Button style={{ transition: 'all 2s' }}>Too Slow</Button>
```

### 3. 缓动函数选择

**✅ 推荐**：根据场景选择合适的缓动

```tsx
// 进入动画 - ease-out
<div style={{ animation: 'fadeIn 0.3s ease-out' }} />

// 退出动画 - ease-in
<div style={{ animation: 'fadeOut 0.3s ease-in' }} />

// 循环动画 - ease-in-out
<div style={{ animation: 'pulse 1s ease-in-out infinite' }} />
```

### 4. 响应式动画

**✅ 推荐**：考虑移动设备性能

```tsx
function ResponsiveAnimation() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setIsMobile(window.innerWidth < 768);
  }, []);

  return (
    <div
      style={{
        transition: isMobile ? 'none' : 'all 0.3s ease',
      }}
    >
      Responsive Animation
    </div>
  );
}
```

### 5. 动画组合

**✅ 推荐**：使用 transition 组合多个属性

```tsx
<div
  style={{
    transition: 'transform 0.3s ease, opacity 0.3s ease, box-shadow 0.3s ease',
  }}
/>
```

**❌ 避免**：过度使用 `transition: all`

```tsx
// ❌ 可能导致性能问题
<div
  style={{
    transition: 'all 0.3s ease',  // 所有属性都会动画
  }}
/>
```

### 6. 减少动画数量

**✅ 推荐**：限制同时运行的动画数量

```tsx
function LimitedAnimations() {
  const [animatingItems, setAnimatingItems] = useState<Set<number>>(new Set());

  const startAnimation = (id: number) => {
    if (animatingItems.size >= 5) return; // 限制最多 5 个动画

    setAnimatingItems(new Set(animatingItems).add(id));

    setTimeout(() => {
      const newSet = new Set(animatingItems);
      newSet.delete(id);
      setAnimatingItems(newSet);
    }, 300);
  };

  return <div>{/* ... */}</div>;
}
```

### 7. 使用 CSS 类而非内联样式

**✅ 推荐**：使用 CSS 类管理动画

```tsx
// styles.css
.animated-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.animated-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

// 组件
<Card className="animated-card" />
```

**❌ 避免**：过度使用内联样式

```tsx
// ❌ 难以维护
<Card
  style={{
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.transform = 'translateY(-5px)';
    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.transform = 'translateY(0)';
    e.currentTarget.style.boxShadow = 'none';
  }}
/>
```

---

## 常见问题

### Q: 为什么我的动画很卡顿?

A: 检查以下几点：

1. **是否使用了 GPU 加速属性?**
   - 使用 `transform` 和 `opacity` 代替 `left`、`top`、`width`、`height`

2. **是否同时运行太多动画?**
   - 限制同时运行的动画数量（不超过 5-10 个）

3. **是否动画了复杂 DOM?**
   - 避免动画包含大量子元素的容器

4. **是否使用了 will-change?**
   - 对已知会动画的元素添加 `will-change` 属性

### Q: 如何禁用所有动画?

A: 通过 ConfigProvider 设置极短的动画时间：

```tsx
<ConfigProvider
  theme={{
    token: {
      motionDurationSlow: '0s',
      motionDurationBase: '0s',
      motionDurationFast: '0s',
    },
  }}
>
  <App />
</ConfigProvider>
```

### Q: 如何实现流畅的页面切换动画?

A: 使用条件渲染 + 动画延迟：

```tsx
function PageTransition() {
  const [page, setPage] = useState('home');
  const [mounted, setMounted] = useState(true);

  const changePage = (newPage: string) => {
    // 1. 退出动画
    setMounted(false);

    // 2. 等待退出动画完成
    setTimeout(() => {
      setPage(newPage);
      setMounted(true); // 3. 进入动画
    }, 300);
  };

  return (
    <div>
      {mounted && (
        <div
          key={page}
          style={{
            animation: 'fadeIn 0.3s ease-in-out',
          }}
        >
          {/* Page content */}
        </div>
      )}
    </div>
  );
}
```

### Q: 动画完成后如何执行回调?

A: 使用 `transitionend` 或 `animationend` 事件：

```tsx
function AnimationCallback() {
  const ref = useRef<HTMLDivElement>(null);

  const startAnimation = () => {
    if (ref.current) {
      ref.current.style.animation = 'fadeIn 0.3s ease-in-out';

      const handleAnimationEnd = () => {
        console.log('Animation completed!');
        ref.current?.removeEventListener('animationend', handleAnimationEnd);
      };

      ref.current.addEventListener('animationend', handleAnimationEnd);
    }
  };

  return (
    <div ref={ref} onClick={startAnimation}>
      Animate me
    </div>
  );
}
```

### Q: 如何实现响应式动画?

A: 根据屏幕尺寸调整动画参数：

```tsx
function ResponsiveAnimation() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div
      style={{
        transition: isMobile ? 'none' : 'all 0.3s ease',
      }}
    >
      Responsive Content
    </div>
  );
}
```

### Q: 如何优化列表渲染性能?

A: 使用 React.memo + 虚拟滚动：

```tsx
const ListItem = React.memo(function ListItem({ item }: { item: any }) {
  return (
    <div
      style={{
        animation: 'fadeIn 0.3s ease-in-out',
      }}
    >
      {item.text}
    </div>
  );
});

// 对于长列表，使用虚拟滚动
import { List as VirtualList } from 'react-virtualized';

function VirtualizedList({ items }: { items: any[] }) {
  return (
    <VirtualList
      width={300}
      height={600}
      rowCount={items.length}
      rowHeight={50}
      rowRenderer={({ index, key, style }) => (
        <div key={key} style={style}>
          {items[index].text}
        </div>
      )}
    />
  );
}
```

---

## 参考资料

- [Ant Design 动画组件](https://ant.design/components/overview-cn/)
- [CSS Transitions MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/transition)
- [CSS Animations MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/animation)
- [Web 动画性能优化](https://web.dev/animations-guide/)
- [CSS will-change](https://developer.mozilla.org/en-US/docs/Web/CSS/will-change)
- [Framer Motion 文档](https://www.framer.com/motion/)
- [React Spring 文档](https://www.react-spring.dev/)
- [GSAP 文档](https://greensock.com/docs/)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- 现代浏览器（Chrome、Firefox、Safari、Edge 最新版本）

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
