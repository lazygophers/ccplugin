// Scala 测试文件 - 包含类、对象、trait

case class User(
    id: Int,
    name: String,
    email: String,
    createdAt: java.time.Instant = java.time.Instant.now()
)

object User {
  def apply(id: Int, name: String, email: String): User = {
    new User(id, name, email)
  }

  def authenticate(user: User, password: String): Boolean = {
    checkPassword(password)
  }

  private def checkPassword(password: String): Boolean = {
    password.nonEmpty
  }
}

trait UserService {
  def getUser(id: Int): Option[User]
  def createUser(user: User): User
}

class UserServiceImpl extends UserService {
  private val db: Database = new Database()

  override def getUser(id: Int): Option[User] = {
    // 实现逻辑
    Some(User(id, "Test", "test@example.com"))
  }

  override def createUser(user: User): User = {
    // 实现逻辑
    user
  }
}

object SessionFactory {
  def createSession(user: User): Session = {
    val session = new Session(user.id)
    session.save()
    session
  }
}

class Session(val userId: Int) {
  val createdAt: java.time.Instant = java.time.Instant.now()

  def isValid: Boolean = {
    val hours = java.time.Duration.between(createdAt, java.time.Instant.now()).toHours
    hours < 24
  }

  def save(): Unit = {
    // 保存会话
  }
}

// 泛型示例
trait Repository[T] {
  def findById(id: Int): Option[T]
  def save(entity: T): T
}

class UserRepository extends Repository[User] {
  override def findById(id: Int): Option[User] = {
    // 实现
    None
  }

  override def save(user: User): User = {
    // 实现
    user
  }
}
