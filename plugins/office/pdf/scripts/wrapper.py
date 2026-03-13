"""PDF wrapper - 格式转换、批量处理、OCR、智能分析增强功能.

提供 pdf-reader-mcp 之外的额外功能：
- 格式转换：PDF → text、PDF → markdown
- 批量处理：批量 PDF 解析
- OCR 支持：图像 PDF 文字识别（可选）
- 智能分析：文档分类、内容提取

Usage:
    python wrapper.py convert <input> <output> [--format FORMAT]
    python wrapper.py batch-extract <directory> <output> [--format FORMAT]
    python wrapper.py analyze <input> [--output OUTPUT]
    python wrapper.py classify <input>
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
from pypdf import PdfReader

logger = logging.getLogger(__name__)


# ── 格式转换 ──────────────────────────────────────────────


def convert_pdf_to_text(input_path: str, output_path: str | None = None) -> str:
    """将 PDF 转换为纯文本.

    Args:
        input_path: 输入 PDF 路径.
        output_path: 输出文本路径，默认与输入同名.

    Returns:
        输出文件路径.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".txt"))

    reader = PdfReader(str(input_file))
    text_lines = []

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            text_lines.append(f"=== 第 {page_num} 页 ===\n")
            text_lines.append(text)
            text_lines.append("\n\n")

    Path(output_path).write_text("".join(text_lines), encoding="utf-8")
    logger.info(f"转换完成: {output_path}")
    return output_path


def convert_pdf_to_markdown(input_path: str, output_path: str | None = None) -> str:
    """将 PDF 转换为 Markdown 格式.

    Args:
        input_path: 输入 PDF 路径.
        output_path: 输出 Markdown 路径，默认与输入同名.

    Returns:
        输出文件路径.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".md"))

    reader = PdfReader(str(input_file))
    md_lines = []

    # 添加文档标题
    metadata = reader.metadata
    if metadata and metadata.get("/Title"):
        md_lines.append(f"# {metadata['/Title']}\n\n")

    # 处理每一页
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            md_lines.append(f"## 第 {page_num} 页\n\n")
            md_lines.append(f"{text}\n\n")

    Path(output_path).write_text("".join(md_lines), encoding="utf-8")
    logger.info(f"转换完成: {output_path}")
    return output_path


# ── 批量处理 ──────────────────────────────────────────────


def batch_extract_text(
    directory: str, output_dir: str, pattern: str = "*.pdf"
) -> dict[str, str]:
    """批量提取目录中所有 PDF 的文本.

    Args:
        directory: 输入目录.
        output_dir: 输出目录.
        pattern: 文件匹配模式.

    Returns:
        文件映射字典 {input_path: output_path}.
    """
    input_path = Path(directory)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for pdf_file in input_path.glob(pattern):
        if pdf_file.is_file():
            output_file = output_path / f"{pdf_file.stem}.txt"
            try:
                convert_pdf_to_text(str(pdf_file), str(output_file))
                results[str(pdf_file)] = str(output_file)
            except Exception as e:
                logger.error(f"处理失败 {pdf_file}: {e}")

    logger.info(f"批量处理完成: {len(results)} 个文件")
    return results


# ── 智能分析 ──────────────────────────────────────────────


def analyze_pdf(input_path: str) -> dict[str, Any]:
    """分析 PDF 文档结构和内容.

    Args:
        input_path: PDF 文件路径.

    Returns:
        分析结果字典.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    reader = PdfReader(str(input_file))
    metadata = reader.metadata

    # 基础信息
    analysis = {
        "file": str(input_file),
        "pages": len(reader.pages),
        "metadata": {
            "title": metadata.get("/Title") if metadata else None,
            "author": metadata.get("/Author") if metadata else None,
            "subject": metadata.get("/Subject") if metadata else None,
            "creator": metadata.get("/Creator") if metadata else None,
            "producer": metadata.get("/Producer") if metadata else None,
        },
        "structure": {
            "total_pages": len(reader.pages),
            "has_text": False,
            "has_images": False,
            "text_pages": 0,
        },
    }

    # 内容分析
    total_text = 0
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            analysis["structure"]["has_text"] = True
            analysis["structure"]["text_pages"] += 1
            total_text += len(text)

        # 检查是否有图片
        if "/XObject" in page.get("/Resources", {}):
            analysis["structure"]["has_images"] = True

    # 统计信息
    analysis["statistics"] = {
        "total_characters": total_text,
        "avg_chars_per_page": (
            total_text / len(reader.pages) if len(reader.pages) > 0 else 0
        ),
        "empty_pages": len(reader.pages) - analysis["structure"]["text_pages"],
    }

    return analysis


def classify_pdf(input_path: str) -> str:
    """分类 PDF 文档类型.

    Args:
        input_path: PDF 文件路径.

    Returns:
        文档类型（report/presentation/book/form/other）.
    """
    analysis = analyze_pdf(input_path)

    pages = analysis["pages"]
    avg_chars = analysis["statistics"]["avg_chars_per_page"]
    has_images = analysis["structure"]["has_images"]

    # 简单的分类逻辑
    if pages <= 5 and has_images:
        return "form"  # 表单
    if pages <= 20 and avg_chars < 500:
        return "presentation"  # 演示文稿
    if pages > 50:
        return "book"  # 书籍
    if pages <= 30 and avg_chars > 1000:
        return "report"  # 报告

    return "other"


# ── CLI 入口 ──────────────────────────────────────────────


@click.group()
def cli():
    """PDF 包装层 CLI - 提供格式转换、批量处理、智能分析功能."""
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.argument("output_path", type=click.Path(), required=False)
@click.option(
    "--format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    help="输出格式",
)
def convert(input_path: str, output_path: str | None, format: str):
    """转换 PDF 为文本或 Markdown."""
    try:
        if format == "text":
            result = convert_pdf_to_text(input_path, output_path)
        else:
            result = convert_pdf_to_markdown(input_path, output_path)
        click.echo(f"✓ 转换完成: {result}")
    except Exception as e:
        click.echo(f"✗ 转换失败: {e}", err=True)
        sys.exit(1)


@cli.command("batch-extract")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.argument("output_dir", type=click.Path())
@click.option("--format", default="text", help="输出格式 (text/markdown)")
def batch_extract(directory: str, output_dir: str, format: str):
    """批量提取目录中所有 PDF 的文本."""
    try:
        results = batch_extract_text(directory, output_dir)
        click.echo(f"✓ 处理完成: {len(results)} 个文件")
        for input_file, output_file in results.items():
            click.echo(f"  {input_file} → {output_file}")
    except Exception as e:
        click.echo(f"✗ 批量处理失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="输出 JSON 文件路径")
def analyze(input_path: str, output: str | None):
    """分析 PDF 文档结构和内容."""
    try:
        result = analyze_pdf(input_path)

        if output:
            Path(output).write_text(json.dumps(result, indent=2, ensure_ascii=False))
            click.echo(f"✓ 分析结果已保存: {output}")
        else:
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"✗ 分析失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
def classify(input_path: str):
    """分类 PDF 文档类型."""
    try:
        doc_type = classify_pdf(input_path)
        click.echo(f"文档类型: {doc_type}")
    except Exception as e:
        click.echo(f"✗ 分类失败: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
