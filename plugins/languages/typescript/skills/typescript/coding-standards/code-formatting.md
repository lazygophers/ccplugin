# TypeScript 代码格式规范

## 核心原则

### ✅ 必须遵守

1. **使用 Prettier** - 统一代码格式
2. **使用 ESLint** - 检查代码质量
3. **2 空格缩进** - 不使用 tab
4. **单引号** - 字符串使用单引号
5. **分号** - 每个语句后添加分号
6. **行宽 80** - 单行不超过 80 字符
7. **尾随逗号** - 对象/数组最后一个元素后添加逗号

### ❌ 禁止行为

- 手动格式化代码（让 Prettier 处理）
- 混用单双引号
- 混用空格和 tab
- 超长行不换行
- 不使用尾随逗号

## Prettier 配置

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf",
  "bracketSpacing": true,
  "jsxSingleQuote": false,
  "jsxBracketSameLine": false
}
```

## 基本格式

### 缩进和空格

```typescript
// ✅ 正确 - 2 空格缩进
function getUser(id: string): Promise<User> {
  if (isValidId(id)) {
    return fetchUser(id);
  }
  throw new Error('Invalid ID');
}

// ❌ 错误 - 4 空格缩进
function getUser(id: string): Promise<User> {
    if (isValidId(id)) {
        return fetchUser(id);
    }
    throw new Error('Invalid ID');
}

// ❌ 错误 - 使用 tab
function getUser(id: string): Promise<User> {
	if (isValidId(id)) {
		return fetchUser(id);
	}
	throw new Error('Invalid ID');
}
```

### 行宽

```typescript
// ✅ 正确 - 长行自动换行
const result = await fetch(
  `${API_BASE_URL}/users/${userId}?include=${includeFields.join(',')}`,
);

function longFunctionName(
  param1: string,
  param2: number,
  param3: boolean,
): ReturnType {
  // ...
}

// ❌ 错误 - 超长行不换行
const result = await fetch(`${API_BASE_URL}/users/${userId}?include=${includeFields.join(',')}`);

function longFunctionName(param1: string, param2: number, param3: boolean): ReturnType { }
```

### 对象格式

```typescript
// ✅ 正确 - 对象格式
const user = {
  id: '123',
  name: 'John',
  email: 'john@example.com',
};

// ✅ 正确 - 多行对象使用尾随逗号
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  retries: 3,
};

// ❌ 错误 - 不使用尾随逗号
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  retries: 3
};

// ❌ 错误 - 单行对象格式不一致
const user = { id: '123', name: 'John', email: 'john@example.com' };
```

### 数组格式

```typescript
// ✅ 正确 - 数组格式
const items = [1, 2, 3, 4, 5];

// ✅ 正确 - 多行数组使用尾随逗号
const users = [
  { id: '1', name: 'Alice' },
  { id: '2', name: 'Bob' },
  { id: '3', name: 'Charlie' },
];

// ❌ 错误 - 不一致的数组格式
const users = [
  { id: '1', name: 'Alice' },
  { id: '2', name: 'Bob' },
  { id: '3', name: 'Charlie' }
];
```

## 导入规范

### 导入顺序

```typescript
// ✅ 正确 - 导入顺序
// 1. Node.js 内置模块
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// 2. 第三方库
import { useState, useEffect } from 'react';
import { z } from 'zod';

// 3. 内部模块 - 绝对路径
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

// 4. 内部模块 - 相对路径
import { UserRepository } from './repositories';
import { validateUser } from './validators';

// 5. 类型导入
import type { User } from '@/types';
import type { ApiResponse } from './api';

// ❌ 错误 - 混乱的导入顺序
import { useState } from 'react';
import path from 'node:path';
import { Button } from '@/components/ui/button';
import { z } from 'zod';
import type { User } from '@/types';
import { UserRepository } from './repositories';
```

### 类型导入

```typescript
// ✅ 正确 - 使用 type 关键字导入类型
import type { User, UserRole } from '@/types';
import type { ApiResponse } from './api';

// ✅ 正确 - 值和类型混合导入
import { UserService, type UserServiceConfig } from './services';

// ✅ 正确 - 内联类型导入
function processUser(user: import('./types').User) {
  // ...
}

// ❌ 避免 - 不使用 type 关键字
import { User, UserRole } from '@/types';
import type { ApiResponse } from './api';
```

### 路径别名

```typescript
// ✅ 正确 - 使用路径别名
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { User } from '@/types';

// ❌ 避免 - 使用相对路径（深层目录）
import { Button } from '../../../components/ui/button';
import { useAuth } from '../../hooks/useAuth';
import { User } from '../../types';
```

### 禁止默认导出

```typescript
// ❌ 避免 - 默认导出
export default function UserService() {
  // ...
}

// ✅ 推荐 - 具名导出
export function UserService() {
  // ...
}

// ❌ 避免 - 默认导出类
export default class UserService {
  // ...
}

// ✅ 推荐 - 具名导出类
export class UserService {
  // ...
}

// ✅ 正确 - 导入时使用具名导入
import { UserService } from './services';

// ❌ 避免 - 导入默认导出时改名
import Service from './services';
```

## 空行规范

### 函数之间

```typescript
// ✅ 正确 - 函数之间空一行
function getUser(id: string): Promise<User> {
  // ...
}

function createUser(data: UserInput): Promise<User> {
  // ...
}

function updateUser(id: string, data: Partial<UserInput>): Promise<User> {
  // ...
}

// ❌ 错误 - 没有空行
function getUser(id: string): Promise<User> {
  // ...
}
function createUser(data: UserInput): Promise<User> {
  // ...
}
```

### 代码块之间

```typescript
// ✅ 正确 - 逻辑块之间空行
function processUser(user: User) {
  // 验证用户
  if (!isValidUser(user)) {
    throw new Error('Invalid user');
  }

  // 转换用户数据
  const dto = toDto(user);

  // 保存用户
  await userRepository.save(dto);

  // 返回结果
  return dto;
}

// ❌ 错误 - 没有空行分隔
function processUser(user: User) {
  if (!isValidUser(user)) {
    throw new Error('Invalid user');
  }
  const dto = toDto(user);
  await userRepository.save(dto);
  return dto;
}
```

## 运算符和空格

### 运算符空格

```typescript
// ✅ 正确 - 运算符前后有空格
const sum = a + b;
const result = condition ? value1 : value2;
const isActive = user.status === 'active';

// ❌ 错误 - 没有空格
const sum = a+b;
const result = condition?value1:value2;
const isActive = user.status==='active';

// ❌ 错误 - 多余的空格
const sum = a + b ;
const result = condition ? value1 : value2 ;
```

### 括号空格

```typescript
// ✅ 正确 - 括号内无空格
function foo(a: string, b: number): void {
  const result = (a + b).toString();
}

// ❌ 错误 - 括号内有空格
function foo( a: string, b: number ): void {
  const result = ( a + b ).toString();
}
```

## TypeScript 特定格式

### 泛型格式

```typescript
// ✅ 正确 - 泛型无空格
function identity<T>(value: T): T {
  return value;
}

type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

// ❌ 错误 - 泛型有空格
function identity <T> (value: T): T {
  return value;
}

type Result <T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

### 类型注解格式

```typescript
// ✅ 正确 - 冒号后有空格
const name: string = 'John';
const users: User[] = [];
const config: Partial<Config> = {};

function getUser(id: string): Promise<User> {
  // ...
}

// ❌ 错误 - 冒号后没有空格
const name:string = 'John';
const users:User[] = [];

// ❌ 错误 - 冒号前有空格
const name : string = 'John';
```

### 箭头函数格式

```typescript
// ✅ 正确 - 参数与箭头之间有空格
const add = (a: number, b: number): number => a + b;

// ✅ 正确 - 单参数无括号（无类型注解时）
const double = x => x * 2;

// ✅ 正确 - 单参数有括号（有类型注解时）
const double = (x: number) => x * 2;

// ✅ 正确 - 多行箭头函数
const processUser = (user: User): UserDTO => {
  const validated = validateUser(user);
  return toDto(validated);
};

// ❌ 错误 - 参数与箭头之间没有空格
const add = (a: number, b: number): number => a + b;
```

## 检查清单

提交代码前，确保：

- [ ] 运行 `pnpm format` 格式化代码
- [ ] 运行 `pnpm lint` 检查代码质量
- [ ] 使用 2 空格缩进
- [ ] 使用单引号
- [ ] 语句后有分号
- [ ] 对象/数组有尾随逗号
- [ ] 导入按正确顺序排列
- [ ] 使用路径别名而非相对路径
- [ ] 运算符前后有空格
- [ ] 没有默认导出（使用具名导出）
