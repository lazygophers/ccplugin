#!/bin/bash

# Bash 测试文件

# 函数定义
greet() {
    local name=$1
    echo "Hello, $name"
}

# 计算和的函数
calculate_sum() {
    local a=$1
    local b=$2
    echo $((a + b))
}

# 日志函数
log_message() {
    local level=$1
    local message=$2
    echo "[$level] $message"
}

# 创建用户函数
create_user() {
    local username=$1
    log_message "INFO" "Creating user: $username"
    echo "User $username created"
}

# 主函数
main() {
    greet "Alice"

    sum=$(calculate_sum 5 3)
    echo "Sum: $sum"

    create_user "Bob"
}

# 执行主函数
main
