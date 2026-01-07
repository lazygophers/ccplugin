// 结构体定义
struct Point {
    x: i32,
    y: i32,
}

// Trait 定义
trait Shape {
    fn area(&self) -> i32;
}

// Impl 块
impl Point {
    fn new(x: i32, y: i32) -> Self {
        Point { x, y }
    }
}

impl Shape for Point {
    fn area(&self) -> i32 {
        self.x * self.y
    }
}

// 函数定义
fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}

// Module 定义
mod utils {
    pub fn helper() -> i32 {
        42
    }
}

fn main() {
    let p = Point::new(10, 20);
    println!("Area: {}", p.area());
}
