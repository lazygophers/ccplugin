---
description: "C语言嵌入式开发规范，涵盖硬件寄存器操作（volatile/MMIO）、中断处理（ISR）、MISRA C 2023合规、静态分配策略、固件尺寸与执行速度优化。适用于MCU固件开发、驱动编写、资源受限环境。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C 嵌入式开发规范

## 适用 Agents
- **dev** - 嵌入式固件开发
- **debug** - 硬件寄存器和中断调试
- **perf** - 固件大小和执行速度优化

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(c:core) | C11/C17 标准、编码约定 |
| 内存管理 | Skills(c:memory) | 内存池、静态分配 |
| 并发编程 | Skills(c:concurrency) | 原子操作、中断安全 |
| 错误处理 | Skills(c:error) | 嵌入式错误处理策略 |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "不需要 volatile" | 变量是否被 ISR 或硬件修改？ |
| "malloc 在嵌入式可以用" | 是否有动态分配的替代方案？ |
| "ISR 里可以做复杂操作" | ISR 是否尽快退出？ |
| "不需要 MISRA 检查" | 项目是否有安全认证要求？ |
| "浮点运算没问题" | 目标 MCU 是否有 FPU？ |
| "全局变量很方便" | 是否需要限制作用域？ |

## MISRA C 2023 关键规则

| 规则 | 说明 | 级别 |
|------|------|------|
| Dir 4.1 | 运行时故障应最小化 | 必须 |
| Rule 1.3 | 无未定义行为 | 必须 |
| Rule 2.2 | 无死代码 | 必须 |
| Rule 10.3 | 赋值不隐式窄化 | 必须 |
| Rule 11.3 | 指针转换不改变对象类型 | 必须 |
| Rule 17.7 | 函数返回值不可忽略 | 必须 |
| Rule 21.3 | 不使用 malloc/free | 必须 |
| Rule 21.6 | 不使用 stdio.h | 建议 |

## 寄存器操作

### 内存映射 I/O（volatile 必须）
```c
// 结构体映射（推荐方式）
typedef struct {
    volatile uint32_t CR;      // 控制寄存器
    volatile uint32_t SR;      // 状态寄存器
    volatile uint32_t DR;      // 数据寄存器
    uint32_t RESERVED[1];      // 保留
    volatile uint32_t BRR;     // 波特率寄存器
} UART_TypeDef;

#define UART1 ((UART_TypeDef*)0x40011000U)

// 位操作宏（类型安全）
#define BIT_SET(reg, bit)     ((reg) |= (1U << (bit)))
#define BIT_CLEAR(reg, bit)   ((reg) &= ~(1U << (bit)))
#define BIT_READ(reg, bit)    (((reg) >> (bit)) & 1U)
#define BITS_SET(reg, mask)   ((reg) |= (mask))
#define BITS_CLEAR(reg, mask) ((reg) &= ~(mask))

// 使用
BIT_SET(UART1->CR, 13);     // 使能 UART
while (!BIT_READ(UART1->SR, 6)) { }  // 等待发送完成
UART1->DR = data;
```

## 中断处理

### ISR 规范
```c
// ISR 规则：快进快出，只设 flag，主循环处理
static volatile bool uart_rx_ready = false;
static volatile uint8_t uart_rx_byte;

void UART1_IRQHandler(void) {
    if (UART1->SR & (1U << 5)) {        // RXNE 标志
        uart_rx_byte = (uint8_t)UART1->DR;  // 读取清除标志
        uart_rx_ready = true;
    }
}

// 主循环处理
int main(void) {
    while (1) {
        if (uart_rx_ready) {
            uart_rx_ready = false;
            process_byte(uart_rx_byte);
        }
        __asm__ volatile("wfi");  // 低功耗等待中断
    }
}

// 临界区保护
static inline uint32_t disable_irq(void) {
    uint32_t primask;
    __asm__ volatile("mrs %0, primask\n\tcpsid i" : "=r"(primask));
    return primask;
}

static inline void restore_irq(uint32_t primask) {
    __asm__ volatile("msr primask, %0" :: "r"(primask));
}

// 使用
uint32_t saved = disable_irq();
// 临界区操作
restore_irq(saved);
```

## 静态分配策略（禁止 malloc）

```c
// 静态缓冲池
#define BUFFER_POOL_SIZE 8
#define BUFFER_SIZE 128

static uint8_t buffer_pool[BUFFER_POOL_SIZE][BUFFER_SIZE];
static bool buffer_used[BUFFER_POOL_SIZE] = {false};

uint8_t* buffer_alloc(void) {
    for (int i = 0; i < BUFFER_POOL_SIZE; i++) {
        if (!buffer_used[i]) {
            buffer_used[i] = true;
            return buffer_pool[i];
        }
    }
    return NULL;  // 池耗尽
}

void buffer_free(uint8_t* buf) {
    for (int i = 0; i < BUFFER_POOL_SIZE; i++) {
        if (buffer_pool[i] == buf) {
            buffer_used[i] = false;
            return;
        }
    }
}
```

## 资源约束优化

### ROM 优化
```c
// const 数据放入 Flash
const uint8_t lookup_table[256] = { /* ... */ };

// 编译器特定的 Flash 段
__attribute__((section(".rodata")))
const char version_string[] = "v1.0.0";
```

### RAM 优化
```c
// 位域压缩
struct DeviceFlags {
    unsigned enabled   : 1;
    unsigned mode      : 3;
    unsigned error     : 1;
    unsigned ready     : 1;
    unsigned reserved  : 2;
};
static_assert(sizeof(struct DeviceFlags) == 1, "flags must be 1 byte");

// 联合体复用内存
union MessageBuffer {
    struct { uint16_t id; uint8_t data[6]; } can_frame;
    struct { uint8_t addr; uint8_t reg; uint16_t value; } i2c_msg;
    uint8_t raw[8];
};
```

### 栈优化
```c
// 避免递归，使用迭代
// 大数组使用 static（不在栈上）
void process(void) {
    static uint8_t large_buffer[1024];  // static，不占栈空间
    // ...
}
```

## volatile 正确性

```c
// 必须 volatile 的场景：
// 1. 硬件寄存器
volatile uint32_t* const REG = (volatile uint32_t*)0x40000000;

// 2. ISR 与主循环共享变量
static volatile bool flag = false;

// 3. 信号处理器共享变量
static volatile sig_atomic_t signal_flag = 0;

// 不需要 volatile 的场景：
// - 仅在一个线程访问的变量
// - 使用 _Atomic 的变量（_Atomic 已包含所需语义）
```

## 检查清单

- [ ] 硬件寄存器使用 volatile
- [ ] ISR 快进快出，仅设置 flag
- [ ] ISR 与主循环共享变量使用 volatile
- [ ] 临界区正确保护（disable/restore IRQ）
- [ ] 无动态内存分配（malloc/free）
- [ ] 使用位域/联合体优化 RAM
- [ ] const 数据放入 Flash
- [ ] 无递归，栈使用可分析
- [ ] MISRA C 2023 关键规则合规
- [ ] 编译时启用 -Wconversion -Wsign-conversion
