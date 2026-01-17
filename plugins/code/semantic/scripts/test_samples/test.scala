// Scala 测试文件

// 类定义
class Person(val name: String, val age: Int) {
    def greet(): String = {
        s"Hello, I'm $name"
    }
}

// Case class
case class Point(x: Int, y: Int)

// Object 定义（单例）
object Config {
    val version = "1.0.0"

    def getVersion(): String = {
        version
    }
}

// Trait 定义
trait Logger {
    def log(message: String): Unit = {
        println(s"[LOG] $message")
    }
}

// 继承 Trait 的类
class UserService extends Logger {
    def createUser(name: String): Person = {
        log(s"Creating user: $name")
        new Person(name, 25)
    }
}

// 函数定义
def calculateSum(a: Int, b: Int): Int = {
    a + b
}

// 执行代码
val person = new Person("Alice", 30)
println(person.greet())

val service = new UserService()
service.createUser("Bob")

println(s"Version: ${Config.getVersion()}")
