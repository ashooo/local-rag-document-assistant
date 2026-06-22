import chromadb

from app.config import CHROMA_DIR

COLLECTION_NAME = "document_chunks"

def get_collection():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Local document chunks for RAG search",
        },
    )