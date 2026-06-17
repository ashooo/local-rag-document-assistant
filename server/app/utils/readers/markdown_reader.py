from .txt_reader import read_text_file


def read(file_path: str) -> list[dict]:
    text = read_text_file(file_path).strip()

    if not text:
        return []

    return [{"page": 1, "text": text}]
