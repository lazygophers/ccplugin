"""Word docx 包装层 - 提供格式转换、批量处理、模板生成、智能分析功能."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import click
from docx import Document

logger = logging.getLogger(__name__)


# ============================================================
# 格式转换模块
# ============================================================


def convert_docx_to_markdown(input_path: str, output_path: str | None = None) -> str:
    """将 docx 文件转换为 Markdown 格式.

    Args:
        input_path: 输入的 docx 文件路径.
        output_path: 输出的 Markdown 文件路径，默认与输入同名.

    Returns:
        输出文件的路径.

    Raises:
        FileNotFoundError: 输入文件不存在.
        RuntimeError: 转换失败.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".md"))

    try:
        import pypandoc

        pypandoc.convert_file(str(input_file), "md", outputfile=output_path)
    except ImportError:
        # 回退到简单的手动转换
        doc = Document(str(input_file))
        lines: list[str] = []
        for para in doc.paragraphs:
            style_name = para.style.name if para.style else ""
            if style_name.startswith("Heading"):
                level = int(style_name[-1]) if style_name[-1].isdigit() else 1
                lines.append(f"{'#' * level} {para.text}")
            elif para.text.strip():
                lines.append(para.text)
            lines.append("")
        Path(output_path).write_text("\n".join(lines), encoding="utf-8")

    logger.info("转换完成: %s -> %s", input_path, output_path)
    return output_path


def convert_markdown_to_docx(input_path: str, output_path: str | None = None) -> str:
    """将 Markdown 文件转换为 docx 格式.

    Args:
        input_path: 输入的 Markdown 文件路径.
        output_path: 输出的 docx 文件路径，默认与输入同名.

    Returns:
        输出文件的路径.

    Raises:
        FileNotFoundError: 输入文件不存在.
        RuntimeError: 转换失败.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".docx"))

    try:
        import pypandoc

        pypandoc.convert_file(str(input_file), "docx", outputfile=output_path)
    except ImportError:
        # 回退到简单的手动转换
        doc = Document()
        content = input_file.read_text(encoding="utf-8")
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                match = re.match(r"^(#{1,6})\s+(.*)", stripped)
                if match:
                    level = len(match.group(1))
                    doc.add_heading(match.group(2), level=level)
                    continue
            if stripped:
                doc.add_paragraph(stripped)
        doc.save(output_path)

    logger.info("转换完成: %s -> %s", input_path, output_path)
    return output_path


def convert_docx_to_pdf(input_path: str, output_path: str | None = None) -> str:
    """将 docx 文件转换为 PDF 格式.

    Args:
        input_path: 输入的 docx 文件路径.
        output_path: 输出的 PDF 文件路径，默认与输入同名.

    Returns:
        输出文件的路径.

    Raises:
        FileNotFoundError: 输入文件不存在.
        RuntimeError: 转换失败.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    try:
        import pypandoc

        pypandoc.convert_file(str(input_file), "pdf", outputfile=output_path)
    except ImportError:
        raise RuntimeError(
            "PDF 转换需要 pypandoc 和 pandoc。"
            "请安装: pip install pypandoc && brew install pandoc"
        )

    logger.info("转换完成: %s -> %s", input_path, output_path)
    return output_path


# ============================================================
# 批量处理模块
# ============================================================


def batch_read_documents(
    directory: str, pattern: str = "*.docx"
) -> list[dict[str, Any]]:
    """批量读取目录中的 docx 文件信息.

    Args:
        directory: 目标目录路径.
        pattern: 文件匹配模式，默认 *.docx.

    Returns:
        文档信息列表，每项包含 path, title, paragraphs, tables 字段.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"目录不存在: {directory}")

    results: list[dict[str, Any]] = []
    for file_path in sorted(dir_path.glob(pattern)):
        try:
            doc = Document(str(file_path))
            info = {
                "path": str(file_path),
                "filename": file_path.name,
                "paragraphs": len(doc.paragraphs),
                "tables": len(doc.tables),
                "title": doc.core_properties.title or "",
                "author": doc.core_properties.author or "",
            }
            results.append(info)
        except Exception as e:
            logger.warning("读取失败 %s: %s", file_path, e)
            results.append({
                "path": str(file_path),
                "filename": file_path.name,
                "error": str(e),
            })

    return results


def batch_convert(
    directory: str,
    target_format: str = "md",
    output_dir: str | None = None,
    pattern: str = "*.docx",
) -> list[dict[str, str]]:
    """批量转换目录中的 docx 文件.

    Args:
        directory: 源文件目录.
        target_format: 目标格式 (md/pdf).
        output_dir: 输出目录，默认与源文件同目录.
        pattern: 文件匹配模式.

    Returns:
        转换结果列表，每项包含 source, output, status 字段.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"目录不存在: {directory}")

    out_path = Path(output_dir) if output_dir else dir_path
    out_path.mkdir(parents=True, exist_ok=True)

    converters = {
        "md": convert_docx_to_markdown,
        "markdown": convert_docx_to_markdown,
        "pdf": convert_docx_to_pdf,
    }

    converter = converters.get(target_format)
    if converter is None:
        raise ValueError(f"不支持的目标格式: {target_format}，支持: md, pdf")

    results: list[dict[str, str]] = []
    for file_path in sorted(dir_path.glob(pattern)):
        suffix = ".md" if target_format in ("md", "markdown") else f".{target_format}"
        output_file = str(out_path / file_path.with_suffix(suffix).name)
        try:
            converter(str(file_path), output_file)
            results.append({
                "source": str(file_path),
                "output": output_file,
                "status": "success",
            })
        except Exception as e:
            logger.error("转换失败 %s: %s", file_path, e)
            results.append({
                "source": str(file_path),
                "output": output_file,
                "status": f"error: {e}",
            })

    return results


# ============================================================
# 模板生成模块
# ============================================================


def generate_from_template(
    template_path: str,
    output_path: str,
    variables: dict[str, str],
) -> str:
    """基于模板文件生成新文档，替换占位符变量.

    模板中使用 {{变量名}} 作为占位符，例如 {{title}}、{{date}}.

    Args:
        template_path: 模板文件路径.
        output_path: 输出文件路径.
        variables: 变量替换映射，key 为变量名，value 为替换值.

    Returns:
        输出文件路径.

    Raises:
        FileNotFoundError: 模板文件不存在.
    """
    tpl_file = Path(template_path)
    if not tpl_file.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    doc = Document(str(tpl_file))

    def replace_in_text(text: str) -> str:
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text

    for para in doc.paragraphs:
        for run in para.runs:
            run.text = replace_in_text(run.text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.text = replace_in_text(run.text)

    doc.save(output_path)
    logger.info("模板生成完成: %s -> %s", template_path, output_path)
    return output_path


def create_report_template(output_path: str, title: str = "报告模板") -> str:
    """创建一个标准报告模板文件.

    Args:
        output_path: 输出模板文件路径.
        title: 报告标题.

    Returns:
        输出文件路径.
    """
    doc = Document()

    doc.add_heading(title, level=0)
    doc.add_paragraph("作者：{{author}}")
    doc.add_paragraph("日期：{{date}}")
    doc.add_paragraph("")

    doc.add_heading("摘要", level=1)
    doc.add_paragraph("{{summary}}")

    doc.add_heading("正文", level=1)
    doc.add_paragraph("{{content}}")

    doc.add_heading("结论", level=1)
    doc.add_paragraph("{{conclusion}}")

    doc.save(output_path)
    logger.info("报告模板已创建: %s", output_path)
    return output_path


# ============================================================
# 智能分析模块
# ============================================================


def analyze_document(file_path: str) -> dict[str, Any]:
    """分析文档结构和内容摘要.

    Args:
        file_path: docx 文件路径.

    Returns:
        分析结果字典，包含结构信息、统计数据和内容摘要.

    Raises:
        FileNotFoundError: 文件不存在.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    doc = Document(str(path))

    # 基本统计
    all_text = [p.text for p in doc.paragraphs if p.text.strip()]
    total_chars = sum(len(t) for t in all_text)
    total_words = sum(len(t.split()) for t in all_text)

    # 标题结构
    headings: list[dict[str, Any]] = []
    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ""
        if style_name.startswith("Heading") and para.text.strip():
            level = int(style_name[-1]) if style_name[-1].isdigit() else 1
            headings.append({"level": level, "text": para.text.strip()})

    # 表格统计
    tables_info: list[dict[str, int]] = []
    for table in doc.tables:
        tables_info.append({
            "rows": len(table.rows),
            "columns": len(table.columns),
        })

    # 内容摘要（取前 3 个非标题段落）
    content_paragraphs = [
        p.text.strip()
        for p in doc.paragraphs
        if p.text.strip()
        and not (p.style and p.style.name.startswith("Heading"))
    ]
    summary_texts = content_paragraphs[:3]

    # 文档属性
    props = doc.core_properties
    properties = {
        "title": props.title or "",
        "author": props.author or "",
        "subject": props.subject or "",
        "created": str(props.created) if props.created else "",
        "modified": str(props.modified) if props.modified else "",
    }

    return {
        "file": str(path),
        "properties": properties,
        "statistics": {
            "paragraphs": len(doc.paragraphs),
            "non_empty_paragraphs": len(all_text),
            "tables": len(doc.tables),
            "characters": total_chars,
            "words": total_words,
            "headings": len(headings),
        },
        "outline": headings,
        "tables": tables_info,
        "summary": summary_texts,
    }


def extract_key_info(file_path: str) -> dict[str, Any]:
    """从文档中提取关键信息（标题、表格数据、列表项）.

    Args:
        file_path: docx 文件路径.

    Returns:
        关键信息字典.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    doc = Document(str(path))

    # 提取标题
    headings = [
        p.text.strip()
        for p in doc.paragraphs
        if p.style and p.style.name.startswith("Heading") and p.text.strip()
    ]

    # 提取表格数据
    tables_data: list[list[list[str]]] = []
    for table in doc.tables:
        table_rows: list[list[str]] = []
        for row in table.rows:
            table_rows.append([cell.text.strip() for cell in row.cells])
        tables_data.append(table_rows)

    # 提取列表项（通过样式名匹配）
    list_items: list[str] = []
    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ""
        if "List" in style_name and para.text.strip():
            list_items.append(para.text.strip())

    # 提取粗体文本（通常是关键信息）
    bold_texts: list[str] = []
    for para in doc.paragraphs:
        for run in para.runs:
            if run.bold and run.text.strip():
                bold_texts.append(run.text.strip())

    return {
        "headings": headings,
        "tables": tables_data,
        "list_items": list_items,
        "bold_texts": bold_texts,
    }


# ============================================================
# CLI 入口
# ============================================================


@click.group()
def main() -> None:
    """Word docx 包装层工具."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@main.command("convert")
@click.argument("input_path")
@click.option("-o", "--output", "output_path", default=None, help="输出文件路径")
@click.option(
    "-f",
    "--format",
    "target_format",
    type=click.Choice(["md", "pdf", "docx"]),
    required=True,
    help="目标格式",
)
def convert_cmd(input_path: str, output_path: str | None, target_format: str) -> None:
    """转换文件格式."""
    input_file = Path(input_path)
    if input_file.suffix == ".docx" and target_format == "md":
        result = convert_docx_to_markdown(input_path, output_path)
    elif input_file.suffix == ".docx" and target_format == "pdf":
        result = convert_docx_to_pdf(input_path, output_path)
    elif input_file.suffix == ".md" and target_format == "docx":
        result = convert_markdown_to_docx(input_path, output_path)
    else:
        click.echo(f"不支持的转换: {input_file.suffix} -> {target_format}")
        sys.exit(1)
    click.echo(json.dumps({"output": result}, ensure_ascii=False))


@main.command("batch-read")
@click.argument("directory")
@click.option("-p", "--pattern", default="*.docx", help="文件匹配模式")
def batch_read_cmd(directory: str, pattern: str) -> None:
    """批量读取文档信息."""
    results = batch_read_documents(directory, pattern)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@main.command("batch-convert")
@click.argument("directory")
@click.option(
    "-f",
    "--format",
    "target_format",
    type=click.Choice(["md", "pdf"]),
    default="md",
    help="目标格式",
)
@click.option("-o", "--output-dir", default=None, help="输出目录")
def batch_convert_cmd(
    directory: str, target_format: str, output_dir: str | None
) -> None:
    """批量转换目录中的文档."""
    results = batch_convert(directory, target_format, output_dir)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@main.command("template")
@click.argument("template_path")
@click.argument("output_path")
@click.option(
    "-v",
    "--var",
    "variables",
    multiple=True,
    help="变量替换，格式: key=value",
)
def template_cmd(
    template_path: str, output_path: str, variables: tuple[str, ...]
) -> None:
    """基于模板生成文档."""
    var_dict: dict[str, str] = {}
    for v in variables:
        if "=" not in v:
            click.echo(f"变量格式错误: {v}，应为 key=value")
            sys.exit(1)
        key, value = v.split("=", 1)
        var_dict[key] = value
    result = generate_from_template(template_path, output_path, var_dict)
    click.echo(json.dumps({"output": result}, ensure_ascii=False))


@main.command("create-template")
@click.argument("output_path")
@click.option("-t", "--title", default="报告模板", help="报告标题")
def create_template_cmd(output_path: str, title: str) -> None:
    """创建标准报告模板."""
    result = create_report_template(output_path, title)
    click.echo(json.dumps({"output": result}, ensure_ascii=False))


@main.command("analyze")
@click.argument("file_path")
def analyze_cmd(file_path: str) -> None:
    """分析文档结构和内容."""
    result = analyze_document(file_path)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@main.command("extract")
@click.argument("file_path")
def extract_cmd(file_path: str) -> None:
    """提取文档关键信息."""
    result = extract_key_info(file_path)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
