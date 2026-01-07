# PowerShell 测试文件

# 函数定义
function Get-Greeting {
    param(
        [string]$Name
    )
    return "Hello, $Name"
}

# 计算和的函数
function Get-Sum {
    param(
        [int]$A,
        [int]$B
    )
    return $A + $B
}

# 类定义
class User {
    [string]$Name
    [int]$Age

    User([string]$name, [int]$age) {
        $this.Name = $name
        $this.Age = $age
    }

    [string] Greet() {
        return "Hello, I'm $($this.Name)"
    }
}

# 日志函数
function Write-Log {
    param(
        [string]$Message
    )
    Write-Host "[LOG] $Message"
}

# 创建用户函数
function New-AppUser {
    param(
        [string]$Username
    )
    Write-Log "Creating user: $Username"
    return [User]::new($Username, 25)
}

# 执行代码
$greeting = Get-Greeting -Name "Alice"
Write-Host $greeting

$sum = Get-Sum -A 5 -B 3
Write-Host "Sum: $sum"

$user = New-AppUser -Username "Bob"
Write-Host $user.Greet()
