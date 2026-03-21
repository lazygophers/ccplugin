#!/usr/bin/env python3
"""
修复 hitl_demo 中的强制确认逻辑
"""
import os
from typing import Dict, List, Any

def hitl_approve_operation_deletion_fixed(
    file_paths: list,
    user_decision: str = "auto_approved"
) -> dict:
    """
    修复后的 task:hitl 审批逻辑
    """

    # 风险评估（保持不变）
    risk_score = 0
    risk_factors = []

    for file_path in file_paths:
        if os.path.exists(file_path):
            risk_score += 4
            risk_factors.append(f"删除存在文件: {file_path}")
        else:
            risk_score += 1

        if file_path.startswith('/'):
            risk_score += 2
        else:
            risk_score += 1

        sensitive_patterns = ['.env', 'config', 'secret', 'id_rsa', 'pem', 'keys']
        if any(pattern in file_path.lower() for pattern in sensitive_patterns):
            risk_score += 5
            risk_factors.append(f"敏感文件: {file_path}")

        if file_path.startswith('/tmp') or file_path.startswith('/var'):
            risk_score += 3

    # 确定风险等级
    if risk_score >= 7:
        risk_level = "mandatory"
    elif risk_score >= 4:
        risk_level = "review"
    else:
        risk_level = "auto"

    # 修复后的审批逻辑
    if risk_level == "auto":
        approved = True
        user_decision_text = "auto_approved"
    elif risk_level == "review":
        if user_decision in ["approved", "auto_approved_trust_mode"]:
            approved = True
            user_decision_text = user_decision
        else:
            approved = False
            user_decision_text = "rejected"
    else:  # mandatory
        # 修复：正确检查用户是否提供了确认文本
        if user_decision == "approved":
            approved = True
            user_decision_text = "approved"
        else:
            approved = False
            user_decision_text = "rejected"

    return {
        "approved": approved,
        "risk_classification": {
            "level": risk_level,
            "score": min(risk_score, 10),
            "reasons": risk_factors
        },
        "approval": {
            "required": risk_level != "auto",
            "user_decision": user_decision_text,
            "response_time_seconds": 15 if risk_level == "review" else 30
        }
    }

def test_fixed_version():
    """测试修复后的版本"""

    print("🔧 修复后的审批测试")
    print("=" * 40)

    high_risk_files = ["config/secrets.yaml", ".env.production"]

    # 测试批准情况
    result_approved = hitl_approve_operation_deletion_fixed(high_risk_files, "approved")
    print(f"\n高风险文件 (已批准):")
    print(f"风险等级: {result_approved['risk_classification']['level']}")
    print(f"审批结果: {'✅ 通过' if result_approved['approved'] else '❌ 拒绝'}")
    print(f"用户决策: {result_approved['approval']['user_decision']}")

    # 测试拒绝情况
    result_rejected = hitl_approve_operation_deletion_fixed(high_risk_files, "rejected")
    print(f"\n高风险文件 (已拒绝):")
    print(f"风险等级: {result_rejected['risk_classification']['level']}")
    print(f"审批结果: {'✅ 通过' if result_rejected['approved'] else '❌ 拒绝'}")
    print(f"用户决策: {result_rejected['approval']['user_decision']}")

if __name__ == "__main__":
    test_fixed_version()