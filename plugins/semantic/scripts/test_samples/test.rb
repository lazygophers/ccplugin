# 类定义
class Person
  attr_accessor :name, :age

  def initialize(name, age)
    @name = name
    @age = age
  end

  def greet
    puts "Hello, I'm #{@name}"
  end
end

# Module 定义
module Logger
  def log(message)
    puts "[LOG] #{message}"
  end
end

# 使用 Module 的类
class UserService
  include Logger

  def create_user(name)
    log("Creating user: #{name}")
    Person.new(name, 25)
  end
end

# 方法定义
def calculate_sum(a, b)
  a + b
end

# 执行代码
person = Person.new("Alice", 30)
person.greet

service = UserService.new
service.create_user("Bob")
