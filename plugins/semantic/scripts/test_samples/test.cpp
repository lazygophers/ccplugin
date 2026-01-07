#include <iostream>
#include <vector>

// 命名空间定义
namespace Math {
    int add(int a, int b) {
        return a + b;
    }
}

// 类定义
class Rectangle {
private:
    int width;
    int height;

public:
    Rectangle(int w, int h) : width(w), height(h) {}

    int area() {
        return width * height;
    }
};

// 结构体定义
struct Point {
    int x;
    int y;

    Point(int x, int y) : x(x), y(y) {}
};

// 枚举定义
enum Color {
    RED,
    GREEN,
    BLUE
};

// 模板函数
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

int main() {
    Rectangle rect(5, 3);
    std::cout << "Area: " << rect.area() << std::endl;
    return 0;
}
