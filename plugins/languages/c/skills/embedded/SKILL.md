---
name: c-embedded
description: |
  C embedded firmware conventions: memory-mapped I/O with volatile structs, short ISR
  with main-loop hand-off, MISRA C:2023 (incl. AMD4 atomics/concurrency guidance)
  compliance, static-only allocation strategies (pools, bitfields, unions, static
  buffers), Flash/RAM/stack budgeting, and bare-metal critical-section primitives.
  Use when writing MCU firmware, drivers, RTOS tasks, or any resource-constrained C.
  Triggers on "MCU", "嵌入式 C", "ISR", "中断处理", "volatile 寄存器", "MISRA",
  "静态分配", "no malloc", "bare metal", "Cortex-M", "RTOS".
---

# C 嵌入式开发规范

## 强制约定

1. 禁用动态内存（`malloc / calloc / realloc / free`）；改用静态池 / 栈 / arena。
2. 硬件寄存器 / ISR ↔ 主流程共享变量 / 信号变量必须 `volatile`。
3. ISR 短小，仅置位 flag / 入队字节，重活在主循环。
4. 临界区用 `disable_irq / restore_irq` 显式保护；时间窗最小化。
5. 无递归；栈使用可在编译期分析（`-fstack-usage`）。
6. 浮点：先确认 MCU 是否有 FPU；无 FPU 用定点。
7. const 数据声明 `const`，链接器放入 Flash 段。
8. 安全 / 功能安全项目按 MISRA C:2023 合规检查。

## MISRA C:2023 关键 Rules（包含 AMD4 并发指南）

| 规则 | 说明 | 等级 |
|------|------|------|
| Dir 4.1 | 最小化运行时错误 | Mandatory |
| Rule 1.3 | 无未定义 / 关键未指定行为 | Required |
| Rule 2.2 | 无死代码 | Required |
| Rule 10.x | 类型转换必须显式且不窄化 | Required |
| Rule 11.3 | 指针类型转换不改变指向对象类型 | Required |
| Rule 17.7 | 非 void 返回值不可丢弃 | Required |
| Rule 21.3 | 不使用 `malloc / free` 等动态内存 | Required |
| Rule 21.6 | 不使用 `<stdio.h>` 标准 I/O | Advisory |
| AMD4 Rule 22.x | 原子 / 多线程使用规范（C11 `_Atomic`） | Required（启用后） |

工具链：Cppcheck `--addon=misra`、PC-lint Plus、Coverity、Polyspace、ECLAIR。

## 内存映射 I/O

```c
typedef struct {
    volatile uint32_t CR;
    volatile uint32_t SR;
    volatile uint32_t DR;
    uint32_t _rsv;
    volatile uint32_t BRR;
} UART_TypeDef;

#define UART1 ((UART_TypeDef *)0x40011000U)

#define BIT_SET(r, b)   ((r) |=  (1U << (b)))
#define BIT_CLR(r, b)   ((r) &= ~(1U << (b)))
#define BIT_GET(r, b)   (((r) >> (b)) & 1U)
```

## 中断服务程序 (ISR)

```c
static volatile bool    rx_ready;
static volatile uint8_t rx_byte;

void UART1_IRQHandler(void) {
    if (UART1->SR & (1U << 5)) {       // RXNE
        rx_byte  = (uint8_t)UART1->DR; // 读 DR 清 flag
        rx_ready = true;
    }
}

int main(void) {
    for (;;) {
        if (rx_ready) { rx_ready = false; on_byte(rx_byte); }
        __asm__ volatile ("wfi");
    }
}
```

### Cortex-M 临界区

```c
static inline uint32_t irq_save(void) {
    uint32_t p; __asm__ volatile ("mrs %0, primask\n\tcpsid i" : "=r"(p));
    return p;
}
static inline void irq_restore(uint32_t p) {
    __asm__ volatile ("msr primask, %0" :: "r"(p) : "memory");
}
```

C11 `_Atomic` 也可用于 ISR ↔ 主循环单字共享（按 MISRA AMD4 章节使用）。

## 静态分配模板

```c
#define POOL_N   8
#define BUF_SZ 128
static uint8_t pool[POOL_N][BUF_SZ];
static bool    used[POOL_N];

uint8_t *buf_alloc(void) {
    for (int i = 0; i < POOL_N; i++)
        if (!used[i]) { used[i] = true; return pool[i]; }
    return NULL;
}
void buf_free(uint8_t *p) {
    for (int i = 0; i < POOL_N; i++)
        if (pool[i] == p) { used[i] = false; return; }
}
```

## ROM / RAM / 栈预算

```c
// const 进 Flash
__attribute__((section(".rodata")))
static const uint8_t lut[256] = { /* ... */ };

// 位域压缩
struct Flags {
    unsigned enabled : 1;
    unsigned mode    : 3;
    unsigned error   : 1;
    unsigned ready   : 1;
    unsigned _rsv    : 2;
};
static_assert(sizeof(struct Flags) == 1, "1 byte");

// 联合体复用
union Msg {
    struct { uint16_t id; uint8_t d[6]; } can;
    struct { uint8_t a, r; uint16_t v; } i2c;
    uint8_t raw[8];
};

// 大缓冲区放 BSS，不占栈
void task(void) { static uint8_t big[1024]; /* ... */ }
```

工具：`-fstack-usage` + `arm-none-eabi-size`，对每个 ISR / 任务函数做最坏栈分析。

## volatile 适用边界

需要 `volatile`：
- 硬件寄存器指针 (`volatile uint32_t *const`)
- ISR ↔ 主流程共享单字变量
- `setjmp/longjmp` 间需保留的局部变量
- 信号处理器共享变量（`sig_atomic_t`）

不需要：
- 仅单线程访问的普通变量
- 已经用 `_Atomic` 的变量（语义重叠）

## 调试与构建

```bash
# 大小报告
arm-none-eabi-size -A -d build/firmware.elf

# 最坏栈
gcc -fstack-usage -c src/foo.c   # 产 src/foo.su

# 静态分析
cppcheck --addon=misra --std=c17 src/
```

## 检查清单

- [ ] 无 `malloc / free` / 动态分配
- [ ] 寄存器与 ISR 共享变量带 `volatile`
- [ ] ISR 短小，仅置位 / 入队
- [ ] 临界区显式保护，时间最短
- [ ] 无递归，栈使用已分析
- [ ] const 数据在 Flash 段
- [ ] 位域 / 联合体优化 RAM
- [ ] MISRA C:2023 关键规则零违例（项目要求时）
- [ ] `-Wconversion -Wsign-conversion -Wshadow` 通过

## 权威参考

- MISRA C:2023 + AMD1/AMD2/AMD3/AMD4 — <https://misra.org.uk/>
- ARM Cortex-M Programming — <https://developer.arm.com/documentation/dui0552/latest/>
- CMSIS — <https://arm-software.github.io/CMSIS_6/latest/General/index.html>
- Cppcheck MISRA addon — <https://cppcheck.sourceforge.io/misra.php>
- GCC `-fstack-usage` — <https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html>
