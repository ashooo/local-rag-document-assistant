import fitz

def read(file_path: str) -> list[dict]:
    pages = []
    
    with fitz.open(file_path) as pdf:
        for index, page in enumerate(pdf):
            text = page.get_text("text").strip()

            if text:
                pages.append({
                    "page": index + 1,
                    "text": text
                })

    return pages