"""PowerPoint pptx 包装层 - 提供格式转换、批量处理、模板生成、智能分析功能."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
from pptx import Presentation

logger = logging.getLogger(__name__)


# ============================================================
# 格式转换模块
# ============================================================


def convert_pptx_to_pdf(input_path: str, output_path: str | None = None) -> str:
    """将 pptx 文件转换为 PDF 格式.

    Args:
        input_path: 输入的 pptx 文件路径.
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


def extract_pptx_to_markdown(
    input_path: str, output_path: str | None = None
) -> str:
    """将 pptx 内容提取为 Markdown 格式.

    按幻灯片顺序提取文本内容，转为可读的 Markdown 文档.

    Args:
        input_path: 输入的 pptx 文件路径.
        output_path: 输出的 Markdown 文件路径，默认与输入同名.

    Returns:
        输出文件的路径.

    Raises:
        FileNotFoundError: 输入文件不存在.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".md"))

    prs = Presentation(str(input_file))
    lines: list[str] = [f"# {input_file.stem}", ""]

    for idx, slide in enumerate(prs.slides, 1):
        lines.append(f"## 幻灯片 {idx}")
        lines.append("")

        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        # 根据字体大小推断标题级别
                        if para.runs and para.runs[0].font.size:
                            font_size = para.runs[0].font.size.pt
                            if font_size >= 28:
                                lines.append(f"### {text}")
                            elif font_size >= 20:
                                lines.append(f"#### {text}")
                            else:
                                lines.append(text)
                        else:
                            lines.append(text)
                lines.append("")

            if shape.has_table:
                table = shape.table
                # 表头
                headers = [cell.text.strip() for cell in table.rows[0].cells]
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                # 数据行
                for row in list(table.rows)[1:]:
                    cells = [cell.text.strip() for cell in row.cells]
                    lines.append("| " + " | ".join(cells) + " |")
                lines.append("")

        lines.append("---")
        lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    logger.info("提取完成: %s -> %s", input_path, output_path)
    return output_path


# ============================================================
# 批量处理模块
# ============================================================


def batch_read_presentations(
    directory: str, pattern: str = "*.pptx"
) -> list[dict[str, Any]]:
    """批量读取目录中的 pptx 文件信息.

    Args:
        directory: 目标目录路径.
        pattern: 文件匹配模式，默认 *.pptx.

    Returns:
        演示文稿信息列表，每项包含 path, slides, shapes 等字段.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"目录不存在: {directory}")

    results: list[dict[str, Any]] = []
    for file_path in sorted(dir_path.glob(pattern)):
        try:
            prs = Presentation(str(file_path))
            total_shapes = sum(len(s.shapes) for s in prs.slides)
            total_text_chars = 0
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        total_text_chars += sum(
                            len(p.text) for p in shape.text_frame.paragraphs
                        )

            info: dict[str, Any] = {
                "path": str(file_path),
                "filename": file_path.name,
                "slides": len(prs.slides),
                "total_shapes": total_shapes,
                "total_text_chars": total_text_chars,
                "width": str(prs.slide_width),
                "height": str(prs.slide_height),
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


def batch_extract_text(
    directory: str,
    output_dir: str | None = None,
    pattern: str = "*.pptx",
) -> list[dict[str, str]]:
    """批量提取目录中所有 pptx 文件的文本内容为 Markdown.

    Args:
        directory: 源文件目录.
        output_dir: 输出目录，默认与源文件同目录.
        pattern: 文件匹配模式.

    Returns:
        提取结果列表，每项包含 source, output, status 字段.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"目录不存在: {directory}")

    out_path = Path(output_dir) if output_dir else dir_path
    out_path.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, str]] = []
    for file_path in sorted(dir_path.glob(pattern)):
        output_file = str(out_path / file_path.with_suffix(".md").name)
        try:
            extract_pptx_to_markdown(str(file_path), output_file)
            results.append({
                "source": str(file_path),
                "output": output_file,
                "status": "success",
            })
        except Exception as e:
            logger.error("提取失败 %s: %s", file_path, e)
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
    """基于模板文件生成新演示文稿，替换占位符文本.

    模板中使用 {{变量名}} 作为占位符.

    Args:
        template_path: 模板文件路径.
        output_path: 输出文件路径.
        variables: 变量替换映射.

    Returns:
        输出文件路径.

    Raises:
        FileNotFoundError: 模板文件不存在.
    """
    tpl_file = Path(template_path)
    if not tpl_file.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    prs = Presentation(str(tpl_file))

    def replace_in_text(text: str) -> str:
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        run.text = replace_in_text(run.text)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for para in cell.text_frame.paragraphs:
                            for run in para.runs:
                                run.text = replace_in_text(run.text)

    prs.save(output_path)
    logger.info("模板生成完成: %s -> %s", template_path, output_path)
    return output_path


def create_report_template(
    output_path: str,
    title: str = "报告模板",
    slide_count: int = 5,
) -> str:
    """创建一个标准报告模板文件.

    生成包含标题页、目录页、内容页、数据页、结论页的演示文稿模板.

    Args:
        output_path: 输出模板文件路径.
        title: 报告标题.
        slide_count: 内容幻灯片数量（最少 3）.

    Returns:
        输出文件路径.
    """
    prs = Presentation()
    slide_count = max(3, slide_count)

    # 标题页
    title_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_layout)
    slide.shapes.title.text = title
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = "{{author}} | {{date}}"

    # 目录页
    content_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(content_layout)
    slide.shapes.title.text = "目录"
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = "{{toc}}"

    # 内容页
    for i in range(1, slide_count - 1):
        slide = prs.slides.add_slide(content_layout)
        slide.shapes.title.text = f"{{{{section_{i}_title}}}}"
        if len(slide.placeholders) > 1:
            slide.placeholders[1].text = f"{{{{section_{i}_content}}}}"

    # 结论页
    slide = prs.slides.add_slide(content_layout)
    slide.shapes.title.text = "结论"
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = "{{conclusion}}"

    prs.save(output_path)
    logger.info("报告模板已创建: %s（%d 张幻灯片）", output_path, len(prs.slides))
    return output_path


# ============================================================
# 智能分析模块
# ============================================================


def analyze_presentation(file_path: str) -> dict[str, Any]:
    """分析演示文稿结构和内容摘要.

    Args:
        file_path: pptx 文件路径.

    Returns:
        分析结果字典，包含结构信息、统计数据和内容摘要.

    Raises:
        FileNotFoundError: 文件不存在.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    prs = Presentation(str(path))

    slides_info: list[dict[str, Any]] = []
    total_text_chars = 0
    total_shapes = 0
    total_tables = 0
    total_images = 0

    for idx, slide in enumerate(prs.slides, 1):
        slide_data: dict[str, Any] = {
            "index": idx,
            "shapes": len(slide.shapes),
            "texts": [],
            "has_table": False,
            "has_image": False,
        }

        for shape in slide.shapes:
            if shape.has_text_frame:
                texts = [
                    p.text.strip()
                    for p in shape.text_frame.paragraphs
                    if p.text.strip()
                ]
                slide_data["texts"].extend(texts)
                total_text_chars += sum(len(t) for t in texts)
            if shape.has_table:
                slide_data["has_table"] = True
                total_tables += 1
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                slide_data["has_image"] = True
                total_images += 1

        total_shapes += len(slide.shapes)
        # 只保留前 3 个文本作为摘要
        slide_data["texts"] = slide_data["texts"][:3]
        slides_info.append(slide_data)

    # 文档属性
    props = prs.core_properties
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
            "slides": len(prs.slides),
            "total_shapes": total_shapes,
            "total_tables": total_tables,
            "total_images": total_images,
            "total_text_chars": total_text_chars,
        },
        "slide_dimensions": {
            "width": str(prs.slide_width),
            "height": str(prs.slide_height),
        },
        "slides": slides_info,
    }


def extract_speaker_notes(file_path: str) -> list[dict[str, Any]]:
    """从演示文稿中提取所有幻灯片的演讲稿（备注）.

    Args:
        file_path: pptx 文件路径.

    Returns:
        演讲稿列表，每项包含 slide_index 和 notes 字段.

    Raises:
        FileNotFoundError: 文件不存在.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    prs = Presentation(str(path))
    notes: list[dict[str, Any]] = []

    for idx, slide in enumerate(prs.slides, 1):
        note_text = ""
        if slide.has_notes_slide:
            notes_slide = slide.notes_slide
            note_text = notes_slide.notes_text_frame.text.strip()

        notes.append({
            "slide_index": idx,
            "has_notes": bool(note_text),
            "notes": note_text,
        })

    return notes


def summarize_content(file_path: str) -> dict[str, Any]:
    """生成演示文稿的内容总结.

    提取每张幻灯片的标题和要点，生成整体结构概览.

    Args:
        file_path: pptx 文件路径.

    Returns:
        内容总结字典.

    Raises:
        FileNotFoundError: 文件不存在.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    prs = Presentation(str(path))
    outline: list[dict[str, Any]] = []
    all_text_parts: list[str] = []

    for idx, slide in enumerate(prs.slides, 1):
        slide_title = ""
        bullet_points: list[str] = []

        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue
                    # 第一个有文本的形状通常是标题
                    if not slide_title and shape == slide.shapes[0]:
                        slide_title = text
                    else:
                        bullet_points.append(text)
                    all_text_parts.append(text)

        outline.append({
            "slide": idx,
            "title": slide_title,
            "key_points": bullet_points[:5],
        })

    total_chars = sum(len(t) for t in all_text_parts)

    return {
        "file": str(path),
        "total_slides": len(prs.slides),
        "total_characters": total_chars,
        "outline": outline,
    }


# ============================================================
# CLI 入口
# ============================================================


@click.group()
def main() -> None:
    """PowerPoint pptx 包装层工具."""
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
    type=click.Choice(["pdf", "md"]),
    required=True,
    help="目标格式",
)
def convert_cmd(input_path: str, output_path: str | None, target_format: str) -> None:
    """转换文件格式."""
    if target_format == "pdf":
        result = convert_pptx_to_pdf(input_path, output_path)
    elif target_format == "md":
        result = extract_pptx_to_markdown(input_path, output_path)
    else:
        click.echo(f"不支持的格式: {target_format}")
        sys.exit(1)
    click.echo(json.dumps({"output": result}, ensure_ascii=False))


@main.command("batch-read")
@click.argument("directory")
@click.option("-p", "--pattern", default="*.pptx", help="文件匹配模式")
def batch_read_cmd(directory: str, pattern: str) -> None:
    """批量读取演示文稿信息."""
    results = batch_read_presentations(directory, pattern)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@main.command("batch-extract")
@click.argument("directory")
@click.option("-o", "--output-dir", default=None, help="输出目录")
@click.option("-p", "--pattern", default="*.pptx", help="文件匹配模式")
def batch_extract_cmd(
    directory: str, output_dir: str | None, pattern: str
) -> None:
    """批量提取演示文稿文本为 Markdown."""
    results = batch_extract_text(directory, output_dir, pattern)
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
    """基于模板生成演示文稿."""
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
@click.option("-n", "--slides", "slide_count", default=5, help="幻灯片数量")
def create_template_cmd(output_path: str, title: str, slide_count: int) -> None:
    """创建标准报告模板."""
    result = create_report_template(output_path, title, slide_count)
    click.echo(json.dumps({"output": result}, ensure_ascii=False))


@main.command("analyze")
@click.argument("file_path")
def analyze_cmd(file_path: str) -> None:
    """分析演示文稿结构和内容."""
    result = analyze_presentation(file_path)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@main.command("notes")
@click.argument("file_path")
def notes_cmd(file_path: str) -> None:
    """提取演讲稿（备注）."""
    result = extract_speaker_notes(file_path)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@main.command("summarize")
@click.argument("file_path")
def summarize_cmd(file_path: str) -> None:
    """生成内容总结."""
    result = summarize_content(file_path)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
