"""计划模板填充工具

根据 planner 结果填充 plan-confirmation-template.md 模板
"""

import json
import re
import sys
from pathlib import Path


def build_flowchart_section(tasks: list[dict], dependencies: dict) -> str:
    """构建完整的 Mermaid flowchart 部分"""
    lines = ["```mermaid", "flowchart TD"]

    # Start节点
    if tasks:
        lines.append(f"    Start([开始]) --> T{tasks[0]['id']}")
        lines.append("")

    # 所有任务节点
    for task in tasks:
        task_id = task["id"]
        description = task["description"]
        agent = task["agent"]
        skills = task.get("skills", [])
        files = task.get("files", [])

        skill_display = skills[0] if skills else "无"
        file_display = files[0] if files else "无"

        node = f'    T{task_id}["{task_id}: {description}<br/>━━━━━━━━━━━━<br/>agent: {agent}<br/>skills: {skill_display}<br/>files: {file_display}"]'
        lines.append(node)

    lines.append("")

    # 依赖关系箭头
    for task in tasks:
        task_id = str(task["id"])
        deps = dependencies.get(task_id, [])

        if deps:
            dep_list = " & ".join([f"T{dep}" for dep in deps])
            lines.append(f"    {dep_list} --> T{task_id}")

    # End节点
    if tasks:
        lines.append("")
        lines.append(f"    T{tasks[-1]['id']} --> End([结束])")

    # 样式类
    lines.append("")
    lines.append("    classDef startEnd fill:#e1f5e1,stroke:#4caf50,stroke-width:2px")
    lines.append("    classDef task fill:#e3f2fd,stroke:#2196f3,stroke-width:2px")
    lines.append("")
    lines.append("    class Start,End startEnd")

    task_ids = ",".join([f"T{t['id']}" for t in tasks])
    lines.append(f"    class {task_ids} task")

    lines.append("```")

    return "\n".join(lines)


def build_journey_section(tasks: list[dict]) -> str:
    """构建完整的 Mermaid journey 部分"""
    lines = ["```mermaid", "journey", "    title Agent 执行旅程"]

    # 简单的阶段分组逻辑
    sections = {
        "需求阶段": [],
        "开发阶段": [],
        "测试优化": [],
        "验收阶段": []
    }

    total = len(tasks)
    for i, task in enumerate(tasks):
        task_name = task["description"]
        agent = task["agent"]

        if i < total * 0.2:
            sections["需求阶段"].append(f"      {task_name}: 5: {agent}")
        elif i < total * 0.6:
            sections["开发阶段"].append(f"      {task_name}: 5: {agent}")
        elif i < total * 0.9:
            sections["测试优化"].append(f"      {task_name}: 4: {agent}")
        else:
            sections["验收阶段"].append(f"      {task_name}: 5: {agent}")

    for section, items in sections.items():
        if items:
            lines.append(f"    section {section}")
            lines.extend(items)

    lines.append("```")

    return "\n".join(lines)


def build_task_table(tasks: list[dict], dependencies: dict) -> str:
    """构建任务清单表格"""
    lines = [
        "| 任务ID | 任务名称 | 负责Agent | 使用Skills | 相关文件 | 依赖任务 |",
        "|--------|---------|-----------|-----------|---------|---------|"
    ]

    for task in tasks:
        task_id = task["id"]
        description = task["description"]
        agent = task["agent"]
        skills = task.get("skills", [])
        files = task.get("files", [])

        skills_str = ", ".join(skills) if skills else "-"
        files_str = ", ".join(files) if files else "-"

        deps = dependencies.get(str(task_id), [])
        deps_str = ", ".join([f"T{dep}" for dep in deps]) if deps else "-"

        row = f"| T{task_id} | {description} | {agent} | {skills_str} | {files_str} | {deps_str} |"
        lines.append(row)

    return "\n".join(lines)


def fill_template(
    template_path: Path,
    planner_result: dict,
    task_content: str,
    iteration: int,
    step_name: str = "计划确认",
    status: str = "进行中"
) -> str:
    """填充计划模板

    Args:
        template_path: 模板文件路径
        planner_result: planner agent 返回的结果
        task_content: 任务内容描述
        iteration: 当前迭代轮数
        step_name: 当前步骤名称
        status: 任务状态

    Returns:
        填充后的 markdown 内容
    """
    # 读取模板
    template_content = template_path.read_text(encoding="utf-8")

    # 提取数据
    tasks = planner_result.get("tasks", [])
    dependencies = planner_result.get("dependencies", {})
    acceptance_criteria = planner_result.get("acceptance_criteria", [])
    report = planner_result.get("report", "[任务概述]")

    # 第 1 行：标题
    template_content = template_content.replace(
        "[MindFlow·${任务内容}·${步骤索引}/${迭代轮数}·${任务状态-总任务的状态}]",
        f"[MindFlow·{task_content}·{step_name}/{iteration}·{status}]"
    )

    # 替换 flowchart（整个代码块）
    flowchart_pattern = r"```mermaid\nflowchart TD\n.*?```"
    flowchart_section = build_flowchart_section(tasks, dependencies)
    template_content = re.sub(flowchart_pattern, flowchart_section, template_content, flags=re.DOTALL, count=1)

    # 替换 journey（整个代码块）
    journey_pattern = r"```mermaid\njourney\n.*?```"
    journey_section = build_journey_section(tasks)
    template_content = re.sub(journey_pattern, journey_section, template_content, flags=re.DOTALL, count=1)

    # 替换任务表格（包括表头）
    table_pattern = r"\| 任务ID \| 任务名称 \| 负责Agent \| 使用Skills \| 相关文件 \| 依赖任务 \|.*?\n(?:\|.*?\n)*"
    task_table = build_task_table(tasks, dependencies)
    template_content = re.sub(table_pattern, task_table + "\n", template_content, flags=re.DOTALL)

    # 替换验收标准
    acceptance_list = "\n".join([f"- [ ] {criterion}" for criterion in acceptance_criteria])
    criteria_pattern = r"- \[ \] 单元测试覆盖率.*?- \[ \] 无影响已有功能（回归测试通过）"
    template_content = re.sub(criteria_pattern, acceptance_list, template_content, flags=re.DOTALL)

    # 替换简要说明
    template_content = template_content.replace("[任务概述]", report)

    return template_content


try:
    import click
except ImportError:
    click = None


def main_cli():
    """命令行入口（非 Click 版本）"""
    if len(sys.argv) < 5:
        print("用法: python fill_plan_template.py <模板路径> <planner结果JSON> <任务内容> <迭代轮数> [步骤名称] [状态]")
        print("示例: python fill_plan_template.py template.md result.json '添加用户认证' 1 '计划确认' '进行中'")
        sys.exit(1)

    template_path = Path(sys.argv[1])
    planner_result_path = Path(sys.argv[2])
    task_content = sys.argv[3]
    iteration = int(sys.argv[4])
    step_name = sys.argv[5] if len(sys.argv) > 5 else "计划确认"
    status = sys.argv[6] if len(sys.argv) > 6 else "进行中"

    # 读取 planner 结果
    with open(planner_result_path, encoding="utf-8") as f:
        planner_result = json.load(f)

    # 填充模板
    filled_content = fill_template(
        template_path=template_path,
        planner_result=planner_result,
        task_content=task_content,
        iteration=iteration,
        step_name=step_name,
        status=status
    )

    # 输出到标准输出
    print(filled_content)


if click:
    @click.command("fill-plan")
    @click.argument("template_path", type=click.Path(exists=True))
    @click.argument("planner_result_path", type=click.Path(exists=True))
    @click.argument("task_content")
    @click.argument("iteration", type=int)
    @click.option("--step-name", default="计划确认", help="步骤名称")
    @click.option("--status", default="进行中", help="任务状态")
    def fill_plan_command(
        template_path: str,
        planner_result_path: str,
        task_content: str,
        iteration: int,
        step_name: str,
        status: str
    ):
        """填充计划模板

        从 planner 结果 JSON 生成计划确认文档
        """
        template_path = Path(template_path)
        planner_result_path = Path(planner_result_path)

        # 读取 planner 结果
        with open(planner_result_path, encoding="utf-8") as f:
            planner_result = json.load(f)

        # 填充模板
        filled_content = fill_template(
            template_path=template_path,
            planner_result=planner_result,
            task_content=task_content,
            iteration=iteration,
            step_name=step_name,
            status=status
        )

        # 输出到标准输出
        click.echo(filled_content)


if __name__ == "__main__":
    if click:
        fill_plan_command()
    else:
        main_cli()
