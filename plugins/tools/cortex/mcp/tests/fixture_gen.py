"""Generate test fixtures (sample.pdf / sample.epub / sample.docx).

Run once; commit the produced files. Tests do not depend on network.

    python3 tests/fixture_gen.py
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Each fixture intentionally includes the AWS AKID example token so masking
# wire-up tests can verify P0 secret redaction after ingest.
SECRET = "AKIAIOSFODNN7EXAMPLE"

SAMPLE_TEXT = (
    "Cortex Ingest Sample Document\n\n"
    "This is a small test document used by cortex-mcp ingest tests. "
    "It mentions a fake AWS access key id like " + SECRET + " "
    "to exercise the masking filter wired into the ingest pipeline.\n\n"
    "Second paragraph. Knowledge base ingestion should preserve paragraph "
    "structure and basic metadata."
)


def make_pdf(path: Path) -> None:
    from pypdf import PdfWriter
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # Inject a minimal text content stream (Helvetica, BT/ET block).
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    resources = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref}),
        }
    )
    page[NameObject("/Resources")] = resources

    lines = SAMPLE_TEXT.split("\n")
    y = 750
    parts = ["BT", "/F1 12 Tf"]
    for ln in lines:
        ln = ln.replace("(", "\\(").replace(")", "\\)")
        parts.append(f"1 0 0 1 72 {y} Tm ({ln}) Tj")
        y -= 18
    parts.append("ET")
    stream = DecodedStreamObject()
    stream.set_data("\n".join(parts).encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    writer.add_metadata({"/Title": "Cortex Sample", "/Author": "cortex-tests"})
    with path.open("wb") as fh:
        writer.write(fh)


def make_epub(path: Path) -> None:
    from ebooklib import epub

    book = epub.EpubBook()
    book.set_identifier("cortex-sample")
    book.set_title("Cortex Sample")
    book.set_language("en")
    book.add_author("cortex-tests")

    chapter_html = (
        "<html><body>"
        "<h1>Chapter One</h1>"
        f"<p>{SAMPLE_TEXT.replace(chr(10) + chr(10), '</p><p>')}</p>"
        "<script>alert('xss')</script>"
        "</body></html>"
    )
    chapter = epub.EpubHtml(title="Chapter One", file_name="ch1.xhtml", lang="en")
    chapter.content = chapter_html
    book.add_item(chapter)
    book.toc = (chapter,)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]
    epub.write_epub(str(path), book)


def make_docx(path: Path) -> None:
    import docx

    doc = docx.Document()
    doc.core_properties.title = "Cortex Sample"
    doc.core_properties.author = "cortex-tests"
    for para in SAMPLE_TEXT.split("\n\n"):
        doc.add_paragraph(para)
    doc.save(str(path))


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    make_pdf(FIXTURES / "sample.pdf")
    make_epub(FIXTURES / "sample.epub")
    make_docx(FIXTURES / "sample.docx")
    # Plain-text helpers used by ingest_file tests.
    (FIXTURES / "sample.md").write_text(
        f"# Sample MD\n\nIncludes secret: {SECRET}\n", encoding="utf-8"
    )
    (FIXTURES / "sample.txt").write_text(
        f"Plain text with secret {SECRET}.\n", encoding="utf-8"
    )
    print(f"generated fixtures in {FIXTURES}")


if __name__ == "__main__":
    main()
