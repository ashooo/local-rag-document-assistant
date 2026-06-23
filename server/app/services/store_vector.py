from app.config import CHROMA_DIR

COLLECTION_NAME = "document_chunks"


def get_collection():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Local document chunks for RAG search",
        },
    )


def add_chunks(
    document_id: str,
    filename: str,
    chunks: list[dict],
) -> None:
    if not chunks:
        return

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for chunk in chunks:
        chunk_index = chunk["chunk_index"]
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "chunk_index": chunk_index,
        }

        if chunk.get("page") is not None:
            metadata["page"] = chunk["page"]

        ids.append(f"{document_id}_chunk_{chunk_index}")
        documents.append(chunk["text"])
        embeddings.append(chunk["embedding"])
        metadatas.append(metadata)

    collection = get_collection()
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search_chunks(
    query_embedding: list[float],
    top_k: int = 5,
    document_ids: list[str] | None = None,
) -> list[dict]:
    collection = get_collection()
    where = None

    if document_ids:
        where = {"document_id": {"$in": document_ids}}

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
    }

    if where:
        query_args["where"] = where

    results = collection.query(**query_args)

    matches = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, chunk_id in enumerate(ids):
        matches.append({
            "id": chunk_id,
            "text": documents[index],
            "metadata": metadatas[index],
            "distance": distances[index],
        })

    return matches


def delete_document_chunks(document_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"document_id": document_id})
