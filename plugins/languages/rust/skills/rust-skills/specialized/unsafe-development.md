# Rust Unsafe 开发规范

## 核心原则

### ✅ 必须遵守

1. **最小化 unsafe** - 尽可能避免 unsafe 代码
2. **隔离 unsafe** - 将 unsafe 代码封装在安全的抽象中
3. **文档说明** - 每个 unsafe 块必须有注释说明
4. **使用 miri** - 使用 miri 检测未定义行为
5. **审查** - unsafe 代码需要仔细审查

### 允许的 Unsafe 操作

- 解引用裸指针
- 调用 unsafe 函数
- 实现 unsafe trait
- 访问可变静态变量
- 访问 union 字段

## 裸指针

### 裸指针操作

```rust
// ✅ 创建裸指针
let x = 42;
let raw = &x as *const i32;

// ✅ 解引用裸指针（unsafe 块）
unsafe {
    println!("Value: {}", *raw);
}

// ✅ 可变裸指针
let mut x = 42;
let raw_mut = &mut x as *mut i32;

unsafe {
    *raw_mut = 100;
}

// ✅ 裸指针偏移
let slice = &[1, 2, 3, 4, 5];
let raw = slice.as_ptr();

unsafe {
    let second = raw.add(1);
    println!("Second: {}", *second);
}

// ❌ 避免：未对齐的解引用
#[repr(packed)]
struct Packed {
    a: u8,
    b: u32,
}

let packed = Packed { a: 1, b: 2 };
let raw = &packed.b as *const u32;

// 这可能未对齐，需要检查对齐
unsafe {
    if raw as usize % std::mem::align_of::<u32>() == 0 {
        println!("Value: {}", *raw);
    }
}
```

## 裸指针迭代器

### 自定义迭代器

```rust
// ✅ 使用裸指针实现迭代器
struct RawPtrIter<'a, T> {
    start: *const T,
    end: *const T,
    _marker: std::marker::PhantomData<&'a T>,
}

impl<'a, T> RawPtrIter<'a, T> {
    fn new(slice: &'a [T]) -> Self {
        let start = slice.as_ptr();
        let end = unsafe { start.add(slice.len()) };
        Self {
            start,
            end,
            _marker: std::marker::PhantomData,
        }
    }
}

// 安全的迭代器实现
unsafe impl<'a, T: Send> Send for RawPtrIter<'a, T> {}
unsafe impl<'a, T: Sync> Sync for RawPtrIter<'a, T> {}

impl<'a, T> Iterator for RawPtrIter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        if self.start == self.end {
            None
        } else {
            unsafe {
                let item = &*self.start;
                self.start = self.start.add(1);
                Some(item)
            }
        }
    }
}
```

## FFI

### C 互操作

```rust
// ✅ 声明外部 C 函数
extern "C" {
    // C 函数声明
    fn strlen(s: *const c_char) -> size_t;
    fn malloc(size: size_t) -> *mut c_void;
    fn free(ptr: *mut c_void);
}

// ✅ 安全包装
pub fn safe_strlen(s: &str) -> size_t {
    let c_string = std::ffi::CString::new(s).unwrap();
    unsafe {
        strlen(c_string.as_ptr())
    }
}

// ✅ 导出 Rust 函数给 C
#[no_mangle]
pub extern "C" fn double_input(input: i32) -> i32 {
    input * 2
}
```

## 可变静态变量

### 静态变量访问

```rust
// ✅ 可变静态变量
static mut COUNTER: u64 = 0;

// ✅ 使用 Mutex 保护可变静态变量
use std::sync::Mutex;

static COUNTER: Mutex<u64> = Mutex::new(0);

pub fn increment() -> u64 {
    let mut counter = COUNTER.lock().unwrap();
    *counter += 1;
    *counter
}

// ✅ 使用原子类型
use std::sync::atomic::{AtomicU64, Ordering};

static COUNTER: AtomicU64 = AtomicU64::new(0);

pub fn increment() -> u64 {
    COUNTER.fetch_add(1, Ordering::SeqCst)
}
```

## Union 访问

### Union 字段访问

```rust
// ✅ 定义 union
union MyUnion {
    f: f32,
    i: u32,
}

// ✅ 访问 union 字段
fn float_to_bits(value: f32) -> u32 {
    let mut u = MyUnion { f: value };
    unsafe { u.i }
}
```

## 未初始化内存

### 使用 MaybeUninit

```rust
// ✅ 使用 MaybeUninit
use std::mem::MaybeUninit;

fn create_vec() -> Vec<i32> {
    let mut data = MaybeUninit::<Vec<i32>>::uninit();

    unsafe {
        // 写入值
        data.write(vec![1, 2, 3, 4, 5]);

        // 假设已初始化
        data.assume_init()
    }
}

// ✅ 数组初始化
fn create_array() -> [i32; 1000] {
    let mut data = MaybeUninit::<[i32; 1000]>::uninit();

    unsafe {
        // 逐个初始化
        let ptr = data.as_mut_ptr() as *mut i32;
        for i in 0..1000 {
            ptr.add(i).write(i as i32);
        }

        // 假设已初始化
        data.assume_init()
    }
}
```

## 内联汇编

### asm! 宏

```rust
// ✅ 内联汇编（nightly）
#[cfg(target_arch = "x86_64")]
fn add_with_asm(a: u64, b: u64) -> u64 {
    unsafe {
        let result: u64;
        std::arch::asm!(
            "add {}, {}, {}",
            out(reg) result,
            in(reg) a,
            in(reg) b,
        );
        result
    }
}
```

## Miri 检测

### 使用 Miri

```bash
# ✅ 使用 miri 检测未定义行为
cargo miri test

# ✅ 使用 miri 运行特定测试
cargo miri test test_name

# ✅ 使用 miri 运行示例
cargo miri run --example example_name
```

## 最佳实践

### 封装 Unsafe

```rust
// ✅ 将 unsafe 封装在安全的 API 中
pub struct SafeVec(Vec<i32>);

impl SafeVec {
    pub fn new() -> Self {
        Self(Vec::new())
    }

    pub fn push(&mut self, value: i32) {
        self.0.push(value);
    }

    pub fn get(&self, index: usize) -> Option<&i32> {
        self.0.get(index)
    }

    // 安全地使用 unsafe
    pub fn as_ptr(&self) -> *const i32 {
        self.0.as_ptr()
    }
}

// ✅ 文档说明 unsafe 的安全性保证
///
/// # Safety
///
/// 调用者必须确保：
/// - `ptr` 不是 null
/// - `ptr` 已正确对齐
/// - `ptr` 指向有效内存
/// - 内存至少包含 `len` 个元素
unsafe fn safe_function(ptr: *const i32, len: usize) -> i32 {
    // unsafe 操作，但已文档化前提条件
    *ptr
}
```

## 检查清单

- [ ] 每个 unsafe 块有注释说明
- [ ] unsafe 代码封装在安全抽象中
- [ ] 使用 miri 检测未定义行为
- [ ] 文档说明安全性前提条件
- [ ] 审查 unsafe 代码
