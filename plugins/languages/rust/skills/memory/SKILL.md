---
name: memory
description: Rust 内存管理规范：智能指针、所有权、内存布局。管理内存时必须加载。
---

# Rust 内存管理规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | Rust 2024 edition、强制约定 |

## 所有权规则

1. 每个值都有一个所有者
2. 同一时间只能有一个所有者
3. 所有者离开作用域时，值被丢弃

## 智能指针

```rust
// Box<T> - 堆分配
let boxed = Box::new(42);

// Rc<T> - 引用计数（单线程）
use std::rc::Rc;
let shared = Rc::new(vec![1, 2, 3]);
let another = Rc::clone(&shared);

// Arc<T> - 原子引用计数（多线程）
use std::sync::Arc;
let shared = Arc::new(vec![1, 2, 3]);

// RefCell<T> - 内部可变性
use std::cell::RefCell;
let cell = RefCell::new(42);
*cell.borrow_mut() = 100;

// Mutex<T> - 互斥锁
use std::sync::Mutex;
let mutex = Mutex::new(42);
*mutex.lock().unwrap() = 100;
```

## 借用规则

```rust
// ✅ 多个不可变借用
let v = vec![1, 2, 3];
let r1 = &v;
let r2 = &v;  // OK

// ❌ 可变借用和不可变借用同时存在
let mut v = vec![1, 2, 3];
let r1 = &v;
v.push(4);  // ERROR: 不能在不可变借用存在时修改

// ✅ Cow 避免克隆
use std::borrow::Cow;
fn process(s: Cow<str>) {
    // 在需要时才克隆
}
```

## 检查清单

- [ ] 理解所有权规则
- [ ] 正确使用智能指针
- [ ] 避免不必要的克隆
- [ ] 使用 Cow 优化
