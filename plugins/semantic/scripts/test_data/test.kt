// Kotlin 测试文件 - 包含类、对象、扩展函数

data class User(
    val id: Int,
    val name: String,
    val email: String,
    val createdAt: DateTime = DateTime.now()
)

fun User.authenticate(password: String): Boolean {
    return this.checkPassword(password)
}

private fun User.checkPassword(password: String): Boolean {
    return password.isNotEmpty()
}

interface UserService {
    suspend fun getUser(id: Int): User?
    suspend fun createUser(user: User): Result<Unit>
}

class UserServiceImpl(private val db: Database) : UserService {

    override suspend fun getUser(id: Int): User? {
        // 实现逻辑
        return User(id, "Test", "test@example.com")
    }

    override suspend fun createUser(user: User): Result<Unit> {
        // 实现逻辑
        return Result.success(Unit)
    }
}

object SessionFactory {
    fun createSession(user: User): Session {
        val session = Session(user.id)
        session.save()
        return session
    }
}

class Session(val userId: Int) {
    val createdAt: DateTime = DateTime.now()

    val isValid: Boolean
        get() = DateTime.now().difference(createdAt).toHours() < 24

    fun save() {
        // 保存会话
    }
}

// 扩展函数示例
fun User.toDto(): UserDto {
    return UserDto(
        id = id,
        name = name,
        email = email
    )
}

data class UserDto(
    val id: Int,
    val name: String,
    val email: String
)
