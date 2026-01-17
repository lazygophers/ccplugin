-- Lua 测试文件 - 包含表、函数、元表

-- 用户模块
local User = {}
User.__index = User

-- 创建新用户
function User.new(id, name, email)
    local self = setmetatable({}, User)
    self.id = id
    self.name = name
    self.email = email
    self.created_at = os.time()
    return self
end

-- 用户认证
function User:authenticate(password)
    return self:checkPassword(password)
end

-- 验证密码（私有方法）
function User:checkPassword(password)
    return password ~= nil and password ~= ""
end

-- 获取用户信息
function User:getId()
    return self.id
end

function User:getName()
    return self.name
end

function User:getEmail()
    return self.email
end

-- 用户服务模块
local UserService = {}

-- 用户存储
UserService.users = {}

-- 获取用户
function UserService.getUser(id)
    for _, user in ipairs(UserService.users) do
        if user:getId() == id then
            return user
        end
    end
    return nil
end

-- 创建用户
function UserService.createUser(user)
    table.insert(UserService.users, user)
    return user
end

-- 会话模块
local Session = {}
Session.__index = Session

-- 创建新会话
function Session.new(user_id)
    local self = setmetatable({}, Session)
    self.user_id = user_id
    self.created_at = os.time()
    return self
end

-- 检查会话是否有效
function Session:isValid()
    local current_time = os.time()
    local elapsed = current_time - self.created_at
    return elapsed < 86400  -- 24 小时
end

-- 保存会话
function Session:save()
    -- 保存会话逻辑
    print("Session saved for user: " .. self.user_id)
end

-- 创建会话
function createSession(user)
    local session = Session.new(user:getId())
    session:save()
    return session
end

-- 表操作示例
local users = {
    {id = 1, name = "Alice", email = "alice@example.com"},
    {id = 2, name = "Bob", email = "bob@example.com"},
    {id = 3, name = "Charlie", email = "charlie@example.com"}
}

-- 遍历表
for i, user in ipairs(users) do
    print(string.format("User %d: %s (%s)", user.id, user.name, user.email))
end

-- 元表示例
local ReadOnlyTable = {}

function ReadOnlyTable.new(t)
    local proxy = {}
    local mt = {
        __index = t,
        __newindex = function()
            error("Cannot modify read-only table")
        end,
        __pairs = function()
            return pairs(t)
        end
    }
    setmetatable(proxy, mt)
    return proxy
end

-- 闭包示例
function createCounter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local counter = createCounter()
print(counter())  -- 1
print(counter())  -- 2
print(counter())  -- 3

-- 协程示例
local function producer()
    for i = 1, 5 do
        coroutine.yield(i)
    end
end

local co = coroutine.create(producer)

while coroutine.status(co) ~= "dead" do
    local success, value = coroutine.resume(co)
    if success then
        print("Produced: " .. tostring(value))
    end
end

-- 面向对象示例 - 继承
local Animal = {}
Animal.__index = Animal

function Animal.new(name)
    local self = setmetatable({}, Animal)
    self.name = name
    return self
end

function Animal:speak()
    return self.name .. " makes a sound"
end

local Dog = {}
Dog.__index = Dog
setmetatable(Dog, {__index = Animal})

function Dog.new(name)
    local self = Animal.new(name)
    setmetatable(self, Dog)
    return self
end

function Dog:speak()
    return self.name .. " barks"
end

local dog = Dog.new("Buddy")
print(dog:speak())  -- Buddy barks

-- 模块导出
return {
    User = User,
    UserService = UserService,
    Session = Session,
    createSession = createSession
}
