---
name: security
description: TypeScript 安全编码规范：输入验证、XSS 防护、依赖审计。处理安全问题时必须加载。
---

# TypeScript 安全编码规范

## 相关 Skills

| 场景     | Skill        | 说明              |
| -------- | ------------ | ----------------- |
| 核心规范 | Skills(core) | TS 5.9+、严格模式 |

## 输入验证

```typescript
import { z } from "zod";

// ✅ 使用 Zod 验证
const UserInputSchema = z.object({
	name: z.string().min(1).max(100),
	email: z.string().email(),
	age: z.number().int().min(0).max(150).optional(),
});

function validateUser(input: unknown) {
	return UserInputSchema.safeParse(input);
}

// 使用
const result = validateUser(req.body);
if (!result.success) {
	return res.status(400).json({ errors: result.error.errors });
}
```

## XSS 防护

```typescript
// ✅ 使用 DOMPurify
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(userInput);

// ✅ React 自动转义
<div>{userInput}</div>

// ❌ 危险
element.innerHTML = userInput;
```

## 依赖审计

```bash
# pnpm 审计
pnpm audit

# 修复漏洞
pnpm audit --fix
```

## 敏感数据处理

```typescript
// ✅ 使用环境变量
const apiKey = process.env.API_KEY;

// ❌ 禁止硬编码
const apiKey = "sk-xxx"; // 危险！

// ✅ 日志脱敏
function sanitizeForLog(data: object): object {
	const { password, token, ...rest } = data;
	return rest;
}
```

## 检查清单

- [ ] 使用 Zod 验证输入
- [ ] 使用 DOMPurify 清理 HTML
- [ ] 运行 pnpm audit
- [ ] 敏感数据使用环境变量
