# Approval Policies - 审批策略

## 概述

审批策略（Approval Policies）定义了不同风险等级操作的审批行为、超时处理、记录追溯和用户交互模式。基于 EU AI Act 2026 的要求，确保所有高风险决策都有人工监督和可追溯性。

---

## 三级审批策略

### Level 1: auto（自动通过）

**触发条件**：
- 风险等级 = `auto`（风险评分 0-3）
- 用户启用信任模式且风险等级 = `review`

**审批行为**：
- ✅ **无需用户确认**，自动执行
- ✅ **静默通过**，不打断用户工作流
- ✅ **记录到日志**，但不展示给用户

**超时处理**：
- 不适用（无需等待用户）

**日志记录**：
```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "operation": "Read file: src/main.go",
  "risk_level": "auto",
  "approval_required": false,
  "executed": true,
  "execution_time_ms": 45
}
```

**示例操作**：
- `Read file: src/api/auth.go`
- `Grep search: function loginHandler`
- `go test ./...`
- `WebSearch: prompt engineering best practices`

---

### Level 2: review（需审查）

**触发条件**：
- 风险等级 = `review`（风险评分 4-6）
- 用户未启用信任模式

**审批行为**：
1. **暂停执行**，等待用户确认
2. **展示摘要**：
   - 操作类型和目标
   - 变更摘要（文件数、修改行数、依赖包名称）
   - 预期影响范围
3. **用户选择**：
   - ✅ **批准（Approve）**：继续执行
   - ❌ **拒绝（Reject）**：跳过该操作
   - 📝 **修改参数（Modify）**：调整后重新提交审批
   - ⏸️ **暂停（Pause）**：暂停整个任务，用户稍后决定

**超时处理**：
- **超时时间**：5 分钟（可配置）
- **超时行为**：**阻塞**并发送提醒通知
- **提醒方式**：
  - 终端输出：`⚠️ 审批超时：操作 "npm install express" 等待确认已超过 5 分钟`
  - 可选：桌面通知（需用户配置）

**交互界面**：
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 需要审批：文件修改操作                                     │
├─────────────────────────────────────────────────────────────┤
│ 操作类型：Edit                                               │
│ 目标文件：src/api/auth.go                                    │
│ 变更摘要：添加 JWT 验证逻辑（+45 行，-3 行）                 │
│ 影响范围：单文件，不影响其他模块                             │
│ 风险评分：5.2 / 10（中等风险）                               │
├─────────────────────────────────────────────────────────────┤
│ 请选择操作：                                                 │
│   ✅ 批准（A）  ❌ 拒绝（R）  📝 修改参数（M）  ⏸️ 暂停（P） │
└─────────────────────────────────────────────────────────────┘
```

**日志记录**：
```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "operation": {
    "tool": "Edit",
    "file": "src/api/auth.go",
    "summary": "添加 JWT 验证逻辑"
  },
  "risk_level": "review",
  "risk_score": 5.2,
  "approval_required": true,
  "approval": {
    "requested_at": "2026-03-20T10:30:00Z",
    "user_decision": "approved",
    "decided_at": "2026-03-20T10:31:15Z",
    "response_time_seconds": 75,
    "notes": "User reviewed changes and confirmed"
  },
  "executed": true,
  "execution_time_ms": 1230
}
```

**示例操作**：
- `Edit file: src/config/settings.json`
- `Write new file: tests/test_auth.py`
- `npm install express@4.18.0`
- `git commit -m 'feat: add user auth'`

---

### Level 3: mandatory（强制审批）

**触发条件**：
- 风险等级 = `mandatory`（风险评分 7-10）
- 永远强制，不受信任模式影响

**审批行为**：
1. **立即暂停执行**
2. **展示详细警告**：
   - ⚠️ **高风险操作警告标识**
   - 操作类型和目标（高亮显示）
   - **详细影响说明**（受影响的资源、潜在风险）
   - **不可逆性提醒**
   - 风险评分和分级原因
3. **用户必须明确确认**：
   - ✅ **明确批准（Explicit Approve）**：输入确认文本后执行
   - ❌ **拒绝（Reject，默认）**：不执行该操作
   - 🛑 **中止任务（Abort）**：终止整个任务

**超时处理**：
- **超时时间**：10 分钟（可配置，建议较长）
- **超时行为**：**自动拒绝**并记录
- **提醒方式**：
  - 终端输出：`🛑 高风险操作超时未确认，已自动拒绝：rm -rf dist/`
  - 桌面通知（强烈建议）

**交互界面**：
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  高风险操作警告                                           │
├─────────────────────────────────────────────────────────────┤
│ 操作类型：Bash (destructive)                                │
│ 命令：rm -rf dist/                                           │
│ 风险评分：8.7 / 10（高风险）                                 │
├─────────────────────────────────────────────────────────────┤
│ 影响说明：                                                   │
│   • 将删除 dist/ 目录及所有内容（约 1.2 GB）                 │
│   • 操作不可逆，无法通过 git 恢复                            │
│   • 可能影响当前部署的构建产物                               │
├─────────────────────────────────────────────────────────────┤
│ 分级原因：                                                   │
│   • 包含破坏性关键字：rm -rf                                 │
│   • 不可逆操作（可逆性评分：10/10）                          │
│   • 批量删除文件（影响范围评分：7/10）                       │
├─────────────────────────────────────────────────────────────┤
│ ⚠️  此操作不可逆！请仔细确认后再继续。                       │
│                                                              │
│ 如需继续，请输入确认文本：DELETE dist                        │
│ 否则输入 N 拒绝，或输入 A 中止整个任务                       │
└─────────────────────────────────────────────────────────────┘
```

**确认文本机制**：
- 用户必须准确输入确认文本（如 `DELETE dist`）才能执行
- 确认文本基于操作内容动态生成
- 防止误触或快速点击导致的意外执行

**日志记录**：
```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "operation": {
    "tool": "Bash",
    "command": "rm -rf dist/",
    "estimated_impact": "删除 dist/ 目录（1.2 GB）"
  },
  "risk_level": "mandatory",
  "risk_score": 8.7,
  "risk_reasons": [
    "包含破坏性关键字：rm -rf",
    "不可逆操作",
    "批量删除文件"
  ],
  "approval_required": true,
  "approval": {
    "requested_at": "2026-03-20T10:30:00Z",
    "confirmation_text_required": "DELETE dist",
    "user_decision": "rejected",
    "decided_at": "2026-03-20T10:32:00Z",
    "response_time_seconds": 120,
    "notes": "User decided not to delete dist/ directory"
  },
  "executed": false,
  "reason": "User rejected the operation"
}
```

**示例操作**：
- `rm -rf dist/`
- `git push --force origin main`
- `DROP TABLE users;`
- `kubectl delete deployment prod-api`
- `POST https://api.stripe.com/v1/charges`

---

## 审批流程

### 完整流程图

```
操作请求
    ↓
风险分级器（Risk Classifier）
    ↓
┌───────────────────────────────┐
│ 风险等级？                     │
├───────────────────────────────┤
│  auto      review    mandatory│
└───┬───────────┬──────────┬────┘
    ↓           ↓          ↓
  执行      展示摘要   展示详细警告
    │           ↓          ↓
    │      等待确认   等待明确确认
    │           ↓          ↓
    │    ┌──────┴──────┐  ┌─────┴─────┐
    │    │批准｜拒绝    │  │批准｜拒绝  │
    │    └──┬───┬──────┘  └──┬───┬────┘
    │       ↓   ↓            ↓   ↓
    │      执行 跳过         执行 跳过
    └───────┴────────────────┴────┘
              ↓
          记录审批日志
              ↓
          返回结果
```

### 状态机

```
[待分级] ──分级──→ [待审批]
                      │
                      ├─ auto → [自动执行] → [已执行]
                      │
                      ├─ review → [等待确认]
                      │              ├─ 批准 → [已执行]
                      │              ├─ 拒绝 → [已跳过]
                      │              ├─ 修改 → [待分级]（重新评估）
                      │              └─ 超时 → [已阻塞]
                      │
                      └─ mandatory → [等待强制确认]
                                       ├─ 明确批准 → [已执行]
                                       ├─ 拒绝 → [已跳过]
                                       ├─ 中止 → [任务终止]
                                       └─ 超时 → [已拒绝]（自动）
```

---

## 配置选项

### 全局配置（`.claude/task.local.md`）

```yaml
---
hitl:
  # 启用/禁用 HITL 审批
  enabled: true

  # 信任模式（review → auto）
  trust_mode: false

  # 超时配置
  timeout:
    review_seconds: 300      # review 级别超时时间（5 分钟）
    mandatory_seconds: 600   # mandatory 级别超时时间（10 分钟）

  # 超时行为
  timeout_behavior:
    review: "block"          # block | auto_approve | auto_reject
    mandatory: "auto_reject" # block | auto_reject

  # 通知配置
  notifications:
    desktop_enabled: false   # 是否启用桌面通知
    sound_enabled: false     # 是否启用声音提示

  # 风险等级覆盖（优先级高于默认规则）
  overrides:
    - pattern: "npm install*"
      risk_level: "auto"
    - pattern: "git push origin feature/*"
      risk_level: "auto"

  # 批量审批模式
  batch_approval:
    enabled: false           # 是否允许批量审批相同操作
    max_batch_size: 10       # 批量审批最大数量
---
```

### 运行时配置（命令行）

```bash
# 启用信任模式（当前会话）
/add --trust-mode

# 禁用 HITL 审批（当前会话，不推荐）
/add --no-hitl

# 设置审批超时时间
/add --review-timeout=600  # 10 分钟
```

---

## 审批日志管理

### 日志存储位置

```
.claude/
├── plans/
│   └── {task_hash}/
│       ├── plan.md                    # 任务计划
│       └── approval-log.json          # 审批日志
```

### 日志结构

```json
{
  "task_hash": "abc123def456",
  "task_description": "实现用户认证功能",
  "created_at": "2026-03-20T10:00:00Z",
  "approvals": [
    {
      "id": "approval-001",
      "timestamp": "2026-03-20T10:30:00Z",
      "operation": {
        "tool": "Edit",
        "target": "src/api/auth.go",
        "summary": "添加 JWT 验证逻辑"
      },
      "risk_classification": {
        "level": "review",
        "score": 5.2,
        "reasons": ["文件修改", "中等复杂度"]
      },
      "approval": {
        "required": true,
        "requested_at": "2026-03-20T10:30:00Z",
        "user_decision": "approved",
        "decided_at": "2026-03-20T10:31:15Z",
        "response_time_seconds": 75,
        "notes": ""
      },
      "execution": {
        "executed": true,
        "execution_time_ms": 1230,
        "result": "success"
      }
    }
  ],
  "statistics": {
    "total_operations": 15,
    "auto_approved": 8,
    "user_reviewed": 5,
    "user_approved": 4,
    "user_rejected": 1,
    "mandatory_count": 2,
    "mandatory_approved": 1,
    "mandatory_rejected": 1,
    "average_response_time_seconds": 62
  }
}
```

### 日志查询

```bash
# 查看当前任务的审批日志
/task-approval-log

# 查看所有任务的审批统计
/task-approval-stats

# 导出审批日志为 CSV（用于合规审计）
/task-approval-export --format=csv --output=approvals.csv
```

---

## 审批追溯性（EU AI Act 合规）

### 合规要求

根据 EU AI Act Article 14（Human Oversight）：
1. ✅ **决策可追溯**：所有审批决策必须记录在案
2. ✅ **时间戳记录**：记录请求时间和决策时间
3. ✅ **用户身份**：记录做出决策的用户（通过系统用户名）
4. ✅ **审计能力**：支持导出审批日志用于审计

### 审计报告生成

```json
{
  "audit_report": {
    "generated_at": "2026-03-20T11:00:00Z",
    "period": {
      "start": "2026-03-01T00:00:00Z",
      "end": "2026-03-20T11:00:00Z"
    },
    "total_tasks": 25,
    "total_operations": 387,
    "approval_statistics": {
      "auto_approved": 310,
      "user_reviewed": 62,
      "user_approved": 55,
      "user_rejected": 7,
      "mandatory_count": 15,
      "mandatory_approved": 12,
      "mandatory_rejected": 3
    },
    "compliance_status": "✅ COMPLIANT",
    "notes": "All high-risk operations required human approval"
  }
}
```

---

## 批量审批模式

### 使用场景

当多个相同类型的操作需要审批时（如批量文件修改），可启用批量审批模式。

### 触发条件

- 连续 3 个相同类型的 review 级别操作
- 用户配置允许批量审批

### 交互界面

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 批量审批请求：文件修改操作                                 │
├─────────────────────────────────────────────────────────────┤
│ 操作类型：Edit                                               │
│ 操作数量：5 个文件                                           │
│ 目标文件：                                                   │
│   1. src/api/auth.go      （+45 行，-3 行）                  │
│   2. src/api/users.go     （+32 行，-1 行）                  │
│   3. src/models/user.go   （+18 行，-0 行）                  │
│   4. src/config/jwt.go    （+28 行，-5 行）                  │
│   5. tests/test_auth.py   （+120 行，-0 行）                 │
│ 总变更：+243 行，-9 行                                       │
│ 风险评分：5.8 / 10（中等风险）                               │
├─────────────────────────────────────────────────────────────┤
│ 请选择操作：                                                 │
│   ✅ 批量批准（A）  ❌ 全部拒绝（R）  📋 逐个审批（I）       │
└─────────────────────────────────────────────────────────────┘
```

### 限制

- 批量审批仅适用于 review 级别操作
- mandatory 级别操作必须逐个审批
- 批量数量上限：10 个操作（可配置）

---

## 验收标准

- ✅ **AC1**: review 级别操作触发审批，展示摘要和确认选项
- ✅ **AC2**: mandatory 级别操作强制确认，要求输入确认文本
- ✅ **AC3**: auto 级别操作静默通过，不打断用户
- ✅ **AC4**: 审批超时后按配置行为处理（block/auto_approve/auto_reject）
- ✅ **AC5**: 审批日志完整记录到 `.claude/plans/{task_hash}/approval-log.json`
- ✅ **AC6**: 支持用户配置覆盖（`.claude/task.local.md`）
- ✅ **AC7**: 支持信任模式（review → auto）
- ✅ **AC8**: 支持批量审批模式（连续相同操作）
- ✅ **AC9**: 审批日志可导出为 CSV 格式用于审计
- ✅ **AC10**: 符合 EU AI Act Article 14 要求（决策可追溯）
