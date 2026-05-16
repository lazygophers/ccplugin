---
name: rust-unsafe
description: Rust unsafe 代码规范 — unsafe 最小化、五种超能力（裸指针 / unsafe fn / static mut / unsafe impl / union）、`// SAFETY:` 注释强制、`# Safety` 文档、安全 API 封装、FFI / CString / CStr / extern "C"、MIRI 验证、bytemuck / OnceLock / LazyLock 安全替代、UB（未定义行为）排查。编写 unsafe 块、调用 C 库、实现底层数据结构、排查未定义行为时加载。触发短语：unsafe、裸指针、FFI、extern C、transmute、UB、undefined behavior、MIRI、static mut。
user-invocable: true
---

# Rust Unsafe 规范

前置：`rust-core`、`rust-memory`。

## 核心铁律

1. **找安全替代**：unsafe 永远是最后手段。
2. **最小化 unsafe 块**：每个 `unsafe { ... }` 只包含必须 unsafe 的语句。
3. **安全 API 封装**：unsafe 内部实现，公共 API 必须安全。
4. **强制 SAFETY 注释**：每个 unsafe 块前 `// SAFETY: <为什么这里安全、调用者保证什么、维护什么不变量>`。
5. **MIRI 全覆盖**：CI 中跑 `cargo +nightly miri test`。

## 五种 unsafe 超能力

```rust
// 1. 解引用裸指针
let p = &42 as *const i32;
// SAFETY: p 指向栈上有效 i32，作用域内未被释放
let v = unsafe { *p };

// 2. 调用 unsafe fn
// SAFETY: src/dst 各有至少 len 个元素，且区间不重叠
unsafe { std::ptr::copy_nonoverlapping(src, dst, len); }

// 3. 访问 / 修改 static mut（强烈不推荐）
static mut COUNTER: u64 = 0;
// SAFETY: 单线程访问，无数据竞争 —— 但建议改用 OnceLock / AtomicU64

// 4. 实现 unsafe trait
// SAFETY: 所有字段均 Send，无内部可变性陷阱
unsafe impl Send for MyType {}

// 5. 读取 union 字段
union FloatBits { f: f32, i: u32 }
let fb = FloatBits { f: 1.0 };
// SAFETY: f32 与 u32 同大小同对齐，IEEE 754 位重解释 well-defined
let bits = unsafe { fb.i };
```

## SAFETY 注释规范

```rust
/// 从原始部件构造 Vec。
///
/// # Safety
///
/// - `ptr` 必须由 `Vec::into_raw_parts` 获得；
/// - 分配器为全局分配器；
/// - `length <= capacity`；
/// - 前 `length` 个元素已初始化。
pub unsafe fn from_raw_parts<T>(ptr: *mut T, length: usize, capacity: usize) -> Vec<T> {
    // SAFETY: 调用者保证以上前置条件
    unsafe { Vec::from_raw_parts(ptr, length, capacity) }
}
```

## FFI 模板

```rust
use std::ffi::{c_char, CStr, CString};

extern "C" {
    fn strlen(s: *const c_char) -> usize;
}

pub fn safe_strlen(s: &CStr) -> usize {
    // SAFETY: CStr 保证 nul-terminated；strlen 仅只读访问
    unsafe { strlen(s.as_ptr()) }
}

#[unsafe(no_mangle)]                  // Edition 2024 起 no_mangle 需 unsafe 属性
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 { a + b }
```

注意 Edition 2024 起 `#[no_mangle]` / `#[export_name]` / `#[link_section]` 需写成 `#[unsafe(...)]`。

## 安全替代速查

| unsafe 场景 | 安全替代 |
|------------|---------|
| `static mut` 全局 | `OnceLock` / `LazyLock` / `AtomicXxx` |
| `transmute` 字节重解释 | `bytemuck::cast` / `from_ne_bytes` |
| 手动分配 | `Vec` / `Box` / `bumpalo` |
| 共享可变 | `Mutex` / `RwLock` / channel |
| 越界访问 | `slice.get` |
| 字符串转换 | `CString::new` / `CStr::from_bytes_with_nul` |

```rust
use std::sync::OnceLock;
static CONFIG: OnceLock<Config> = OnceLock::new();
fn config() -> &'static Config { CONFIG.get_or_init(load_config) }

use bytemuck::{Pod, Zeroable};
#[derive(Copy, Clone, Pod, Zeroable)] #[repr(C)]
struct Color { r: u8, g: u8, b: u8, a: u8 }
let c: Color = bytemuck::cast([255u8, 0, 0, 255]);
```

## MIRI 验证

```bash
rustup +nightly component add miri
cargo +nightly miri test
MIRIFLAGS="-Zmiri-disable-isolation" cargo +nightly miri test   # 文件 IO
```

CI step 模板：

```yaml
- run: rustup toolchain install nightly --component miri
- run: cargo +nightly miri test --workspace
```

## 反模式

| AI 倾向 | 正确做法 |
|---------|---------|
| `unsafe` 提性能 | 先 benchmark 证明热点 |
| `transmute` 强转 | `bytemuck` / `From`/`Into` |
| `static mut` 共享 | `OnceLock` / `AtomicXxx` |
| 无 SAFETY 注释 | 必须写明前置条件 |
| FFI 直接暴露 | 封装为安全 API |
| 无 MIRI | CI 加 miri 步骤 |

## 检查清单

- [ ] 已确认无安全替代
- [ ] 每个 `unsafe` 块前有 `// SAFETY:` 注释
- [ ] 每个 `unsafe fn` 有 `# Safety` 文档
- [ ] 公共 API 全部安全
- [ ] `cargo +nightly miri test` 通过
- [ ] Edition 2024 的 `#[unsafe(no_mangle)]` 等已迁移
- [ ] FFI 使用 `CString` / `CStr` 正确转换
