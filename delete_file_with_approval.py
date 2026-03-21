#!/usr/bin/env python3
"""
使用 task:hitl 技能进行删除文件前的人工审批示例
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

def simulate_hitl_skill_for_deletion(file_paths: List[str]) -> Dict[str, Any]:
    """
    模拟 task:hitl 技能的审批流程

    Args:
        file_paths: 要删除的文件路径列表

    Returns:
        审批结果字典
    """
    # 风险评估逻辑
    risk_score = 0
    risk_factors = []

    # 计算风险评分
    for file_path in file_paths:
        # 可逆性评分
        if os.path.exists(file_path):
            risk_score += 4  # 文件存在，删除不可逆
            risk_factors.append(f"删除存在文件: {file_path}")
        else:
            risk_score += 1  # 文件不存在，风险较低

        # 影响范围评分
        if file_path.startswith('/'):
            risk_score += 2  # 绝对路径
        else:
            risk_score += 1  # 相对路径

        # 敏感性评分
        sensitive_patterns = ['.env', 'config', 'secret', 'id_rsa', 'pem']
        if any(pattern in file_path.lower() for pattern in sensitive_patterns):
            risk_score += 5
            risk_factors.append(f"敏感文件: {file_path}")

    # 确定风险等级
    if risk_score >= 7:
        risk_level = "mandatory"
    elif risk_score >= 4:
        risk_level = "review"
    else:
        risk_level = "auto"

    # 生成操作摘要
    summary = f"删除 {len(file_paths)} 个文件"
    if file_paths:
        summary += f": {', '.join(file_paths)}"

    # 模拟审批请求
    print("\n" + "="*60)
    print("📋 删除文件操作审批请求")
    print("="*60)
    print(f"\n操作摘要: {summary}")
    print(f"风险等级: {risk_level.upper()}")
    print(f"风险评分: {risk_score}/10")

    if risk_factors:
        print("\n风险因素:")
        for factor in risk_factors:
            print(f"  ⚠️  {factor}")

    # 显示不同级别的审批界面
    if risk_level == "auto":
        print("\n✅ 低风险操作，自动批准")
        approval = {
            "approved": True,
            "risk_classification": {
                "level": "auto",
                "score": risk_score,
                "reasons": ["低风险操作"]
            },
            "approval": {
                "required": False,
                "user_decision": "auto_approved"
            }
        }
    elif risk_level == "review":
        print("\n📋 需要您确认操作")
        print("请选择: [A]批准 [R]拒绝 [M]查看文件内容")
        choice = input("\n请输入您的选择: ").upper()

        if choice == 'A':
            print("\n✅ 操作已批准")
            approval = {
                "approved": True,
                "risk_classification": {
                    "level": "review",
                    "score": risk_score,
                    "reasons": risk_factors
                },
                "approval": {
                    "required": True,
                    "user_decision": "approved",
                    "response_time": 5
                }
            }
        elif choice == 'M':
            # 查看文件内容
            for file_path in file_paths:
                if os.path.exists(file_path):
                    print(f"\n📄 {file_path} 内容预览:")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"{content[:200]}...")
                    except Exception as e:
                        print(f"无法读取文件: {e}")
            # 重新询问
            approval = simulate_hitl_skill_for_deletion(file_paths)
        else:
            print("\n❌ 操作已拒绝")
            approval = {
                "approved": False,
                "risk_classification": {
                    "level": "review",
                    "score": risk_score,
                    "reasons": risk_factors
                },
                "approval": {
                    "required": True,
                    "user_decision": "rejected"
                }
            }
    else:  # mandatory
        print("\n⚠️  高风险操作警告!")
        print("删除操作不可逆，请谨慎确认")

        # 显示详细信息
        for file_path in file_paths:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"\n📄 {file_path}:")
                print(f"  大小: {file_size} bytes")
                print(f"  最后修改: {datetime.fromtimestamp(os.path.getmtime(file_path))}")

        print("\n请输入确认文本以继续，或输入 N 拒绝:")
        confirmation = input("> ")

        if confirmation.upper() == "DELETE FILES":
            print("\n✅ 操作已批准")
            approval = {
                "approved": True,
                "risk_classification": {
                    "level": "mandatory",
                    "score": risk_score,
                    "reasons": risk_factors
                },
                "approval": {
                    "required": True,
                    "user_decision": "approved",
                    "confirmation_text": confirmation
                }
            }
        else:
            print("\n❌ 操作已拒绝")
            approval = {
                "approved": False,
                "risk_classification": {
                    "level": "mandatory",
                    "score": risk_score,
                    "reasons": risk_factors
                },
                "approval": {
                    "required": True,
                    "user_decision": "rejected"
                }
            }

    return approval

def main():
    """主函数"""
    print("使用 task:hitl 技能进行删除文件审批示例")
    print("="*60)

    # 示例文件列表
    test_files = [
        "test_file1.txt",
        "config/secret.yaml",
        "data/user_ids.txt",
        "temp/old_cache.log"
    ]

    print("\n准备删除以下文件:")
    for i, file in enumerate(test_files, 1):
        status = "✅ 存在" if os.path.exists(file) else "❌ 不存在"
        print(f"{i}. {file} ({status})")

    # 执行 HITL 审批
    result = simulate_hitl_skill_for_deletion(test_files)

    # 记录审批日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": "delete_files",
        "files": test_files,
        "risk_classification": result["risk_classification"],
        "approval": result["approval"],
        "approved": result["approved"]
    }

    print("\n" + "="*60)
    print("📋 审批结果")
    print("="*60)
    print(f"审批状态: {'✅ 通过' if result['approved'] else '❌ 拒绝'}")
    print(f"风险等级: {result['risk_classification']['level']}")
    print(f"用户决策: {result['approval']['user_decision']}")

    # 保存审批日志
    log_file = "deletion_approval_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, ensure_ascii=False, indent=2)

    print(f"\n审批日志已保存到: {log_file}")

    # 如果批准且文件存在，执行删除
    if result["approved"]:
        print("\n🚀 开始执行删除操作...")
        deleted_count = 0
        for file_path in test_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ 已删除: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 删除失败 {file_path}: {e}")
        print(f"\n删除完成: {deleted_count}/{len(test_files)} 个文件被删除")

if __name__ == "__main__":
    main()