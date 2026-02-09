# 嵌入式开发

## 寄存器操作

### 内存映射 I/O

```c
// ✅ volatile 防止编译器优化
#define REG_STATUS  (*(volatile uint32_t*)(0x40000000))
#define REG_DATA    (*(volatile uint32_t*)(0x40000004))
#define REG_CONTROL (*(volatile uint32_t*)(0x40000008))

// 读取寄存器
uint32_t status = REG_STATUS;

// 写入寄存器
REG_DATA = 0x12345678;

// 位操作
#define BIT_SET(reg, bit)     ((reg) |= (1U << (bit)))
#define BIT_CLEAR(reg, bit)   ((reg) &= ~(1U << (bit)))
#define BIT_TOGGLE(reg, bit)  ((reg) ^= (1U << (bit)))
#define BIT_READ(reg, bit)    (((reg) >> (bit)) & 1U)

// 使用
BIT_SET(REG_CONTROL, 5);
if (BIT_READ(REG_STATUS, 3)) {
    // 处理
}
```

### 结构体映射

```c
// ✅ 内存映射结构体
typedef struct {
    volatile uint32_t CR;     // Control register
    volatile uint32_t SR;     // Status register
    volatile uint32_t DR;     // Data register
    uint8_t RESERVED[4];      // 对齐填充
    volatile uint32_t FR;     // Flag register
} UART_TypeDef;

#define UART1 ((UART_TypeDef*)0x40011000)

// 使用
UART1->CR = 0x01;  // 使能 UART
while (!(UART1->SR & (1 << 6))) {  // 等待 TXE
    // 等待
}
UART1->DR = data;  // 发送数据
```

## 中断处理

### ISR 实现

```c
// ✅ 中断服务程序
void __attribute__((interrupt)) UART1_Handler(void)
{
    volatile uint32_t status = UART1->SR;

    if (status & (1 << 5)) {  // RXNE - 接收中断
        uint8_t data = UART1->DR;
        // 处理接收数据
        process_rx_data(data);
    }

    if (status & (1 << 7)) {  // TXE - 发送中断
        // 发送下一个字节
        if (tx_buffer_has_data()) {
            UART1->DR = tx_buffer_get();
        }
    }
}

// ✅ 简单的 ISR（无属性）
void TIM2_IRQHandler(void)
{
    if (TIM2->SR & TIM_SR_UIF) {
        TIM2->SR &= ~TIM_SR_UIF;  // 清除中断标志
        // 处理定时器中断
        timer_callback();
    }
}
```

### 上下文保存

```c
// ✅ 保存/恢复上下文
typedef struct {
    uint32_t r0, r1, r2, r3, r4, r5, r6, r7;
    uint32_t r8, r9, r10, r11, r12;
    uint32_t sp, lr, pc, psr;
} ContextFrame;

void save_context(ContextFrame* frame) {
    __asm__ volatile (
        "mrs r0, psp\n"
        "stmia r0!, {r4-r11}\n"
        "msr psp, r0\n"
    );
}
```

## 资源约束优化

### ROM 优化

```c
// ✅ 将常量放入 ROM（Flash）
const uint8_t lookup_table[256] = { /* ... */ };

// ✅ 使用 PROGMEM（AVR）
#include <avr/pgmspace.h>

const uint8_t data[] PROGMEM = {0x01, 0x02, 0x03};

uint8_t read_data(uint8_t index) {
    return pgm_read_byte(&data[index]);
}

// ✅ 字符串放入 ROM
const char message[] PROGMEM = "Hello, World!";
```

### RAM 优化

```c
// ✅ 使用位域节省空间
struct Flags {
    unsigned flag1 : 1;
    unsigned flag2 : 1;
    unsigned flag3 : 1;
    unsigned flag4 : 1;
    unsigned reserved : 4;
};

// ✅ 联合体节省空间
union Data {
    uint8_t bytes[4];
    uint32_t word;
    struct {
        uint16_t low;
        uint16_t high;
    };
};

// ✅ 栈优化
// - 减少局部变量大小
// - 减少函数调用深度
// - 使用 static 替代大型栈变量
void process_large_data(void) {
    static uint8_t buffer[1024];  // 静态分配
    // 使用 buffer
}
```

## 延时和定时

### 精确延时

```c
// ✅ 基于系统时钟的延时
void delay_ms(uint32_t ms) {
    uint32_t start = get_system_ticks();
    while ((get_system_ticks() - start) < ms) {
        // 等待
    }
}

// ✅ 忙等待（短延时）
static inline void delay_cycles(uint32_t cycles) {
    while (cycles--) {
        __asm__ volatile ("nop");
    }
}

// ✅ 使用定时器（长延时）
void timer_start(uint32_t ms);
bool timer_expired(void);

void delay_timer_ms(uint32_t ms) {
    timer_start(ms);
    while (!timer_expired()) {
        // 可以执行其他任务
        __asm__ volatile ("wfi");  // 等待中断（ARM）
    }
}
```

---

**最后更新**：2026-02-09
