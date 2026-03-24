# Risk Classifier - 风险分级规则

## 概述

风险分级器（Risk Classifier）负责评估 loop 流程中每个操作的风险等级，决定是否需要人工审批。基于 EU AI Act 2026 的 HITL（Human-in-the-Loop）要求，所有高风险操作必须有人工监督。

## 三级风险分类

### Level 1: auto（自动通过）

**定义**：低风险操作，不会对系统/数据造成破坏性影响，可以自动执行无需用户确认。

**适用操作类型**：
- **只读操作**：文件读取、目录扫描、代码分析、日志查询
- **生成操作**：代码生成、测试用例生成、文档生成
- **测试操作**：单元测试运行、集成测试运行、linter 检查
- **查询操作**：数据库只读查询、API GET 请求、搜索操作
- **分析操作**：性能分析、依赖分析、安全扫描

**示例**：
```yaml
operations:
  - type: "Read"
    risk_level: "auto"
    examples:
      - "Read file: src/main.go"
      - "Glob pattern: **/*.py"
      - "Grep search: function loginHandler"

  - type: "Bash (read-only)"
    risk_level: "auto"
    examples:
      - "go test ./..."
      - "npm run lint"
      - "cat .version"
      - "ls -la"

  - type: "WebSearch"
    risk_level: "auto"
    examples:
      - "Search: prompt engineering best practices 2025"
```

**风险评分**：0-3 分（低风险）

---

### Level 2: review（需审查）

**定义**：中等风险操作，会修改系统状态但可逆，需要用户审查后确认。

**适用操作类型**：
- **文件修改**：代码修改、配置修改、文档修改
- **依赖管理**：安装/更新依赖包（npm install、pip install、go get）
- **配置变更**：修改配置文件、环境变量设置
- **数据库写入**：INSERT、UPDATE 操作（非生产环境）
- **Git 普通操作**：git commit、git push（非 force）、创建分支
- **资源创建**：创建文件、创建目录、创建数据库表

**适用条件**：
- 操作可以通过 git revert、文件恢复等方式回滚
- 不涉及外部系统或生产环境
- 修改范围有限且可追溯

**示例**：
```yaml
operations:
  - type: "Edit"
    risk_level: "review"
    examples:
      - "Edit file: src/api/auth.go (add JWT validation)"
      - "Replace pattern in config/settings.json"

  - type: "Write"
    risk_level: "review"
    examples:
      - "Write new file: tests/test_auth.py"
      - "Create migration: 002_add_users_table.sql"

  - type: "Bash (write)"
    risk_level: "review"
    examples:
      - "npm install express@4.18.0"
      - "pip install --upgrade requests"
      - "git commit -m 'feat: add user auth'"
      - "git push origin feature/auth"

  - type: "Agent (run_in_background)"
    risk_level: "review"
    examples:
      - "Execute 2 tasks in parallel via Agent(run_in_background=True)"
```

**风险评分**：4-6 分（中风险）

**审批展示**：
- 操作类型和目标
- 变更摘要（文件数、修改行数、依赖包名称）
- 预期影响范围
- 建议操作：批准 / 拒绝 / 修改参数

---

### Level 3: mandatory（强制审批）

**定义**：高风险操作，具有破坏性或不可逆性，必须经过用户明确确认才能执行。

**适用操作类型**：
- **破坏性删除**：文件删除、目录删除、数据库表删除
- **强制覆盖**：git force push、git reset --hard、覆盖已存在文件
- **生产部署**：部署到生产环境、修改生产配置、生产数据库操作
- **权限变更**：修改文件权限、修改访问控制、添加 sudo 命令
- **外部影响**：发送邮件/消息、创建/关闭 PR/Issue、调用外部 API（POST/PUT/DELETE）
- **敏感数据**：读取/修改密钥、证书、敏感配置

**适用条件**：
- 操作不可回滚或回滚成本极高
- 影响生产环境或外部系统
- 涉及敏感数据或权限变更
- 可能导致数据丢失或服务中断

**示例**：
```yaml
operations:
  - type: "Bash (destructive)"
    risk_level: "mandatory"
    examples:
      - "rm -rf dist/"
      - "git push --force origin main"
      - "git reset --hard HEAD~3"
      - "DROP TABLE users;"
      - "kubectl delete deployment prod-api"
      - "sudo chmod 777 /etc/passwd"

  - type: "SendMessage (external)"
    risk_level: "mandatory"
    examples:
      - "Send Slack message to #engineering"
      - "Create GitHub PR"
      - "Close GitHub Issue #123"

  - type: "WebFetch (write)"
    risk_level: "mandatory"
    examples:
      - "POST https://api.stripe.com/v1/charges"
      - "DELETE https://api.github.com/repos/owner/repo"

  - type: "Read (sensitive)"
    risk_level: "mandatory"
    examples:
      - "Read .env (contains API keys)"
      - "Read private/keys/id_rsa"
```

**风险评分**：7-10 分（高风险）

**审批展示**：
- **警告标识**：⚠️ 高风险操作
- 操作类型和目标（高亮显示）
- 详细影响说明（受影响的资源、潜在风险）
- 不可逆性提醒
- 建议操作：明确批准 / 拒绝（默认拒绝）

---

## 风险评估规则

### 规则引擎

```python
def classify_risk(operation: dict) -> str:
    """
    评估操作风险等级

    Args:
        operation: {
            "tool": "Bash",
            "command": "rm -rf dist/",
            "files": ["dist/"],
            "context": {"environment": "production"}
        }

    Returns:
        "auto" | "review" | "mandatory"
    """

    # 规则 1: 关键字匹配（最高优先级）
    destructive_keywords = [
        "rm -rf", "DROP TABLE", "DELETE FROM", "--force",
        "reset --hard", "kubectl delete", "sudo"
    ]
    if any(kw in operation.get("command", "") for kw in destructive_keywords):
        return "mandatory"

    # 规则 2: 工具类型判断
    tool = operation.get("tool")

    # 只读工具 → auto
    if tool in ["Read", "Glob", "Grep", "WebSearch"]:
        return "auto"

    # 破坏性工具 → mandatory
    if tool in ["SendMessage", "WebFetch"]:
        method = operation.get("method", "GET")
        if method in ["POST", "PUT", "DELETE"]:
            return "mandatory"

    # 规则 3: 环境判断
    if operation.get("context", {}).get("environment") == "production":
        return "mandatory"

    # 规则 4: 文件路径判断
    files = operation.get("files", [])
    sensitive_patterns = [".env", "id_rsa", "private/", "secrets/"]
    if any(pattern in f for f in files for pattern in sensitive_patterns):
        return "mandatory"

    # 规则 5: 操作类型判断
    if tool in ["Edit", "Write", "Bash"]:
        # 安装依赖、提交代码 → review
        safe_patterns = ["install", "commit", "test", "lint"]
        if any(p in operation.get("command", "") for p in safe_patterns):
            return "review"

        # 其他写入操作 → review
        return "review"

    # 默认 auto
    return "auto"
```

### 决策树

```
操作输入
  │
  ├─ 包含破坏性关键字？ ───→ YES → mandatory
  │                         ↓ NO
  ├─ 工具类型 = Read/Glob/Grep/WebSearch？ ───→ YES → auto
  │                                            ↓ NO
  ├─ 工具类型 = SendMessage/WebFetch (POST/PUT/DELETE)？ ───→ YES → mandatory
  │                                                         ↓ NO
  ├─ 环境 = production？ ───→ YES → mandatory
  │                         ↓ NO
  ├─ 涉及敏感文件？ ───→ YES → mandatory
  │                    ↓ NO
  ├─ 工具类型 = Edit/Write/Bash (write)？ ───→ YES → review
  │                                           ↓ NO
  └─ 默认 ───→ auto
```

---

## 风险评分量化

### 评分维度

| 维度 | 权重 | 评分规则 |
|------|------|---------|
| **可逆性** | 40% | 完全可逆=0，部分可逆=5，不可逆=10 |
| **影响范围** | 30% | 单文件=0，多文件=3，跨系统=7，生产环境=10 |
| **敏感性** | 20% | 公开数据=0，内部数据=5，敏感数据=10 |
| **外部影响** | 10% | 无外部影响=0，读取外部=3，修改外部=10 |

### 评分映射

| 总分 | 风险等级 |
|------|---------|
| 0-3 | auto |
| 4-6 | review |
| 7-10 | mandatory |

### 示例计算

**操作**：`git push --force origin main`

| 维度 | 得分 | 计算 |
|------|------|------|
| 可逆性 | 10 | 不可逆（覆盖远程历史） |
| 影响范围 | 7 | 跨系统（影响所有协作者） |
| 敏感性 | 0 | 代码为公开数据 |
| 外部影响 | 10 | 修改外部 Git 仓库 |

**总分**：10 × 0.4 + 7 × 0.3 + 0 × 0.2 + 10 × 0.1 = 4 + 2.1 + 0 + 1 = **7.1**

**结果**：mandatory（强制审批）

---

## 特殊场景处理

### 场景 1: 批量操作

**规则**：批量操作的风险等级取所有子操作的最高风险等级。

**示例**：
```yaml
operations:
  - Edit file1.py  # review
  - Edit file2.py  # review
  - rm temp.txt    # mandatory

overall_risk: mandatory
```

### 场景 2: 用户配置覆盖

**规则**：允许用户通过配置文件覆盖默认风险等级。

**配置示例**（`.claude/task.local.md`）：
```yaml
---
hitl_overrides:
  - pattern: "npm install*"
    risk_level: "auto"  # 信任 npm install
  - pattern: "git push origin feature/*"
    risk_level: "auto"  # 信任推送到 feature 分支
---
```

### 场景 3: 信任模式

**规则**：用户可以启用"信任模式"，将所有 review 级别操作降级为 auto。

**启用方式**：
```bash
# 临时启用（当前会话）
/add --trust-mode

# 永久启用（配置文件）
echo "trust_mode: true" >> .claude/task.local.md
```

**限制**：信任模式不影响 mandatory 级别操作。

---

## 审批日志格式

每次审批决策都会记录在 `.claude/plans/{task_hash}-approval-log.json`：

```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "operation": {
    "tool": "Bash",
    "command": "npm install express",
    "files": ["package.json", "package-lock.json"]
  },
  "risk_classification": {
    "level": "review",
    "score": 5.2,
    "reasons": ["file modification", "dependency installation"]
  },
  "approval": {
    "required": true,
    "user_decision": "approved",
    "timestamp": "2026-03-20T10:31:00Z",
    "notes": "User confirmed version compatibility"
  }
}
```

---

## 集成接口

### 输入格式

```typescript
interface OperationContext {
  tool: string;                    // 工具名称
  command?: string;                // 命令文本（Bash）
  files?: string[];                // 涉及的文件路径
  method?: string;                 // HTTP 方法（WebFetch）
  environment?: string;            // 环境标识（production/staging/dev）
  user_trust_mode?: boolean;       // 用户是否启用信任模式
}
```

### 输出格式

```typescript
interface RiskClassification {
  level: "auto" | "review" | "mandatory";
  score: number;                   // 0-10 风险评分
  reasons: string[];               // 分级原因列表
  requires_approval: boolean;      // 是否需要审批
  approval_policy: {
    timeout_seconds: number;       // 审批超时时间
    default_action: "block" | "allow";  // 超时默认行为
  };
}
```

---

## 验收标准

- ✅ **AC1**: 破坏性操作（`rm -rf`、`git push --force`、`DROP TABLE`）100% 分类为 mandatory
- ✅ **AC2**: 只读操作（Read、Glob、Grep、WebSearch）100% 分类为 auto
- ✅ **AC3**: 文件修改操作（Edit、Write）100% 分类为 review
- ✅ **AC4**: 风险评分准确性 ≥ 95%（通过测试集验证）
- ✅ **AC5**: 支持用户配置覆盖（`.claude/task.local.md`）
- ✅ **AC6**: 支持信任模式（review → auto，mandatory 不变）
- ✅ **AC7**: 审批日志完整记录（操作、分级、决策）
