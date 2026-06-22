from functools import lru_cache

from app.config import CONFIG


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(CONFIG["embedder_model"])


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embeddings.tolist()


def embed_text(text: str) -> list[float]:
    embeddings = embed_texts([text])
    return embeddings[0] if embeddings else []


def embed_chunks(chunks: list[dict]) -> list[dict]:
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(texts)

    embedded_chunks = []

    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append({
            **chunk,
            "embedding": embedding,
        })

    return embedded_chunks


if __name__ == "__main__":
    print(CONFIG["embedder_model"])
