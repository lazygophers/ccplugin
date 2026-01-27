#include <stdio.h>

// 函数定义
int add(int a, int b) {
    return a + b;
}

// 结构体定义
struct Point {
    int x;
    int y;
};

// 枚举定义
enum Color {
    RED,
    GREEN,
    BLUE
};

// 主函数
int main() {
    struct Point p = {10, 20};
    enum Color c = RED;
    printf("Sum: %d\n", add(5, 3));
    return 0;
}
