// Swift 测试文件

// 类定义
class Person {
    var name: String
    var age: Int

    init(name: String, age: Int) {
        self.name = name
        self.age = age
    }

    func greet() -> String {
        return "Hello, I'm \(name)"
    }
}

// 结构体定义
struct Point {
    var x: Int
    var y: Int

    func distance() -> Int {
        return x * x + y * y
    }
}

// 枚举定义
enum Color {
    case red
    case green
    case blue
}

// Protocol 定义
protocol Drawable {
    func draw()
}

// Extension 定义
extension Int {
    var isEven: Bool {
        return self % 2 == 0
    }
}

// 函数定义
func calculateSum(_ a: Int, _ b: Int) -> Int {
    return a + b
}

// 执行代码
let person = Person(name: "Alice", age: 30)
print(person.greet())

let sum = calculateSum(5, 3)
print("Sum: \(sum)")

print(10.isEven)
