from pathlib import Path

COLLECTION_NAME = "document_chunks"


class VectorStore:
    def __init__(self, chroma_dir: Path, collection_name: str = COLLECTION_NAME):
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name

    def get_collection(self):
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

        import chromadb

        client = chromadb.PersistentClient(path=str(self.chroma_dir))

        return client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Local document chunks for RAG search",
            },
        )


    def add_chunks(
        self,
        project_id: str,
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
                "project_id": project_id,
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

        collection = self.get_collection()
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


    def search_chunks(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        project_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        collection = self.get_collection()
        where = None

        if project_id and document_ids:
            where = {
                "$and": [
                    {"project_id": project_id},
                    {"document_id": {"$in": document_ids}},
                ],
            }
        elif project_id:
            where = {"project_id": project_id}
        elif document_ids:
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


    def get_front_matter_chunks(
        self,
        project_id: str,
        max_chunks_per_document: int = 3,
    ) -> list[dict]:
        collection = self.get_collection()
        results = collection.get(
            where={"project_id": project_id},
            include=["documents", "metadatas"],
        )

        matches = []
        ids = results.get("ids", [])
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] or {}
            matches.append({
                "id": chunk_id,
                "text": documents[index],
                "metadata": metadata,
                "distance": None,
            })

        matches.sort(
            key=lambda result: (
                result["metadata"].get("document_id", ""),
                result["metadata"].get("page", 10**9),
                result["metadata"].get("chunk_index", 10**9),
            )
        )

        selected = []
        selected_counts = {}

        for result in matches:
            document_id = result["metadata"].get("document_id") or result["id"]
            count = selected_counts.get(document_id, 0)

            if count >= max_chunks_per_document:
                continue

            selected.append(result)
            selected_counts[document_id] = count + 1

        return selected


    def delete_document_chunks(self, document_id: str) -> None:
        collection = self.get_collection()
        collection.delete(where={"document_id": document_id})
