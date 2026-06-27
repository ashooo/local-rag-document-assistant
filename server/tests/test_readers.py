from zipfile import ZipFile

import pytest

from app.utils.readers import read_file, supported_extensions


def test_supported_extensions_includes_document_formats():
    assert supported_extensions() == (".docx", ".markdown", ".md", ".pdf", ".txt")


def test_read_file_reads_txt(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Hello text", encoding="utf-8")

    assert read_file(str(file_path)) == [{"page": 1, "text": "Hello text"}]


def test_read_file_reads_markdown(tmp_path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("# Hello markdown", encoding="utf-8")

    assert read_file(str(file_path)) == [{"page": 1, "text": "# Hello markdown"}]


def test_read_file_reads_docx(tmp_path):
    file_path = tmp_path / "notes.docx"
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    document_xml = (
        f'<w:document xmlns:w="{namespace}">'
        "<w:body>"
        "<w:p><w:r><w:t>Hello DOCX</w:t></w:r></w:p>"
        "</w:body>"
        "</w:document>"
    )

    with ZipFile(file_path, "w") as docx:
        docx.writestr("word/document.xml", document_xml)

    assert read_file(str(file_path)) == [{"page": 1, "text": "Hello DOCX"}]


def test_read_file_rejects_unsupported_extension(tmp_path):
    file_path = tmp_path / "notes.xyz"
    file_path.write_text("No reader", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type '.xyz'"):
        read_file(str(file_path))
