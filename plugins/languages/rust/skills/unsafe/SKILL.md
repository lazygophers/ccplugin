---
description: Rust Unsafe 规范 - 最小化 unsafe、MIRI 验证、FFI、safety comments。写 unsafe 代码或 FFI 时加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Rust Unsafe 规范

## 适用 Agents

- **rust:dev** - 必要时的 unsafe 代码编写
- **rust:debug** - unsafe 相关 bug 调试

## 相关 Skills

- **Skills(rust:core)** - 错误处理、工具链
- **Skills(rust:memory)** - 内存布局、裸指针

## 核心原则：最小化 unsafe

1. **优先寻找安全替代**：unsafe 是最后手段
2. **最小化 unsafe 块**：只包含必须 unsafe 的操作
3. **封装为安全 API**：unsafe 内部实现，对外暴露安全接口
4. **强制 safety comments**：每个 unsafe 块必须有 `// SAFETY:` 注释

## unsafe 的五种超能力

```rust
// 1. 解引用裸指针
let ptr = &42 as *const i32;
// SAFETY: ptr 指向有效的 i32 值，且在当前作用域内有效
let value = unsafe { *ptr };

// 2. 调用 unsafe 函数
// SAFETY: slice 的长度 >= offset + len，不存在别名引用
unsafe { std::ptr::copy_nonoverlapping(src, dst, len); }

// 3. 访问/修改可变静态变量
static mut COUNTER: u64 = 0;
// SAFETY: 单线程访问，无数据竞争
unsafe { COUNTER += 1; }

// 4. 实现 unsafe trait
// SAFETY: MyType 的所有字段都是 Send，可以安全跨线程传递
unsafe impl Send for MyType {}

// 5. 访问 union 字段
union FloatInt {
    f: f32,
    i: u32,
}
let fi = FloatInt { f: 1.0 };
// SAFETY: f32 和 u32 大小相同，读取 i 字段是有效的位重解释
let bits = unsafe { fi.i };
```

## Safety Comments 规范

```rust
// 每个 unsafe 块必须有 SAFETY 注释，说明：
// 1. 为什么这个操作是安全的
// 2. 调用者需要保证什么前置条件
// 3. 维护什么不变量

/// 从原始部件构造 Vec。
///
/// # Safety
///
/// - `ptr` 必须是通过 `Vec::into_raw_parts` 获得的
/// - `ptr` 的分配器必须是全局分配器
/// - `length` 不能大于 `capacity`
/// - 前 `length` 个元素必须是已初始化的
pub unsafe fn from_raw_parts(ptr: *mut T, length: usize, capacity: usize) -> Vec<T> {
    // SAFETY: 调用者保证了所有前置条件
    unsafe { Vec::from_raw_parts(ptr, length, capacity) }
}
```

## FFI（外部函数接口）

```rust
// 声明外部 C 函数
extern "C" {
    fn strlen(s: *const std::ffi::c_char) -> usize;
    fn malloc(size: usize) -> *mut std::ffi::c_void;
    fn free(ptr: *mut std::ffi::c_void);
}

// 安全封装
pub fn safe_strlen(s: &std::ffi::CStr) -> usize {
    // SAFETY: CStr 保证以 null 结尾，strlen 只读访问
    unsafe { strlen(s.as_ptr()) }
}

// 导出 Rust 函数给 C
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

// CString / CStr 转换
use std::ffi::{CString, CStr};

fn call_c_api(name: &str) -> Result<(), std::ffi::NulError> {
    let c_name = CString::new(name)?;
    // SAFETY: c_name 有效且以 null 结尾
    unsafe { c_api_function(c_name.as_ptr()); }
    Ok(())
}
```

## MIRI 验证

```bash
# 安装 miri
rustup +nightly component add miri

# 运行全部测试
cargo +nightly miri test

# 运行特定测试
cargo +nightly miri test test_name

# 检查数据竞争（需要 -Zmiri-data-race-detector）
MIRIFLAGS="-Zmiri-disable-isolation" cargo +nightly miri test

# CI 集成
# - name: Miri
#   run: |
#     rustup toolchain install nightly --component miri
#     cargo +nightly miri test
```

## 常见安全替代方案

| unsafe 需求 | 安全替代 |
|------------|---------|
| 裸指针数组访问 | `slice.get(idx)` 或 `slice[idx]`（bounds check） |
| 类型转换 | `From`/`Into` trait |
| 位操作 | `u32::from_ne_bytes()` |
| 全局可变状态 | `OnceLock` / `LazyLock`（Rust 1.80+） |
| 手动内存管理 | `Vec`、`Box`、`Arena` |
| 共享可变状态 | `Mutex`、`RwLock`、channel |
| transmute | `bytemuck::cast()` |

```rust
// 避免 static mut，使用 OnceLock
use std::sync::OnceLock;
static CONFIG: OnceLock<Config> = OnceLock::new();
fn get_config() -> &'static Config {
    CONFIG.get_or_init(|| load_config())
}

// 避免 transmute，使用 bytemuck
use bytemuck::{Pod, Zeroable};
#[derive(Copy, Clone, Pod, Zeroable)]
#[repr(C)]
struct Color { r: u8, g: u8, b: u8, a: u8 }

let bytes: [u8; 4] = [255, 0, 0, 255];
let color: Color = bytemuck::cast(bytes);
```

## Red Flags：AI 常见误区

| AI 可能的解释 | 实际检查 |
|--------------|---------|
| "unsafe 更高效" | ✅ 安全代码是否已经足够快（编译器会优化）？ |
| "transmute 类型转换" | ✅ 是否可用 `From`/`Into` 或 `bytemuck`？ |
| "static mut 全局状态" | ✅ 是否可用 `OnceLock` / `LazyLock`？ |
| "这个 unsafe 很小" | ✅ 是否有 `// SAFETY:` 注释？ |
| "FFI 必须 unsafe" | ✅ 是否封装为安全 API？ |
| "miri 太慢了" | ✅ CI 中是否有 miri 检查？ |

## 检查清单

- [ ] 确认无安全替代方案后才使用 unsafe
- [ ] 每个 unsafe 块有 `// SAFETY:` 注释
- [ ] unsafe 函数有 `# Safety` 文档说明前置条件
- [ ] unsafe 封装为安全的公共 API
- [ ] `cargo +nightly miri test` 通过
- [ ] 使用 `OnceLock`/`LazyLock` 替代 `static mut`
- [ ] FFI 使用 `CString`/`CStr` 正确转换
- [ ] CI 包含 miri 检查步骤
