---
name: antd-mobile-skills
description: Ant Design 移动端适配完整指南 - 响应式设计、移动端组件、触摸交互、性能优化
---

# antd-mobile: Ant Design 移动端适配完整指南

Ant Design 移动端模块提供完整的移动端组件、触摸手势支持和响应式设计方案,帮助开发者构建高性能、体验优秀的移动端应用。

---

## 概述

### 核心功能

- **响应式设计系统** - 基于断点的自适应布局,支持多种设备尺寸
- **移动端专用组件** - 针对触摸交互优化的组件库(Button、List、Picker等)
- **触摸手势支持** - 完整的手势识别系统(滑动、拖拽、缩放、长按)
- **性能优化方案** - 虚拟滚动、懒加载、资源优化
- **PWA 支持** - 离线可用、添加到主屏幕、推送通知
- **移动端表单增强** - 虚拟键盘适配、输入优化、验证增强
- **移动端导航** - 底部导航栏、侧边菜单、标签页
- **安全区域适配** - 刘海屏、底部指示器区域自动适配

### 设备支持

| 设备类型 | 屏幕宽度 | 断点名称 | 典型设备 |
|---------|---------|---------|---------|
| 超小屏 | < 576px | xs | iPhone SE, 小屏手机 |
| 小屏 | 576px - 768px | sm | iPhone 12/13/14, 大屏手机 |
| 中屏 | 768px - 992px | md | iPad Mini, 小平板 |
| 大屏 | 992px - 1200px | lg | iPad Pro, 平板 |
| 超大屏 | > 1200px | xl | 桌面显示器 |

---

## 响应式设计系统

### Grid 系统移动端适配

Ant Design Grid 系统支持 24 栅格响应式布局:

```tsx
import { Row, Col } from 'antd';

function ResponsiveGrid() {
  return (
    <div>
      {/* 移动端 1 列,平板 2 列,桌面 3 列 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <div>Item 1</div>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <div>Item 2</div>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <div>Item 3</div>
        </Col>
      </Row>

      {/* 使用 offset 响应式偏移 */}
      <Row>
        <Col xs={20} xsOffset={2} sm={16} smOffset={4} md={12} mdOffset={6}>
          <div>居中内容</div>
        </Col>
      </Row>

      {/* 使用 push/pull 响应式排序 */}
      <Row>
        <Col xs={24} sm={8} smPush={16}>
          <div>在平板上显示在右侧</div>
        </Col>
        <Col xs={24} sm={16} smPull={8}>
          <div>在平板上显示在左侧</div>
        </Col>
      </Row>
    </div>
  );
}
```

### 响应式工具

#### useBreakpoint Hook

```tsx
import { Grid } from 'antd';

const { useBreakpoint } = Grid;

function ResponsiveComponent() {
  const screens = useBreakpoint();

  return (
    <div>
      {screens.xs && <div>超小屏布局</div>}
      {screens.sm && !screens.md && <div>小屏布局</div>}
      {screens.md && !screens.lg && <div>中屏布局</div>}
      {screens.lg && <div>大屏布局</div>}
    </div>
  );
}
```

#### 根据断点显示内容

```tsx
import { Col } from 'antd';

function ShowOnDevices() {
  return (
    <div>
      {/* 仅在移动端显示 */}
      <Col xs={24} md={0} lg={0}>
        <MobileOnlyComponent />
      </Col>

      {/* 仅在桌面端显示 */}
      <Col xs={0} sm={0} md={24}>
        <DesktopOnlyComponent />
      </Col>

      {/* 移动端和桌面端显示不同内容 */}
      <>
        <Col xs={24} md={0}>
          <MobileVersion />
        </Col>
        <Col xs={0} md={24}>
          <DesktopVersion />
        </Col>
      </>
    </div>
  );
}
```

### 响应式间距

```tsx
import { Row, Col } from 'antd';

function ResponsiveGutter() {
  return (
    <div>
      {/* 响应式栅格间距 */}
      <Row gutter={[8, 8]}>  {/* 移动端 8px 间距 */}
        <Col span={12}>Item</Col>
        <Col span={12}>Item</Col>
      </Row>

      <Row gutter={[16, 16]}>  {/* 平板 16px 间距 */}
        <Col span={12}>Item</Col>
        <Col span={12}>Item</Col>
      </Row>

      <Row gutter={[24, 24]}>  {/* 桌面 24px 间距 */}
        <Col span={12}>Item</Col>
        <Col span={12}>Item</Col>
      </Row>

      {/* 使用对象设置不同断点的间距 */}
      <Row gutter={{
        xs: 8,
        sm: 16,
        md: 24,
        lg: 32,
      }}>
        <Col span={12}>Item</Col>
        <Col span={12}>Item</Col>
      </Row>

      {/* 分别设置水平和垂直间距 */}
      <Row gutter={{
        xs: [8, 8],
        sm: [16, 16],
        md: [24, 24],
      }}>
        <Col span={12}>Item</Col>
        <Col span={12}>Item</Col>
      </Row>
    </div>
  );
}
```

---

## 移动端专用组件

### Button 移动端优化

```tsx
import { Button } from 'antd';

function MobileButtons() {
  return (
    <div style={{ padding: 16 }}>
      {/* 移动端全宽按钮 */}
      <Button type="primary" block style={{ height: 44 }}>
        全宽按钮
      </Button>

      {/* 移动端危险按钮 */}
      <Button danger block style={{ height: 44, marginTop: 12 }}>
        危险操作
      </Button>

      {/* 移动端按钮组 */}
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <Button type="primary" style={{ flex: 1, height: 44 }}>
          确定
        </Button>
        <Button style={{ flex: 1, height: 44 }}>
          取消
        </Button>
      </div>

      {/* 图标按钮(增大触摸区域) */}
      <Button
        type="primary"
        icon={<SearchOutlined />}
        style={{ height: 48, fontSize: 16 }}
      >
        搜索
      </Button>
    </div>
  );
}
```

### List 移动端列表

```tsx
import { List, Avatar, Typography } from 'antd';

const { Text } = Typography;

function MobileList() {
  const data = [
    { id: 1, name: 'Item 1', description: 'Description 1' },
    { id: 2, name: 'Item 2', description: 'Description 2' },
    { id: 3, name: 'Item 3', description: 'Description 3' },
  ];

  return (
    <List
      dataSource={data}
      renderItem={(item) => (
        <List.Item
          style={{
            padding: '16px',
            cursor: 'pointer',
            // 增加触摸反馈
            activeBackgroundColor: '#f0f0f0',
          }}
          onClick={() => console.log('Clicked:', item.id)}
        >
          <List.Item.Meta
            avatar={<Avatar>{item.name[0]}</Avatar>}
            title={<Text strong>{item.name}</Text>}
            description={<Text type="secondary">{item.description}</Text>}
          />
        </List.Item>
      )}
    />
  );
}
```

### Picker 移动端选择器

```tsx
import { Picker } from 'antd';

function MobilePicker() {
  const [value, setValue] = useState(['Monday']);

  const days = [
    { label: 'Monday', value: 'Monday' },
    { label: 'Tuesday', value: 'Tuesday' },
    {_label: 'Wednesday', value: 'Wednesday' },
    { label: 'Thursday', value: 'Thursday' },
    { label: 'Friday', value: 'Friday' },
    { label: 'Saturday', value: 'Saturday' },
    { label: 'Sunday', value: 'Sunday' },
  ];

  return (
    <Picker
      columns={[days]}
      value={value}
      onConfirm={setValue}
      visible={false}
    >
      {(_, actions) => (
        <Button onClick={actions.open}>
          选择日期: {value[0]}
        </Button>
      )}
    </Picker>
  );
}
```

### Form 移动端表单

```tsx
import { Form, Input, Button, Checkbox, DatePicker, Space } from 'antd';

function MobileForm() {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    console.log('Form values:', values);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      style={{ padding: 16 }}
    >
      <Form.Item
        label="用户名"
        name="username"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input
          placeholder="请输入用户名"
          size="large"
          // 移动端输入优化
          autoComplete="username"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
        />
      </Form.Item>

      <Form.Item
        label="密码"
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password
          placeholder="请输入密码"
          size="large"
          autoComplete="current-password"
        />
      </Form.Item>

      <Form.Item
        label="生日"
        name="birthday"
      >
        <DatePicker
          size="large"
          style={{ width: '100%' }}
          // 移动端优化
          inputReadOnly
          showTime={false}
        />
      </Form.Item>

      <Form.Item name="remember" valuePropName="checked">
        <Checkbox>记住我</Checkbox>
      </Form.Item>

      <Form.Item>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Button type="primary" htmlType="submit" block size="large">
            登录
          </Button>
          <Button block size="large">
            注册
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
}
```

### Modal 移动端对话框

```tsx
import { Modal, Button, Space } from 'antd';

function MobileModal() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const showModal = () => setIsModalOpen(true);
  const handleCancel = () => setIsModalOpen(false);
  const handleOk = () => {
    console.log('Confirmed');
    setIsModalOpen(false);
  };

  return (
    <>
      <Button type="primary" onClick={showModal} block size="large">
        显示对话框
      </Button>

      <Modal
        title="确认操作"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
        // 移动端优化
        centered
        width={typeof window !== 'undefined' && window.innerWidth < 576 ? '90%' : 520}
        okText="确定"
        cancelText="取消"
        okButtonProps={{ size: 'large', block: true }}
        cancelButtonProps={{ size: 'large', block: true }}
        footer={[
          <Button key="cancel" onClick={handleCancel} size="large" block>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={handleOk} size="large" block>
            确定
          </Button>,
        ]}
      >
        <p>确定要执行此操作吗?</p>
      </Modal>
    </>
  );
}
```

---

## 触摸手势支持

### 基础触摸事件

```tsx
import { useState, useRef } from 'react';
import { Card } from 'antd';

function TouchEvents() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);
  const startY = useRef(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    startX.current = touch.clientX - position.x;
    startY.current = touch.clientY - position.y;
    setIsDragging(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    const touch = e.touches[0];
    setPosition({
      x: touch.clientX - startX.current,
      y: touch.clientY - startY.current,
    });
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
  };

  return (
    <Card
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        cursor: isDragging ? 'grabbing' : 'grab',
        touchAction: 'none', // 防止滚动
        userSelect: 'none',
      }}
    >
      <div>拖动我!</div>
    </Card>
  );
}
```

### 滑动手势(Swipe)

```tsx
import { useState, useRef } from 'react';
import { Card } from 'antd';

function SwipeGesture() {
  const [direction, setDirection] = useState<string>('');
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    touchStartX.current = touch.clientX;
    touchStartY.current = touch.clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartX.current;
    const deltaY = touch.clientY - touchStartY.current;

    // 最小滑动距离阈值(避免误触)
    const minSwipeDistance = 50;

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // 水平滑动
      if (Math.abs(deltaX) > minSwipeDistance) {
        setDirection(deltaX > 0 ? 'right' : 'left');
      }
    } else {
      // 垂直滑动
      if (Math.abs(deltaY) > minSwipeDistance) {
        setDirection(deltaY > 0 ? 'down' : 'up');
      }
    }
  };

  return (
    <Card
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      style={{ textAlign: 'center', padding: 40 }}
    >
      <div>滑动手势: {direction || '等待滑动...'}</div>
      <div style={{ marginTop: 16, fontSize: 12, color: '#999' }}>
        在卡片上滑动以检测方向
      </div>
    </Card>
  );
}
```

### 长按手势(Long Press)

```tsx
import { useState, useRef } from 'react';
import { Card, Button } from 'antd';

function LongPressGesture() {
  const [isPressed, setIsPressed] = useState(false);
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);

  const LONG_PRESS_DURATION = 500; // 500ms 长按

  const handleTouchStart = () => {
    setIsPressed(false);

    longPressTimer.current = setTimeout(() => {
      setIsPressed(true);
      // 震动反馈(如果设备支持)
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
    }, LONG_PRESS_DURATION);
  };

  const handleTouchMove = () => {
    // 移动时取消长按
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  const handleTouchEnd = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  return (
    <Card
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{
        textAlign: 'center',
        padding: 40,
        backgroundColor: isPressed ? '#f0f0f0' : undefined,
      }}
    >
      <div>{isPressed ? '长按触发!' : '长按我...'}</div>
      <div style={{ marginTop: 16, fontSize: 12, color: '#999' }}>
        按住 500ms 触发长按
      </div>
    </Card>
  );
}
```

### 缩放手势(Pinch)

```tsx
import { useState, useRef } from 'react';
import { Card } from 'antd';

function PinchGesture() {
  const [scale, setScale] = useState(1);
  const initialDistance = useRef(0);
  const initialScale = useRef(1);

  const getDistance = (touch1: React.Touch, touch2: React.Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      initialDistance.current = getDistance(e.touches[0], e.touches[1]);
      initialScale.current = scale;
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const currentDistance = getDistance(e.touches[0], e.touches[1]);
      const newScale = (currentDistance / initialDistance.current) * initialScale.current;

      // 限制缩放范围
      setScale(Math.min(Math.max(0.5, newScale), 3));
    }
  };

  return (
    <Card
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: 300,
        touchAction: 'none',
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          transition: 'transform 0.1s',
        }}
      >
        缩放: {scale.toFixed(2)}x
      </div>
    </Card>
  );
}
```

### 自定义手势 Hook

```tsx
import { useRef, useEffect } from 'react';

interface SwipeHandlers {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
}

interface SwipeOptions {
  threshold?: number; // 滑动阈值(像素)
  preventDefault?: boolean;
}

function useSwipe(handlers: SwipeHandlers, options: SwipeOptions = {}) {
  const {
    threshold = 50,
    preventDefault = true,
  } = options;

  const touchStart = useRef<{ x: number; y: number } | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    touchStart.current = { x: touch.clientX, y: touch.clientY };
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStart.current) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStart.current.x;
    const deltaY = touch.clientY - touchStart.current.y;

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // 水平滑动
      if (Math.abs(deltaX) > threshold) {
        if (deltaX > 0) {
          handlers.onSwipeRight?.();
        } else {
          handlers.onSwipeLeft?.();
        }
      }
    } else {
      // 垂直滑动
      if (Math.abs(deltaY) > threshold) {
        if (deltaY > 0) {
          handlers.onSwipeDown?.();
        } else {
          handlers.onSwipeUp?.();
        }
      }
    }

    touchStart.current = null;
  };

  return {
    onTouchStart: handleTouchStart,
    onTouchEnd: handleTouchEnd,
  };
}

// 使用示例
function SwipeableCard() {
  const swipeHandlers = useSwipe({
    onSwipeLeft: () => console.log('Swiped left!'),
    onSwipeRight: () => console.log('Swiped right!'),
    onSwipeUp: () => console.log('Swiped up!'),
    onSwipeDown: () => console.log('Swiped down!'),
  }, { threshold: 50 });

  return (
    <Card {...swipeHandlers} style={{ padding: 40, textAlign: 'center' }}>
      <div>在各个方向上滑动我!</div>
    </Card>
  );
}
```

---

## 性能优化

### 虚拟滚动

```tsx
import { List } from 'antd';

// 大数据列表使用虚拟滚动
function VirtualScrollList() {
  // 生成 10000 条数据
  const data = Array.from({ length: 10000 }, (_, i) => ({
    id: i,
    title: `Item ${i}`,
    description: `Description for item ${i}`,
  }));

  return (
    <List
      dataSource={data}
      // 启用虚拟滚动
      virtual
      height={600} // 必须设置固定高度
      itemHeight={80} // 估计每项高度
      renderItem={(item) => (
        <List.Item key={item.id}>
          <List.Item.Meta
            title={item.title}
            description={item.description}
          />
        </List.Item>
      )}
    />
  );
}
```

### 图片懒加载

```tsx
import { Image } from 'antd';

function LazyLoadImages() {
  const images = [
    { id: 1, src: 'https://example.com/image1.jpg', alt: 'Image 1' },
    { id: 2, src: 'https://example.com/image2.jpg', alt: 'Image 2' },
    { id: 3, src: 'https://example.com/image3.jpg', alt: 'Image 3' },
  ];

  return (
    <div>
      {images.map((image) => (
        <Image
          key={image.id}
          src={image.src}
          alt={image.alt}
          // 启用懒加载
          loading="lazy"
          // 占位符
          preview={{
            placeholder: (
              <div style={{ height: 200, backgroundColor: '#f0f0f0' }}>
                加载中...
              </div>
            ),
          }}
          // 响应式图片
          width="100%"
          height={200}
          style={{ objectFit: 'cover' }}
        />
      ))}
    </div>
  );
}
```

### 代码分割

```tsx
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

// 懒加载移动端组件
const MobileComponent = lazy(() => import('./MobileComponent'));
const DesktopComponent = lazy(() => import('./DesktopComponent'));

function SplitCode() {
  const isMobile = useMediaQuery({ maxWidth: 768 });

  return (
    <Suspense fallback={<Spin size="large" />}>
      {isMobile ? <MobileComponent /> : <DesktopComponent />}
    </Suspense>
  );
}

// Hook 实现
function useMediaQuery(query: { maxWidth?: number; minWidth?: number }) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(
      `(max-width: ${query.maxWidth}px), (min-width: ${query.minWidth}px)`
    );
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}
```

### 防抖与节流

```tsx
import { useCallback } from 'react';
import { Input, Button } from 'antd';

// 防抖搜索
function DebouncedSearch() {
  const [searchTerm, setSearchTerm] = useState('');

  // 防抖处理(500ms)
  const debouncedSearch = useCallback(
    debounce((value: string) => {
      console.log('Searching for:', value);
      // 执行搜索 API 调用
    }, 500),
    []
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    debouncedSearch(value);
  };

  return (
    <Input
      placeholder="搜索..."
      value={searchTerm}
      onChange={handleChange}
      size="large"
    />
  );
}

// 节流滚动处理
function ThrottotedScroll() {
  const handleScroll = useCallback(
    throttle(() => {
      console.log('Scroll position:', window.scrollY);
      // 执行滚动相关操作
    }, 100),
    []
  );

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return <div>滚动页面查看节流效果</div>;
}

// 辅助函数
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  let previous = 0;
  return (...args: Parameters<T>) => {
    const now = Date.now();
    const remaining = wait - (now - previous);

    if (remaining <= 0 || remaining > wait) {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }
      previous = now;
      func(...args);
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now();
        timeout = null;
        func(...args);
      }, remaining);
    }
  };
}
```

---

## 安全区域适配

### 刘海屏适配

```tsx
import { ConfigProvider, Layout } from 'antd';

const { Header, Content, Footer } = Layout;

function SafeAreaLayout() {
  return (
    <ConfigProvider
      theme={{
        token: {
          // 使用 CSS 变量适配安全区域
          headerHeight: 'calc(56px + env(safe-area-inset-top))',
          footerHeight: 'calc(56px + env(safe-area-inset-bottom))',
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          style={{
            paddingTop: 'env(safe-area-inset-top)',
            height: 'calc(64px + env(safe-area-inset-top))',
            display: 'flex',
            alignItems: 'flex-end',
            paddingBottom: 16,
          }}
        >
          <h1 style={{ margin: 0 }}>应用标题</h1>
        </Header>

        <Content style={{ padding: 16 }}>
          <div>主要内容</div>
        </Content>

        <Footer
          style={{
            paddingBottom: 'env(safe-area-inset-bottom)',
            height: 'calc(64px + env(safe-area-inset-bottom))',
            display: 'flex',
            alignItems: 'flex-start',
            paddingTop: 16,
          }}
        >
          <div>底部内容</div>
        </Footer>
      </Layout>
    </ConfigProvider>
  );
}
```

### 全局安全区域样式

```css
/* globals.css 或在 App.css 中 */

/* 适配 iOS 刘海屏 */
@supports (padding: max(0px)) {
  body {
    padding-left: max(0px, env(safe-area-inset-left));
    padding-right: max(0px, env(safe-area-inset-right));
  }

  .safe-area-top {
    padding-top: max(0px, env(safe-area-inset-top));
  }

  .safe-area-bottom {
    padding-bottom: max(0px, env(safe-area-inset-bottom));
  }

  .safe-area-left {
    padding-left: max(0px, env(safe-area-inset-left));
  }

  .safe-area-right {
    padding-right: max(0px, env(safe-area-inset-right));
  }

  .safe-area-all {
    padding: max(0px, env(safe-area-inset-top))
             max(0px, env(safe-area-inset-right))
             max(0px, env(safe-area-inset-bottom))
             max(0px, env(safe-area-inset-left));
  }
}
```

```tsx
// 使用示例
function SafeAreaComponent() {
  return (
    <div>
      {/* 顶部安全区域 */}
      <div className="safe-area-top">顶部内容</div>

      {/* 底部安全区域 */}
      <div className="safe-area-bottom">底部内容</div>

      {/* 全部安全区域 */}
      <div className="safe-area-all">完整内容</div>
    </div>
  );
}
```

---

## PWA 支持

### Service Worker 配置

```tsx
// service-worker.ts
const CACHE_NAME = 'antd-mobile-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css',
];

self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('fetch', (event: FetchEvent) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // 缓存优先策略
      return response || fetch(event.request);
    })
  );
});

self.addEventListener('activate', (event: ExtendableEvent) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
```

### 注册 Service Worker

```tsx
// App.tsx
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/service-worker.ts')
        .then((registration) => {
          console.log('Service Worker registered:', registration);
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error);
        });
    }
  }, []);

  return (
    <div>
      <h1>PWA 应用</h1>
      <YourApp />
    </div>
  );
}
```

### Manifest 配置

```json
// public/manifest.json
{
  "name": "Ant Design Mobile App",
  "short_name": "Antd Mobile",
  "description": "Ant Design 移动端 PWA 应用",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#1890ff",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/mobile-1.png",
      "sizes": "540x720",
      "type": "image/png"
    }
  ],
  "categories": ["productivity", "utilities"],
  "shortcuts": [
    {
      "name": "新建任务",
      "short_name": "新建",
      "description": "创建新任务",
      "url": "/create-task",
      "icons": [{ "src": "/icons/shortcut.png", "sizes": "96x96" }]
    }
  ]
}
```

```html
<!-- index.html -->
<head>
  <link rel="manifest" href="/manifest.json" />
  <meta name="theme-color" content="#1890ff" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <link rel="apple-touch-icon" href="/icons/icon-152x152.png" />
</head>
```

### 添加到主屏幕提示

```tsx
import { useState, useEffect } from 'react';
import { Modal, Button } from 'antd';

function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('PWA 安装成功');
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
  };

  if (!showPrompt) return null;

  return (
    <Modal
      title="安装应用"
      open={showPrompt}
      onCancel={handleDismiss}
      footer={[
        <Button key="dismiss" onClick={handleDismiss}>
          稍后再说
        </Button>,
        <Button key="install" type="primary" onClick={handleInstall}>
          立即安装
        </Button>,
      ]}
    >
      <p>将此应用添加到主屏幕,获得更好的使用体验!</p>
    </Modal>
  );
}
```

---

## 完整使用示例

### 示例 1: 移动端登录页面

```tsx
import { Form, Input, Button, Checkbox, Card, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

function MobileLoginPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Login success:', values);
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
        backgroundColor: '#f0f2f5',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          borderRadius: 8,
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ margin: 0 }}>
              欢迎登录
            </Title>
            <Text type="secondary">Ant Design 移动端应用</Text>
          </div>

          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            autoComplete="off"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                size="large"
                autoComplete="username"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                size="large"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox>记住我</Checkbox>
                </Form.Item>
                <a href="#forgot">忘记密码?</a>
              </div>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={loading}
              >
                登录
              </Button>
            </Form.Item>

            <Form.Item>
              <Button block size="large">
                注册账号
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
```

### 示例 2: 移动端列表页(支持下拉刷新)

```tsx
import { useState, useEffect } from 'react';
import { List, Avatar, Typography, PullToRefresh, InfiniteScroll } from 'antd';
import { UserOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface Item {
  id: number;
  name: string;
  description: string;
}

function MobileListWithRefresh() {
  const [data, setData] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  // 模拟数据加载
  const loadData = async (page: number): Promise<Item[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const items = Array.from({ length: 20 }, (_, i) => ({
          id: (page - 1) * 20 + i,
          name: `Item ${(page - 1) * 20 + i}`,
          description: `Description for item ${(page - 1) * 20 + i}`,
        }));
        resolve(items);
      }, 1000);
    });
  };

  // 下拉刷新
  const handleRefresh = async () => {
    setLoading(true);
    const newData = await loadData(1);
    setData(newData);
    setLoading(false);
  };

  // 加载更多
  const loadMore = async () => {
    if (loading) return;

    setLoading(true);
    const page = Math.floor(data.length / 20) + 1;
    const newData = await loadData(page);

    setData([...data, ...newData]);
    setLoading(false);

    // 模拟数据加载完毕
    if (data.length + newData.length >= 100) {
      setHasMore(false);
    }
  };

  useEffect(() => {
    handleRefresh();
  }, []);

  return (
    <PullToRefresh onRefresh={handleRefresh} loading={loading}>
      <List
        dataSource={data}
        renderItem={(item) => (
          <List.Item
            style={{
              padding: 16,
              cursor: 'pointer',
            }}
            onClick={() => console.log('Clicked:', item.id)}
          >
            <List.Item.Meta
              avatar={<Avatar icon={<UserOutlined />} />}
              title={<Text strong>{item.name}</Text>}
              description={<Text type="secondary">{item.description}</Text>}
            />
          </List.Item>
        )}
      />
      <InfiniteScroll
        loadMore={loadMore}
        hasMore={hasMore}
        loading={loading}
      />
    </PullToRefresh>
  );
}
```

### 示例 3: 响应式布局(移动端/桌面端)

```tsx
import { Layout, Menu, Button, Dropdown, Grid } from 'antd';
import { MenuOutlined, UserOutlined } from '@ant-design/icons';

const { Header, Content, Sider } = Layout;
const { useBreakpoint } = Grid;

function ResponsiveLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const screens = useBreakpoint();

  const isMobile = !screens.md;

  const menuItems = [
    { key: '1', label: '首页' },
    { key: '2', label: '产品' },
    { key: '3', label: '服务' },
    { key: '4', label: '关于' },
  ];

  const userMenuItems = [
    { key: 'profile', label: '个人资料' },
    { key: 'settings', label: '设置' },
    { key: 'logout', label: '退出登录' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 移动端顶部栏 */}
      {isMobile && (
        <Header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 16px',
            backgroundColor: '#001529',
          }}
        >
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setDrawerVisible(true)}
            style={{ color: '#fff' }}
          />
          <div style={{ color: '#fff', fontSize: 18 }}>Logo</div>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button
              type="text"
              icon={<UserOutlined />}
              style={{ color: '#fff' }}
            />
          </Dropdown>
        </Header>
      )}

      {/* 侧边栏(仅桌面端) */}
      {!isMobile && (
        <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
          <div
            style={{
              height: 32,
              margin: 16,
              color: '#fff',
              fontSize: 20,
              textAlign: 'center',
            }}
          >
            Logo
          </div>
          <Menu
            theme="dark"
            defaultSelectedKeys={['1']}
            mode="inline"
            items={menuItems}
          />
        </Sider>
      )}

      {/* 主内容区 */}
      <Layout>
        <Content style={{ padding: isMobile ? 16 : 24 }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              backgroundColor: '#fff',
              borderRadius: 4,
            }}
          >
            <h1>主内容</h1>
            <p>当前设备: {isMobile ? '移动端' : '桌面端'}</p>
          </div>
        </Content>
      </Layout>

      {/* 移动端侧边抽屉 */}
      {isMobile && (
        <Drawer
          title="菜单"
          placement="left"
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
        >
          <Menu
            defaultSelectedKeys={['1']}
            mode="vertical"
            items={menuItems}
            onClick={() => setDrawerVisible(false)}
          />
        </Drawer>
      )}
    </Layout>
  );
}
```

### 示例 4: 移动端表单(带验证)

```tsx
import { Form, Input, Button, Select, DatePicker, Checkbox, Space } from 'antd';
import { UserOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';

function MobileFormWithValidation() {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Form values:', values);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      style={{ padding: 16 }}
    >
      <Form.Item
        label="姓名"
        name="name"
        rules={[
          { required: true, message: '请输入姓名' },
          { min: 2, message: '姓名至少 2 个字符' },
          { max: 20, message: '姓名最多 20 个字符' },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="请输入姓名"
          size="large"
        />
      </Form.Item>

      <Form.Item
        label="邮箱"
        name="email"
        rules={[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '邮箱格式不正确' },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="请输入邮箱"
          size="large"
          autoComplete="email"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
        />
      </Form.Item>

      <Form.Item
        label="手机号"
        name="phone"
        rules={[
          { required: true, message: '请输入手机号' },
          {
            pattern: /^1[3-9]\d{9}$/,
            message: '手机号格式不正确',
          },
        ]}
      >
        <Input
          prefix={<PhoneOutlined />}
          placeholder="请输入手机号"
          size="large"
          type="tel"
          maxLength={11}
        />
      </Form.Item>

      <Form.Item
        label="性别"
        name="gender"
        rules={[{ required: true, message: '请选择性别' }]}
      >
        <Select
          placeholder="请选择性别"
          size="large"
          options={[
            { label: '男', value: 'male' },
            { label: '女', value: 'female' },
            { label: '其他', value: 'other' },
          ]}
        />
      </Form.Item>

      <Form.Item
        label="生日"
        name="birthday"
        rules={[{ required: true, message: '请选择生日' }]}
      >
        <DatePicker
          placeholder="请选择生日"
          size="large"
          style={{ width: '100%' }}
          inputReadOnly
        />
      </Form.Item>

      <Form.Item
        name="agree"
        valuePropName="checked"
        rules={[{
          validator: (_, value) =>
            value ? Promise.resolve() : Promise.reject(new Error('请同意用户协议')),
        }]}
      >
        <Checkbox>
          我已阅读并同意
          <a href="#terms">用户协议</a>
          和
          <a href="#privacy">隐私政策</a>
        </Checkbox>
      </Form.Item>

      <Form.Item>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Button type="primary" htmlType="submit" block size="large">
            提交
          </Button>
          <Button htmlType="reset" block size="large">
            重置
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
}
```

### 示例 5: 移动端底部导航

```tsx
import { useState } from 'react';
import { Layout, TabBar, Badge } from 'antd';
import {
  HomeOutlined,
  AppstoreOutlined,
  MessageOutlined,
  UserOutlined,
} from '@ant-design/icons';

const { Content } = Layout;

function MobileTabBar() {
  const [activeKey, setActiveKey] = useState('home');

  const tabItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      title: '首页',
      badge: '3',
    },
    {
      key: 'apps',
      icon: <AppstoreOutlined />,
      title: '应用',
    },
    {
      key: 'messages',
      icon: <MessageOutlined />,
      title: '消息',
      badge: <Badge count={99} overflowCount={99} />,
    },
    {
      key: 'me',
      icon: <UserOutlined />,
      title: '我的',
    },
  ];

  const renderContent = () => {
    switch (activeKey) {
      case 'home':
        return <div>首页内容</div>;
      case 'apps':
        return <div>应用内容</div>;
      case 'messages':
        return <div>消息内容</div>;
      case 'me':
        return <div>我的内容</div>;
      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ paddingBottom: 50 }}>
        {renderContent()}
      </Content>

      <TabBar
        activeKey={activeKey}
        onChange={setActiveKey}
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 999,
          paddingBottom: 'env(safe-area-inset-bottom)',
        }}
      >
        {tabItems.map((item) => (
          <TabBar.Item key={item.key} icon={item.icon} title={item.title} badge={item.badge} />
        ))}
      </TabBar>
    </Layout>
  );
}
```

---

## 最佳实践

### 1. 响应式设计

**✅ 推荐**: 移动优先设计,使用相对单位

```tsx
// 使用百分比和 fr 单位
<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
  <div>Item 1</div>
  <div>Item 2</div>
</div>

// 使用视口单位
<div style={{ fontSize: 'clamp(14px, 4vw, 18px)' }}>
  响应式文本
</div>
```

**❌ 避免**: 固定像素尺寸

```tsx
<div style={{ width: 375, height: 667 }}>固定尺寸</div>
```

### 2. 触摸目标大小

**✅ 推荐**: 触摸目标至少 44x44 像素(iOS)或 48x48 像素(Android)

```tsx
<Button style={{ minWidth: 44, minHeight: 44 }}>
  按钮
</Button>
```

**❌ 避免**: 小于推荐尺寸的触摸目标

```tsx
<Button style={{ width: 30, height: 30 }}>
  图标
</Button>
```

### 3. 性能优化

**✅ 推荐**: 使用虚拟滚动处理大数据

```tsx
<List virtual height={600} dataSource={largeData} />
```

**❌ 避免**: 一次性渲染大量 DOM

```tsx
{largeData.map(item => <div key={item.id}>{item.name}</div>)}
```

### 4. 图片优化

**✅ 推荐**: 使用 srcset 和 sizes 提供响应式图片

```tsx
<img
  src="image-800.jpg"
  srcSet="image-400.jpg 400w, image-800.jpg 800w, image-1200.jpg 1200w"
  sizes="(max-width: 600px) 100vw, 50vw"
  loading="lazy"
  alt="响应式图片"
/>
```

**❌ 避免**: 加载过大的图片

```tsx
<img src="image-4000.jpg" alt="大图" />
```

### 5. 输入优化

**✅ 推荐**: 为移动端输入框设置正确的键盘类型

```tsx
<Input
  type="email"      // 邮箱键盘
  type="tel"        // 数字键盘
  type="url"        // URL 键盘
  type="number"     // 数字键盘
  inputMode="numeric" // 数字输入模式
  pattern="[0-9]*"  // 限制输入格式
/>
```

**❌ 避免**: 不指定输入类型

```tsx
<Input placeholder="手机号" /> {/* 显示全键盘 */}
```

### 6. 滚动优化

**✅ 推荐**: 使用 CSS 属性优化滚动性能

```css
.smooth-scroll {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  will-change: scroll-position;
}
```

**❌ 避免**: 监听 scroll 事件执行重操作

```tsx
useEffect(() => {
  const handleScroll = () => {
    // 执行复杂计算,影响性能
  };
  window.addEventListener('scroll', handleScroll);
}, []);
```

---

## 常见问题

### Q1: 如何检测设备类型?

A: 使用 `useBreakpoint` Hook 或 `window.innerWidth`:

```tsx
import { Grid } from 'antd';

const { useBreakpoint } = Grid;

function DeviceDetector() {
  const screens = useBreakpoint();
  const isMobile = screens.xs && !screens.md;
  const isTablet = screens.md && !screens.lg;
  const isDesktop = screens.lg;

  return (
    <div>
      {isMobile && <div>移动端</div>}
      {isTablet && <div>平板</div>}
      {isDesktop && <div>桌面端</div>}
    </div>
  );
}
```

### Q2: 如何禁用移动端双击缩放?

A: 在 `<head>` 中添加 meta 标签:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
```

### Q3: 如何适配安全区域(刘海屏)?

A: 使用 CSS 环境变量:

```css
.header {
  padding-top: env(safe-area-inset-top);
}

.footer {
  padding-bottom: env(safe-area-inset-bottom);
}
```

### Q4: 如何优化移动端滚动性能?

A: 使用 CSS 属性和虚拟滚动:

```css
.container {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  will-change: scroll-position;
}
```

```tsx
<List virtual height={600} dataSource={data} />
```

### Q5: 如何处理移动端输入焦点问题?

A: 监听视口变化并调整布局:

```tsx
useEffect(() => {
  const handleResize = () => {
    const isKeyboardOpen = window.innerHeight < window.screen.height * 0.75;
    // 根据键盘状态调整布局
  };

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

### Q6: 如何实现移动端下拉刷新?

A: 使用 antd 的 `PullToRefresh` 组件:

```tsx
import { PullToRefresh } from 'antd';

<PullToRefresh onRefresh={handleRefresh}>
  <YourContent />
</PullToRefresh>
```

### Q7: 如何实现移动端无限滚动?

A: 使用 antd 的 `InfiniteScroll` 组件:

```tsx
import { InfiniteScroll } from 'antd';

<InfiniteScroll loadMore={loadMore} hasMore={hasMore}>
  <List dataSource={data} />
</InfiniteScroll>
```

### Q8: 如何优化移动端图片加载?

A: 使用懒加载和响应式图片:

```tsx
<Image
  src={src}
  loading="lazy"
  width="100%"
  height={200}
  style={{ objectFit: 'cover' }}
/>
```

### Q9: 如何实现移动端底部导航?

A: 使用 antd 的 `TabBar` 组件:

```tsx
import { TabBar } from 'antd';

<TabBar activeKey={activeKey} onChange={setActiveKey}>
  <TabBar.Item key="home" icon={<HomeOutlined />} title="首页" />
  <TabBar.Item key="apps" icon={<AppstoreOutlined />} title="应用" />
</TabBar>
```

### Q10: 如何禁用移动端长按选中文本?

A: 使用 CSS 属性:

```css
.no-select {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
```

---

## 参考资料

- [Ant Design 移动端组件文档](https://ant.design/components/)
- [响应式设计指南](https://ant.design/docs/react/responsive-cn)
- [PWA 官方文档](https://web.dev/progressive-web-apps/)
- [Web 性能优化](https://web.dev/fast/)
- [触摸事件 API](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events)
- [安全区域适配](https://webkit.org/blog/7925/designing-websites-for-iphone-x/)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- 现代浏览器(iOS Safari 12+, Android Chrome 80+)

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
