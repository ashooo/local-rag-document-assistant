def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must not be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            paragraph_break = text.rfind("\n\n", start, end)
            sentence_break = text.rfind(". ", start, end)
            space_break = text.rfind(" ", start, end)
            split_at = max(paragraph_break, sentence_break, space_break)

            if split_at > start:
                end = split_at + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = max(end - overlap, 0)
        word_boundary = text.rfind(" ", start, next_start)

        if word_boundary > start:
            next_start = word_boundary + 1

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict]:
    chunks = []

    for page in pages:
        page_number = page.get("page")
        text = page.get("text", "")

        for chunk_text in _split_text(text, chunk_size, overlap):
            chunks.append({
                "page": page_number,
                "chunk_index": len(chunks),
                "text": chunk_text,
            })

    return chunks
