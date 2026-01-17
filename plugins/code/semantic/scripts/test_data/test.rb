# Ruby 测试文件 - 包含类、模块、方法

class User
  attr_reader :id, :name, :email, :created_at

  def initialize(id, name, email)
    @id = id
    @name = name
    @email = email
    @created_at = Time.now
  end

  def authenticate(password)
    check_password(password)
  end

  private

  def check_password(password)
    !password.nil? && !password.empty?
  end
end

module UserService
  def get_user(id)
    # 实现逻辑
    User.new(id, 'Test', 'test@example.com')
  end

  def create_user(user)
    # 实现逻辑
    user
  end

  module_function
  def fetch_user(id)
    # 实现逻辑
  end
end

class Session
  attr_reader :user_id, :created_at

  def initialize(user_id)
    @user_id = user_id
    @created_at = Time.now
  end

  def valid?
    Time.now - @created_at < 86400
  end

  def save
    # 保存会话
  end
end

def create_session(user)
  session = Session.new(user.id)
  session.save
  session
end

# 单例示例
class Config
  include Singleton

  def initialize
    @settings = {}
  end

  def self.instance
    @instance ||= new
  end
end

# Block 示例
User.all.each do |user|
  puts "User: #{user.name}"
end
