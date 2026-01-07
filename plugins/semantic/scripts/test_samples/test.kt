// 数据类
data class Person(val name: String, val age: Int)

// 接口
interface Greeter {
    fun greet()
}

// 类定义
class UserService : Greeter {
    override fun greet() {
        println("Hello from UserService")
    }

    fun createUser(name: String): Person {
        println("Creating user: $name")
        return Person(name, 25)
    }
}

// Object 定义（单例）
object Config {
    const val VERSION = "1.0.0"

    fun getVersion(): String {
        return VERSION
    }
}

// 函数定义
fun calculateSum(a: Int, b: Int): Int {
    return a + b
}

// 扩展函数
fun String.printWithPrefix() {
    println(">> $this")
}

fun main() {
    val person = Person("Alice", 30)
    println(person)

    val service = UserService()
    service.greet()

    println("Version: ${Config.getVersion()}")

    "Hello".printWithPrefix()
}
