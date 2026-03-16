from __future__ import annotations

from pathlib import Path

from plugins.tools.task.scripts.fill_plan_template import (
    build_flowchart_section,
    build_journey_section,
    build_task_table,
    fill_template,
)


def test_flowchart_normalizes_task_ids_and_escapes_html_labels() -> None:
    # Arrange
    tasks = [
        {
            "id": "T1",
            "description": 'Add "quote" & <tag>',
            "agent": "coder:task",
            "skills": ["s1"],
            "files": ["a.py"],
        },
        {"id": 2, "description": "Second", "agent": "verifier", "skills": [], "files": []},
    ]
    dependencies = {"2": ["T1"]}

    # Act
    mermaid = build_flowchart_section(tasks, dependencies)

    # Assert
    assert "Start([开始]) --> T1" in mermaid
    assert 'T1["T1: Add &quot;quote&quot; &amp; &lt;tag&gt;' in mermaid
    assert 'T2["T2: Second' in mermaid
    assert "T1 --> T2" in mermaid
    assert "T2 --> End([结束])" in mermaid


def test_journey_replaces_colons_and_compacts_long_labels() -> None:
    # Arrange
    tasks = [
        {
            "id": 1,
            "description": "do: something very very very very long that should be compacted",
            "agent": "coder:task",
        }
    ]

    # Act
    mermaid = build_journey_section(tasks)

    # Assert
    assert "journey" in mermaid
    assert "title Agent 执行旅程" in mermaid
    assert "do：" in mermaid
    assert "coder：task" in mermaid
    assert "do: something" not in mermaid


def test_task_table_uses_display_ids_and_dependency_display() -> None:
    # Arrange
    tasks = [
        {"id": "T1", "description": "First", "agent": "a", "skills": [], "files": []},
        {"id": 2, "description": "Second", "agent": "b", "skills": [], "files": []},
    ]
    dependencies = {"2": ["T1"]}

    # Act
    table = build_task_table(tasks, dependencies)

    # Assert
    assert "| T1 | First |" in table
    assert "| T2 | Second |" in table
    assert table.strip().endswith("| T2 | Second | b | - | - | T1 |")


def test_fill_template_matches_plan_confirmation_template_structure() -> None:
    # Arrange
    template_path = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "loop"
        / "plan-confirmation-template.md"
    )
    planner_result = {
        "tasks": [
            {
                "id": 1,
                "description": "需求分析",
                "agent": "analyst@project",
                "skills": ["requirements@project"],
                "files": ["docs/requirements.md"],
            },
            {
                "id": 2,
                "description": "核心功能实现",
                "agent": "developer@task",
                "skills": ["python:core@python", "python:async@python"],
                "files": ["src/core.py", "src/utils.py"],
            },
        ],
        "dependencies": {"2": [1]},
        "acceptance_criteria": ["单元测试覆盖率 ≥ 90%", "无影响已有功能（回归测试通过）"],
        "report": "这里是一段任务说明",
    }

    # Act
    md = fill_template(
        template_path=template_path,
        planner_result=planner_result,
        task_content="demo",
        iteration=1,
        step_name="计划确认",
        status="待确认",
    )

    # Assert
    assert "[MindFlow·demo·计划确认/1·待确认]" in md
    assert "### 任务编排" in md
    assert "```mermaid\nstateDiagram-v2" in md
    assert 'state "T1: 需求分析' in md
    assert "T1 --> T2" in md
    assert "### Agent/成员 视角" in md
    assert "```mermaid\ngantt" in md
    assert "### 任务清单" in md
    assert "| 任务ID | 任务名称 | 负责Agent | 使用Skills | 相关文件 | 依赖任务 |" in md
    assert "### 验收标准" in md
    assert "- [ ] 单元测试覆盖率 ≥ 90%" in md
    assert "- [ ] 无影响已有功能（回归测试通过）" in md
    assert "### 任务说明（≤100字）" in md
    assert "这里是一段任务说明" in md
