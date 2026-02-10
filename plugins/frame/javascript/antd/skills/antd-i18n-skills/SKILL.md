---
name: antd-i18n-skills
description: Ant Design 国际化完整指南 - 多语言支持、语言切换、日期格式化、数字格式化、RTL支持
---

# Ant Design 国际化完整指南

## 概述

Ant Design 提供了完整的国际化（i18n）支持,通过 `ConfigProvider` 组件的 `locale` 属性,可以为所有内置组件提供多语言支持。同时结合 dayjs、React Intl、i18next 等第三方库,可以实现应用级别的完整国际化方案。

### 核心特性

- **内置语言包** - 提供 40+ 种语言的官方语言包
- **组件级国际化** - DatePicker、Table、Pagination 等组件的自动本地化
- **日期时间国际化** - 结合 dayjs 实现日期格式、星期、月份的本地化
- **数字货币格式化** - 支持不同地区的数字和货币格式
- **RTL 支持** - 完整的从右到左（RTL）布局支持
- **自定义语言包** - 支持扩展和自定义语言包
- **动态语言切换** - 运行时无缝切换语言
- **第三方集成** - 与 React Intl、i18next 无缝集成

### 架构设计

```
antd-i18n/
├── ConfigProvider locale       # Ant Design 组件国际化
├── dayjs/locale               # 日期时间国际化
├── React Intl                 # UI 文本国际化
├── i18next                    # 企业级 i18n 方案
├── RTL Support                # RTL 布局支持
└── Custom Locale              # 自定义语言包
```

---

## 核心概念

### 1. ConfigProvider locale

`ConfigProvider` 组件的 `locale` 属性是 Ant Design 国际化的核心,用于配置所有内置组件的语言环境:

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <YourApplication />
    </ConfigProvider>
  );
}
```

### 2. 内置语言包

Ant Design 内置了 40+ 种语言包,位于 `antd/locale/` 目录:

```typescript
// 常用语言包
import zhCN from 'antd/locale/zh_CN';      // 简体中文
import enUS from 'antd/locale/en_US';      // 英语
import jaJP from 'antd/locale/ja_JP';      // 日语
import koKR from 'antd/locale/ko_KR';      // 韩语
import frFR from 'antd/locale/fr_FR';      // 法语
import deDE from 'antd/locale/de_DE';      // 德语
import esES from 'antd/locale/es_ES';      // 西班牙语
import arEG from 'antd/locale/ar_EG';      // 阿拉伯语（RTL）
import ruRU from 'antd/locale/ru_RU';      // 俄语
import itIT from 'antd/locale/it_IT';      // 意大利语
import ptBR from 'antd/locale/pt_BR';      // 葡萄牙语（巴西）
import thTH from 'antd/locale/th_TH';      // 泰语
import viVN from 'antd/locale/vi_VN';      // 越南语
import idID from 'antd/locale/id_ID';      // 印尼语
```

### 3. 语言包结构

每个语言包包含以下组件的翻译:

```typescript
interface Locale {
  locale: string;                    // 语言代码
  Pagination?: PaginationLocale;     // 分页组件
  DatePicker?: DatePickerLocale;     // 日期选择器
  TimePicker?: TimePickerLocale;     // 时间选择器
  Calendar?: CalendarLocale;         // 日历
  Table?: TableLocale;               // 表格
  Modal?: ModalLocale;               // 模态框
  Popconfirm?: PopconfirmLocale;     // 气泡确认框
  Transfer?: TransferLocale;         // 穿梭框
  Select?: SelectLocale;             // 选择器
  Upload?: UploadLocale;             // 上传
  Form?: FormLocale;                 // 表单
  Icon?: IconLocale;                 // 图标
  Empty?: EmptyLocale;               // 空状态
  Global?: GlobalLocale;             // 全局配置
  Text?: TextLocale;                 // 文本
}
```

---

## 基础配置

### 1. 引入语言包

```typescript
// 方式 1: 直接引入
import zhCN from 'antd/locale/zh_CN';

// 方式 2: 动态导入（推荐用于大型应用）
const loadLocale = async (lang: string) => {
  switch (lang) {
    case 'zh-CN':
      return (await import('antd/locale/zh_CN')).default;
    case 'en-US':
      return (await import('antd/locale/en_US')).default;
    case 'ja-JP':
      return (await import('antd/locale/ja_JP')).default;
    default:
      return (await import('antd/locale/en_US')).default;
  }
};
```

### 2. 配置 locale

```tsx
import { ConfigProvider, DatePicker, Button } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

// 配置 dayjs 语言
dayjs.locale('zh-cn');

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        <DatePicker />
        <Button>按钮</Button>
      </div>
    </ConfigProvider>
  );
}
```

### 3. 语言切换

**完整的语言切换系统**:

```tsx
import React, { useState, useEffect } from 'react';
import { ConfigProvider, DatePicker, Select, Button, Typography } from 'antd';
import type { Locale } from 'antd/es/locale';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import 'dayjs/locale/ja';

const { Title, Text } = Typography;

// 支持的语言列表
const SUPPORTED_LOCALES = [
  { value: 'zh-CN', label: '简体中文', antdLocale: 'zh_CN', dayjsLocale: 'zh-cn' },
  { value: 'en-US', label: 'English', antdLocale: 'en_US', dayjsLocale: 'en' },
  { value: 'ja-JP', label: '日本語', antdLocale: 'ja_JP', dayjsLocale: 'ja' },
  { value: 'ko-KR', label: '한국어', antdLocale: 'ko_KR', dayjsLocale: 'ko' },
  { value: 'fr-FR', label: 'Français', antdLocale: 'fr_FR', dayjsLocale: 'fr' },
  { value: 'de-DE', label: 'Deutsch', antdLocale: 'de_DE', dayjsLocale: 'de' },
];

function I18nApp() {
  const [currentLocale, setCurrentLocale] = useState<string>('zh-CN');
  const [antdLocale, setAntdLocale] = useState<Locale | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载语言包
  const loadLocale = async (locale: string) => {
    setLoading(true);
    try {
      const localeConfig = SUPPORTED_LOCALES.find(l => l.value === locale);
      if (!localeConfig) return;

      // 动态导入 Ant Design 语言包
      const antdLoc = await import(`antd/locale/${localeConfig.antdLocale}`);
      setAntdLocale(antdLoc.default);

      // 配置 dayjs 语言
      await import(`dayjs/locale/${localeConfig.dayjsLocale}.js`);
      dayjs.locale(localeConfig.dayjsLocale);

      // 保存到 localStorage
      localStorage.setItem('locale', locale);
    } catch (error) {
      console.error('Failed to load locale:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始化时加载语言
  useEffect(() => {
    const savedLocale = localStorage.getItem('locale') || 'zh-CN';
    loadLocale(savedLocale);
  }, []);

  // 切换语言
  const handleLocaleChange = (locale: string) => {
    setCurrentLocale(locale);
    loadLocale(locale);
  };

  if (!antdLocale) {
    return <div>Loading...</div>;
  }

  return (
    <ConfigProvider locale={antdLocale}>
      <div style={{ padding: 24, maxWidth: 800 }}>
        <Title level={2}>Ant Design 国际化示例</Title>

        {/* 语言选择器 */}
        <div style={{ marginBottom: 24 }}>
          <Text strong>选择语言 / Select Language:</Text>
          <Select
            value={currentLocale}
            onChange={handleLocaleChange}
            loading={loading}
            style={{ width: 200, marginLeft: 12 }}
            options={SUPPORTED_LOCALES.map(loc => ({
              value: loc.value,
              label: loc.label,
            }))}
          />
        </div>

        {/* 组件示例 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* 日期选择器 */}
          <div>
            <Text strong>日期选择器 / Date Picker:</Text>
            <DatePicker style={{ marginTop: 8 }} />
            <DatePicker.RangePicker style={{ marginTop: 8, marginLeft: 8 }} />
          </div>

          {/* 分页器 */}
          <div>
            <Text strong>分页器 / Pagination:</Text>
            <div style={{ marginTop: 8 }}>
              <Pagination
                total={100}
                showSizeChanger
                showQuickJumper
                showTotal={(total) => `Total ${total} items`}
              />
            </div>
          </div>

          {/* 表格 */}
          <div>
            <Text strong>表格 / Table:</Text>
            <Table
              style={{ marginTop: 8 }}
              dataSource={[
                { key: '1', name: 'John Brown', age: 32 },
                { key: '2', name: 'Jim Green', age: 42 },
              ]}
              columns={[
                { title: 'Name', dataIndex: 'name', key: 'name' },
                { title: 'Age', dataIndex: 'age', key: 'age' },
              ]}
            />
          </div>
        </div>
      </div>
    </ConfigProvider>
  );
}

export default I18nApp;
```

---

## 组件国际化

### 1. DatePicker 日期格式

```tsx
import { ConfigProvider, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';

function DatePickerExample() {
  const [locale, setLocale] = useState(zhCN);

  return (
    <ConfigProvider locale={locale}>
      <div>
        <DatePicker format="YYYY-MM-DD" />
        <DatePicker.WeekPicker format="YYYY-wo" />
        <DatePicker.MonthPicker format="YYYY-MM" />
        <DatePicker.YearPicker format="YYYY" />
        <DatePicker.RangePicker format="YYYY-MM-DD" />

        {/* 自定义日期格式 */}
        <DatePicker
          format="YYYY年MM月DD日"
          placeholder="选择日期"
        />
      </div>
    </ConfigProvider>
  );
}
```

### 2. TimePicker 时间格式

```tsx
import { ConfigProvider, TimePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function TimePickerExample() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        <TimePicker format="HH:mm:ss" />
        <TimePicker.RangePicker format="HH:mm" />

        {/* 12小时制 */}
        <TimePicker use12Hours format="h:mm:ss A" />
      </div>
    </ConfigProvider>
  );
}
```

### 3. Calendar 日历

```tsx
import { ConfigProvider, Calendar } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs, { Dayjs } from 'dayjs';

function CalendarExample() {
  const onSelect = (date: Dayjs) => {
    console.log(date.format('YYYY-MM-DD'));
  };

  return (
    <ConfigProvider locale={zhCN}>
      <Calendar
        fullscreen={false}
        onSelect={onSelect}
        validRange={[dayjs().subtract(1, 'month'), dayjs().add(1, 'month')]}
      />
    </ConfigProvider>
  );
}
```

### 4. Pagination 分页

```tsx
import { ConfigProvider, Pagination } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function PaginationExample() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        {/* 基础分页 */}
        <Pagination
          total={100}
          current={1}
          pageSize={10}
        />

        {/* 完整功能分页 */}
        <Pagination
          total={500}
          showSizeChanger
          showQuickJumper
          showTotal={(total) => `共 ${total} 条`}
          pageSizeOptions={['10', '20', '50', '100']}
        />

        {/* 简洁分页 */}
        <Pagination
          total={100}
          simple
        />
      </div>
    </ConfigProvider>
  );
}
```

### 5. Table 表格

```tsx
import { ConfigProvider, Table } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function TableExample() {
  const dataSource = [
    { key: '1', name: 'John Brown', age: 32, address: 'New York No. 1 Lake Park' },
    { key: '2', name: 'Jim Green', age: 42, address: 'London No. 1 Lake Park' },
  ];

  const columns = [
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '年龄', dataIndex: 'age', key: 'age' },
    { title: '地址', dataIndex: 'address', key: 'address' },
  ];

  return (
    <ConfigProvider locale={zhCN}>
      <Table
        dataSource={dataSource}
        columns={columns}
        // 表格国际化配置
        pagination={{
          total: 100,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </ConfigProvider>
  );
}
```

### 6. Form 表单

```tsx
import { ConfigProvider, Form, Input, Button } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function FormExample() {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Received values:', values);
  };

  return (
    <ConfigProvider
      locale={zhCN}
      form={{
        requiredMark: 'optional',
        validateMessages: {
          required: '${label}是必填项',
          types: {
            email: '${label}格式不正确',
          },
        },
      }}
    >
      <Form
        form={form}
        onFinish={onFinish}
        layout="vertical"
      >
        <Form.Item
          label="邮箱"
          name="email"
          rules={[{ required: true, type: 'email' }]}
        >
          <Input placeholder="请输入邮箱" />
        </Form.Item>

        <Form.Item
          label="密码"
          name="password"
          rules={[{ required: true, min: 8 }]}
        >
          <Input.Password placeholder="请输入密码" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            提交
          </Button>
        </Form.Item>
      </Form>
    </ConfigProvider>
  );
}
```

---

## 自定义语言包

### 1. 扩展内置语言

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import type { Locale } from 'antd/es/locale';

// 扩展中文语言包
const customZhCN: Locale = {
  ...zhCN,
  Locale: {
    ...zhCN.Locale,
    lang: 'zh-CN',
  },
  // 自定义 DatePicker 翻译
  DatePicker: {
    ...zhCN.DatePicker,
    lang: {
      ...zhCN.DatePicker.lang,
      placeholder: '请选择日期',
      rangePlaceholder: ['开始日期', '结束日期'],
      locale: 'zh_CN',
      today: '今天',
      now: '此刻',
      backToToday: '返回今天',
      ok: '确定',
      clear: '清除',
      month: '月',
      year: '年',
      timeSelect: '选择时间',
      dateSelect: '选择日期',
      weekSelect: '选择周',
      monthSelect: '选择月份',
      yearSelect: '选择年份',
      decadeSelect: '选择年代',
      yearFormat: 'YYYY年',
      dateFormat: 'YYYY-MM-DD',
      dayFormat: 'D日',
      dateTimeFormat: 'YYYY-MM-DD HH:mm:ss',
      monthBeforeYear: true,
      previousMonth: '上个月',
      nextMonth: '下个月',
      previousYear: '上一年',
      nextYear: '下一年',
      previousDecade: '上一年代',
      nextDecade: '下一年代',
      previousCentury: '上一世纪',
      nextCentury: '下一世纪',
    },
    timePickerLocale: {
      ...zhCN.DatePicker.timePickerLocale,
      placeholder: '请选择时间',
    },
  },
  // 自定义 Table 翻译
  Table: {
    ...zhCN.Table,
    filterTitle: '筛选',
    filterConfirm: '确定',
    filterReset: '重置',
    filterEmptyText: '暂无筛选结果',
    selectAll: '全部选择',
    selectInvert: '反向选择',
    selectionAll: '全选所有',
    selectionInvert: '反选所有',
    sortTitle: '排序',
    expand: '展开行',
    collapse: '关闭行',
    triggerDesc: '点击降序',
    triggerAsc: '点击升序',
    cancelSort: '取消排序',
  },
  // 自定义 Pagination 翻译
  Pagination: {
    ...zhCN.Pagination,
    items_per_page: '条/页',
    jump_to: '跳至',
    page: '页',
    prev_page: '上一页',
    next_page: '下一页',
    prev_5: '向前 5 页',
    next_5: '向后 5 页',
    prev_3: '向前 3 页',
    next_3: '向后 3 页',
  },
  // 自定义 Modal 翻译
  Modal: {
    ...zhCN.Modal,
    okText: '确定',
    cancelText: '取消',
    justOkText: '知道了',
  },
  // 自定义 Popconfirm 翻译
  Popconfirm: {
    ...zhCN.Popconfirm,
    cancelText: '取消',
    okText: '确定',
  },
  // 自定义 Transfer 翻译
  Transfer: {
    ...zhCN.Transfer,
    titles: ['', ''],
    searchPlaceholder: '请输入搜索内容',
    itemUnit: '项',
    itemsUnit: '项',
    remove: '删除',
    selectCurrent: '全选当前页',
    removeCurrent: '删除当前页',
    selectAll: '全选所有',
    removeAll: '删除所有',
    selectInvert: '反选所有',
  },
};

function CustomLocaleApp() {
  return (
    <ConfigProvider locale={customZhCN}>
      <YourApp />
    </ConfigProvider>
  );
}
```

### 2. 创建新语言

```tsx
import { ConfigProvider } from 'antd';
import type { Locale } from 'antd/es/locale';

// 创建粤语（繁体中文）语言包
const zhTWLocale: Locale = {
  locale: 'zh-TW',
  Pagination: {
    items_per_page: '條/頁',
    jump_to: '跳至',
    jump_to_confirm: '確定',
    page: '頁',
    prev_page: '上一頁',
    next_page: '下一頁',
    prev_5: '向前 5 頁',
    next_5: '向後 5 頁',
    prev_3: '向前 3 頁',
    next_3: '向後 3 頁',
  },
  DatePicker: {
    lang: {
      placeholder: '請選擇日期',
      rangePlaceholder: ['開始日期', '結束日期'],
      locale: 'zh_TW',
      today: '今天',
      now: '此刻',
      backToToday: '返回今天',
      ok: '確定',
      clear: '清除',
      month: '月',
      year: '年',
      timeSelect: '選擇時間',
      dateSelect: '選擇日期',
      weekSelect: '選擇週',
      monthSelect: '選擇月份',
      yearSelect: '選擇年份',
      decadeSelect: '選擇年代',
      yearFormat: 'YYYY年',
      dateFormat: 'YYYY-MM-DD',
      dayFormat: 'D日',
      dateTimeFormat: 'YYYY-MM-DD HH:mm:ss',
      monthBeforeYear: true,
      previousMonth: '上個月',
      nextMonth: '下個月',
      previousYear: '上一年',
      nextYear: '下一年',
      previousDecade: '上一年代',
      nextDecade: '下一年代',
      previousCentury: '上一世紀',
      nextCentury: '下一世紀',
    },
    timePickerLocale: {
      placeholder: '請選擇時間',
    },
  },
  TimePicker: {
    placeholder: '請選擇時間',
  },
  Calendar: {
    lang: {
      locale: 'zh_TW',
      today: '今天',
      now: '此刻',
      backToToday: '返回今天',
      ok: '確定',
      clear: '清除',
      month: '月',
      year: '年',
      timeSelect: '選擇時間',
      dateSelect: '選擇日期',
      weekSelect: '選擇週',
      monthSelect: '選擇月份',
      yearSelect: '選擇年份',
      decadeSelect: '選擇年代',
      yearFormat: 'YYYY年',
      dateFormat: 'YYYY-MM-DD',
      dayFormat: 'D日',
      dateTimeFormat: 'YYYY-MM-DD HH:mm:ss',
      monthBeforeYear: true,
      previousMonth: '上個月',
      nextMonth: '下個月',
      previousYear: '上一年',
      nextYear: '下一年',
      previousDecade: '上一年代',
      nextDecade: '下一年代',
      previousCentury: '上一世紀',
      nextCentury: '下一世紀',
    },
    timePickerLocale: {
      placeholder: '請選擇時間',
    },
  },
  Table: {
    filterTitle: '篩選',
    filterConfirm: '確定',
    filterReset: '重置',
    filterEmptyText: '暫無篩選結果',
    selectAll: '全部選擇',
    selectInvert: '反向選擇',
  },
  Modal: {
    okText: '確定',
    cancelText: '取消',
    justOkText: '知道了',
  },
  Popconfirm: {
    cancelText: '取消',
    okText: '確定',
  },
  Transfer: {
    titles: ['', ''],
    searchPlaceholder: '請輸入搜索內容',
    itemUnit: '項',
    itemsUnit: '項',
  },
  Upload: {
    uploading: '上傳中...',
    removeFile: '刪除文件',
    uploadError: '上傳錯誤',
    previewFile: '預覽文件',
    downloadFile: '下載文件',
  },
  Empty: {
    description: '暫無數據',
  },
  Form: {
    defaultValidateMessages: {
      default: '字段驗證錯誤',
      required: '${label}是必填項',
      enum: '${label}必須是[${enum}]其中之一',
      whitespace: '${label}不能為空字符',
      date: {
        format: '${label}日期格式無效',
        parse: '${label}不能轉換為日期',
        invalid: '${label}是無效日期',
      },
    },
  },
};

function ZhTWApp() {
  return (
    <ConfigProvider locale={zhTWLocale}>
      <YourApp />
    </ConfigProvider>
  );
}
```

### 3. 语言包结构

完整的语言包结构参考:

```typescript
interface Locale {
  locale: string;
  Pagination?: {
    items_per_page?: string;
    jump_to?: string;
    jump_to_confirm?: string;
    page?: string;
    prev_page?: string;
    next_page?: string;
    prev_5?: string;
    next_5?: string;
    prev_3?: string;
    next_3?: string;
  };
  DatePicker?: {
    lang?: {
      placeholder?: string;
      rangePlaceholder?: [string, string];
      locale?: string;
      today?: string;
      now?: string;
      backToToday?: string;
      ok?: string;
      clear?: string;
      month?: string;
      year?: string;
      timeSelect?: string;
      dateSelect?: string;
      weekSelect?: string;
      monthSelect?: string;
      yearSelect?: string;
      decadeSelect?: string;
      yearFormat?: string;
      dateFormat?: string;
      dayFormat?: string;
      dateTimeFormat?: string;
      monthBeforeYear?: boolean;
      previousMonth?: string;
      nextMonth?: string;
      previousYear?: string;
      nextYear?: string;
      previousDecade?: string;
      nextDecade?: string;
      previousCentury?: string;
      nextCentury?: string;
    };
    timePickerLocale?: {
      placeholder?: string;
    };
  };
  TimePicker?: {
    placeholder?: string;
  };
  Calendar?: {
    lang?: any;
    timePickerLocale?: {
      placeholder?: string;
    };
  };
  Table?: {
    filterTitle?: string;
    filterConfirm?: string;
    filterReset?: string;
    filterEmptyText?: string;
    selectAll?: string;
    selectInvert?: string;
  };
  Modal?: {
    okText?: string;
    cancelText?: string;
    justOkText?: string;
  };
  Popconfirm?: {
    cancelText?: string;
    okText?: string;
  };
  Transfer?: {
    titles?: [string, string];
    searchPlaceholder?: string;
    itemUnit?: string;
    itemsUnit?: string;
  };
  Upload?: {
    uploading?: string;
    removeFile?: string;
    uploadError?: string;
    previewFile?: string;
    downloadFile?: string;
  };
  Empty?: {
    description?: string;
  };
  Form?: {
    defaultValidateMessages?: any;
  };
  Select?: {
    notFoundContent?: string;
  };
}
```

---

## 日期时间国际化

### 1. dayjs 国际化

```tsx
import { ConfigProvider, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import 'dayjs/locale/ja';
import 'dayjs/locale/fr';

function DayjsI18nExample() {
  const [locale, setLocale] = useState('zh-cn');

  const changeLocale = (newLocale: string) => {
    setLocale(newLocale);
    dayjs.locale(newLocale);
  };

  return (
    <ConfigProvider locale={zhCN}>
      <div>
        <DatePicker />
        <p>当前日期: {dayjs().format('LL')}</p>
        <p>当前时间: {dayjs().format('LTS')}</p>

        {/* 切换语言 */}
        <button onClick={() => changeLocale('zh-cn')}>中文</button>
        <button onClick={() => changeLocale('en')}>English</button>
        <button onClick={() => changeLocale('ja')}>日本語</button>
        <button onClick={() => changeLocale('fr')}>Français</button>
      </div>
    </ConfigProvider>
  );
}
```

### 2. 自定义日期格式

```tsx
import { ConfigProvider, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';

function CustomDateFormat() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        {/* 年月日格式 */}
        <DatePicker
          format="YYYY年MM月DD日"
          placeholder="请选择日期"
        />

        {/* 完整日期时间 */}
        <DatePicker
          showTime
          format="YYYY年MM月DD日 HH:mm:ss"
          placeholder="请选择日期时间"
        />

        {/* 星期格式 */}
        <DatePicker
          format="YYYY-MM-DD (dddd)"
          placeholder="请选择日期"
        />

        {/* 自定义格式化函数 */}
        <DatePicker
          format={(value) => {
            return value.format('YYYY/MM/DD');
          }}
          placeholder="请选择日期"
        />
      </div>
    </ConfigProvider>
  );
}
```

### 3. 时区处理

```tsx
import { ConfigProvider, DatePicker } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

function TimezoneExample() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        {/* UTC 时间 */}
        <DatePicker
          showTime
          format="YYYY-MM-DD HH:mm:ss [UTC]"
          placeholder="选择 UTC 时间"
        />

        {/* 特定时区时间 */}
        <DatePicker
          showTime
          format="YYYY-MM-DD HH:mm:ss [Asia/Shanghai]"
          placeholder="选择北京时间"
        />

        {/* 显示多个时区 */}
        <div>
          <p>UTC: {dayjs().utc().format('YYYY-MM-DD HH:mm:ss')}</p>
          <p>北京: {dayjs().tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')}</p>
          <p>纽约: {dayjs().tz('America/New_York').format('YYYY-MM-DD HH:mm:ss')}</p>
          <p>伦敦: {dayjs().tz('Europe/London').format('YYYY-MM-DD HH:mm:ss')}</p>
        </div>
      </div>
    </ConfigProvider>
  );
}
```

---

## 数字货币国际化

### 1. 数字格式化

```tsx
import { ConfigProvider, Statistic } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function NumberFormatExample() {
  return (
    <ConfigProvider locale={zhCN}>
      <div>
        {/* 基础数字格式化 */}
        <Statistic
          title="用户数"
          value={1289000}
          formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
        />

        {/* 精度控制 */}
        <Statistic
          title="百分比"
          value={92.8}
          precision={2}
          suffix="%"
        />

        {/* 自定义格式化 */}
        <Statistic
          title="金额"
          value={1234567.89}
          precision={2}
          formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
        />
      </div>
    </ConfigProvider>
  );
}
```

### 2. 货币格式化

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function CurrencyFormatExample() {
  // 货币格式化函数
  const formatCurrency = (amount: number, currency: string, locale: string) => {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  return (
    <ConfigProvider locale={zhCN}>
      <div>
        {/* 人民币 */}
        <p>人民币: {formatCurrency(1234567.89, 'CNY', 'zh-CN')}</p>

        {/* 美元 */}
        <p>美元: {formatCurrency(1234567.89, 'USD', 'en-US')}</p>

        {/* 欧元 */}
        <p>欧元: {formatCurrency(1234567.89, 'EUR', 'de-DE')}</p>

        {/* 日元 */}
        <p>日元: {formatCurrency(1234567.89, 'JPY', 'ja-JP')}</p>

        {/* 英镑 */}
        <p>英镑: {formatCurrency(1234567.89, 'GBP', 'en-GB')}</p>
      </div>
    </ConfigProvider>
  );
}
```

---

## React Intl 集成

### 1. 基础集成

**React Intl + Ant Design 完整集成示例**:

```tsx
import React, { useState, useEffect } from 'react';
import { ConfigProvider, Button, DatePicker, Card, Space } from 'antd';
import type { Locale } from 'antd/es/locale';
import { IntlProvider, FormattedMessage, FormattedDate } from 'react-intl';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';

// 定义翻译消息
const messages = {
  'zh-CN': {
    title: 'React Intl 集成示例',
    description: '这是一个 React Intl 与 Ant Design 集成的示例',
    welcome: '欢迎',
    currentDate: '当前日期',
    selectDate: '选择日期',
    switchLanguage: '切换语言',
  },
  'en-US': {
    title: 'React Intl Integration Example',
    description: 'This is an example of React Intl with Ant Design',
    welcome: 'Welcome',
    currentDate: 'Current Date',
    selectDate: 'Select Date',
    switchLanguage: 'Switch Language',
  },
};

// React Intl + Ant Design 集成
function ReactIntlApp() {
  const [locale, setLocale] = useState<string>('zh-CN');
  const [antdLocale, setAntdLocale] = useState<Locale>(zhCN);

  const changeLanguage = (lang: string) => {
    setLocale(lang);
    if (lang === 'zh-CN') {
      setAntdLocale(zhCN);
      dayjs.locale('zh-cn');
    } else {
      setAntdLocale(enUS);
      dayjs.locale('en');
    }
  };

  return (
    <IntlProvider locale={locale} messages={messages[locale]}>
      <ConfigProvider locale={antdLocale}>
        <Card style={{ maxWidth: 600, margin: '0 auto', marginTop: 50 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 标题 */}
            <h2>
              <FormattedMessage id="title" />
            </h2>

            {/* 描述 */}
            <p>
              <FormattedMessage id="description" />
            </p>

            {/* 语言切换按钮 */}
            <Button
              type="primary"
              onClick={() => changeLanguage(locale === 'zh-CN' ? 'en-US' : 'zh-CN')}
            >
              <FormattedMessage id="switchLanguage" />
            </Button>

            {/* 日期选择器 */}
            <div>
              <FormattedMessage id="selectDate" />:
              <DatePicker style={{ marginLeft: 8 }} />
            </div>

            {/* 格式化日期 */}
            <div>
              <FormattedMessage id="currentDate" />:
              <FormattedDate
                value={Date.now()}
                year="numeric"
                month="long"
                day="2-digit"
              />
            </div>

            {/* 欢迎消息 */}
            <p>
              <FormattedMessage id="welcome" />
            </p>
          </Space>
        </Card>
      </ConfigProvider>
    </IntlProvider>
  );
}

export default ReactIntlApp;
```

### 2. 高级用法

```tsx
import { IntlProvider, FormattedMessage, FormattedNumber, FormattedDate } from 'react-intl';

function AdvancedReactIntlExample() {
  const messages = {
    'en-US': {
      price: 'Price: {price, number, USD}',
      members: 'We have {value, plural, =0 {no members} one {# member} other {# members}}',
      deadline: 'Deadline: {date, date, short}',
    },
  };

  return (
    <IntlProvider locale="en-US" messages={messages['en-US']}>
      <div>
        {/* 数字格式化 */}
        <FormattedMessage
          id="price"
          values={{ price: 1234.56 }}
        />

        {/* 复数处理 */}
        <FormattedMessage
          id="members"
          values={{ value: 5 }}
        />

        {/* 日期格式化 */}
        <FormattedMessage
          id="deadline"
          values={{ date: new Date() }}
        />
      </div>
    </IntlProvider>
  );
}
```

---

## i18next 集成

### 1. 基础配置

```tsx
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

// 初始化 i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': {
        translation: {
          title: 'i18next 集成示例',
          description: '这是 i18next 与 Ant Design 的集成',
          welcome: '欢迎',
        },
      },
      'en-US': {
        translation: {
          title: 'i18next Integration Example',
          description: 'This is i18next with Ant Design',
          welcome: 'Welcome',
        },
      },
    },
    lng: 'zh-CN',
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false,
    },
  });

function I18nextApp() {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  const antdLocale = i18n.language === 'zh-CN' ? zhCN : enUS;

  return (
    <ConfigProvider locale={antdLocale}>
      <div>
        <h1>{t('title')}</h1>
        <p>{t('description')}</p>
        <button onClick={() => changeLanguage('zh-CN')}>中文</button>
        <button onClick={() => changeLanguage('en-US')}>English</button>
      </div>
    </ConfigProvider>
  );
}
```

---

## RTL 支持

### 1. 启用 RTL

```tsx
import { ConfigProvider, Button, Input, Space } from 'antd';
import arEG from 'antd/locale/ar_EG';

function RTLExample() {
  return (
    <ConfigProvider
      direction="rtl"
      locale={arEG}
    >
      <Space direction="vertical">
        <Button type="primary">زر الأساسي</Button>
        <Input placeholder="بحث" />
        <Button>زر عادي</Button>
      </Space>
    </ConfigProvider>
  );
}
```

### 2. 动态切换 LTR/RTL

```tsx
import { useState } from 'react';
import { ConfigProvider, Button, Input, Select } from 'antd';
import enUS from 'antd/locale/en_US';
import arEG from 'antd/locale/ar_EG';

function DirectionSwitcher() {
  const [direction, setDirection] = useState<'ltr' | 'rtl'>('ltr');
  const [locale, setLocale] = useState(enUS);

  const toggleDirection = () => {
    const newDirection = direction === 'ltr' ? 'rtl' : 'ltr';
    setDirection(newDirection);

    if (newDirection === 'rtl') {
      setLocale(arEG);
      document.documentElement.setAttribute('dir', 'rtl');
    } else {
      setLocale(enUS);
      document.documentElement.setAttribute('dir', 'ltr');
    }
  };

  return (
    <ConfigProvider direction={direction} locale={locale}>
      <div>
        <Button onClick={toggleDirection}>
          {direction === 'ltr' ? 'Switch to RTL' : 'التبديل إلى LTR'}
        </Button>

        <Input placeholder="Search" />

        <Select>
          <Select.Option value="1">Option 1</Select.Option>
          <Select.Option value="2">Option 2</Select.Option>
        </Select>
      </div>
    </ConfigProvider>
  );
}
```

---

## 最佳实践

### 1. 语言包管理

**✅ 推荐**: 集中管理语言包

```tsx
// locales/index.ts
import { Locale } from 'antd/es/locale';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

export const locales: Record<string, Locale> = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

export const defaultLocale = 'zh-CN';

// 使用
import { locales, defaultLocale } from './locales';

function App() {
  const [locale, setLocale] = useState(defaultLocale);
  return (
    <ConfigProvider locale={locales[locale]}>
      <YourApp />
    </ConfigProvider>
  );
}
```

**❌ 避免**: 分散的语言包配置

### 2. 语言切换优化

**✅ 推荐**: 使用 localStorage 持久化语言

```tsx
useEffect(() => {
  const savedLocale = localStorage.getItem('locale') || 'zh-CN';
  setLocale(savedLocale);
  dayjs.locale(savedLocale);
}, []);

const changeLocale = (newLocale: string) => {
  setLocale(newLocale);
  localStorage.setItem('locale', newLocale);
  dayjs.locale(newLocale);
};
```

**❌ 避免**: 每次刷新都重置为默认语言

### 3. 组件 prop 国际化

**✅ 推荐**: 使用 ConfigProvider 统一配置

```tsx
<ConfigProvider locale={zhCN}>
  <App />
</ConfigProvider>
```

**❌ 避免**: 单独为每个组件配置 locale

```tsx
// 不推荐
<DatePicker locale={zhCN.DatePicker} />
<Table locale={zhCN.Table} />
```

### 4. 日期格式化

**✅ 推荐**: 统一使用 dayjs

```tsx
import dayjs from 'dayjs';

dayjs().format('YYYY-MM-DD');
```

**❌ 避免**: 使用原生 Date 对象

```tsx
// 不推荐
new Date().toLocaleDateString();
```

### 5. 文本国际化

**✅ 推荐**: 使用国际化库处理 UI 文本

```tsx
<FormattedMessage id="welcome" />
// 或
{t('welcome')}
```

**❌ 避免**: 硬编码文本

```tsx
// 不推荐
<h1>Welcome</h1>
```

---

## 常见问题

### Q: 为什么 DatePicker 的语言没有切换?

A: 检查以下几点:
1. 是否同时配置了 `ConfigProvider` 的 `locale` 和 dayjs 的 `locale`
2. 是否正确导入了 dayjs 的语言包: `import 'dayjs/locale/zh-cn'`
3. 是否调用了 `dayjs.locale('zh-cn')` 设置语言

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

// 正确配置
dayjs.locale('zh-cn');

<ConfigProvider locale={zhCN}>
  <DatePicker />
</ConfigProvider>
```

### Q: 如何添加自定义翻译?

A: 有两种方式:

1. **扩展内置语言包**:
```tsx
const customZhCN = {
  ...zhCN,
  DatePicker: {
    ...zhCN.DatePicker,
    lang: {
      ...zhCN.DatePicker.lang,
      placeholder: '请选择日期',
    },
  },
};
```

2. **使用国际化库处理 UI 文本**:
```tsx
// 使用 react-intl
<FormattedMessage id="custom.text" />
```

### Q: 如何实现动态语言切换?

A: 使用 state 管理,并同步更新 antd locale 和 dayjs locale:

```tsx
const [locale, setLocale] = useState('zh-CN');

const changeLocale = async (newLocale: string) => {
  const antdLoc = await import(`antd/locale/${newLocale === 'zh-CN' ? 'zh_CN' : 'en_US'}`);
  setAntdLocale(antdLoc.default);

  await import(`dayjs/locale/${newLocale === 'zh-CN' ? 'zh-cn' : 'en'}.js`);
  dayjs.locale(newLocale === 'zh-CN' ? 'zh-cn' : 'en');

  setLocale(newLocale);
};
```

### Q: 支持哪些语言?

A: Ant Design 官方支持 40+ 种语言,包括:
- 中文（简体、繁体）
- 英语
- 日语
- 韩语
- 法语
- 德语
- 西班牙语
- 葡萄牙语
- 俄语
- 意大利语
- 阿拉伯语（RTL）
- 泰语
- 越南语
- 印尼语
- 等等...

完整列表请参考: [antd/locale](https://github.com/ant-design/ant-design/tree/master/components/locale)

### Q: 如何处理时区?

A: 使用 dayjs 的 UTC 和 timezone 插件:

```tsx
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

// UTC 时间
dayjs().utc().format();

// 特定时区
dayjs().tz('Asia/Shanghai').format();
```

---

## 参考资源

### 官方文档

- [Ant Design 国际化文档](https://ant.design/docs/react/i18n-cn)
- [ConfigProvider API](https://ant.design/components/config-provider-cn/)
- [DatePicker 国际化](https://ant.design/components/date-picker-cn/#components-date-picker-demo-locale)
- [dayjs 文档](https://day.js.org/docs/en/i18n/i18n)

### 相关库

- [react-intl](https://formatjs.io/docs/react-intl/)
- [i18next](https://www.i18next.com/)
- [dayjs](https://day.js.org/)

### 示例代码

- [Ant Design 国际化示例](https://ant.design/components/date-picker-cn/#components-date-picker-demo-locale)
- [React Intl 示例](https://github.com/formatjs/formatjs/tree/main/packages/react-intl/examples)

---

## 版本要求

- Ant Design >= 5.0.0
- React >= 16.9.0
- dayjs >= 1.11.0
- react-intl >= 6.0.0（可选）
- i18next >= 23.0.0（可选）

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
