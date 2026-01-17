# PowerShell 测试脚本 - 包含函数、类、哈希表

# 全局变量
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "config.json"
$LogFile = Join-Path $ScriptDir "app.log"

# 日志函数
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Level,

        [Parameter(Mandatory=$true)]
        [string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
}

# 用户类
class User {
    [int]$Id
    [string]$Name
    [string]$Email
    [DateTime]$CreatedAt

    User([int]$id, [string]$name, [string]$email) {
        $this.Id = $id
        $this.Name = $name
        $this.Email = $email
        $this.CreatedAt = Get-Date
    }

    [bool] Authenticate([string]$password) {
        return $this.CheckPassword($password)
    }

    hidden [bool] CheckPassword([string]$password) {
        return -not [string]::IsNullOrEmpty($password)
    }
}

# 创建用户函数
function New-User {
    param(
        [Parameter(Mandatory=$true)]
        [int]$Id,

        [Parameter(Mandatory=$true)]
        [string]$Name,

        [Parameter(Mandatory=$true)]
        [string]$Email
    )

    $user = [User]::new($Id, $Name, $Email)
    Write-Log -Level "INFO" -Message "Creating user: $Name ($Email)"
    return $user
}

# 用户认证函数
function Test-UserAuthentication {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Username,

        [Parameter(Mandatory=$true)]
        [string]$Password
    )

    if ([string]::IsNullOrEmpty($Password)) {
        Write-Log -Level "ERROR" -Message "Password cannot be empty"
        return $false
    }

    # 模拟认证逻辑
    if ($Username -eq "admin" -and $Password -eq "secret") {
        Write-Log -Level "INFO" -Message "User $Username authenticated successfully"
        return $true
    } else {
        Write-Log -Level "WARNING" -Message "Authentication failed for user $Username"
        return $false
    }
}

# 会话类
class Session {
    [int]$UserId
    [DateTime]$CreatedAt

    Session([int]$userId) {
        $this.UserId = $userId
        $this.CreatedAt = Get-Date
    }

    [bool] IsValid() {
        $elapsed = (Get-Date) - $this.CreatedAt
        return $elapsed.TotalHours -lt 24
    }

    [void] Save() {
        # 保存会话逻辑
        Write-Log -Level "INFO" -Message "Session saved for user: $($this.UserId)"
    }
}

# 创建会话函数
function New-Session {
    param(
        [Parameter(Mandatory=$true)]
        [int]$UserId
    )

    $session = [Session]::new($UserId)
    $session.Save()
    return $session
}

# 处理用户数组
function Get-UserList {
    $users = @(
        @{Id=1; Name="Alice"; Email="alice@example.com"},
        @{Id=2; Name="Bob"; Email="bob@example.com"},
        @{Id=3; Name="Charlie"; Email="charlie@example.com"}
    )

    return $users
}

# 管道处理示例
function Show-Users {
    param(
        [Parameter(ValueFromPipeline=$true)]
        $User
    )

    process {
        Write-Host "User: $($User.Name) ($($User.Email))"
    }
}

# 错误处理
function Invoke-WithErrorHandling {
    [CmdletBinding()]
    param()

    try {
        # 可能出错的代码
        $result = Get-Content -Path "nonexistent.txt" -ErrorAction Stop
    }
    catch {
        Write-Log -Level "ERROR" -Message "Error: $($_.Exception.Message)"
        Write-Error "Failed to read file"
    }
    finally {
        Write-Log -Level "INFO" -Message "Operation completed"
    }
}

# 哈希表操作
function Get-UserConfig {
    $config = @{
        DatabaseServer = "localhost"
        DatabasePort = 5432
        MaxConnections = 100
        Timeout = 30
    }

    return $config
}

# 管道使用示例
$users = Get-UserList
$users | ForEach-Object {
    Write-Host "Processing: $($_.Name)"
}

# 主函数
function Main {
    Write-Log -Level "INFO" -Message "Application started"

    # 创建用户
    $user1 = New-User -Id 1 -Name "Alice" -Email "alice@example.com"
    $user2 = New-User -Id 2 -Name "Bob" -Email "bob@example.com"

    # 测试认证
    if (Test-UserAuthentication -Username "admin" -Password "secret") {
        Write-Host "Authentication successful" -ForegroundColor Green
        $session = New-Session -UserId 1

        if ($session.IsValid()) {
            Write-Host "Session is valid" -ForegroundColor Green
        }
    } else {
        Write-Host "Authentication failed" -ForegroundColor Red
    }

    Write-Log -Level "INFO" -Message "Application finished"
}

# 执行主函数
Main
