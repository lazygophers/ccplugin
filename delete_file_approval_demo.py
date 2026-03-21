#!/usr/bin/env python3
"""
task:hitl 技能删除文件审批示例 - 非交互版本
演示不同风险等级的审批流程
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

def hitl_approve_operation_deletion(
    file_paths: List[str],
    user_decision: str = "auto_approved"
) -> Dict[str, Any]:
    """
    task:hitl 技能的核心审批逻辑 - 删除文件操作

    Args:
        file_paths: 要删除的文件路径列表
        user_decision: 用户决策（用于演示）

    Returns:
        审批结果
    """

    # 风险评估
    risk_score = 0
    risk_factors = []

    for file_path in file_paths:
        # 可逆性评分 (40% 权重)
        if os.path.exists(file_path):
            risk_score += 4  # 存在的文件删除不可逆
            risk_factors.append(f"删除存在文件: {file_path}")
        else:
            risk_score += 1  # 不存在的文件风险低

        # 影响范围评分 (30% 权重)
        if file_path.startswith('/'):
            risk_score += 2  # 绝对路径
        else:
            risk_score += 1  # 相对路径

        # 敏感性评分 (20% 权重)
        sensitive_patterns = ['.env', 'config', 'secret', 'id_rsa', 'pem', 'keys']
        if any(pattern in file_path.lower() for pattern in sensitive_patterns):
            risk_score += 5
            risk_factors.append(f"敏感文件: {file_path}")

        # 外部影响评分 (10% 权重)
        if file_path.startswith('/tmp') or file_path.startswith('/var'):
            risk_score += 3  # 系统目录

    # 确定风险等级
    if risk_score >= 7:
        risk_level = "mandatory"
    elif risk_score >= 4:
        risk_level = "review"
    else:
        risk_level = "auto"

    # 根据风险等级和用户决策生成结果
    if risk_level == "auto":
        # auto 级别自动通过
        approved = True
        user_decision_text = "auto_approved"
    elif risk_level == "review":
        # review 级别根据用户决策
        if user_decision in ["approved", "auto_approved_trust_mode"]:
            approved = True
            user_decision_text = user_decision
        else:
            approved = False
            user_decision_text = "rejected"
    else:  # mandatory
        # mandatory 级别需要特殊确认
        if user_decision == "approved" and "DELETE FILES" in user_decision:
            approved = True
            user_decision_text = "approved_with_confirmation"
        else:
            approved = False
            user_decision_text = "rejected"

    # 构建返回结果
    result = {
        "approved": approved,
        "risk_classification": {
            "level": risk_level,
            "score": min(risk_score, 10),  # 限制最高分
            "reasons": risk_factors
        },
        "approval": {
            "required": risk_level != "auto",
            "user_decision": user_decision_text,
            "response_time_seconds": 15 if risk_level == "review" else 30
        },
        "operation": {
            "tool": "Bash",
            "command": f"rm -f {' '.join(file_paths)}",
            "target": f"删除 {len(file_paths)} 个文件",
            "summary": f"删除文件: {', '.join(file_paths)}"
        },
        "log_entry": {
            "timestamp": datetime.now().isoformat(),
            "task_hash": "demo_task_123",
            "operation_type": "delete_files",
            "files": file_paths,
            "risk_classification": risk_level,
            "user_decision": user_decision_text,
            "approved": approved
        }
    }

    return result

def demo_scenarios():
    """演示不同场景的审批流程"""

    print("🔍 task:hitl 技能 - 删除文件审批示例")
    print("=" * 70)

    # 场景 1: 低风险操作 (auto)
    print("\n📋 场景 1: 低风险操作 (auto 级别)")
    print("-" * 50)
    safe_files = ["logs/output.log", "temp/tmp.txt"]
    result1 = hitl_approve_operation_deletion(safe_files, "auto_approved")
    print(f"文件: {safe_files}")
    print(f"风险等级: {result1['risk_classification']['level']}")
    print(f"风险评分: {result1['risk_classification']['score']}/10")
    print(f"审批结果: {'✅ 自动通过' if result1['approved'] else '❌ 拒绝'}")
    print(f"用户决策: {result1['approval']['user_decision']}")
    print("说明: 低风险操作自动通过，无需用户确认")

    # 场景 2: 中等风险操作 (review)
    print("\n📋 场景 2: 中等风险操作 (review 级别)")
    print("-" * 50)
    medium_files = ["src/old_module.py", "docs/legacy.md"]
    result2 = hitl_approve_operation_deletion(medium_files, "approved")
    print(f"文件: {medium_files}")
    print(f"风险等级: {result2['risk_classification']['level']}")
    print(f"风险评分: {result2['risk_classification']['score']}/10")
    print(f"审批结果: {'✅ 需要用户确认后通过' if result2['approved'] else '❌ 用户拒绝'}")
    print(f"用户决策: {result2['approval']['user_decision']}")
    print("说明: 中等风险操作需要用户确认")

    # 场景 3: 高风险操作 (mandatory)
    print("\n📋 场景 3: 高风险操作 (mandatory 级别)")
    print("-" * 50)
    high_risk_files = ["config/secrets.yaml", ".env.production"]
    result3_rejected = hitl_approve_operation_deletion(high_risk_files, "rejected")
    print(f"文件: {high_risk_files}")
    print(f"风险等级: {result3_rejected['risk_classification']['level']}")
    print(f"风险评分: {result3_rejected['risk_classification']['score']}/10")
    print(f"审批结果: {'❌ 拒绝 (缺少确认文本)' if not result3_rejected['approved'] else '✅ 通过'}")
    print(f"用户决策: {result3_rejected['approval']['user_decision']}")

    # 正确的 mandatory 审批
    result3_approved = hitl_approve_operation_deletion(
        high_risk_files,
        "approved_with_confirmation_text_DELETE_FILES"
    )
    print(f"\n✅ 正确输入确认文本后:")
    print(f"审批结果: {'✅ 通过' if result3_approved['approved'] else '❌ 拒绝'}")
    print(f"用户决策: {result3_approved['approval']['user_decision']}")
    print("说明: 高风险操作必须输入确认文本才能通过")

    # 保存审批日志示例
    save_approval_log([result1, result2, result3_rejected, result3_approved])

    return [result1, result2, result3_rejected, result3_approved]

def save_approval_log(results: List[Dict]):
    """保存审批日志"""

    log_data = {
        "session_id": "demo_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().isoformat(),
        "total_operations": len(results),
        "statistics": {
            "auto_approved": sum(1 for r in results if r["risk_classification"]["level"] == "auto"),
            "review_approved": sum(1 for r in results if r["risk_classification"]["level"] == "review" and r["approved"]),
            "mandatory_approved": sum(1 for r in results if r["risk_classification"]["level"] == "mandatory" and r["approved"]),
            "rejected": sum(1 for r in results if not r["approved"])
        },
        "approvals": results
    }

    log_file = "deletion_approval_demo_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"\n📁 审批日志已保存: {log_file}")
    print(f"包含 {len(results)} 条审批记录")

def show_configuration_example():
    """显示配置文件示例"""

    print("\n" + "=" * 70)
    print("⚙️  task:hitl 配置示例 (claude/task.local.md)")
    print("=" * 70)

    config_example = """---
# HITL 审批配置
hitl:
  # 启用 HITL 审批
  enabled: true

  # 信任模式（review 级别自动通过）
  trust_mode: false

  # 超时设置
  timeout:
    review_seconds: 300    # review 级别超时 5 分钟
    mandatory_seconds: 600 # mandatory 级别超时 10 分钟

  # 超时行为
  timeout_behavior:
    review: "block"          # block | auto_approve | auto_reject
    mandatory: "auto_reject" # block | auto_reject

  # 风险等级覆盖规则
  overrides:
    # 信任常见的 npm 清理操作
    - pattern: "npm cache clean*"
      risk_level: "auto"

    # 信任非生产环境的 git 操作
    - pattern: "git push origin feature/*"
      risk_level: "auto"

    # 永远要求审批危险操作
    - pattern: "rm -rf*"
      risk_level: "mandatory"

  # 通知设置
  notifications:
    desktop_enabled: true
    sound_enabled: false
---
"""

    print(config_example)

if __name__ == "__main__":
    # 运行演示
    results = demo_scenarios()

    # 显示配置示例
    show_configuration_example()

    print("\n" + "=" * 70)
    print("✅ task:hitl 技能演示完成")
    print("核心要点:")
    print("1. auto 级别: 自动通过，无需确认")
    print("2. review 级别: 需要用户确认后执行")
    print("3. mandatory 级别: 必须输入确认文本才能通过")
    print("4. 所有审批决策都会被记录，支持审计")
    print("=" * 70)