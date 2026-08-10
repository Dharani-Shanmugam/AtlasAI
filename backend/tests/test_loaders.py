from __future__ import annotations

import pytest

from app.services.ingestion.loaders import (
    UnsupportedFileTypeError,
    extract_text,
)


def test_plain_text_utf8():
    result = extract_text("note.txt", "héllo wörld".encode())
    assert result.text == "héllo wörld"
    assert result.content_type == "text/plain"


def test_markdown():
    result = extract_text("doc.md", b"# Title\n\nSome **bold** text")
    assert "# Title" in result.text
    assert result.content_type == "text/markdown"


def test_unsupported_type_raises():
    with pytest.raises(UnsupportedFileTypeError):
        extract_text("virus.exe", b"MZ...")


def test_empty_pdf_returns_empty():
    from io import BytesIO

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = BytesIO()
    writer.write(buf)
    pdf = buf.getvalue()

    result = extract_text("blank.pdf", pdf)
    assert result.text == ""
    assert result.content_type == "application/pdf"


def test_pdf_with_text_extracts():
    result = extract_text("real.pdf", _build_text_pdf("Hello from a real PDF"))
    assert "Hello from a real PDF" in result.text


def _build_text_pdf(text: str) -> bytes:
    """Hand-build a small, spec-valid PDF with one text page (no library)."""
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET\n".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF").encode()
    return bytes(out)
