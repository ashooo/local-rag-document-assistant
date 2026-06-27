import pytest

from app.utils.chunker import chunk_pages


def test_chunk_pages_returns_empty_for_empty_text():
    chunks = chunk_pages([{"page": 1, "text": "   "}])

    assert chunks == []


def test_chunk_pages_keeps_short_text_as_single_chunk():
    chunks = chunk_pages([{"page": 3, "text": "Short document text."}])

    assert chunks == [
        {
            "page": 3,
            "chunk_index": 0,
            "text": "Short document text.",
        }
    ]


def test_chunk_pages_splits_long_text_and_preserves_page_metadata():
    pages = [{"page": 2, "text": "Alpha beta gamma delta epsilon zeta eta theta."}]

    chunks = chunk_pages(pages, chunk_size=20, overlap=5)

    assert len(chunks) > 1
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert {chunk["page"] for chunk in chunks} == {2}
    assert all(chunk["text"] for chunk in chunks)


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [
        (0, 0, "chunk_size must be greater than 0"),
        (10, -1, "overlap must not be negative"),
        (10, 10, "overlap must be smaller than chunk_size"),
    ],
)
def test_chunk_pages_rejects_invalid_chunk_settings(chunk_size, overlap, message):
    with pytest.raises(ValueError, match=message):
        chunk_pages([{"page": 1, "text": "Some text"}], chunk_size=chunk_size, overlap=overlap)
