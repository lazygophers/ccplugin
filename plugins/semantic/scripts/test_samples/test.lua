-- Lua 测试文件

-- 表作为类
Person = {}
Person.__index = Person

function Person.new(name, age)
    local self = setmetatable({}, Person)
    self.name = name
    self.age = age
    return self
end

function Person:greet()
    return "Hello, I'm " .. self.name
end

-- Module 定义
local Utils = {}

function Utils.calculateSum(a, b)
    return a + b
end

function Utils.formatMessage(msg)
    return "[INFO] " .. msg
end

return Utils

-- 全局函数
function printData(data)
    print("Data: " .. tostring(data))
end

-- 执行代码
local person = Person.new("Alice", 30)
print(person:greet())

local sum = Utils.calculateSum(5, 3)
print("Sum: " .. sum)

printData({name = "Bob", age = 25})
