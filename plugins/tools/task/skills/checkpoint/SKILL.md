---
description: 检查点管理 - 保存/恢复/清理任务执行状态，支持中断恢复
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:checkpoint) - 检查点管理

<overview>

检查点机制为 MindFlow Loop 提供状态持久化能力，允许任务在中断后恢复执行。每次阶段转换时自动保存检查点，包含当前迭代号、已完成任务、执行进度、上下文状态等关键信息。

核心能力：
- **保存检查点**：在阶段转换时自动保存状态到 JSON 文件
- **恢复检查点**：初始化时检测并恢复上次中断的状态
- **清理检查点**：任务完成后删除检查点文件

使用场景：
- 长时间运行任务意外中断（进程崩溃、网络断开、用户主动终止）
- 需要暂停任务并稍后继续执行
- 调试时需要从特定阶段重新开始

</overview>

<api>

## 核心 API

### 1. save_checkpoint()

在每个阶段转换时保存检查点。

**调用时机**：
- 计划设计完成后
- 计划确认后（用户批准或自动批准）
- 任务执行完成后
- 结果验证完成后
- 失败调整完成后

**参数**：
```python
def save_checkpoint(
    user_task: str,           # 用户任务描述
    iteration: int,           # 当前迭代号
    phase: str,               # 当前阶段（planning/confirmation/execution/verification/adjustment）
    context: dict,            # 上下文状态（replan_trigger等）
    plan_md_path: str = None, # 计划文档路径（可选）
    additional_state: dict = None  # 额外状态信息（可选）
) -> bool:
    """
    保存检查点到 .claude/checkpoints/{task_hash}.json

    返回：
    - True: 保存成功
    - False: 保存失败
    """
```

**实现逻辑**：
```python
import hashlib
import json
from pathlib import Path
from datetime import datetime

def save_checkpoint(user_task, iteration, phase, context, plan_md_path=None, additional_state=None):
    # 生成任务哈希作为检查点文件名
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]

    checkpoints_dir = Path(".claude/checkpoints")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = checkpoints_dir / f"{task_hash}.json"

    # 构建检查点数据（详见 state-serializer.md）
    checkpoint_data = {
        "user_task": user_task,
        "task_hash": task_hash,
        "iteration": iteration,
        "phase": phase,
        "context": context,
        "plan_md_path": str(plan_md_path) if plan_md_path else None,
        "timestamp": datetime.now().isoformat(),
        "additional_state": additional_state or {}
    }

    # 写入 JSON 文件
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        print(f"[MindFlow] ✓ 检查点已保存: {checkpoint_path}")
        return True
    except Exception as e:
        print(f"[MindFlow] ⚠️ 检查点保存失败: {e}")
        return False
```

### 2. load_checkpoint()

初始化时检测并加载上次中断的检查点。

**调用时机**：
- Loop 初始化阶段开始时

**参数**：
```python
def load_checkpoint(
    user_task: str  # 用户任务描述（用于匹配检查点文件）
) -> dict | None:
    """
    从 .claude/checkpoints/{task_hash}.json 加载检查点

    返回：
    - dict: 检查点数据（包含 iteration, phase, context 等）
    - None: 未找到检查点或加载失败
    """
```

**实现逻辑**：
```python
def load_checkpoint(user_task):
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
    checkpoint_path = Path(".claude/checkpoints") / f"{task_hash}.json"

    if not checkpoint_path.exists():
        print(f"[MindFlow] 未找到检查点，从头开始执行")
        return None

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)

        # 验证检查点完整性
        required_fields = ["user_task", "iteration", "phase", "context", "timestamp"]
        if not all(field in checkpoint_data for field in required_fields):
            print(f"[MindFlow] ⚠️ 检查点数据不完整，从头开始执行")
            return None

        # 检查时效性（超过24小时的检查点视为过期）
        from datetime import datetime, timedelta
        checkpoint_time = datetime.fromisoformat(checkpoint_data["timestamp"])
        if datetime.now() - checkpoint_time > timedelta(hours=24):
            print(f"[MindFlow] ⚠️ 检查点已过期（>24小时），从头开始执行")
            return None

        print(f"[MindFlow] ✓ 检测到检查点:")
        print(f"[MindFlow]   迭代: {checkpoint_data['iteration']}")
        print(f"[MindFlow]   阶段: {checkpoint_data['phase']}")
        print(f"[MindFlow]   时间: {checkpoint_data['timestamp']}")

        # 询问用户是否恢复
        user_decision = AskUserQuestion(
            question=f"检测到上次中断的任务（迭代 {checkpoint_data['iteration']}，阶段 {checkpoint_data['phase']}），是否恢复？",
            options=["恢复执行", "重新开始"]
        )

        if user_decision == "恢复执行":
            print(f"[MindFlow] ✓ 从检查点恢复执行")
            return checkpoint_data
        else:
            print(f"[MindFlow] 用户选择重新开始，忽略检查点")
            # 清理旧检查点
            cleanup_checkpoint(user_task)
            return None

    except Exception as e:
        print(f"[MindFlow] ⚠️ 检查点加载失败: {e}")
        return None
```

### 3. cleanup_checkpoint()

任务完成后删除检查点文件。

**调用时机**：
- 任务全部完成阶段（Completion）
- 用户选择重新开始时

**参数**：
```python
def cleanup_checkpoint(
    user_task: str  # 用户任务描述
) -> bool:
    """
    删除检查点文件

    返回：
    - True: 删除成功
    - False: 删除失败或文件不存在
    """
```

**实现逻辑**：
```python
def cleanup_checkpoint(user_task):
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
    checkpoint_path = Path(".claude/checkpoints") / f"{task_hash}.json"

    if not checkpoint_path.exists():
        return False

    try:
        checkpoint_path.unlink()
        print(f"[MindFlow] ✓ 检查点已清理")
        return True
    except Exception as e:
        print(f"[MindFlow] ⚠️ 检查点清理失败: {e}")
        return False
```

</api>

<references>

## 相关文档

- **集成与示例**：详见 [integration-examples.md](./integration-examples.md)
  - Loop 集成方式
  - 使用场景示例

</references>

<notes>

## 注意事项

1. **检查点文件位置**：`.claude/checkpoints/{task_hash}.json`
2. **任务哈希算法**：MD5(user_task)[:12]，确保唯一性
3. **时效性检查**：超过24小时的检查点视为过期
4. **数据完整性**：加载时验证必需字段是否存在
5. **用户确认**：恢复前必须询问用户，避免意外覆盖
6. **清理时机**：任务完成或用户选择重新开始时清理
7. **并发安全**：单个任务同时只能有一个检查点文件
8. **状态一致性**：检查点必须包含完整的上下文状态，确保恢复后逻辑连续

</notes>
