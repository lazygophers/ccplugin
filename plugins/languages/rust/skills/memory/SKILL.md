---
name: rust-memory
description: Rust 内存管理与所有权规范 — 借用规则、生命周期标注、智能指针（Box / Rc / Arc / Cow）、内部可变性（RefCell / Mutex / RwLock / atomic）、零拷贝（bytes / Cow / &[u8]）、内存布局（repr / 字段排序 / SmallVec / bumpalo）。处理借用冲突、生命周期错误、内存分配优化、`Arc<Mutex<T>>` 重构时加载。触发短语：借用冲突、生命周期错误、cannot borrow、does not live long enough、智能指针、Arc Mutex、零拷贝、内存优化。
user-invocable: true
---

# Rust 内存管理规范

前置：`rust-core` 的所有权三原则。本 skill 聚焦借用、生命周期、智能指针、零拷贝。

## 借用规则

1. 多个 `&T` 共存 OR 唯一 `&mut T`，二者互斥。
2. 借用不得长于所有者。
3. NLL（non-lexical lifetimes）下借用作用域 = 最后一次使用，主动缩短借用即可解冲突。

```rust
// 缩短借用作用域
let value = map.get("k").cloned();   // 借用结束
if value.is_none() { map.insert("k", 42); }

// entry API 避免双查
map.entry("k").or_insert(42);
```

## 智能指针选型

| 类型 | 场景 | 线程安全 | 备注 |
|------|------|---------|------|
| `Box<T>` | 堆分配 / 递归类型 / `Box<dyn Trait>` | 取决于 T | 单一所有权 |
| `Rc<T>` | 单线程共享只读 | 否 | 弱引用用 `Weak` |
| `Arc<T>` | 多线程共享只读 | 是 | 原子计数有开销 |
| `Cow<'a, T>` | 大概率只读、偶尔修改 | 取决于 T | 零或一次分配 |

## 内部可变性

```rust
// 单线程：RefCell（运行时借用检查，panic 风险）
use std::cell::RefCell;

// 多线程：Mutex / RwLock
use std::sync::{Arc, RwLock};

// 优先：原子 / channel 替代锁
use std::sync::atomic::{AtomicU64, Ordering};
let counter = AtomicU64::new(0);
counter.fetch_add(1, Ordering::Relaxed);
```

`Arc<Mutex<T>>` 是反模式信号：先考虑 mpsc channel、`Arc<RwLock<T>>` 或 actor 拆分。

## 生命周期

- 优先依赖省略规则（input 单参 → 自动传播；`&self` 方法 → 借 self）。
- 必须标注时保持最小化，结构体优先用 `'a` 而非 `'static`。
- `'static` 仅在真正跨线程 spawn 或全局数据时使用。

```rust
struct Parser<'input> { input: &'input str, pos: usize }
```

## 零拷贝模式

```rust
// Cow：延迟克隆
use std::borrow::Cow;
fn normalize(p: &str) -> Cow<'_, str> {
    if p.contains("//") { Cow::Owned(p.replace("//", "/")) } else { Cow::Borrowed(p) }
}

// bytes::Bytes：网络 / 缓冲零拷贝切片
use bytes::Bytes;
let head = Bytes::from_static(b"hello").slice(0..3);

// 切片视图
fn parse_header(data: &[u8]) -> &[u8] { &data[..4] }
```

## 内存布局优化

```rust
#[repr(C)]                   // FFI / 显式布局
#[repr(align(64))] struct CacheAligned([u8; 64]);

// 字段按大小降序排，减少 padding
struct Optimized { a: u64, b: u32, c: u16, d: u8 }

// SmallVec：小容量栈分配
use smallvec::SmallVec;
let tags: SmallVec<[String; 4]> = SmallVec::new();

// bumpalo：批量同生命周期对象
use bumpalo::Bump;
let arena = Bump::new();
let n = arena.alloc(42);
```

## 函数签名指南

| 参数 | 写法 |
|------|------|
| 字符串只读 | `&str` 或 `impl AsRef<str>` |
| 切片只读 | `&[T]` |
| 路径 | `&Path` / `impl AsRef<Path>` |
| 字节 | `&[u8]` / `&Bytes` |
| 必须拥有 | `String` / `Vec<T>` / `T` |

## 反模式

| AI 倾向 | 正确做法 |
|---------|---------|
| `.clone()` 绕借用 | 重构作用域 / `Cow` / 借用 |
| `Arc<Mutex<T>>` 万能 | channel / atomic / 拆分状态 |
| `'static` 一把梭 | 引入 `'a` 缩短生命周期 |
| `Vec` 装小集合 | `SmallVec` / 数组 |
| `Box<dyn Trait>` | 优先泛型静态分派 |

## 检查清单

- [ ] 入参优先借用（`&str`、`&[T]`、`&Path`）
- [ ] 热路径无 `.clone()` / `.to_string()`
- [ ] 可能修改的借用数据用 `Cow`
- [ ] 智能指针选型正确，无 `Arc<Mutex<T>>` 滥用
- [ ] 生命周期标注最小化
- [ ] 结构体字段大小降序排列

## 相关 Skill

- `rust-core`：所有权三原则、错误处理
- `rust-async`：跨 await 的借用、`Send` 边界
- `rust-unsafe`：裸指针、手动内存
