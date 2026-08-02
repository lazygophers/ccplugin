---
title: mypy-patterns
category: build
keywords: [mixin,type-checking,TYPE_CHECKING,protocol,属性声明,type-ignore,unused-ignore,错误收敛]
status: active
inclusion: auto
---

## Mixin 跨引用的类型错误 — TYPE_CHECKING 属性声明块

### 触发场景
把大类拆成 Mixin 组合后，Mixin 中的方法引用由最终组合类持有的属性。

### 陷阱-正解
**陷阱**：Mixin 里的方法引用由最终类持有的属性，类型检查器看单个 Mixin 时看不到这些属性，报「没有某某属性」。

**正解**：在 Mixin 类体首行加 `if TYPE_CHECKING:` 块，声明它引用的兄弟属性与方法，签名照抄真实实现处。

**禁用 Protocol 继承** —— Mixin 继承 Protocol 会把 stub 方法塞进最终类的 MRO，若排在真实实现前面会在运行时把真方法遮蔽掉，改变运行时行为。`TYPE_CHECKING` 块是恒 False 的死分支，零运行时代价。

### 铁律
- MUST：Mixin 引用属性时，在类体首行声明 `if TYPE_CHECKING:` 块
- MUST：块内声明兄弟属性与方法的类型签名
- MUST：禁 Mixin 继承 Protocol（会遮蔽真方法）

### 反例表
| 禁 | 改为 |
|---|---|
| Mixin 直接引用属性无声明 | Mixin 首行加 `if TYPE_CHECKING:` 块声明兄弟属性 |
| Mixin 继承 Protocol 提供类型 | 去掉 Protocol 继承，仅 `TYPE_CHECKING` 块声明 |
| Sibling mixin 互相依赖抽象基类 | 各 mixin `if TYPE_CHECKING:` 块独立声明所需属性 |

## `type: ignore` 注释语法

### 触发场景
需要抑制 mypy 对某个表达式的类型检查报错。

### 陷阱-正解
**陷阱**：`# type: ignore[code]  自由文本` 单 `#` 是非法语法，mypy 会报 `[syntax]` 并吞掉本该拦下的真错误码（虚假通过）。

**正解**：注释必须写成 `# type: ignore[code]  # 自由文本`（双 `#` 分隔）。ignore 后跟的是错误码，然后新行或双 `#` 开始解释。

### 铁律
- MUST：`# type: ignore[code]` 后若跟自由文本说明，必须用 `#` 再分隔
- MUST：格式：`# type: ignore[code]  # 说明文本` 或单行 `# type: ignore[code]`
- MUST：禁单 `#` 后直接跟文本（`# type: ignore[code]  文本`）

### 反例表
| 禁 | 改为 |
|---|---|
| `# type: ignore[attr-defined]  mypy 误判` | `# type: ignore[attr-defined]  # mypy 误判` |
| 无错误码的通用 ignore | `# type: ignore[specific-code]` |

## `unused-ignore` 处理

### 触发场景
依赖升级后（如 pytest 带上 stub）或重构后，旧的 `type: ignore` 压制变多余，strict 模式报 `[unused-ignore]`。

### 陷阱-正解
**陷阱**：在旧的 ignore 旁边再加新的 ignore 来压制 `unused-ignore`。

**正解**：删掉那条已失效的 ignore。`unused-ignore` 是提示你清理过时的压制，不是让你再压一层。

### 铁律
- MUST：`unused-ignore` 报错时删掉那条无效的 ignore
- MUST：禁用新的 ignore 来压制 `unused-ignore`

### 反例表
| 禁 | 改为 |
|---|---|
| 在 `# type: ignore` 上再加 `# type: ignore[unused-ignore]` | 删掉原来的 `# type: ignore` |
| 保留过时的压制 | 清理已失效的 ignore 行 |

## 收敛类型错误的判别方法

### 触发场景
大量 mypy strict 错误需要逐条判是「真 bug」还是「类型检查器的视角局限」。

### 陷阱-正解
**陷阱**：噪声太多时淹没真问题；不判就一股脑改，改错方向。

**正解**：逐条判「是类型检查器的视角局限，还是真 bug」。常见三种模式与解法：
- (a) `.get()` 无默认值导致推出 Optional → 补默认值或显式类型注解
- (b) 对**表达式**而非变量做 `isinstance`，mypy 无法跨重复求值窄化 → 先绑局部变量再判
- (c) 同一函数作用域内变量名复用装了两种类型（运行时分支互斥） → 改名或类型注解

### 价值
噪声清干净后，真正的类型 bug 才浮得出来。大量同模式噪声会淹没真问题。

### 铁律
- MUST：逐条判错误是视角局限还是真 bug
- MUST：`.get()` 补默认值而非忽略；`isinstance` 绑变量而非表达式直判
- MUST：变量名复用需改名或注解，不能忽略

### 反例表
| 禁 | 改为 |
|---|---|
| `.get()` 直接 `# type: ignore` | `.get(default=...)` 或 `x: T \| None = ...` 显式注解 |
| `isinstance(expr, T)` 直接窄化 | `x = expr; if isinstance(x, T):` 先绑变量 |
| 变量重复装不同类型无注解 | 改变量名或加类型注解保持一致 |
