# JavaScript 代码格式规范

## ESLint 配置

### ESLint 9+ Flat Config

```javascript
// eslint.config.js
import js from '@eslint/js';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  {
    ignores: ['dist/', 'node_modules/', '*.config.js'],
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
    },
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2025,
      },
    },
    rules: {
      // 强制规则
      'no-console': ['error', { allow: ['warn', 'error'] }],
      'no-debugger': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-arrow-callback': 'error',

      // React 规则
      'react/react-in-jsx-scope': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // 代码风格
      'semi': ['error', 'always'],
      'quotes': ['error', 'single'],
      'indent': ['error', 2],
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
];
```

## Prettier 配置

### .prettierrc

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### .prettierignore

```
dist/
node_modules/
*.config.js
*.min.js
```

## 基本格式

### 分号

```javascript
// ✅ 推荐：始终使用分号
const greeting = 'Hello, World!';
function sayHello() {
  console.log(greeting);
}

// ❌ 避免：省略分号（除非有充分理由）
const greeting = 'Hello, World!'
function sayHello() {
  console.log(greeting)
}
```

### 引号

```javascript
// ✅ 推荐：使用单引号
const name = 'John';
const template = `Hello, ${name}`;

// ❌ 避免：混合使用
const name = "John";
```

### 缩进

```javascript
// ✅ 推荐：2 空格缩进
function calculateTotal(price, tax) {
  const taxAmount = price * tax;
  const total = price + taxAmount;
  return total;
}

// ❌ 避免：Tab 缩进或混合
function calculateTotal(price, tax) {
	const taxAmount = price * tax;
  const total = price + taxAmount;
  return total;
}
```

### 花括号

```javascript
// ✅ 推荐：同一行打开花括号
function greet(name) {
  return `Hello, ${name}`;
}

// ❌ 避免：花括号换行
function greet(name)
{
  return `Hello, ${name}`;
}
```

## 空格

### 操作符周围

```javascript
// ✅ 推荐：操作符周围加空格
const sum = a + b;
const average = total / count;
const isGreater = a > b;

// ❌ 避免：缺少空格
const sum = a+b;
```

### 逗号后

```javascript
// ✅ 推荐：逗号后加空格
const numbers = [1, 2, 3, 4, 5];
const person = {
  name: 'John',
  age: 30,
};

// ❌ 避免：逗号前或后缺少空格
const numbers = [1,2,3,4,5];
const person = {name:'John',age:30};
```

### 函数参数

```javascript
// ✅ 推荐：参数间加空格
function greet(name, greeting = 'Hello') {
  return `${greeting}, ${name}!`;
}

// ❌ 避免
function greet(name,greeting='Hello') {}
```

## 数组和对象

### 数组

```javascript
// ✅ 推荐：换行风格
const numbers = [
  1,
  2,
  3,
  4,
  5,
];

// ✅ 推荐：单行（简短时）
const colors = ['red', 'green', 'blue'];

// ❌ 避免：混合风格
const numbers = [
  1, 2, 3,
  4, 5,
];
```

### 对象

```javascript
// ✅ 推荐：换行风格
const user = {
  name: 'John',
  email: 'john@example.com',
  age: 30,
};

// ✅ 推荐：单行（简短时）
const point = { x: 10, y: 20 };

// ❌ 避免
const user = {
  name: 'John', email: 'john@example.com',
};
```

### 解构

```javascript
// ✅ 推荐：数组解构
const [first, second, third] = items;

// ✅ 推荐：对象解构
const {
  name,
  email,
  age,
} = user;

// ✅ 推荐：函数参数解构
function greet({ name, title = 'Mr.' }) {
  return `Hello, ${title} ${name}`;
}
```

## 函数

### 函数声明

```javascript
// ✅ 推荐：命名函数（提升）
function calculateTotal(price, tax) {
  return price + price * tax;
}

// ❌ 避免：过于复杂
function c(p, t) {
  return p + p * t;
}
```

### 箭头函数

```javascript
// ✅ 推荐：单参数可省略括号
const double = x => x * 2;
const getName = user => user.name;

// ✅ 推荐：多参数需要括号
const sum = (a, b) => a + b;

// ✅ 推荐：多行函数体需要花括号
const calculate = (a, b) => {
  const result = a * b;
  return result;
};

// ❌ 避免
const double = (x) => { return x * 2; };  // 冗余
```

### IIFE

```javascript
// ✅ 推荐：箭头函数 IIFE
const config = (() => {
  const env = process.env.NODE_ENV;
  return env === 'production' ? prodConfig : devConfig;
})();

// ✅ 推荐：函数表达式 IIFE
const config = (function() {
  const env = process.env.NODE_ENV;
  return env === 'production' ? prodConfig : devConfig;
})();
```

## 条件语句

### if 语句

```javascript
// ✅ 推荐：花括号和多行
if (isValid) {
  saveData();
}

// ✅ 推荐：else 同一行
if (isValid) {
  saveData();
} else {
  showError();
}

// ❌ 避免：单行 if（危险）
if (isValid) saveData();

// ❌ 避免：else 换行
if (isValid)
{
  saveData();
}
else
{
  showError();
}
```

### switch 语句

```javascript
// ✅ 推荐：break 和 case 同一缩进
switch (status) {
  case 'pending':
    showPendingMessage();
    break;
  case 'approved':
    showApprovedMessage();
    break;
  case 'rejected':
    showRejectedMessage();
    break;
  default:
    showDefaultMessage();
}
```

## Promise 和 async/await

### async/await

```javascript
// ✅ 推荐：清晰易读
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

// ❌ 避免：过度嵌套
async function fetchData(url) {
  const response = await fetch(url);
  const data = await response.json();
  return data;
}
```

## React 组件

### 函数组件

```javascript
// ✅ 推荐：清晰格式
export function UserCard({ user, onEdit }) {
  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <button onClick={() => onEdit(user.id)}>Edit</button>
    </div>
  );
}

// ✅ 推荐：复杂组件换行
export function ComplexForm({
  initialData,
  onSubmit,
  onCancel,
  validationRules,
}) {
  const [formData, setFormData] = useState(initialData);

  return (
    <form onSubmit={handleSubmit}>
      {/* 表单内容 */}
    </form>
  );
}
```

## 导入导出

### 导入顺序

```javascript
// ✅ 推荐：分组导入
// 1. React/框架
import React, { useState, useEffect } from 'react';

// 2. 外部库
import { useForm } from 'react-hook-form';
import axios from 'axios';

// 3. 内部模块（相对路径）
import { UserCard } from '@/components/UserCard';
import { useAuth } from '@/hooks/useAuth';

// 4. 样式
import './Button.css';
```

### 导出

```javascript
// ✅ 推荐：具名导出（推荐）
export const fetchUser = async (id) => { };
export function UserCard({ user }) { }

// ✅ 推荐：默认导出仅用于主要功能
export default function App() { }

// ❌ 避免：混合导出
export const name = 'John';
export default const age = 30;  // 错误
```

## 注释

### 单行注释

```javascript
// ✅ 推荐：空格后注释
// Calculate the total price including tax
const calculateTotal = (price, tax) => {
  return price + price * tax;
};

// ✅ 推荐：行内注释（空格后）
const total = price + tax; // 包括税费
```

### JSDoc

```javascript
/**
 * Calculates the total price including tax.
 *
 * @param {number} price - The base price
 * @param {number} tax - The tax rate (e.g., 0.1 for 10%)
 * @returns {number} The total price
 */
function calculateTotal(price, tax) {
  return price + price * tax;
}
```

## 快速检查清单

- [ ] ESLint 和 Prettier 已配置
- [ ] 始终使用分号
- [ ] 使用单引号
- [ ] 2 空格缩进
- [ ] 操作符周围有空格
- [ ] 逗号后有空格
- [ ] if/else 始终使用花括号
- [ ] 组件格式清晰
- [ ] 导入分组有序
- [ ] 注释简洁有效
