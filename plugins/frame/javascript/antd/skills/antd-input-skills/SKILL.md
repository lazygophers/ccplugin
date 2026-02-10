---
name: antd-input-skills
description: Ant Design 输入组件完整指南 - Input、Select、DatePicker、Upload、Radio、Checkbox、Switch、Slider、Rate
---

# antd-input-skills - Ant Design 输入组件完整指南

## 概述

Ant Design 输入组件是一套完整的数据采集解决方案，涵盖文本输入、选择输入、日期时间、文件上传等常见场景。所有输入组件都遵循 Ant Design 的设计规范，提供一致的交互体验、完善的错误处理、无障碍访问支持，以及与 Form 组件的深度集成。

## 核心特性

- **统一 API 设计** - 所有输入组件遵循相同的属性约定（value/onChange、disabled、readOnly）
- **表单集成** - 与 Form.Item 无缝集成，自动处理验证和错误状态
- **类型安全** - 完整的 TypeScript 类型定义
- **国际化** - 内置多语言支持
- **可访问性** - 符合 WCAG 2.1 标准，支持键盘导航和屏幕阅读器
- **自定义样式** - 支持通过 theme token 或 className 自定义外观
- **性能优化** - 虚拟滚动、防抖搜索、懒加载等优化策略

## 组件分类

### 1. 文本输入组件
- **Input** - 基础文本输入框
- **Input.TextArea** - 多行文本输入
- **Input.Password** - 密码输入框
- **Input.Search** - 搜索输入框
- **InputNumber** - 数字输入框

### 2. 选择输入组件
- **Select** - 下拉选择框（单选/多选/分组/异步搜索）
- **AutoComplete** - 自动完成输入
- **Cascader** - 级联选择器
- **TreeSelect** - 树形选择器

### 3. 日期时间组件
- **DatePicker** - 日期选择器
- **DatePicker.RangePicker** - 日期范围选择器
- **TimePicker** - 时间选择器
- **Calendar** - 日历面板

### 4. 其他输入组件
- **Radio / Radio.Group** - 单选框组
- **Checkbox / Checkbox.Group** - 复选框组
- **Switch** - 开关
- **Slider** - 滑动输入条
- **Rate** - 评分组件
- **Upload** - 文件上传

---

## 文本输入组件

### Input - 基础文本输入

基础文本输入框，支持前缀、后缀、图标等多种形态。

**核心属性：**

```typescript
interface InputProps {
  value?: string;                    // 输入值
  onChange?: (e: ChangeEvent) => void; // 值变化回调
  placeholder?: string;              // 占位符
  disabled?: boolean;                // 禁用状态
  readOnly?: boolean;                // 只读状态
  maxLength?: number;                // 最大长度
  prefix?: ReactNode;                // 前缀
  suffix?: ReactNode;                // 后缀
  allowClear?: boolean;              // 显示清除按钮
  addonBefore?: ReactNode;           // 带标签的前缀
  addonAfter?: ReactNode;            // 带标签的后缀
  size?: 'large' | 'middle' | 'small'; // 尺寸
  status?: 'error' | 'warning';      // 状态
}
```

**示例 1：基础 Input 输入（文本、密码、搜索）**

```tsx
import React, { useState } from 'react';
import { Input, Form, Button, Space, message } from 'antd';
import type { ChangeEvent } from 'react';
import { UserOutlined, LockOutlined, SearchOutlined } from '@ant-design/icons';

const InputExamples: React.FC = () => {
  const [searchValue, setSearchValue] = useState('');
  const [form] = Form.useForm();

  // 普通文本输入
  const [textValue, setTextValue] = useState('');

  // 密码输入
  const [passwordValue, setPasswordValue] = useState('');

  // 搜索输入
  const handleSearch = (value: string) => {
    message.info(`搜索: ${value}`);
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础文本输入 */}
        <div>
          <h4>基础文本输入</h4>
          <Space direction="vertical">
            <Input
              placeholder="请输入用户名"
              prefix={<UserOutlined />}
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              allowClear
              style={{ width: 300 }}
            />

            <Input
              placeholder="禁用状态"
              disabled
              defaultValue="不可编辑"
            />

            <Input
              placeholder="只读状态"
              readOnly
              defaultValue="只读内容"
            />
          </Space>
        </div>

        {/* 2. 密码输入 */}
        <div>
          <h4>密码输入</h4>
          <Space direction="vertical">
            <Input.Password
              placeholder="请输入密码"
              prefix={<LockOutlined />}
              value={passwordValue}
              onChange={(e) => setPasswordValue(e.target.value)}
              iconRender={(visible) => (visible ? '👁️' : '👁️‍🗨️')}
              style={{ width: 300 }}
            />

            <Input.Password
              placeholder="带可见性切换的密码"
              visibilityToggle
            />
          </Space>
        </div>

        {/* 3. 搜索输入 */}
        <div>
          <h4>搜索输入</h4>
          <Input.Search
            placeholder="搜索内容..."
            allowClear
            enterButton={<Button type="primary" icon={<SearchOutlined />}>搜索</Button>}
            size="large"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 400 }}
          />
        </div>

        {/* 4. 带标签的组合输入 */}
        <div>
          <h4>组合输入</h4>
          <Space direction="vertical">
            <Input
              addonBefore="http://"
              placeholder="域名"
              addonAfter=".com"
              defaultValue="example"
              style={{ width: 300 }}
            />

            <Input
              addonBefore={<Select defaultValue="http" style={{ width: 80 }}>
                <Select.Option value="http">http://</Select.Option>
              </Select>}
              placeholder="输入 URL"
              style={{ width: 400 }}
            />
          </Space>
        </div>

        {/* 5. 在表单中使用 */}
        <div>
          <h4>表单集成</h4>
          <Form
            form={form}
            layout="vertical"
            onFinish={(values) => {
              message.success('提交成功');
              console.log(values);
            }}
          >
            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '邮箱格式不正确' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="example@email.com"
              />
            </Form.Item>

            <Form.Item
              label="手机号"
              name="phone"
              rules={[
                { required: true, message: '请输入手机号' },
                { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
              ]}
            >
              <Input
                addonBefore="+86"
                placeholder="请输入手机号"
                maxLength={11}
              />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Form.Item>
          </Form>
        </div>

      </Space>
    </div>
  );
};

export default InputExamples;
```

### Input.TextArea - 多行文本输入

用于长文本输入场景，如评论、描述、备注等。

**核心属性：**

```typescript
interface TextAreaProps extends InputProps {
  autoSize?: boolean | { minRows?: number; maxRows?: number }; // 自动高度
  rows?: number;              // 固定行数
  showCount?: boolean;        // 显示字符计数
  maxLength?: number;         // 最大字符数
}
```

**示例：多行文本输入**

```tsx
import React from 'react';
import { Input, Form } from 'antd';
import { TextArea } from 'antd/es/input';

const TextAreaExamples: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Form layout="vertical">
        {/* 自动高度 */}
        <Form.Item label="自动调整高度">
          <TextArea
            placeholder="内容增加时自动扩展"
            autoSize={{ minRows: 2, maxRows: 6 }}
          />
        </Form.Item>

        {/* 固定行数 */}
        <Form.Item label="固定 4 行">
          <TextArea
            rows={4}
            placeholder="固定 4 行高度"
          />
        </Form.Item>

        {/* 带字符计数 */}
        <Form.Item
          label="产品描述"
          name="description"
          rules={[{ max: 200, message: '最多 200 个字符' }]}
        >
          <TextArea
            showCount
            maxLength={200}
            placeholder="请输入产品描述（最多 200 字）"
            autoSize={{ minRows: 3, maxRows: 6 }}
          />
        </Form.Item>
      </Form>
    </div>
  );
};

export default TextAreaExamples;
```

### InputNumber - 数字输入

专用于数字输入，支持步进器、范围限制、格式化等。

**核心属性：**

```typescript
interface InputNumberProps {
  value?: number;              // 值
  onChange?: (value: number | null) => void;
  min?: number;                // 最小值
  max?: number;                // 最大值
  step?: number;               // 步长
  precision?: number;          // 精度（小数位数）
  disabled?: boolean;          // 禁用
  placeholder?: string;        // 占位符
  controls?: boolean;          // 显示增减按钮
  stringMode?: boolean;        // 字符串模式（避免精度丢失）
  formatter?: (value: string) => string; // 格式化显示
  parser?: (value: string) => string;     // 解析输入
  prefix?: ReactNode;          // 前缀
  suffix?: ReactNode;          // 后缀
}
```

**示例：数字输入**

```tsx
import React from 'react';
import { InputNumber, Form, Space } from 'antd';

const InputNumberExamples: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Form layout="vertical">
        <Form.Item label="基础数字输入">
          <InputNumber
            min={0}
            max={100}
            defaultValue={50}
            style={{ width: 200 }}
          />
        </Form.Item>

        <Form.Item label="带步进">
          <InputNumber
            min={0}
            max={100}
            step={5}
            defaultValue={0}
            style={{ width: 200 }}
          />
        </Form.Item>

        <Form.Item label="小数精度">
          <InputNumber
            min={0}
            max={1}
            step={0.01}
            precision={2}
            defaultValue={0.5}
            style={{ width: 200 }}
          />
        </Form.Item>

        <Form.Item label="货币格式化">
          <InputNumber
            defaultValue={1000}
            formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value!.replace(/¥\s?|(,*)/g, '')}
            style={{ width: 200 }}
          />
        </Form.Item>

        <Form.Item label="百分比">
          <InputNumber
            min={0}
            max={100}
            formatter={(value) => `${value}%`}
            parser={(value) => value!.replace('%', '')}
            style={{ width: 200 }}
          />
        </Form.Item>
      </Form>
    </div>
  );
};

export default InputNumberExamples;
```

---

## 选择输入组件

### Select - 下拉选择

Select 是最常用的选择组件，支持单选、多选、分组、异步搜索等。

**核心属性：**

```typescript
interface SelectProps<ValueType = any> {
  value?: ValueType | ValueType[];
  onChange?: (value: ValueType | ValueType[]) => void;
  mode?: 'multiple' | 'tags' | 'combobox'; // 多选模式
  options?: Array<{           // 选项数据
    label: string;
    value: any;
    disabled?: boolean;
    children?: any[];
  }>;
  disabled?: boolean;
  placeholder?: string;
  allowClear?: boolean;
  showSearch?: boolean;       // 显示搜索框
  filterOption?: boolean | ((input: string, option: any) => boolean);
  loading?: boolean;          // 加载状态
  onSearch?: (value: string) => void; // 搜索回调
  notFoundContent?: ReactNode; // 无数据提示
  virtual?: boolean;          // 虚拟滚动（大数据量）
  listHeight?: number;        // 下拉列表高度
  maxTagCount?: number | 'responsive'; // 多选标签显示数量
  bordered?: boolean;         // 显示边框
}
```

**示例 2：Select 异步搜索**

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { Select, Form, Tag, Spin } from 'antd';
import type { SelectProps } from 'antd';
import debounce from 'lodash/debounce';

// 模拟异步搜索 API
const searchUsers = async (keyword: string): Promise<SelectProps['options']> => {
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 500));

  const allUsers = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
    { id: 3, name: 'Charlie', email: 'charlie@example.com' },
    { id: 4, name: 'David', email: 'david@example.com' },
    { id: 5, name: 'Emma', email: 'emma@example.com' },
    { id: 6, name: 'Frank', email: 'frank@example.com' },
    { id: 7, name: 'Grace', email: 'grace@example.com' },
    { id: 8, name: 'Henry', email: 'henry@example.com' },
  ];

  if (!keyword) {
    return allUsers.map(user => ({
      label: user.name,
      value: user.id,
    }));
  }

  const filtered = allUsers.filter(user =>
    user.name.toLowerCase().includes(keyword.toLowerCase()) ||
    user.email.toLowerCase().includes(keyword.toLowerCase())
  );

  return filtered.map(user => ({
    label: user.name,
    value: user.id,
  }));
};

const SelectExamples: React.FC = () => {
  const [options, setOptions] = useState<SelectProps['options']>([]);
  const [fetching, setFetching] = useState(false);
  const [value, setValue] = useState<number[]>([]);
  const searchRef = useRef<() => void>();

  // 防抖搜索
  const debounceFetcher = React.useMemo(
    () =>
      debounce((keyword: string) => {
        setOptions([]);
        setFetching(true);

        searchUsers(keyword).then((newOptions) => {
          setOptions(newOptions);
          setFetching(false);
        });
      }, 300),
    []
  );

  searchRef.current = debounceFetcher;

  useEffect(() => {
    // 初始加载
    searchUsers('').then(setOptions);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础单选 */}
        <div>
          <h4>基础单选</h4>
          <Form layout="vertical">
            <Form.Item label="选择角色">
              <Select
                placeholder="请选择角色"
                style={{ width: 200 }}
                allowClear
                options={[
                  { label: '管理员', value: 'admin' },
                  { label: '编辑', value: 'editor' },
                  { label: '访客', value: 'guest' },
                ]}
              />
            </Form.Item>
          </Form>
        </div>

        {/* 2. 分组选择 */}
        <div>
          <h4>分组选择</h4>
          <Select
            placeholder="请选择"
            style={{ width: 250 }}
            options={[
              {
                label: '前端',
                options: [
                  { label: 'React', value: 'react' },
                  { label: 'Vue', value: 'vue' },
                  { label: 'Angular', value: 'angular' },
                ],
              },
              {
                label: '后端',
                options: [
                  { label: 'Node.js', value: 'nodejs' },
                  { label: 'Python', value: 'python' },
                  { label: 'Go', value: 'go' },
                ],
              },
            ]}
          />
        </div>

        {/* 3. 多选 */}
        <div>
          <h4>多选</h4>
          <Select
            mode="multiple"
            placeholder="选择技术栈"
            style={{ width: 300 }}
            defaultValue={['react', 'typescript']}
            options={[
              { label: 'React', value: 'react' },
              { label: 'Vue', value: 'vue' },
              { label: 'Angular', value: 'angular' },
              { label: 'TypeScript', value: 'typescript' },
              { label: 'JavaScript', value: 'javascript' },
            ]}
            maxTagCount="responsive"
          />
        </div>

        {/* 4. 标签模式（可添加新选项） */}
        <div>
          <h4>标签模式</h4>
          <Select
            mode="tags"
            placeholder="输入标签后回车"
            style={{ width: 400 }}
            defaultValue={['react', 'antd']}
            options={[
              { label: 'React', value: 'react' },
              { label: 'Vue', value: 'vue' },
              { label: 'Angular', value: 'angular' },
            ]}
          />
        </div>

        {/* 5. 异步搜索（多选） */}
        <div>
          <h4>异步搜索（多选）</h4>
          <Select
            mode="multiple"
            labelInValue
            value={value}
            placeholder="搜索用户（支持多选）"
            style={{ width: 400 }}
            filterOption={false}
            onSearch={(keyword) => searchRef.current?.(keyword)}
            options={options}
            loading={fetching}
            notFoundContent={fetching ? <Spin size="small" /> : '无数据'}
            onChange={(newValue) => {
              setValue(newValue as unknown as number[]);
            }}
            maxTagCount={3}
            maxTagPlaceholder={(omittedValues) => `+${omittedValues.length} ...`}
          >
            {/* 自定义选项渲染 */}
            {options?.map((option) => (
              <Select.Option key={option.value} value={option.value}>
                <div>
                  <div>{option.label}</div>
                  <div style={{ fontSize: 12, color: '#999' }}>
                    User ID: {option.value}
                  </div>
                </div>
              </Select.Option>
            ))}
          </Select>

          <div style={{ marginTop: 8 }}>
            已选择: {value.length} 位用户
          </div>
        </div>

        {/* 6. 表单集成 */}
        <div>
          <h4>表单集成</h4>
          <Form layout="vertical" onFinish={(values) => console.log(values)}>
            <Form.Item
              label="所属部门"
              name="department"
              rules={[{ required: true, message: '请选择部门' }]}
            >
              <Select
                placeholder="请选择部门"
                options={[
                  { label: '研发部', value: 'rd' },
                  { label: '产品部', value: 'product' },
                  { label: '设计部', value: 'design' },
                  { label: '市场部', value: 'marketing' },
                ]}
              />
            </Form.Item>

            <Form.Item
              label="负责项目（多选）"
              name="projects"
            >
              <Select
                mode="multiple"
                placeholder="选择项目"
                options={[
                  { label: '项目 A', value: 'project-a' },
                  { label: '项目 B', value: 'project-b' },
                  { label: '项目 C', value: 'project-c' },
                ]}
              />
            </Form.Item>
          </Form>
        </div>

      </Space>
    </div>
  );
};

export default SelectExamples;
```

### AutoComplete - 自动完成

自动完成输入框，根据用户输入提供匹配建议。

**示例：自动完成**

```tsx
import React, { useState } from 'react';
import { AutoComplete } from 'antd';

const AutoCompleteExample: React.FC = () => {
  const [options, setOptions] = useState<{ value: string }[]>([]);
  const allOptions = [
    { value: 'Burns Bay Road' },
    { value: 'Downing Street' },
    { value: 'Wall Street' },
  ];

  const handleSearch = (searchText: string) => {
    if (!searchText) {
      setOptions([]);
    } else {
      setOptions(
        allOptions.filter((option) =>
          option.value.toUpperCase().includes(searchText.toUpperCase())
        )
      );
    }
  };

  return (
    <AutoComplete
      options={options}
      style={{ width: 200 }}
      onSearch={handleSearch}
      placeholder="输入街道名称"
    />
  );
};

export default AutoCompleteExample;
```

### Cascader - 级联选择

用于具有层级关系的数据选择，如省市区选择。

**示例：级联选择**

```tsx
import React from 'react';
import { Cascader } from 'antd';

interface Option {
  value: string;
  label: string;
  children?: Option[];
}

const options: Option[] = [
  {
    label: '浙江',
    value: 'zhejiang',
    children: [
      {
        label: '杭州',
        value: 'hangzhou',
        children: [
          { label: '西湖', value: 'xihu' },
          { label: '滨江', value: 'binjiang' },
        ],
      },
      {
        label: '宁波',
        value: 'ningbo',
        children: [
          { label: '海曙', value: 'haishu' },
          { label: '江北', value: 'jiangbei' },
        ],
      },
    ],
  },
  {
    label: '江苏',
    value: 'jiangsu',
    children: [
      {
        label: '南京',
        value: 'nanjing',
        children: [
          { label: '玄武', value: 'xuanwu' },
          { label: '秦淮', value: 'qinhuai' },
        ],
      },
    ],
  },
];

const CascaderExample: React.FC = () => {
  return (
    <Cascader
      options={options}
      placeholder="请选择省/市/区"
      style={{ width: 300 }}
      changeOnSelect
    />
  );
};

export default CascaderExample;
```

### TreeSelect - 树形选择

适用于树形结构的数据选择，如组织架构、分类目录等。

**示例：树形选择**

```tsx
import React from 'react';
import { TreeSelect } from 'antd';

const treeData = [
  {
    title: 'Node1',
    value: '1',
    children: [
      { title: 'Child Node1', value: '1-1' },
      { title: 'Child Node2', value: '1-2' },
    ],
  },
  {
    title: 'Node2',
    value: '2',
    children: [
      { title: 'Child Node3', value: '2-1' },
      { title: 'Child Node4', value: '2-2' },
    ],
  },
];

const TreeSelectExample: React.FC = () => {
  const [value, setValue] = React.useState<string>();

  return (
    <TreeSelect
      style={{ width: 300 }}
      value={value}
      dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
      treeData={treeData}
      placeholder="请选择"
      treeDefaultExpandAll
      onChange={(newValue) => setValue(newValue as string)}
    />
  );
};

export default TreeSelectExample;
```

---

## 日期时间组件

### DatePicker - 日期选择器

日期选择器支持单日期、日期范围、时间等多种模式。

**核心属性：**

```typescript
interface DatePickerProps {
  value?: Dayjs;               // 日期值
  onChange?: (date: Dayjs | null, dateString: string) => void;
  format?: string;             // 显示格式
  disabled?: boolean;          // 禁用
  placeholder?: string;        // 占位符
  disabledDate?: (date: Dayjs) => boolean; // 禁用日期
  showTime?: boolean | object; // 显示时间
  picker?: 'date' | 'week' | 'month' | 'quarter' | 'year'; // 选择器类型
  allowClear?: boolean;        // 显示清除按钮
  inputReadOnly?: boolean;     // 只读
  size?: 'large' | 'middle' | 'small';
  variant?: 'outlined' | 'filled' | 'borderless';
}
```

**示例 3：DatePicker 日期范围选择**

```tsx
import React, { useState } from 'react';
import { DatePicker, Form, Space, Radio, ConfigProvider } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

// 禁用未来日期
const disabledFutureDate = (current: Dayjs) => {
  return current && current > dayjs().endOf('day');
};

// 禁用周末
const disabledWeekends = (current: Dayjs) => {
  const day = current.day();
  return day === 0 || day === 6; // 0=周日, 6=周六
};

const DatePickerExamples: React.FC = () => {
  const [date, setDate] = useState<Dayjs | null>(null);
  const [dates, setDates] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [pickerType, setPickerType] = useState<'date' | 'week' | 'month' | 'quarter' | 'year'>('date');

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础日期选择 */}
        <div>
          <h4>基础日期选择</h4>
          <DatePicker
            placeholder="选择日期"
            onChange={(date) => {
              setDate(date);
              console.log('Selected date:', date?.format('YYYY-MM-DD'));
            }}
            style={{ width: 250 }}
          />
        </div>

        {/* 2. 日期范围选择 */}
        <div>
          <h4>日期范围选择</h4>
          <Space direction="vertical">
            <RangePicker
              placeholder={['开始日期', '结束日期']}
              onChange={(dates) => {
                setDates(dates);
                if (dates && dates[0] && dates[1]) {
                  console.log('Range:', [
                    dates[0].format('YYYY-MM-DD'),
                    dates[1].format('YYYY-MM-DD')
                  ]);
                }
              }}
              style={{ width: 400 }}
            />

            <RangePicker
              showTime
              placeholder={['开始时间', '结束时间']}
              onChange={(dates) => console.log('Range with time:', dates)}
              style={{ width: 450 }}
            />
          </Space>
        </div>

        {/* 3. 禁用特定日期 */}
        <div>
          <h4>禁用特定日期</h4>
          <Space direction="vertical">
            <DatePicker
              placeholder="不能选择未来日期"
              disabledDate={disabledFutureDate}
              style={{ width: 250 }}
            />

            <DatePicker
              placeholder="不能选择周末"
              disabledDate={disabledWeekends}
              style={{ width: 250 }}
            />

            <RangePicker
              placeholder={['开始日期', '结束日期']}
              disabledDate={disabledFutureDate}
              style={{ width: 400 }}
            />
          </Space>
        </div>

        {/* 4. 自定义格式 */}
        <div>
          <h4>自定义格式</h4>
          <Space direction="vertical">
            <DatePicker
              format="YYYY年MM月DD日"
              placeholder="选择日期"
              style={{ width: 250 }}
            />

            <DatePicker
              format="YYYY/MM/DD HH:mm:ss"
              showTime
              placeholder="选择日期时间"
              style={{ width: 300 }}
            />

            <RangePicker
              format="YYYY年MM月DD日"
              placeholder={['开始日期', '结束日期']}
              style={{ width: 400 }}
            />
          </Space>
        </div>

        {/* 5. 不同选择器类型 */}
        <div>
          <h4>选择器类型</h4>
          <Space direction="vertical">
            <Radio.Group
              value={pickerType}
              onChange={(e) => setPickerType(e.target.value)}
              style={{ marginBottom: 8 }}
            >
              <Radio.Button value="date">日期</Radio.Button>
              <Radio.Button value="week">周</Radio.Button>
              <Radio.Button value="month">月</Radio.Button>
              <Radio.Button value="quarter">季度</Radio.Button>
              <Radio.Button value="year">年</Radio.Button>
            </Radio.Group>

            <DatePicker
              picker={pickerType}
              placeholder={pickerType === 'date' ? '选择日期' : `选择${pickerType}`}
              style={{ width: 250 }}
            />
          </Space>
        </div>

        {/* 6. 表单集成 */}
        <div>
          <h4>表单集成</h4>
          <Form
            layout="vertical"
            onFinish={(values) => {
              console.log('Form values:', values);
            }}
          >
            <Form.Item
              label="出生日期"
              name="birthday"
              rules={[{ required: true, message: '请选择出生日期' }]}
            >
              <DatePicker
                placeholder="选择出生日期"
                disabledDate={disabledFutureDate}
                style={{ width: 250 }}
              />
            </Form.Item>

            <Form.Item
              label="有效期"
              name="validityPeriod"
              rules={[{ required: true, message: '请选择有效期' }]}
            >
              <RangePicker
                placeholder={['开始日期', '结束日期']}
                disabledDate={disabledFutureDate}
                style={{ width: 400 }}
              />
            </Form.Item>

            <Form.Item
              label="预约时间"
              name="appointmentTime"
              rules={[{ required: true, message: '请选择预约时间' }]}
            >
              <DatePicker
                showTime
                format="YYYY-MM-DD HH:mm"
                placeholder="选择预约时间"
                style={{ width: 300 }}
              />
            </Form.Item>
          </Form>
        </div>

        {/* 7. 预设范围 */}
        <div>
          <h4>预设范围</h4>
          <RangePicker
            presets={[
              {
                label: '最近 7 天',
                value: [dayjs().add(-7, 'd'), dayjs()],
              },
              {
                label: '最近 30 天',
                value: [dayjs().add(-30, 'd'), dayjs()],
              },
              {
                label: '本月',
                value: [dayjs().startOf('month'), dayjs().endOf('month')],
              },
              {
                label: '本季度',
                value: [dayjs().startOf('quarter'), dayjs().endOf('quarter')],
              },
              {
                label: '今年',
                value: [dayjs().startOf('year'), dayjs().endOf('year')],
              },
            ]}
            style={{ width: 400 }}
            onChange={(dates) => console.log('Preset range:', dates)}
          />
        </div>

      </Space>
    </div>
  );
};

export default DatePickerExamples;
```

### TimePicker - 时间选择器

专门用于时间选择的组件。

**示例：时间选择**

```tsx
import React from 'react';
import { TimePicker } from 'antd';

const TimePickerExample: React.FC = () => {
  return (
    <TimePicker
      placeholder="选择时间"
      format="HH:mm:ss"
      style={{ width: 200 }}
      onChange={(time) => console.log('Selected time:', time?.format('HH:mm:ss'))}
    />
  );
};

export default TimePickerExample;
```

---

## 其他输入组件

### Radio / Radio.Group - 单选框组

用于从多个选项中选择一个的场景。

**示例 4：Radio 单选组**

```tsx
import React, { useState } from 'react';
import { Radio, Form, Space, Button } from 'antd';
import type { RadioChangeEvent } from 'antd';

const RadioExamples: React.FC = () => {
  const [value1, setValue1] = useState('a');
  const [value2, setValue2] = useState(1);
  const [form] = Form.useForm();

  const plainOptions = [
    { label: 'Apple', value: 'Apple' },
    { label: 'Pear', value: 'Pear' },
    { label: 'Orange', value: 'Orange' },
  ];

  const optionsWithDisabled = [
    { label: 'Apple', value: 'Apple' },
    { label: 'Pear', value: 'Pear' },
    { label: 'Orange', value: 'Orange', disabled: true },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础单选 */}
        <div>
          <h4>基础单选</h4>
          <Radio.Group
            onChange={(e) => setValue1(e.target.value)}
            value={value1}
          >
            <Radio value="a">选项 A</Radio>
            <Radio value="b">选项 B</Radio>
            <Radio value="c">选项 C</Radio>
          </Radio.Group>
          <div style={{ marginTop: 8 }}>已选择: {value1}</div>
        </div>

        {/* 2. 按钮样式 */}
        <div>
          <h4>按钮样式</h4>
          <Radio.Group
            onChange={(e) => setValue2(e.target.value)}
            value={value2}
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value={1}>选项 1</Radio.Button>
            <Radio.Button value={2}>选项 2</Radio.Button>
            <Radio.Button value={3}>选项 3</Radio.Button>
          </Radio.Group>
        </div>

        {/* 3. 使用 options 配置 */}
        <div>
          <h4>使用 options 配置</h4>
          <Space direction="vertical">
            <Radio.Group options={plainOptions} defaultValue="Apple" />

            <Radio.Group
              options={optionsWithDisabled}
              defaultValue="Apple"
              onChange={(e) => console.log(e.target.value)}
            />
          </Space>
        </div>

        {/* 4. 垂直排列 */}
        <div>
          <h4>垂直排列</h4>
          <Radio.Group defaultValue="a" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Radio value="a">选项 A</Radio>
            <Radio value="b">选项 B</Radio>
            <Radio value="c">选项 C</Radio>
          </Radio.Group>
        </div>

        {/* 5. 禁用状态 */}
        <div>
          <h4>禁用状态</h4>
          <Radio.Group defaultValue="a" disabled>
            <Radio value="a">选项 A</Radio>
            <Radio value="b">选项 B</Radio>
            <Radio value="c">选项 C</Radio>
          </Radio.Group>
        </div>

        {/* 6. 表单集成 */}
        <div>
          <h4>表单集成</h4>
          <Form
            form={form}
            layout="vertical"
            onFinish={(values) => {
              console.log('Form values:', values);
            }}
          >
            <Form.Item
              label="性别"
              name="gender"
              rules={[{ required: true, message: '请选择性别' }]}
            >
              <Radio.Group>
                <Radio value="male">男</Radio>
                <Radio value="female">女</Radio>
                <Radio value="other">其他</Radio>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              label="会员类型"
              name="membershipType"
              rules={[{ required: true, message: '请选择会员类型' }]}
            >
              <Radio.Group
                optionType="button"
                buttonStyle="solid"
              >
                <Radio.Button value="free">免费会员</Radio.Button>
                <Radio.Button value="vip">VIP 会员</Radio.Button>
                <Radio.Button value="svip">SVIP 会员</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Form.Item>
          </Form>
        </div>

      </Space>
    </div>
  );
};

export default RadioExamples;
```

### Checkbox / Checkbox.Group - 复选框组

用于从多个选项中选择多个的场景。

**示例 5：Checkbox 复选框组**

```tsx
import React, { useState } from 'react';
import { Checkbox, Form, Space, Button } from 'antd';

const CheckboxExamples: React.FC = () => {
  const [checked1, setChecked1] = useState(false);
  const [checked2, setChecked2] = useState(true);
  const [checkedGroup, setCheckedGroup] = useState<string[]>(['Apple', 'Orange']);
  const [form] = Form.useForm();

  const plainOptions = ['Apple', 'Pear', 'Orange'];
  const defaultCheckedList = ['Apple', 'Orange'];

  const onChange = (checkedValues: string[]) => {
    console.log('checked = ', checkedValues);
    setCheckedGroup(checkedValues);
  };

  const checkAll = plainOptions.length === checkedGroup.length;
  const indeterminate = checkedGroup.length > 0 && checkedGroup.length < plainOptions.length;

  const onCheckAllChange = (e: any) => {
    setCheckedGroup(e.target.checked ? plainOptions : []);
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础复选框 */}
        <div>
          <h4>基础复选框</h4>
          <Space>
            <Checkbox
              checked={checked1}
              onChange={(e) => setChecked1(e.target.checked)}
            >
              未选中
            </Checkbox>

            <Checkbox
              checked={checked2}
              onChange={(e) => setChecked2(e.target.checked)}
            >
              已选中
            </Checkbox>

            <Checkbox disabled>禁用</Checkbox>
          </Space>
        </div>

        {/* 2. 复选框组 */}
        <div>
          <h4>复选框组</h4>
          <Checkbox.Group
            options={plainOptions}
            value={checkedGroup}
            onChange={onChange}
          />
        </div>

        {/* 3. 全选 */}
        <div>
          <h4>全选示例</h4>
          <Checkbox
            indeterminate={indeterminate}
            onChange={onCheckAllChange}
            checked={checkAll}
          >
            全选
          </Checkbox>
          <Divider />
          <Checkbox.Group
            options={plainOptions}
            value={checkedGroup}
            onChange={onChange}
          />
        </div>

        {/* 4. 垂直排列 */}
        <div>
          <h4>垂直排列</h4>
          <Checkbox.Group
            defaultValue={[1]}
            style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
          >
            <Checkbox value={1}>选项 A</Checkbox>
            <Checkbox value={2}>选项 B</Checkbox>
            <Checkbox value={3}>选项 C</Checkbox>
          </Checkbox.Group>
        </div>

        {/* 5. 带禁用选项 */}
        <div>
          <h4>带禁用选项</h4>
          <Checkbox.Group
            options={[
              { label: 'Apple', value: 'Apple' },
              { label: 'Pear', value: 'Pear' },
              { label: 'Orange', value: 'Orange', disabled: true },
            ]}
            defaultValue={['Apple']}
          />
        </div>

        {/* 6. 表单集成 */}
        <div>
          <h4>表单集成</h4>
          <Form
            form={form}
            layout="vertical"
            onFinish={(values) => {
              console.log('Form values:', values);
            }}
          >
            <Form.Item
              label="兴趣爱好（多选）"
              name="hobbies"
              rules={[{ required: true, message: '请至少选择一项' }]}
            >
              <Checkbox.Group
                options={[
                  { label: '阅读', value: 'reading' },
                  { label: '运动', value: 'sports' },
                  { label: '音乐', value: 'music' },
                  { label: '旅行', value: 'travel' },
                  { label: '编程', value: 'coding' },
                ]}
              />
            </Form.Item>

            <Form.Item
              label="同意条款"
              name="agreed"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value ? Promise.resolve() : Promise.reject(new Error('请同意服务条款'))
                }
              ]}
            >
              <Checkbox>
                我已阅读并同意 <a href="#">服务条款</a> 和 <a href="#">隐私政策</a>
              </Checkbox>
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Form.Item>
          </Form>
        </div>

      </Space>
    </div>
  );
};

export default CheckboxExamples;
```

### Switch - 开关

用于表示开关状态的组件。

**示例：Switch 开关**

```tsx
import React, { useState } from 'react';
import { Switch, Space, Typography } from 'antd';

const { Text } = Typography;

const SwitchExample: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [disabled, setDisabled] = useState(false);

  const onChange = (checked: boolean) => {
    console.log(`switch to ${checked}`);
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large">

        {/* 基础开关 */}
        <div>
          <Switch defaultChecked onChange={onChange} />
        </div>

        {/* 带文字 */}
        <div>
          <Space>
            <Switch checkedChildren="开" unCheckedChildren="关" defaultChecked />
            <Switch checkedChildren="1" unCheckedChildren="0" />
            <Switch
              checkedChildren={<span>ON</span>}
              unCheckedChildren={<span>OFF</span>}
              defaultChecked
            />
          </Space>
        </div>

        {/* 加载中 */}
        <div>
          <Space>
            <Switch loading={loading} onChange={(checked) => {
              setLoading(checked);
              setTimeout(() => setLoading(false), 2000);
            }} />

            <Switch loading defaultChecked />
          </Space>
        </div>

        {/* 禁用 */}
        <div>
          <Space>
            <Switch disabled={disabled} />
            <Switch disabled defaultChecked />
          </Space>

          <div style={{ marginTop: 8 }}>
            <Switch checked={!disabled} onChange={setDisabled} />
            <Text type="secondary"> 禁用下面开关</Text>
          </div>
        </div>

      </Space>
    </div>
  );
};

export default SwitchExample;
```

### Slider - 滑动输入条

用于选择一个数值范围的组件。

**示例：Slider 滑动条**

```tsx
import React, { useState } from 'react';
import { Slider, Space, Typography } from 'antd';

const { Text } = Typography;

const SliderExample: React.FC = () => {
  const [value, setValue] = useState(30);
  const [rangeValue, setRangeValue] = useState<[number, number]>([20, 50]);

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 基础滑动条 */}
        <div style={{ width: 300 }}>
          <Slider
            min={0}
            max={100}
            value={value}
            onChange={setValue}
            marks={{
              0: '0%',
              50: '50%',
              100: '100%',
            }}
          />
          <Text>当前值: {value}</Text>
        </div>

        {/* 范围滑动条 */}
        <div style={{ width: 300 }}>
          <Slider
            range
            min={0}
            max={100}
            value={rangeValue}
            onChange={(newValue) => setRangeValue(newValue as [number, number])}
            marks={{
              0: '0°C',
              26: '26°C',
              37: '37°C',
              100: '100°C',
            }}
          />
          <Text>范围: {rangeValue[0]}°C - {rangeValue[1]}°C</Text>
        </div>

        {/* 禁用 */}
        <div style={{ width: 300 }}>
          <Slider disabled defaultValue={30} />
        </div>

      </Space>
    </div>
  );
};

export default SliderExample;
```

### Rate - 评分

用于评分的组件。

**示例：Rate 评分**

```tsx
import React from 'react';
import { Rate, Space } from 'antd';

const RateExample: React.FC = () => {
  const [value, setValue] = React.useState(3);

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large">

        {/* 基础评分 */}
        <Rate v-model:value={value} />

        {/* 只读 */}
        <Rate disabled defaultValue={2} />

        {/* 半星 */}
        <Rate allowHalf defaultValue={2.5} />

        {/* 自定义字符 */}
        <Rate character={<span>A</span>} defaultValue={4} />
        <Rate character={<span>好</span>} defaultValue={4} />

        {/* 不同数量 */}
        <Rate count={10} defaultValue={7} />

      </Space>
    </div>
  );
};

export default RateExample;
```

### Upload - 文件上传

用于文件上传的组件，支持点击、拖拽、图片裁剪等多种方式。

**示例 6：Upload 文件上传**

```tsx
import React, { useState } from 'react';
import { Upload, Button, message, Space, Image, Form, Tag } from 'antd';
import type { UploadProps, UploadFile } from 'antd';
import {
  UploadOutlined,
  InboxOutlined,
  PlusOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { RcFile, UploadChangeParam } from 'antd/es/upload';

const { Dragger } = Upload;
const { TextArea } = Input;

const UploadExamples: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string>();

  // 1. 基础上传
  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload', // 替换为实际的上传接口
    headers: {
      authorization: 'authorization-text',
    },
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 2. 拖拽上传
  const draggerProps: UploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/upload',
    onChange(info) {
      const status = info.file.status;
      if (status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (status === 'done') {
        message.success(`${info.file.name} 上传成功`);
      } else if (status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
    onDrop(e) {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  // 3. 图片上传（带预览）
  const beforeUpload = (file: RcFile) => {
    const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
    if (!isJpgOrPng) {
      message.error('只能上传 JPG/PNG 文件');
    }
    const isLt2M = file.size / 1024 / 1024 < 2;
    if (!isLt2M) {
      message.error('图片必须小于 2MB');
    }
    return isJpgOrPng && isLt2M;
  };

  const handleChange: UploadProps['onChange'] = (info: UploadChangeParam<UploadFile>) => {
    if (info.file.status === 'uploading') {
      setUploading(true);
      return;
    }
    if (info.file.status === 'done') {
      // 获取图片 URL
      setImageUrl(info.file.response?.url);
      setUploading(false);
    }
  };

  const uploadButton = (
    <button style={{ border: 0, background: 'none' }} type="button">
      {uploading ? <LoadingOutlined /> : <PlusOutlined />}
      <div style={{ marginTop: 8 }}>上传</div>
    </button>
  );

  // 4. 多文件上传
  const handleMultipleChange: UploadProps['onChange'] = ({ fileList: newFileList }) => {
    setFileList(newFileList);
  };

  const handleUpload = () => {
    const formData = new FormData();
    fileList.forEach((file) => {
      formData.append('files[]', file as RcFile);
    });
    setUploading(true);

    // 模拟上传
    setTimeout(() => {
      setUploading(false);
      message.success('上传成功');
      setFileList([]);
    }, 2000);
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>

        {/* 1. 基础上传 */}
        <div>
          <h4>基础上传</h4>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>点击上传</Button>
          </Upload>
        </div>

        {/* 2. 拖拽上传 */}
        <div>
          <h4>拖拽上传</h4>
          <Dragger {...draggerProps} style={{ width: 500 }}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单次或批量上传。严禁上传公司数据或其他带有版权的文件
            </p>
          </Dragger>
        </div>

        {/* 3. 图片上传（带预览） */}
        <div>
          <h4>图片上传</h4>
          <Upload
            name="avatar"
            listType="picture-card"
            className="avatar-uploader"
            showUploadList={false}
            action="/api/upload"
            beforeUpload={beforeUpload}
            onChange={handleChange}
          >
            {imageUrl ? (
              <Image src={imageUrl} alt="avatar" style={{ width: '100%' }} />
            ) : (
              uploadButton
            )}
          </Upload>
        </div>

        {/* 4. 多文件上传（带列表） */}
        <div>
          <h4>多文件上传</h4>
          <Upload
            fileList={fileList}
            onChange={handleMultipleChange}
            multiple
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          <Button
            type="primary"
            onClick={handleUpload}
            disabled={fileList.length === 0}
            loading={uploading}
            style={{ marginTop: 16 }}
          >
            {uploading ? '上传中' : '开始上传'}
          </Button>
        </div>

        {/* 5. 图片列表上传 */}
        <div>
          <h4>图片列表上传</h4>
          <Upload
            action="/api/upload"
            listType="picture-card"
            defaultFileList={[
              {
                uid: '-1',
                name: 'image.png',
                status: 'done',
                url: 'https://via.placeholder.com/150',
              },
            ]}
          >
            <PlusOutlined />
          </Upload>
        </div>

        {/* 6. 表单集成 */}
        <div>
          <h4>表单集成</h4>
          <Form layout="vertical" onFinish={(values) => console.log(values)}>
            <Form.Item
              label="上传头像"
              name="avatar"
              valuePropName="fileList"
              getValueFromEvent={(e) => {
                if (Array.isArray(e)) {
                  return e;
                }
                return e && e.fileList;
              }}
              rules={[{ required: true, message: '请上传头像' }]}
            >
              <Upload
                action="/api/upload"
                listType="picture-card"
                maxCount={1}
              >
                <PlusOutlined />
              </Upload>
            </Form.Item>

            <Form.Item
              label="上传附件（支持多文件）"
              name="attachments"
              valuePropName="fileList"
              getValueFromEvent={(e) => {
                if (Array.isArray(e)) {
                  return e;
                }
                return e && e.fileList;
              }}
            >
              <Upload.Dragger
                action="/api/upload"
                multiple
                maxCount={5}
              >
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              </Upload.Dragger>
            </Form.Item>
          </Form>
        </div>

        {/* 7. 文件大小和格式限制 */}
        <div>
          <h4>文件限制</h4>
          <Upload
            action="/api/upload"
            beforeUpload={(file) => {
              const isValidType = ['image/jpeg', 'image/png', 'application/pdf'].includes(file.type);
              if (!isValidType) {
                message.error('只能上传 JPG/PNG/PDF 文件');
              }
              const isValidSize = file.size / 1024 / 1024 < 5;
              if (!isValidSize) {
                message.error('文件大小不能超过 5MB');
              }
              return isValidType && isValidSize ? false : Upload.LIST_IGNORE; // 返回 false 手动上传
            }}
          >
            <Button icon={<UploadOutlined />}>
              上传文件（仅支持 JPG/PNG/PDF，最大 5MB）
            </Button>
          </Upload>
        </div>

      </Space>
    </div>
  );
};

export default UploadExamples;
```

---

## 完整表单示例

### 示例 7：用户信息完整表单

```tsx
import React, { useState } from 'react';
import {
  Form,
  Input,
  Select,
  DatePicker,
  Radio,
  Checkbox,
  Switch,
  Upload,
  Button,
  Space,
  message,
  Card,
  Row,
  Col,
} from 'antd';
import type { UploadFile, UploadProps } from 'antd';
import { UploadOutlined, UserOutlined, MailOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

interface UserFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  gender: 'male' | 'female' | 'other';
  birthday: Dayjs;
  department: string;
  position: string;
  skills: string[];
  experience: number;
  bio: string;
  avatar: UploadFile[];
  attachments: UploadFile[];
  agreed: boolean;
  notifications: boolean;
}

const CompleteFormExample: React.FC = () => {
  const [form] = Form.useForm<UserFormData>();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: UserFormData) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise((resolve) => setTimeout(resolve, 1500));
      console.log('Form values:', values);
      message.success('提交成功');
    } catch (error) {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  const normFile = (e: any) => {
    if (Array.isArray(e)) {
      return e;
    }
    return e?.fileList;
  };

  return (
    <div style={{ padding: 24, background: '#f0f2f5', minHeight: '100vh' }}>
      <Card title="用户信息登记表" style={{ maxWidth: 900, margin: '0 auto' }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            gender: 'male',
            notifications: true,
            experience: 3,
          }}
        >

          {/* 基本信息 */}
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="用户名"
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, max: 20, message: '用户名长度为 3-20 个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线' },
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="请输入用户名"
                  allowClear
                />
              </Form.Item>
            </Col>

            <Col span={12}>
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
                  placeholder="example@email.com"
                  allowClear
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="密码"
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 8, message: '密码至少 8 个字符' },
                  { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '必须包含大小写字母和数字' },
                ]}
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="确认密码"
                name="confirmPassword"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('两次密码不一致'));
                    },
                  }),
                ]}
              >
                <Input.Password placeholder="请再次输入密码" />
              </Form.Item>
            </Col>
          </Row>

          {/* 个人信息 */}
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="性别"
                name="gender"
                rules={[{ required: true, message: '请选择性别' }]}
              >
                <Radio.Group>
                  <Radio value="male">男</Radio>
                  <Radio value="female">女</Radio>
                  <Radio value="other">其他</Radio>
                </Radio.Group>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="出生日期"
                name="birthday"
                rules={[{ required: true, message: '请选择出生日期' }]}
              >
                <DatePicker
                  placeholder="选择出生日期"
                  style={{ width: '100%' }}
                  disabledDate={(current) => current && current > dayjs().endOf('day')}
                />
              </Form.Item>
            </Col>
          </Row>

          {/* 工作信息 */}
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="部门"
                name="department"
                rules={[{ required: true, message: '请选择部门' }]}
              >
                <Select placeholder="请选择部门" allowClear>
                  <Select.Option value="rd">研发部</Select.Option>
                  <Select.Option value="product">产品部</Select.Option>
                  <Select.Option value="design">设计部</Select.Option>
                  <Select.Option value="marketing">市场部</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="职位"
                name="position"
                rules={[{ required: true, message: '请选择职位' }]}
              >
                <Select placeholder="请选择职位" allowClear mode="tags" maxTagCount={2}>
                  <Select.Option value="frontend">前端工程师</Select.Option>
                  <Select.Option value="backend">后端工程师</Select.Option>
                  <Select.Option value="fullstack">全栈工程师</Select.Option>
                  <Select.Option value="manager">技术经理</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* 技能和经验 */}
          <Form.Item
            label="技术栈（多选）"
            name="skills"
            rules={[{ required: true, message: '请至少选择一项技能' }]}
          >
            <Checkbox.Group
              style={{ width: '100%' }}
              options={[
                { label: 'React', value: 'react' },
                { label: 'Vue', value: 'vue' },
                { label: 'Angular', value: 'angular' },
                { label: 'Node.js', value: 'nodejs' },
                { label: 'Python', value: 'python' },
                { label: 'Go', value: 'go' },
                { label: 'TypeScript', value: 'typescript' },
              ]}
            />
          </Form.Item>

          <Form.Item
            label="工作经验（年）"
            name="experience"
            rules={[{ required: true, message: '请输入工作经验' }]}
          >
            <Input.Number
              min={0}
              max={50}
              precision={0}
              style={{ width: '100%' }}
              addonAfter="年"
            />
          </Form.Item>

          <Form.Item
            label="个人简介"
            name="bio"
            rules={[{ max: 500, message: '最多 500 个字符' }]}
          >
            <Input.TextArea
              rows={4}
              showCount
              maxLength={500}
              placeholder="请输入个人简介"
            />
          </Form.Item>

          {/* 头像上传 */}
          <Form.Item
            label="上传头像"
            name="avatar"
            valuePropName="fileList"
            getValueFromEvent={normFile}
            rules={[{ required: true, message: '请上传头像' }]}
          >
            <Upload
              action="/api/upload"
              listType="picture-card"
              maxCount={1}
              beforeUpload={(file) => {
                const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
                if (!isJpgOrPng) {
                  message.error('只能上传 JPG/PNG 文件');
                }
                const isLt2M = file.size / 1024 / 1024 < 2;
                if (!isLt2M) {
                  message.error('图片必须小于 2MB');
                }
                return isJpgOrPng && isLt2M;
              }}
            >
              <Button icon={<UploadOutlined />}>上传头像</Button>
            </Upload>
          </Form.Item>

          {/* 附件上传 */}
          <Form.Item
            label="上传附件"
            name="attachments"
            valuePropName="fileList"
            getValueFromEvent={normFile}
          >
            <Upload.Dragger
              action="/api/upload"
              multiple
              maxCount={5}
              beforeUpload={(file) => {
                const isValidSize = file.size / 1024 / 1024 < 10;
                if (!isValidSize) {
                  message.error('文件大小不能超过 10MB');
                }
                return isValidSize;
              }}
            >
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持多文件上传，单个文件不超过 10MB</p>
            </Upload.Dragger>
          </Form.Item>

          {/* 其他选项 */}
          <Form.Item
            name="notifications"
            valuePropName="checked"
          >
            <Switch checkedChildren="开启通知" unCheckedChildren="关闭通知" />
          </Form.Item>

          <Form.Item
            name="agreed"
            valuePropName="checked"
            rules={[
              {
                validator: (_, value) =>
                  value ? Promise.resolve() : Promise.reject(new Error('请同意服务条款')),
              },
            ]}
          >
            <Checkbox>
              我已阅读并同意 <a href="#">服务条款</a> 和 <a href="#">隐私政策</a>
            </Checkbox>
          </Form.Item>

          {/* 提交按钮 */}
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交
              </Button>
              <Button htmlType="reset" onClick={() => form.resetFields()}>
                重置
              </Button>
            </Space>
          </Form.Item>

        </Form>
      </Card>
    </div>
  );
};

export default CompleteFormExample;
```

---

## 最佳实践

### 1. 性能优化

#### Select 虚拟滚动

对于大数据量的 Select，启用虚拟滚动：

```tsx
<Select
  virtual={true}
  listHeight={200}
  options={largeDataArray} // 10000+ 条数据
/>
```

#### 防抖搜索

为异步搜索添加防抖：

```tsx
import debounce from 'lodash/debounce';

const debouncedSearch = debounce((value) => {
  // 执行搜索
}, 300);

<Select onSearch={debouncedSearch} />
```

#### DatePicker 禁用日期优化

避免在 `disabledDate` 中执行复杂计算：

```tsx
// ❌ 不推荐
const disabledDate = (date) => {
  // 复杂的 API 调用
  return checkAvailability(date);
};

// ✅ 推荐
const disabledDates = new Set(['2024-01-01', '2024-01-02']);
const disabledDate = (date) => {
  return disabledDates.has(date.format('YYYY-MM-DD'));
};
```

### 2. 无障碍访问

#### 添加 aria-label

```tsx
<Input aria-label="用户名输入框" placeholder="请输入用户名" />

<DatePicker aria-label="选择日期" />
```

#### 键盘导航

所有输入组件都支持键盘操作：
- `Tab` - 切换焦点
- `Enter` - 确认选择
- `Esc` - 关闭下拉

### 3. 表单验证

#### 自定义验证

```tsx
<Form.Item
  name="password"
  rules={[
    { required: true },
    {
      validator: async (_, value) => {
        if (value && value.length < 8) {
          throw new Error('密码至少 8 个字符');
        }
        // 异步验证
        const exists = await checkPasswordExists(value);
        if (exists) {
          throw new Error('密码已被使用');
        }
      },
    },
  ]}
>
  <Input.Password />
</Form.Item>
```

#### 跨字段验证

```tsx
<Form.Item
  name="confirmPassword"
  dependencies={['password']}
  rules={[
    { required: true },
    ({ getFieldValue }) => ({
      validator(_, value) {
        if (!value || getFieldValue('password') === value) {
          return Promise.resolve();
        }
        return Promise.reject(new Error('两次密码不一致'));
      },
    }),
  ]}
>
  <Input.Password />
</Form.Item>
```

### 4. 文件上传最佳实践

#### 客户端预验证

```tsx
const beforeUpload = (file: RcFile) => {
  // 文件类型验证
  const isValidType = ['image/jpeg', 'image/png'].includes(file.type);
  if (!isValidType) {
    message.error('只能上传 JPG/PNG 文件');
    return Upload.LIST_IGNORE;
  }

  // 文件大小验证
  const isValidSize = file.size / 1024 / 1024 < 2;
  if (!isValidSize) {
    message.error('文件必须小于 2MB');
    return Upload.LIST_IGNORE;
  }

  // 图片尺寸验证
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const img = document.createElement('img');
      img.src = reader.result as string;
      img.onload = () => {
        if (img.width < 300 || img.height < 300) {
          message.error('图片尺寸至少 300x300');
          resolve(Upload.LIST_IGNORE);
        } else {
          resolve(true);
        }
      };
    };
  });
};
```

#### 分片上传大文件

```tsx
const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB

const uploadInChunks = async (file: File) => {
  const chunks = Math.ceil(file.size / CHUNK_SIZE);
  const fileId = `${file.name}-${Date.now()}`;

  for (let i = 0; i < chunks; i++) {
    const start = i * CHUNK_SIZE;
    const end = Math.min(file.size, start + CHUNK_SIZE);
    const chunk = file.slice(start, end);

    const formData = new FormData();
    formData.append('fileId', fileId);
    formData.append('chunk', String(i));
    formData.append('totalChunks', String(chunks));
    formData.append('file', chunk);

    await fetch('/api/upload-chunk', {
      method: 'POST',
      body: formData,
    });
  }

  // 通知服务器合并分片
  await fetch('/api/merge-chunks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fileId, fileName: file.name }),
  });
};
```

### 5. 国际化

使用 `ConfigProvider` 配置国际化：

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

const App = () => (
  <ConfigProvider locale={zhCN}>
    <YourApp />
  </ConfigProvider>
);
```

### 6. 主题定制

使用 ConfigProvider 自定义输入组件样式：

```tsx
<ConfigProvider
  theme={{
    components: {
      Input: {
        colorBgContainer: '#f0f0f0',
        borderRadius: 8,
      },
      Select: {
        colorBgContainer: '#f0f0f0',
        borderRadius: 8,
      },
      DatePicker: {
        colorBgContainer: '#f0f0f0',
        borderRadius: 8,
      },
    },
  }}
>
  <YourApp />
</ConfigProvider>
```

### 7. 移动端优化

为移动端优化输入体验：

```tsx
// 数字键盘
<Input type="tel" /> // 电话键盘
<Input type="number" /> // 数字键盘
<Input inputMode="numeric" /> // 数字输入模式

// 禁用缩放
<Input
  style={{ fontSize: 16 }} // iOS 防止缩放
/>

// 自动聚焦
<Input autoFocus />

// 只读（移动端不弹出键盘）
<Input readOnly />
```

---

## 常见问题

### 1. Select 搜索不生效

确保设置 `showSearch` 和 `filterOption`：

```tsx
<Select
  showSearch
  filterOption={(input, option) =>
    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
  }
  options={options}
/>
```

### 2. DatePicker 时区问题

使用 dayjs 的 `utc` 插件：

```tsx
import utc from 'dayjs/plugin/utc';
dayjs.extend(utc);

<DatePicker
  onChange={(date) => {
    console.log(date?.utc().format()); // UTC 时间
  }}
/>
```

### 3. Upload 上传无 token

通过 headers 添加认证：

```tsx
<Upload
  headers={{
    Authorization: `Bearer ${token}`,
  }}
  action="/api/upload"
/>
```

### 4. Form.Item 初始值不显示

确保 Form 使用 `initialValues`：

```tsx
<Form
  initialValues={{
    username: 'default',
  }}
>
  <Form.Item name="username">
    <Input />
  </Form.Item>
</Form>
```

---

## 参考资源

- [Ant Design 官方文档](https://ant.design/components/input-cn/)
- [Input 组件 API](https://ant.design/components/input-cn/#API)
- [Select 组件 API](https://ant.design/components/select-cn/#API)
- [DatePicker 组件 API](https://ant.design/components/date-picker-cn/#API)
- [Upload 组件 API](https://ant.design/components/upload-cn/#API)
- [Form 组件 API](https://ant.design/components/form-cn/#API)
- [Ant Design 设计规范](https://ant.design/docs/spec/introduce-cn)
