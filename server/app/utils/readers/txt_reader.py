ENCODINGS = ("utf-8-sig", "utf-16", "cp1252")


def read_text_file(file_path: str) -> str:
    last_error: UnicodeDecodeError | None = None

    for encoding in ENCODINGS:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError("Unable to decode text file with supported encodings") from last_error


def read(file_path: str) -> list[dict]:
    text = read_text_file(file_path).strip()

    if not text:
        return []

    return [{"page": 1, "text": text}]
