# Rust 内存管理规范

## 核心原则

### ✅ 必须遵守

1. **理解栈与堆** - 明确数据分配位置
2. **避免不必要分配** - 减少堆分配
3. **使用智能指针** - Box、Rc、Arc
4. **理解内存布局** - 了解结构体内存布局
5. **使用 Cow** - 避免不必要的克隆

## 栈与堆

### 栈分配

```rust
// ✅ 栈分配（固定大小）
let x: i32 = 42;
let arr: [i32; 100] = [0; 100];
struct Point { x: i32, y: i32 }

// ✅ 小型结构体在栈上
struct SmallStruct {
    a: u8,
    b: u16,
    c: u32,
}

// ✅ 使用栈分配缓冲区
let mut buffer = [0u8; 1024];
// 使用 buffer
```

### 堆分配

```rust
// ✅ 使用 Box 进行堆分配
let large_array: Box<[u32; 10000]> = Box::new([0; 10000]);

// ✅ Box 用于递归类型
enum List {
    Cons(i32, Box<List>),
    Nil,
}

// ✅ Box 用于 trait 对象
trait Processor {
    fn process(&self);
}

struct MyProcessor;

impl Processor for MyProcessor {
    fn process(&self) {
        // ...
    }
}

let processor: Box<dyn Processor> = Box::new(MyProcessor);
```

## 智能指针

### Box

```rust
// ✅ Box 用于大数组
let data: Box<[u8; 1024 * 1024]> = Box::new([0; 1024 * 1024]);

// ✅ Box 用于递归类型
struct Node {
    value: i32,
    next: Option<Box<Node>>,
}

// ✅ Box 转移所有权
let boxed = Box::new(42);
let value = *boxed;  // 解引用
```

### Rc

```rust
// ✅ Rc 用于共享所有权
use std::rc::Rc;

let data = Rc::new(vec![1, 2, 3]);
let data2 = Rc::clone(&data);
let data3 = Rc::clone(&data);

// ✅ Rc 用于引用计数
println!("Count: {}", Rc::strong_count(&data));

// ✅ Rc::make_mut
use std::rc::Rc;

let mut data = Rc::new(vec![1, 2, 3]);
Rc::make_mut(&mut data).push(4);
```

### Arc

```rust
// ✅ Arc 用于线程安全的共享所有权
use std::sync::Arc;

let data = Arc::new(vec![1, 2, 3]);
let data2 = Arc::clone(&data);

// ✅ Arc 在多线程中使用
use std::thread;

let data = Arc::new(vec![1, 2, 3]);
let handles: Vec<_> = (0..4)
    .map(|_| {
        let data = Arc::clone(&data);
        thread::spawn(move || {
            println!("Data: {:?}", *data);
        })
    })
    .collect();

for handle in handles {
    handle.join().unwrap();
}
```

### Cell 和 RefCell

```rust
// ✅ Cell 用于 Copy 类型
use std::cell::Cell;

let counter = Cell::new(0);
counter.set(counter.get() + 1);
println!("Count: {}", counter.get());

// ✅ RefCell 用于运行时借用检查
use std::cell::RefCell;

let data = RefCell::new(vec![1, 2, 3]);

// 可变借用
*data.borrow_mut() += 4;

// 不可变借用
let borrowed = data.borrow();
println!("Data: {:?}", borrowed);
```

## Cow（Clone on Write）

### 使用 Cow 避免克隆

```rust
// ✅ Cow 用于避免不必要的克隆
use std::borrow::Cow;

fn process(s: Cow<str>) {
    // 根据需要决定是否克隆
}

// ✅ 返回 Cow
fn get_cow(borrowed: &str, owned: String) -> Cow<str> {
    if borrowed.is_empty() {
        Cow::Owned(owned)
    } else {
        Cow::Borrowed(borrowed)
    }
}
```

## 内存布局

### 结构体布局

```rust
// ✅ 默认布局（可能有填充）
struct DefaultLayout {
    a: u8,
    b: u32,
    c: u8,
}

// ✅ 重新排序以减少填充
struct OptimizedLayout {
    b: u32,
    a: u8,
    c: u8,
}

// ✅ 使用 repr(C) 控制布局
#[repr(C)]
struct CLayout {
    a: u8,
    b: u32,
    c: u8,
}

// ✅ 使用 repr(packed) 去除填充
#[repr(packed)]
struct Packed {
    a: u8,
    b: u32,
}
```

## 内存优化

### 避免分配

```rust
// ✅ 使用迭代器避免临时分配
let sum: i32 = data.iter().map(|x| x.value).sum();

// ✅ 重用缓冲区
let mut buffer = Vec::with_capacity(1024);
for _ in 0..100 {
    buffer.clear();
    // 使用 buffer
}

// ✅ 使用 SmallVec
use smallvec::SmallVec;

let vec: SmallVec<[i32; 4]> = SmallVec::new();
vec.push(1);
vec.push(2);
```

## 检查清单

- [ ] 理解数据分配位置
- [ ] 避免不必要的克隆
- [ ] 使用智能指针正确
- [ ] 使用 Cow 避免克隆
- [ ] 理解结构体内存布局
- [ ] 使用 repr 属性控制布局
