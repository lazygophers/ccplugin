---
name: embedded
description: C 嵌入式开发规范：寄存器操作、中断处理、资源约束优化。嵌入式开发时必须加载。
---

# C 嵌入式开发规范

## 相关 Skills

| 场景     | Skill               | 说明                   |
| -------- | ------------------- | ---------------------- |
| 核心规范 | Skills(core)        | C11/C17 标准、强制约定 |
| 内存管理 | Skills(memory)      | 内存池、栈优化         |
| 并发编程 | Skills(concurrency) | 中断安全               |

## 寄存器操作

### 内存映射 I/O

```c
#define REG_STATUS  (*(volatile uint32_t*)(0x40000000))
#define REG_DATA    (*(volatile uint32_t*)(0x40000004))
#define REG_CONTROL (*(volatile uint32_t*)(0x40000008))

uint32_t status = REG_STATUS;
REG_DATA = 0x12345678;

#define BIT_SET(reg, bit)     ((reg) |= (1U << (bit)))
#define BIT_CLEAR(reg, bit)   ((reg) &= ~(1U << (bit)))
#define BIT_TOGGLE(reg, bit)  ((reg) ^= (1U << (bit)))
#define BIT_READ(reg, bit)    (((reg) >> (bit)) & 1U)

BIT_SET(REG_CONTROL, 5);
if (BIT_READ(REG_STATUS, 3)) {
}
```

### 结构体映射

```c
typedef struct {
    volatile uint32_t CR;
    volatile uint32_t SR;
    volatile uint32_t DR;
    uint8_t RESERVED[4];
    volatile uint32_t FR;
} UART_TypeDef;

#define UART1 ((UART_TypeDef*)0x40011000)

UART1->CR = 0x01;
while (!(UART1->SR & (1 << 6))) {
}
UART1->DR = data;
```

## 中断处理

### ISR 实现

```c
void __attribute__((interrupt)) UART1_Handler(void)
{
    volatile uint32_t status = UART1->SR;

    if (status & (1 << 5)) {
        uint8_t data = UART1->DR;
        process_rx_data(data);
    }

    if (status & (1 << 7)) {
        if (tx_buffer_has_data()) {
            UART1->DR = tx_buffer_get();
        }
    }
}

void TIM2_IRQHandler(void)
{
    if (TIM2->SR & TIM_SR_UIF) {
        TIM2->SR &= ~TIM_SR_UIF;
        timer_callback();
    }
}
```

## 资源约束优化

### ROM 优化

```c
const uint8_t lookup_table[256] = { };

#include <avr/pgmspace.h>
const uint8_t data[] PROGMEM = {0x01, 0x02, 0x03};

uint8_t read_data(uint8_t index) {
    return pgm_read_byte(&data[index]);
}
```

### RAM 优化

```c
struct Flags {
    unsigned flag1 : 1;
    unsigned flag2 : 1;
    unsigned flag3 : 1;
    unsigned flag4 : 1;
    unsigned reserved : 4;
};

union Data {
    uint8_t bytes[4];
    uint32_t word;
    struct {
        uint16_t low;
        uint16_t high;
    };
};

void process_large_data(void) {
    static uint8_t buffer[1024];
}
```

## 延时和定时

```c
void delay_ms(uint32_t ms) {
    uint32_t start = get_system_ticks();
    while ((get_system_ticks() - start) < ms) {
    }
}

static inline void delay_cycles(uint32_t cycles) {
    while (cycles--) {
        __asm__ volatile ("nop");
    }
}

void delay_timer_ms(uint32_t ms) {
    timer_start(ms);
    while (!timer_expired()) {
        __asm__ volatile ("wfi");
    }
}
```

## 检查清单

- [ ] 寄存器使用 volatile
- [ ] ISR 使用安全函数
- [ ] ROM 常量使用 const
- [ ] RAM 使用位域/联合体优化
- [ ] 大型变量使用 static
