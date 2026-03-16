from __future__ import annotations

from plugins.tools.task.scripts.fill_plan_template import (
    build_flowchart_section,
    build_journey_section,
    build_task_table,
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

