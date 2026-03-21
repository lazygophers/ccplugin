# 自愈机制（Self-Healing）指南

## 概述

自愈机制是 Adjuster 在 Level 1 Retry 之前的自动修复层（Level 1.5），针对常见的、可预测的错误类型进行即时修复，无需进入完整的失败升级流程。自愈操作快速、确定性强，能够显著减少人工介入和重试次数。

## 自愈层级定位

```
Level 1: Retry（快速重试）
    ↑
Level 1.5: Self-Healing（自动修复）← 插入此层
    ↓
Level 2: Debug（深度诊断）
Level 3: Replan（重新规划）
Level 4: Ask User（请求指导）
```

**触发时机**：
- 首次失败检测时
- 在 Level 1 Retry 之前
- 错误类型匹配自愈目录

**决策流程**：
```
失败检测 → 错误分类 → 匹配自愈目录
    ↓                      ↓
    ↓                  执行自愈操作
    ↓                      ↓
    ↓              成功 → 继续执行
    ↓                      ↓
    └────── 失败 ──────→ Level 1 Retry
```

## 可自愈错误目录

### 1. 依赖缺失（Dependency Missing）

**错误特征**：
- `ModuleNotFoundError`
- `ImportError`
- `No module named 'xxx'`
- `Cannot find package 'xxx'`

**修复方案**：
```bash
# Python
pip install <package_name>

# Node.js
npm install <package_name>

# Rust
cargo add <package_name>
```

**自愈策略**：
1. 从错误信息提取缺失的包名
2. 识别项目类型（Python/Node.js/Rust）
3. 执行对应的安装命令
4. 验证安装成功（重新导入/编译）

**HITL 联动**：
- `auto` 模式：自动执行安装
- `review` 模式：询问用户是否允许安装

### 2. 端口占用（Port Already in Use）

**错误特征**：
- `Address already in use`
- `Port XXXX is already in use`
- `EADDRINUSE`
- `bind: address already in use`

**修复方案**：
```bash
# 查找占用进程
lsof -i :PORT

# 终止进程（需用户确认）
kill -9 <PID>

# 或自动选择新端口
PORT=$((PORT + 1))
```

**自愈策略**：
1. 从错误信息提取端口号
2. 查找占用该端口的进程
3. 根据 HITL 模式决策：
   - `auto` 模式：自动选择新端口（PORT + 1）
   - `review` 模式：询问用户是否终止进程或选择新端口

**HITL 联动**：
- `auto` 模式：自动选择新端口，不终止现有进程
- `review` 模式：提供选项（终止进程/选择新端口/手动处理）

### 3. 目录不存在（Directory Not Found）

**错误特征**：
- `FileNotFoundError`
- `No such file or directory`
- `ENOENT`
- `cannot find the path`

**修复方案**：
```bash
# 创建缺失的目录
mkdir -p /path/to/directory
```

**自愈策略**：
1. 从错误信息提取目录路径
2. 验证路径合法性（不在系统目录、不包含危险字符）
3. 创建目录（包括父目录）
4. 验证创建成功

**HITL 联动**：
- `auto` 模式：自动创建用户工作目录下的目录
- `review` 模式：创建系统目录前需确认

### 4. 权限不足（Permission Denied）

**错误特征**：
- `Permission denied`
- `EACCES`
- `Access is denied`
- `Operation not permitted`

**修复方案**：
```bash
# 修改文件权限
chmod +x /path/to/file

# 修改目录权限
chmod 755 /path/to/directory

# 修改所有者（需 sudo）
sudo chown user:group /path/to/file
```

**自愈策略**：
1. 从错误信息提取文件/目录路径
2. 检查当前权限状态
3. 根据操作类型调整权限：
   - 可执行文件：`chmod +x`
   - 目录访问：`chmod 755`
   - 文件读写：`chmod 644`
4. 验证权限修改成功

**HITL 联动**：
- `auto` 模式：自动调整用户文件权限
- `review` 模式：涉及 sudo 操作需确认

### 5. 配置缺失（Configuration Missing）

**错误特征**：
- `Configuration file not found`
- `Missing required configuration`
- `Environment variable XXX is not set`
- `Config key 'XXX' not found`

**修复方案**：
```bash
# 创建默认配置文件
cp config.example.json config.json

# 设置环境变量
export VAR_NAME=default_value

# 写入配置文件
echo "key=value" >> config.ini
```

**自愈策略**：
1. 识别缺失的配置项
2. 检查是否存在示例配置（`.example`/`.template`）
3. 复制示例配置或生成默认配置
4. 对于环境变量，使用合理默认值或询问用户

**HITL 联动**：
- `auto` 模式：使用默认值或示例配置
- `review` 模式：需要敏感信息（密钥/密码）时询问用户

### 6. 网络超时（Network Timeout）

**错误特征**：
- `Connection timeout`
- `Read timeout`
- `Request timeout`
- `ETIMEDOUT`

**修复方案**：
```python
# 增加超时时间
timeout = timeout * 2

# 添加重试机制
max_retries = 3
retry_delay = 2  # 秒
```

**自愈策略**：
1. 识别超时类型（连接超时/读取超时）
2. 扩大超时时间（2 倍递增，最大 120 秒）
3. 配置重试参数（最多 3 次，指数退避）
4. 重新发起请求

**HITL 联动**：
- `auto` 模式：自动调整超时参数
- `review` 模式：超过 3 次超时后询问用户

## 自愈操作执行流程

### 阶段 1：错误匹配

```python
def match_healable_error(error_message: str) -> Optional[str]:
    """
    匹配可自愈的错误类型

    Returns:
        错误类型 ID（dependency_missing/port_in_use/...）或 None
    """
    error_patterns = {
        "dependency_missing": [
            r"ModuleNotFoundError",
            r"ImportError",
            r"No module named",
            r"Cannot find package"
        ],
        "port_in_use": [
            r"Address already in use",
            r"Port .* is already in use",
            r"EADDRINUSE"
        ],
        # ... 其他错误模式
    }

    for error_type, patterns in error_patterns.items():
        for pattern in patterns:
            if re.search(pattern, error_message):
                return error_type

    return None
```

### 阶段 2：提取参数

从错误信息中提取修复所需的参数：

```python
def extract_parameters(error_type: str, error_message: str) -> dict:
    """
    提取自愈操作所需的参数

    Examples:
        - dependency_missing: {"package_name": "numpy"}
        - port_in_use: {"port": 8080}
        - directory_not_found: {"path": "/tmp/data"}
    """
    # 根据错误类型使用正则提取参数
    if error_type == "dependency_missing":
        match = re.search(r"No module named '(\w+)'", error_message)
        return {"package_name": match.group(1)} if match else {}
    # ... 其他类型的参数提取
```

### 阶段 3：HITL 决策

根据 HITL 模式和操作风险决定是否需要用户确认：

```python
def require_user_confirmation(error_type: str, hitl_mode: str, parameters: dict) -> bool:
    """
    判断是否需要用户确认

    Args:
        error_type: 错误类型
        hitl_mode: HITL 模式（auto/review/manual）
        parameters: 操作参数

    Returns:
        True 需要确认，False 自动执行
    """
    if hitl_mode == "manual":
        return True  # manual 模式总是需要确认

    if hitl_mode == "auto":
        # auto 模式下，高风险操作仍需确认
        high_risk_operations = {
            "port_in_use": lambda p: "kill_process" in p,
            "permission_denied": lambda p: "sudo" in str(p),
            "configuration_missing": lambda p: "sensitive" in str(p)
        }

        if error_type in high_risk_operations:
            return high_risk_operations[error_type](parameters)

        return False  # 低风险操作自动执行

    # review 模式默认需要确认
    return True
```

### 阶段 4：执行修复

执行具体的修复操作：

```python
def execute_healing(error_type: str, parameters: dict) -> HealingResult:
    """
    执行自愈操作

    Returns:
        HealingResult 包含成功状态、修复操作、验证结果
    """
    healing_actions = {
        "dependency_missing": install_dependency,
        "port_in_use": resolve_port_conflict,
        "directory_not_found": create_directory,
        "permission_denied": fix_permissions,
        "configuration_missing": create_config,
        "network_timeout": adjust_timeout
    }

    action = healing_actions.get(error_type)
    if not action:
        return HealingResult(success=False, reason="未知错误类型")

    return action(parameters)
```

### 阶段 5：验证修复

验证修复是否成功：

```python
def verify_healing(error_type: str, parameters: dict, original_task: Task) -> bool:
    """
    验证修复是否成功

    Returns:
        True 修复成功，False 修复失败
    """
    verification_methods = {
        "dependency_missing": lambda p: verify_import(p["package_name"]),
        "port_in_use": lambda p: verify_port_available(p["port"]),
        "directory_not_found": lambda p: os.path.exists(p["path"]),
        "permission_denied": lambda p: os.access(p["path"], os.W_OK),
        "configuration_missing": lambda p: verify_config(p["config_key"]),
        "network_timeout": lambda p: verify_network_connection(p["url"])
    }

    verify = verification_methods.get(error_type)
    return verify(parameters) if verify else False
```

## 自愈输出格式

### 成功修复

```json
{
  "status": "healed",
  "strategy": "self_healing",
  "report": "依赖缺失已自动修复，安装 numpy==1.21.0。",
  "healing_details": {
    "error_type": "dependency_missing",
    "action_taken": "pip install numpy==1.21.0",
    "verification": "success",
    "next_step": "继续执行原任务"
  },
  "retry_config": {
    "backoff_seconds": 0,
    "immediate_retry": true
  }
}
```

### 需要用户确认

```json
{
  "status": "healing_pending",
  "strategy": "self_healing_review",
  "report": "检测到端口 8080 被占用，需要确认修复方案。",
  "healing_proposal": {
    "error_type": "port_in_use",
    "detected_issue": "端口 8080 被进程 PID 1234 占用",
    "options": [
      {
        "id": 1,
        "action": "终止占用进程（PID 1234）",
        "risk": "medium"
      },
      {
        "id": 2,
        "action": "使用新端口 8081",
        "risk": "low"
      },
      {
        "id": 3,
        "action": "手动处理",
        "risk": "none"
      }
    ],
    "recommended": 2
  }
}
```

### 修复失败

```json
{
  "status": "healing_failed",
  "strategy": "self_healing_failed",
  "report": "自愈失败，降级到 Level 1 Retry。",
  "healing_details": {
    "error_type": "dependency_missing",
    "action_tried": "pip install unknown-package",
    "failure_reason": "Package not found in PyPI",
    "next_strategy": "retry"
  },
  "retry_config": {
    "backoff_seconds": 1
  }
}
```

## 自愈策略决策树

```
失败检测
    ↓
错误分类
    ↓
┌─ 匹配自愈目录？
│   ├─ Yes → 提取参数
│   │           ↓
│   │       HITL 决策
│   │           ↓
│   │   ┌─ 需要确认？
│   │   │   ├─ Yes → 向用户请求确认
│   │   │   │           ↓
│   │   │   │       用户批准？
│   │   │   │       ├─ Yes → 执行修复
│   │   │   │       └─ No → 降级到 Retry
│   │   │   └─ No → 执行修复
│   │   │               ↓
│   │   │           验证修复
│   │   │               ↓
│   │   │           成功？
│   │   │           ├─ Yes → 继续执行
│   │   │           └─ No → 降级到 Retry
│   └─ No → 跳过自愈，直接 Retry
```

## 自愈与 HITL 模式联动

| HITL 模式 | 低风险操作 | 中风险操作 | 高风险操作 |
|-----------|-----------|-----------|-----------|
| `auto` | 自动执行 | 自动执行 | 需要确认 |
| `review` | 需要确认 | 需要确认 | 需要确认 |
| `manual` | 需要确认 | 需要确认 | 需要确认 |

**风险级别定义**：

| 风险级别 | 操作示例 | 判断标准 |
|---------|---------|---------|
| **低风险** | 创建用户目录、调整超时参数、使用新端口 | 不修改系统文件、不终止进程、不需要 sudo |
| **中风险** | 安装依赖包、修改文件权限、复制配置文件 | 修改用户文件、安装第三方软件、修改配置 |
| **高风险** | 终止进程、修改系统目录、需要 sudo 操作 | 影响其他进程、修改系统、需要提权 |

## 自愈最佳实践

### 1. 优先自愈

对于可预测、低风险的错误，优先尝试自愈而非直接重试。自愈成功率高且速度快。

### 2. 快速失败

如果自愈操作 5 秒内未完成，立即降级到 Retry。避免自愈操作阻塞任务执行。

### 3. 验证修复

修复后必须验证操作是否成功，验证失败应降级到 Retry 而非假装成功。

### 4. 记录历史

记录所有自愈操作（成功/失败）到任务历史，帮助分析和优化。

### 5. 限制范围

自愈操作仅限于用户工作区，不修改系统文件或全局配置。

### 6. 安全第一

涉及进程终止、sudo 操作、敏感配置时，优先考虑安全而非便利。

## 执行检查清单

### 错误匹配检查
- [ ] 提取完整错误信息
- [ ] 匹配自愈错误目录
- [ ] 识别错误类型

### 参数提取检查
- [ ] 从错误信息提取参数
- [ ] 验证参数合法性
- [ ] 检查参数完整性

### HITL 决策检查
- [ ] 获取当前 HITL 模式
- [ ] 评估操作风险级别
- [ ] 决定是否需要用户确认

### 修复执行检查
- [ ] 执行修复操作
- [ ] 设置操作超时（5 秒）
- [ ] 捕获执行异常

### 验证检查
- [ ] 验证修复是否成功
- [ ] 记录修复历史
- [ ] 决定下一步策略（继续/降级）

## 降级条件

当满足以下任一条件时，自愈失败并降级到 Level 1 Retry：

1. 错误类型不在自愈目录中
2. 参数提取失败（无法解析错误信息）
3. 用户拒绝修复操作（review/manual 模式）
4. 修复操作超时（>5 秒）
5. 修复操作执行失败
6. 修复验证失败
7. 同一错误已尝试自愈 2 次失败

降级后，错误信息和失败历史将传递给 Level 1 Retry 策略处理。
