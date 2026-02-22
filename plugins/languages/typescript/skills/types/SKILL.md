---
name: types
description: TypeScript 类型系统规范：类型安全、泛型、类型守卫。设计类型时必须加载。
---

# TypeScript 类型系统规范

## 相关 Skills

| 场景     | Skill        | 说明              |
| -------- | ------------ | ----------------- |
| 核心规范 | Skills(core) | TS 5.9+、严格模式 |

## 类型命名

```typescript
// ✅ 正确
type UserDTO = { id: string; name: string };
interface ApiResponse {
	data: unknown;
	status: number;
}
type Status = "active" | "inactive" | "pending";

// ❌ 错误
type IUser = {}; // 禁止 I 前缀
type user = {}; // 类型使用 PascalCase
```

## 类型守卫

```typescript
function isString(value: unknown): value is string {
	return typeof value === "string";
}

function isUser(value: unknown): value is User {
	return typeof value === "object" && value !== null && "id" in value;
}

// 使用
if (isString(value)) {
	console.log(value.toUpperCase());
}
```

## 泛型

```typescript
// 泛型函数
function identity<T>(value: T): T {
	return value;
}

// 泛型约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
	return obj[key];
}

// 泛型接口
interface Repository<T> {
	findById(id: string): Promise<T | null>;
	save(entity: T): Promise<void>;
}
```

## Zod 运行时验证

```typescript
import { z } from "zod";

const UserSchema = z.object({
	id: z.string().uuid(),
	name: z.string().min(1),
	email: z.string().email(),
});

type User = z.infer<typeof UserSchema>;

// 使用
const user = UserSchema.parse(data);
```

## 检查清单

- [ ] 无 any 类型
- [ ] 使用类型守卫
- [ ] 使用 Zod 运行时验证
- [ ] 泛型约束正确
