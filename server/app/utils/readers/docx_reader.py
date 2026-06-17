from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _paragraph_text(paragraph: ElementTree.Element) -> str:
    pieces: list[str] = []

    for node in paragraph.iter():
        if node.tag == f"{{{NAMESPACE['w']}}}t" and node.text:
            pieces.append(node.text)
        elif node.tag == f"{{{NAMESPACE['w']}}}tab":
            pieces.append("\t")
        elif node.tag in {f"{{{NAMESPACE['w']}}}br", f"{{{NAMESPACE['w']}}}cr"}:
            pieces.append("\n")

    return "".join(pieces).strip()


def read(file_path: str) -> list[dict]:
    try:
        with ZipFile(file_path) as docx:
            document_xml = docx.read("word/document.xml")
    except (BadZipFile, KeyError) as exc:
        raise ValueError(f"Invalid DOCX file: {Path(file_path).name}") from exc

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid DOCX file: {Path(file_path).name}") from exc
    paragraphs = [
        text
        for paragraph in root.findall(".//w:p", NAMESPACE)
        if (text := _paragraph_text(paragraph))
    ]
    text = "\n\n".join(paragraphs).strip()

    if not text:
        return []

    return [{"page": 1, "text": text}]
