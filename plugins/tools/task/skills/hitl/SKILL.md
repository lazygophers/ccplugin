---
agent: task:loop
description: HITL 审批技能 - 在关键决策点插入人工审批，实现风险分级审批策略，满足 EU AI Act 2026 合规要求
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (5200+ tokens) -->

# Skills(task:hitl) - HITL 审批规范

## 技能概述

Human-in-the-Loop (HITL) 审批技能负责在 task:loop 的关键决策点插入人工审批机制，确保高风险操作得到用户明确确认。基于 EU AI Act 2026 Article 14（Human Oversight）的要求，所有高风险 AI 系统必须有人工监督机制。

**核心能力**：
- ✅ **风险分级**：基于操作类型、影响范围、可逆性等维度自动评估风险等级
- ✅ **三级审批**：auto（自动通过）、review（需审查）、mandatory（强制审批）
- ✅ **审批追溯**：完整记录所有审批决策，支持合规审计
- ✅ **超时保护**：审批超时后按策略阻塞或拒绝，防止意外执行
- ✅ **批量审批**：相同操作可批量确认，提升效率

**设计原则**：
1. **安全优先**：默认拒绝高风险操作，宁可阻塞也不误执行
2. **用户体验**：80%+ 操作自动通过（auto），不打断用户工作流
3. **可追溯性**：所有决策记录在案，符合合规要求
4. **可配置性**：支持用户自定义风险阈值和审批策略

---

## 风险分级体系

### 三级分类（详见 `risk-classifier.md`）

| 级别 | 风险评分 | 审批行为 | 适用操作 | 示例 |
|------|---------|---------|---------|------|
| **auto** | 0-3 | 自动通过，无需确认 | 只读/生成/测试 | Read、Grep、go test |
| **review** | 4-6 | 展示摘要，等待确认 | 文件修改/依赖安装 | Edit、Write、npm install |
| **mandatory** | 7-10 | 详细警告，强制确认 | 破坏性/不可逆操作 | rm -rf、git push --force |

### 风险评估维度

| 维度 | 权重 | 评分规则 |
|------|------|---------|
| **可逆性** | 40% | 完全可逆=0，部分可逆=5，不可逆=10 |
| **影响范围** | 30% | 单文件=0，多文件=3，跨系统=7，生产=10 |
| **敏感性** | 20% | 公开数据=0，内部数据=5，敏感数据=10 |
| **外部影响** | 10% | 无外部影响=0，读取外部=3，修改外部=10 |

**总分计算**：`score = 可逆性×0.4 + 影响范围×0.3 + 敏感性×0.2 + 外部影响×0.1`

---

## 审批流程

### 完整流程图

```
操作请求
    ↓
风险分级器
    ├─ 规则1: 关键字匹配（rm -rf、--force、DROP TABLE）→ mandatory
    ├─ 规则2: 工具类型（Read/Grep → auto，SendMessage → mandatory）
    ├─ 规则3: 环境判断（production → mandatory）
    ├─ 规则4: 文件路径（.env、id_rsa → mandatory）
    └─ 规则5: 操作类型（Edit/Write → review）
    ↓
风险等级判定
    ├─ auto → 静默执行 → 记录日志 → 完成
    ├─ review → 展示摘要 → 等待确认
    │              ├─ 批准 → 执行 → 记录日志 → 完成
    │              ├─ 拒绝 → 跳过 → 记录日志 → 完成
    │              ├─ 修改 → 重新评估 → 返回风险分级器
    │              └─ 超时 → 阻塞 → 提醒用户
    └─ mandatory → 详细警告 → 等待强制确认
                   ├─ 明确批准 → 执行 → 记录日志 → 完成
                   ├─ 拒绝 → 跳过 → 记录日志 → 完成
                   ├─ 中止 → 终止任务
                   └─ 超时 → 自动拒绝 → 记录日志 → 完成
```

### 状态机

```
[待分级] → [待审批] → [auto] → [自动执行] → [已执行]
                     ↓ [review] → [等待确认] → [批准/拒绝/修改/超时]
                     ↓ [mandatory] → [等待强制确认] → [批准/拒绝/中止/超时]
```

---

## API 接口

### 主接口：`hitl_approve_operation`

```python
def hitl_approve_operation(
    operation: dict,
    context: dict = None,
    user_config: dict = None
) -> dict:
    """
    HITL 审批主接口

    Args:
        operation: {
            "tool": str,              # 工具名称（必需）
            "command": str,           # 命令文本（Bash）
            "files": List[str],       # 涉及的文件路径
            "method": str,            # HTTP 方法（WebFetch）
            "target": str,            # 操作目标描述
            "summary": str            # 操作摘要
        }
        context: {
            "environment": str,       # 环境标识（production/staging/dev）
            "task_hash": str,         # 当前任务哈希
            "iteration": int          # 当前迭代次数
        }
        user_config: {
            "trust_mode": bool,       # 是否启用信任模式
            "timeout_seconds": int,   # 审批超时时间
            "overrides": List[dict]   # 风险等级覆盖规则
        }

    Returns: {
        "approved": bool,             # 是否批准执行
        "risk_classification": {
            "level": str,             # auto | review | mandatory
            "score": float,           # 风险评分 0-10
            "reasons": List[str]      # 分级原因
        },
        "approval": {
            "required": bool,         # 是否需要用户确认
            "user_decision": str,     # approved | rejected | timeout
            "response_time_seconds": int,
            "notes": str
        },
        "log_entry": dict             # 审批日志条目
    }
    """
```

### 辅助接口

```python
def classify_risk(operation: dict, context: dict) -> dict:
    """风险分级接口，返回风险等级和评分"""

def request_approval(
    operation: dict,
    risk_classification: dict,
    timeout_seconds: int
) -> dict:
    """请求用户审批，返回用户决策"""

def log_approval(
    task_hash: str,
    operation: dict,
    risk_classification: dict,
    approval: dict
) -> None:
    """记录审批决策到日志文件"""

def load_user_config() -> dict:
    """加载用户配置（.claude/task.local.md）"""
```

---

## 集成点（Loop 流程）

### 集成点 1: 计划确认（Plan Confirmation）

**位置**：`skills/loop/flows/plan.md` - 步骤 3

**触发时机**：planner 生成计划后，执行前

**审批内容**：
- 整体执行计划（任务分解、依赖关系、资源分配）
- 风险评估摘要（预计会触发多少次 review/mandatory 审批）
- 预估成本和时间

**实现**：
```python
# 步骤 3: 计划确认（增强 HITL）
plan = planner_result["plan"]
risk_summary = analyze_plan_risks(plan)  # 新增：风险摘要分析

# 展示计划 + 风险摘要
print(f"## 执行计划\n{plan}")
print(f"\n## 风险评估\n{risk_summary}")

# HITL 审批
approval = hitl_approve_operation(
    operation={
        "tool": "TaskExecute",
        "target": f"{len(plan['tasks'])} 个任务",
        "summary": plan["summary"]
    },
    context={"risk_summary": risk_summary}
)

if not approval["approved"]:
    return {"status": "plan_rejected", "reason": approval["approval"]["notes"]}
```

**风险摘要示例**：
```
## 风险评估

预计操作分布：
  • auto（自动通过）: 12 个操作（80%）
  • review（需审查）: 2 个操作（13%） - 文件修改、依赖安装
  • mandatory（强制审批）: 1 个操作（7%） - git push origin main

高风险操作提醒：
  ⚠️ 任务 T3: git push origin main（mandatory 级别，需要明确确认）
```

---

### 集成点 2: 任务执行前（Pre-Execution）

**位置**：`skills/loop/detailed-flow.md` - 阶段 4（执行阶段）

**触发时机**：每个任务执行前

**审批内容**：
- 单个任务的所有工具调用（Edit、Write、Bash 等）
- 逐个操作评估风险等级

**实现**：
```python
# 阶段 4: 任务执行（集成 HITL）
for task in pending_tasks:
    print(f"[MindFlow·{user_task}·执行/{iteration}·进行中] 任务 {task['id']}")

    # 执行任务（内部包含 HITL 审批）
    result = execute_task_with_hitl(task, context)

    if result["status"] == "rejected_by_user":
        # 用户拒绝了某个操作
        failed_tasks.append({
            "id": task["id"],
            "reason": "User rejected operation",
            "details": result["rejected_operation"]
        })
        continue

    if result["status"] == "success":
        completed_tasks.append(task["id"])
```

**execute_task_with_hitl 实现**：
```python
def execute_task_with_hitl(task: dict, context: dict) -> dict:
    """
    执行任务，集成 HITL 审批

    对 Agent 调用的每个工具操作进行 HITL 审批
    """
    agent_result = Agent(
        agent=task["agent"],
        prompt=task["prompt"]
    )

    # 拦截 agent 的工具调用，逐个审批
    for tool_use in agent_result["tool_uses"]:
        approval = hitl_approve_operation(
            operation={
                "tool": tool_use["tool"],
                "command": tool_use.get("command"),
                "files": tool_use.get("files", []),
                ...
            },
            context=context
        )

        if not approval["approved"]:
            return {
                "status": "rejected_by_user",
                "rejected_operation": tool_use,
                "approval": approval["approval"]
            }

    return {"status": "success", "result": agent_result}
```

---

### 集成点 3: 危险操作拦截（Dangerous Operation Intercept）

**位置**：`skills/loop/detailed-flow.md` - 阶段 6（失败调整）

**触发时机**：adjuster 建议执行危险操作时

**审批内容**：
- adjuster 建议的自愈操作（如自动删除文件、修改配置）
- 重新规划建议（如大幅调整任务分解）

**实现**：
```python
# 阶段 6: 失败调整（集成 HITL）
adjuster_result = Agent(
    agent="task:adjuster",
    prompt=f"分析失败原因并建议恢复策略：{failure_info}"
)

recovery_action = adjuster_result["recovery_action"]

# HITL 审批 adjuster 建议的操作
approval = hitl_approve_operation(
    operation={
        "tool": "AdjusterAction",
        "target": recovery_action["type"],
        "summary": recovery_action["description"]
    },
    context={"failure_count": failure_count}
)

if not approval["approved"]:
    # 用户拒绝了 adjuster 的建议，请求用户指导
    user_guidance = AskUserQuestion(
        questions=[{
            "question": f"Adjuster 建议的恢复操作被拒绝：{recovery_action['description']}。请问如何处理？",
            "options": [
                {"label": "手动修复", "description": "暂停任务，由用户手动修复"},
                {"label": "跳过该任务", "description": "标记该任务失败，继续其他任务"},
                {"label": "终止循环", "description": "停止所有任务执行"}
            ]
        }]
    )
```

---

## 审批界面设计

### review 级别界面

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 需要审批：文件修改操作                                     │
├─────────────────────────────────────────────────────────────┤
│ 任务：T2 - 实现 API 接口                                     │
│ 操作类型：Edit                                               │
│ 目标文件：src/api/auth.go                                    │
│ 变更摘要：添加 JWT 验证逻辑（+45 行，-3 行）                 │
│ 影响范围：单文件，不影响其他模块                             │
│ 风险评分：5.2 / 10（中等风险）                               │
├─────────────────────────────────────────────────────────────┤
│ 请选择操作：                                                 │
│   ✅ 批准（A）  ❌ 拒绝（R）  📝 修改参数（M）  ⏸️ 暂停（P） │
└─────────────────────────────────────────────────────────────┘
输入选择（A/R/M/P）:
```

### mandatory 级别界面

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  高风险操作警告                                           │
├─────────────────────────────────────────────────────────────┤
│ 任务：T5 - 清理临时文件                                      │
│ 操作类型：Bash (destructive)                                │
│ 命令：rm -rf .cache/                                         │
│ 风险评分：8.7 / 10（高风险）                                 │
├─────────────────────────────────────────────────────────────┤
│ 影响说明：                                                   │
│   • 将删除 .cache/ 目录及所有内容（约 450 MB）               │
│   • 操作不可逆，无法通过 git 恢复                            │
│   • 可能包含未保存的中间结果                                 │
├─────────────────────────────────────────────────────────────┤
│ 分级原因：                                                   │
│   • 包含破坏性关键字：rm -rf                                 │
│   • 不可逆操作（可逆性评分：10/10）                          │
│   • 批量删除文件（影响范围评分：7/10）                       │
├─────────────────────────────────────────────────────────────┤
│ ⚠️  此操作不可逆！请仔细确认后再继续。                       │
│                                                              │
│ 如需继续，请输入确认文本：DELETE .cache                      │
│ 否则输入 N 拒绝，或输入 A 中止整个任务                       │
└─────────────────────────────────────────────────────────────┘
输入确认文本或 N/A:
```

---

## 配置选项

### 全局配置（`.claude/task.local.md`）

```yaml
---
hitl:
  # 启用/禁用 HITL 审批
  enabled: true

  # 信任模式（review → auto，mandatory 不受影响）
  trust_mode: false

  # 超时配置
  timeout:
    review_seconds: 300      # 5 分钟
    mandatory_seconds: 600   # 10 分钟

  # 超时行为
  timeout_behavior:
    review: "block"          # block | auto_approve | auto_reject
    mandatory: "auto_reject" # block | auto_reject

  # 通知配置
  notifications:
    desktop_enabled: false
    sound_enabled: false

  # 风险等级覆盖
  overrides:
    - pattern: "npm install*"
      risk_level: "auto"
    - pattern: "git push origin feature/*"
      risk_level: "auto"

  # 批量审批
  batch_approval:
    enabled: false
    max_batch_size: 10
---
```

### 运行时配置（命令行）

```bash
# 启用信任模式（当前会话）
/add --trust-mode

# 禁用 HITL 审批（不推荐，仅用于测试）
/add --no-hitl

# 设置审批超时时间
/add --review-timeout=600
```

---

## 审批日志

### 日志存储

```
.claude/
├── plans/
│   └── {task_hash}/
│       ├── plan.md
│       └── approval-log.json  # 审批日志
```

### 日志格式

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
        "user_decision": "approved",
        "response_time_seconds": 75
      },
      "execution": {
        "executed": true,
        "result": "success"
      }
    }
  ],
  "statistics": {
    "total_operations": 15,
    "auto_approved": 8,
    "user_reviewed": 5,
    "user_approved": 4,
    "user_rejected": 1
  }
}
```

---

## 合规性（EU AI Act）

### Article 14: Human Oversight 要求

| 要求 | 实现方式 | 验证 |
|------|---------|------|
| **高风险操作需人工监督** | mandatory 级别强制确认 | ✅ |
| **决策可追溯** | 审批日志记录所有决策 | ✅ |
| **时间戳记录** | 记录请求和决策时间 | ✅ |
| **用户身份** | 记录系统用户名 | ✅ |
| **审计能力** | 支持导出 CSV 格式 | ✅ |

### 审计报告生成

```bash
# 生成合规审计报告
/task-audit-report --period=2026-03 --format=json

# 导出审批日志（CSV）
/task-approval-export --format=csv --output=approvals.csv
```

---

## 使用示例

### 示例 1: 文件修改（review 级别）

```python
# loop 执行过程中
operation = {
    "tool": "Edit",
    "files": ["src/api/auth.go"],
    "summary": "添加 JWT 验证逻辑"
}

approval = hitl_approve_operation(operation)
# 用户看到审批界面，选择批准
# approval = {
#     "approved": True,
#     "risk_classification": {"level": "review", "score": 5.2},
#     "approval": {"user_decision": "approved", "response_time_seconds": 15}
# }

if approval["approved"]:
    # 执行文件修改
    Edit(file="src/api/auth.go", ...)
```

### 示例 2: 破坏性操作（mandatory 级别）

```python
operation = {
    "tool": "Bash",
    "command": "rm -rf dist/"
}

approval = hitl_approve_operation(operation)
# 用户看到高风险警告，需要输入确认文本 "DELETE dist"
# 用户选择拒绝
# approval = {
#     "approved": False,
#     "risk_classification": {"level": "mandatory", "score": 8.7},
#     "approval": {"user_decision": "rejected"}
# }

if not approval["approved"]:
    print("操作已拒绝，跳过该步骤")
```

### 示例 3: 信任模式

```python
# 用户配置信任模式
# .claude/task.local.md:
# ---
# hitl:
#   trust_mode: true
# ---

operation = {
    "tool": "Write",
    "files": ["tests/test_auth.py"]
}

approval = hitl_approve_operation(operation)
# 信任模式下，review 级别自动通过
# approval = {
#     "approved": True,
#     "risk_classification": {"level": "review", "score": 4.5},
#     "approval": {"required": False, "user_decision": "auto_approved_trust_mode"}
# }
```

---

## 最佳实践

### 1. 合理设置风险阈值

- **开发环境**：信任模式（review → auto），提升效率
- **生产环境**：严格模式（mandatory 不可跳过），确保安全

### 2. 利用风险等级覆盖

```yaml
# 信任常见操作
overrides:
  - pattern: "npm install*"
    risk_level: "auto"
  - pattern: "go test*"
    risk_level: "auto"
  - pattern: "git push origin feature/*"
    risk_level: "auto"
```

### 3. 定期审计日志

```bash
# 每月生成审计报告
/task-audit-report --period=2026-03 --output=audit-2026-03.json
```

### 4. 批量审批模式

当需要修改多个相似文件时，启用批量审批：

```yaml
batch_approval:
  enabled: true
  max_batch_size: 10
```

---

## 性能优化

### 1. 风险分级缓存

对相同操作的风险分级结果缓存 5 分钟，避免重复计算。

### 2. 审批日志异步写入

审批决策立即返回，日志写入异步执行，不阻塞任务执行。

### 3. 批量日志写入

积累 10 条日志后批量写入文件，减少 I/O 开销。

---

## 故障处理

### 1. 审批超时

**现象**：用户未在超时时间内确认

**处理**：
- review 级别：阻塞并提醒用户
- mandatory 级别：自动拒绝

### 2. 日志写入失败

**现象**：磁盘空间不足或权限问题

**处理**：
- 降级为内存日志
- 警告用户并继续执行
- 任务完成后尝试重新写入

### 3. 用户配置损坏

**现象**：`.claude/task.local.md` 格式错误

**处理**：
- 忽略损坏配置
- 使用默认配置
- 警告用户修复配置文件

---

## 验收标准

- ✅ **AC1**: 风险操作（文件删除、git force push）100% 触发 mandatory 审批
- ✅ **AC2**: 低风险操作（代码生成、测试运行）自动通过，无用户干扰
- ✅ **AC3**: 审批超时（可配置，默认 5 分钟）自动阻塞并提醒用户
- ✅ **AC4**: 审批记录追溯：每次审批决策记录在计划文件的审批日志中
- ✅ **AC5**: 通过质量检查命令验证 AI 可正确理解 HITL 技能
- ✅ **AC6**: 支持用户配置覆盖（`.claude/task.local.md`）
- ✅ **AC7**: 支持信任模式（review → auto，mandatory 不受影响）
- ✅ **AC8**: 支持批量审批模式（连续相同操作）
- ✅ **AC9**: mandatory 级别操作要求输入确认文本
- ✅ **AC10**: 符合 EU AI Act Article 14 要求（决策可追溯）

<!-- /STATIC_CONTENT -->
