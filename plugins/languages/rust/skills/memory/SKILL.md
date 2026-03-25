---
name: memory
description: Rust 内存管理规范 - 所有权、借用、生命周期、智能指针、零拷贝模式。管理内存和优化分配时加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Rust 内存管理规范

## 适用 Agents

- **rust:dev** - 日常开发中的内存管理
- **rust:debug** - 调试借用冲突和生命周期问题
- **rust:perf** - 内存优化和分配减少

## 相关 Skills

- **Skills(rust:core)** - 所有权三原则、错误处理
- **Skills(rust:async)** - 异步代码中的生命周期
- **Skills(rust:unsafe)** - 裸指针、手动内存管理

## 借用规则

### 核心规则
1. **多个 `&T`**（不可变借用）可以同时存在
2. **一个 `&mut T`**（可变借用）独占存在
3. 借用不能比所有者活得更久

### 常见模式
```rust
// 缩短借用作用域解决冲突
let mut map = HashMap::new();
let value = map.get("key").cloned(); // 借用在此结束
if value.is_none() {
    map.insert("key", 42); // 现在可以可变借用
}

// 使用 entry API 避免两次查找
map.entry("key").or_insert(42);

// 函数参数优先借用
fn process(data: &[u8]) -> Result<Output> { /* ... */ }  // 好
fn process(data: Vec<u8>) -> Result<Output> { /* ... */ } // 通常不必要
```

## 智能指针选择

| 类型 | 用途 | 线程安全 | 开销 |
|------|------|---------|------|
| `Box<T>` | 堆分配、递归类型、trait 对象 | 由 T 决定 | 一次分配 |
| `Rc<T>` | 单线程共享所有权 | 否 | 引用计数 |
| `Arc<T>` | 多线程共享所有权 | 是 | 原子引用计数 |
| `Cow<'a, T>` | 延迟克隆 | 由 T 决定 | 零或一次分配 |

### 内部可变性

```rust
// 单线程：RefCell（运行时借用检查）
use std::cell::RefCell;
let cell = RefCell::new(vec![1, 2, 3]);
cell.borrow_mut().push(4);

// 多线程：Mutex / RwLock
use std::sync::{Arc, RwLock};
let shared = Arc::new(RwLock::new(vec![1, 2, 3]));
shared.write().unwrap().push(4);

// 优先考虑：通道或原子类型替代锁
use std::sync::atomic::{AtomicU64, Ordering};
let counter = AtomicU64::new(0);
counter.fetch_add(1, Ordering::Relaxed);
```

## 生命周期

```rust
// 省略规则覆盖大部分场景
fn first(s: &str) -> &str { &s[..1] }

// 需要标注时保持最小化
struct Parser<'input> {
    input: &'input str,
    pos: usize,
}

// 'static 仅在真正需要时使用
fn spawn_task(name: String) {  // String 是 'static
    tokio::spawn(async move {
        println!("{name}");
    });
}
```

## 零拷贝模式

```rust
// Cow：可能需要修改时延迟克隆
use std::borrow::Cow;

fn normalize_path(path: &str) -> Cow<'_, str> {
    if path.contains("//") {
        Cow::Owned(path.replace("//", "/"))
    } else {
        Cow::Borrowed(path)
    }
}

// bytes crate：网络数据零拷贝
use bytes::{Bytes, BytesMut};
let data = Bytes::from_static(b"hello");
let slice = data.slice(0..3); // 无拷贝，引用计数

// &[u8] 切片：零拷贝视图
fn parse_header(data: &[u8]) -> Result<Header> {
    let name = &data[..4];  // 无拷贝
    // ...
}
```

## 内存布局优化

```rust
// 使用 repr 控制布局
#[repr(C)]          // C 兼容布局
#[repr(packed)]     // 紧凑布局（慎用）
#[repr(align(64))]  // 缓存行对齐

// 字段排序减少 padding
struct Optimized {
    large: u64,   // 8 bytes
    medium: u32,  // 4 bytes
    small: u16,   // 2 bytes
    tiny: u8,     // 1 byte
    flag: bool,   // 1 byte
}  // 16 bytes（无 padding）

// SmallVec 避免小数组堆分配
use smallvec::SmallVec;
let tags: SmallVec<[String; 4]> = SmallVec::new();

// Arena 分配（大量同类型对象）
use bumpalo::Bump;
let arena = Bump::new();
let value = arena.alloc(42);
```

## Red Flags：AI 常见误区

| AI 可能的解释 | 实际检查 |
|--------------|---------|
| "clone 更简单" | ✅ 热路径中是否有不必要的克隆？ |
| "用 String 参数方便" | ✅ 是否应为 `&str` 或 `impl AsRef<str>`？ |
| "Arc\<Mutex\<T\>\> 是标准做法" | ✅ 是否可用 channel 或原子类型替代？ |
| "Vec 够用" | ✅ 是否考虑 SmallVec 或固定数组？ |
| "加个 'static 就行" | ✅ 是否真的需要 'static？能否缩短生命周期？ |
| "Box\<dyn Trait\> 灵活" | ✅ 是否可用泛型实现静态分派？ |

## 检查清单

- [ ] 函数参数优先借用（`&str`、`&[T]`、`&Path`）
- [ ] 无不必要的 `.clone()` 或 `.to_string()`
- [ ] 使用 `Cow` 处理可能需要修改的借用数据
- [ ] 智能指针选择正确（Box/Rc/Arc 按需）
- [ ] 内部可变性使用正确（RefCell/Mutex/RwLock）
- [ ] 热路径考虑零拷贝模式
- [ ] 生命周期注解最小化
