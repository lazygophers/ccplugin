---
name: naming-conventions
description: Cross-language naming standards and best practices
---

# 命名规范指南

## 一、通用原则

### 1. 清晰性（Clarity）

- 名称应该清楚表达其含义
- 避免使用过于简洁的缩写（除非是广为人知的术语）
- 使用完整的单词组合

**✓ 好的做法**

```
user_name, get_user_by_id, calculate_total_price
```

**✗ 不推荐**

```
u, gubi, calc_tp
```

### 2. 一致性（Consistency）

- 项目内保持命名风格统一
- 相同概念使用相同命名方式
- 遵循语言社区的标准

### 3. 可读性（Readability）

- 避免过长的名称（通常 < 40 字符）
- 使用有意义的词汇
- 优先考虑团队可读性

### 4. 避免混淆（Avoid Confusion）

- 不要使用相似的名称
- 不要使用容易误解的缩写
- 避免歧义的单数/复数形式

---

## 二、命名清单

使用前检查：

- [ ] 名称是否清晰表达意图？
- [ ] 是否遵循语言社区规范？
- [ ] 名称长度是否合理（< 40 字符）？
- [ ] 是否与项目内其他命名一致？
- [ ] 避免了歧义吗？
- [ ] 是否需要代码注释来解释这个名称？（如果是，考虑重新命名）
- [ ] 避免了过度缩写吗？
- [ ] 避免了容易混淆的相似名称吗？

---

## 三、常用命名错误清单

以下是开发中常见的命名错误，应当避免：

| 错误命名          | 正确命名                         | 说明                         |
|---------------|------------------------------|----------------------------|
| `status`      | `state`                      | 使用 state 表示状态，status 过于通用  |
| `ID`          | `Id`                         | ID 应使用 PascalCase，保持一致性    |
| `Users`       | `UserList`                   | 使用清晰的集合名称，而非仅加 s 后缀        |
| `id`          | `uid`/`userId`               | 简单的 `id` 易混淆，应使用带前缀的形式     |
| `user_id`     | `uid`                        | 在某些项目中统一使用短形式 `uid`        |
| `get_status`  | `get_state`                  | 保持方法命名与属性命名一致              |
| `FLAG_ENABLE` | `IS_ENABLED` 或 `ENABLE_FLAG` | 布尔值使用 `IS_` 或 `HAS_` 前缀更清晰 |
| `data`        | `user_data`/`config_data`    | 避免过于泛化的名称                  |
| `temp`        | `temporary_buffer`/`cache`   | 避免 temp 等临时性命名             |
| `obj`         | 具体类型名                        | 避免使用 obj、item 等过于抽象的名称     |
| `created_time` | `created_at`                  | 时间字段使用 `_at` 后缀，不用 `_time`   |
| `update_time` | `updated_at`                  | 保持 `_at` 命名规范，表示某个时间点     |
| 字符串时间    | 时间戳（数字/整数）                 | 时间必须使用时间戳格式，不允许字符串类型  |