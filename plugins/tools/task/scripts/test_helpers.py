"""测试辅助函数

提供消息流解析、任务状态验证、文件系统检查等辅助功能。
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MessageEvent:
    """消息事件"""

    type: str  # system, result, tool_use, etc.
    subtype: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """测试结果"""

    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MessageCollector:
    """消息流收集器

    Agent SDK 消息模型：
    - AssistantMessage.content = [ThinkingBlock, TextBlock, ToolUseBlock]
    - UserMessage.content = [ToolResultBlock]
    - ResultMessage.result = str
    - SystemMessage.subtype = init/hook_started/hook_response
    """

    def __init__(self):
        self.messages: List[Any] = []
        self.text_outputs: List[str] = []
        self.thinking_outputs: List[str] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.tool_results: List[Dict[str, Any]] = []
        self.state_transitions: List[str] = []
        self.actual_model: Optional[str] = None

    def add_message(self, message: Any) -> None:
        """添加消息到收集器"""
        self.messages.append(message)
        cls = type(message).__name__

        if cls == "AssistantMessage":
            if not self.actual_model:
                self.actual_model = getattr(message, "model", None)
            for block in getattr(message, "content", []):
                block_type = type(block).__name__
                if block_type == "ToolUseBlock":
                    self.tool_calls.append({
                        "name": getattr(block, "name", ""),
                        "input": getattr(block, "input", {}),
                    })
                elif block_type == "TextBlock":
                    text = getattr(block, "text", "")
                    if text:
                        self.text_outputs.append(text)
                        self._extract_state_transitions(text)
                elif block_type == "ThinkingBlock":
                    thinking = getattr(block, "thinking", "")
                    if thinking:
                        self.thinking_outputs.append(thinking)

        elif cls == "UserMessage":
            for block in getattr(message, "content", []):
                if type(block).__name__ == "ToolResultBlock":
                    self.tool_results.append({
                        "tool_use_id": getattr(block, "tool_use_id", ""),
                        "content": str(getattr(block, "content", ""))[:500],
                        "is_error": getattr(block, "is_error", False),
                    })

        elif cls == "ResultMessage":
            result = getattr(message, "result", "")
            if result:
                self.text_outputs.append(result)
                self._extract_state_transitions(result)

    def _extract_state_transitions(self, text: str) -> None:
        """从文本中提取状态转换

        格式: [flow·{task_id}·{state}]
        """
        pattern = r"\[flow·[^·]+·([^\]]+)\]"
        matches = re.findall(pattern, text)
        for state in matches:
            if not self.state_transitions or self.state_transitions[-1] != state:
                self.state_transitions.append(state)

    def get_tool_call_count(self, tool_name: str) -> int:
        """获取特定工具的调用次数"""
        return sum(1 for call in self.tool_calls if call["name"] == tool_name)

    def has_tool_call(self, tool_name: str) -> bool:
        """检查是否调用过特定工具"""
        return self.get_tool_call_count(tool_name) > 0

    def get_final_state(self) -> Optional[str]:
        """获取最终状态"""
        return self.state_transitions[-1] if self.state_transitions else None

    def get_full_output(self) -> str:
        """获取完整输出文本"""
        return "\n".join(self.text_outputs)


class TaskStateVerifier:
    """任务状态验证器"""

    def __init__(self, task_root: Path = Path(".lazygophers/tasks")):
        self.task_root = task_root

    def task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        index_file = self.task_root / "index.json"
        if not index_file.exists():
            return False

        try:
            with open(index_file) as f:
                index = json.load(f)
            return task_id in index
        except Exception:
            return False

    def get_task_state(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        index_file = self.task_root / "index.json"
        if not index_file.exists():
            return None

        try:
            with open(index_file) as f:
                index = json.load(f)
            return index.get(task_id, {}).get("status")
        except Exception:
            return None

    def verify_files_created(self, task_id: str, expected_files: List[str]) -> TestResult:
        """验证任务文件是否创建

        Args:
            task_id: 任务 ID
            expected_files: 预期的文件列表（支持通配符 *）

        Returns:
            TestResult: 验证结果
        """
        task_dir = self.task_root / task_id
        if not task_dir.exists():
            return TestResult(
                passed=False,
                message=f"任务目录不存在: {task_dir}",
            )

        missing_files = []
        for pattern in expected_files:
            # 简单的通配符支持
            if "*" in pattern:
                # 提取目录和文件名模式
                pattern_path = Path(pattern)
                parent = pattern_path.parent
                name_pattern = pattern_path.name

                search_dir = task_dir / parent if str(parent) != "." else task_dir
                if not search_dir.exists():
                    missing_files.append(pattern)
                    continue

                # 查找匹配的文件
                found = False
                for file in search_dir.iterdir():
                    if file.name.endswith(name_pattern.replace("*", "")):
                        found = True
                        break

                if not found:
                    missing_files.append(pattern)
            else:
                file_path = task_dir / pattern
                if not file_path.exists():
                    missing_files.append(pattern)

        if missing_files:
            return TestResult(
                passed=False,
                message=f"缺少预期文件: {', '.join(missing_files)}",
                details={"missing": missing_files},
            )

        return TestResult(passed=True, message="所有预期文件已创建")


class TestVerifier:
    """测试验证器"""

    def __init__(self, collector: MessageCollector, expectations: Dict[str, Any]):
        self.collector = collector
        self.expectations = expectations
        self.results: List[TestResult] = []

    def verify_state_transitions(self) -> TestResult:
        """验证状态转换序列"""
        expected = self.expectations.get("state_transitions", [])
        actual = self.collector.state_transitions

        if not expected:
            return TestResult(passed=True, message="未指定状态转换期望")

        # 检查是否包含所有预期状态（顺序可能不同）
        missing_states = [s for s in expected if s not in actual]
        if missing_states:
            return TestResult(
                passed=False,
                message=f"缺少预期状态: {', '.join(missing_states)}",
                details={"expected": expected, "actual": actual},
            )

        return TestResult(
            passed=True,
            message=f"状态转换正确: {' → '.join(actual)}",
            details={"transitions": actual},
        )

    def verify_tool_calls(self) -> TestResult:
        """验证工具调用"""
        expected = self.expectations.get("tool_calls", {})

        if not expected:
            return TestResult(passed=True, message="未指定工具调用期望")

        failures = []
        for tool_name, constraints in expected.items():
            actual_count = self.collector.get_tool_call_count(tool_name)

            if "min" in constraints and actual_count < constraints["min"]:
                failures.append(
                    f"{tool_name}: 至少 {constraints['min']} 次，实际 {actual_count} 次"
                )

            if "max" in constraints and actual_count > constraints["max"]:
                failures.append(
                    f"{tool_name}: 最多 {constraints['max']} 次，实际 {actual_count} 次"
                )

            if "exact" in constraints and actual_count != constraints["exact"]:
                failures.append(
                    f"{tool_name}: 期望 {constraints['exact']} 次，实际 {actual_count} 次"
                )

        if failures:
            return TestResult(
                passed=False,
                message="工具调用不符合预期",
                details={"failures": failures},
            )

        return TestResult(passed=True, message="工具调用符合预期")

    def verify_final_state(self) -> TestResult:
        """验证最终状态"""
        expected = self.expectations.get("final_state")

        if not expected:
            return TestResult(passed=True, message="未指定最终状态期望")

        actual = self.collector.get_final_state()

        if actual != expected:
            return TestResult(
                passed=False,
                message=f"最终状态不匹配: 期望 {expected}，实际 {actual}",
                details={"expected": expected, "actual": actual},
            )

        return TestResult(
            passed=True,
            message=f"最终状态正确: {actual}",
        )

    def verify_all(self) -> "TestReport":
        """执行所有验证"""
        self.results = [
            self.verify_state_transitions(),
            self.verify_tool_calls(),
            self.verify_final_state(),
        ]

        return TestReport(results=self.results)


@dataclass
class TestReport:
    """测试报告"""

    results: List[TestResult]

    @property
    def all_passed(self) -> bool:
        """是否所有测试都通过"""
        return all(r.passed for r in self.results)

    @property
    def passed_count(self) -> int:
        """通过的测试数量"""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        """失败的测试数量"""
        return sum(1 for r in self.results if not r.passed)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "all_passed": self.all_passed,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "total": len(self.results),
            "results": [
                {
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }

    def __str__(self) -> str:
        """格式化输出"""
        lines = [
            "=" * 60,
            "测试报告",
            "=" * 60,
            f"总计: {len(self.results)} | 通过: {self.passed_count} | 失败: {self.failed_count}",
            "",
        ]

        for i, result in enumerate(self.results, 1):
            status = "✓" if result.passed else "✗"
            lines.append(f"{i}. {status} {result.message}")

            if result.details and not result.passed:
                lines.append(f"   详情: {result.details}")

        lines.append("=" * 60)
        return "\n".join(lines)
