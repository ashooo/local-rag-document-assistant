from pathlib import Path
from importlib import import_module


READERS = {
    ".pdf": "app.utils.readers.pdf_reader",
    ".docx": "app.utils.readers.docx_reader",
    ".md": "app.utils.readers.markdown_reader",
    ".markdown": "app.utils.readers.markdown_reader",
    ".txt": "app.utils.readers.txt_reader",
}


def supported_extensions() -> tuple[str, ...]:
    return tuple(sorted(READERS))


def read_file(file_path: str, filename: str | None = None) -> list[dict]:
    extension_source = filename or file_path
    extension = Path(extension_source).suffix.lower()
    reader = READERS.get(extension)

    if reader is None:
        supported = ", ".join(supported_extensions())
        raise ValueError(f"Unsupported file type '{extension or 'unknown'}'. Supported file types: {supported}")

    module = import_module(reader)
    return module.read(file_path)
