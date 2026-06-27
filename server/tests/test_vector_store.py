from app.services import store_vector


class FakeCollection:
    def __init__(self):
        self.add_call = None
        self.query_call = None
        self.delete_call = None

    def add(self, **kwargs):
        self.add_call = kwargs

    def query(self, **kwargs):
        self.query_call = kwargs
        return {
            "ids": [["doc_1_chunk_0"]],
            "documents": [["Chunk text"]],
            "metadatas": [[{"project_id": "project_1", "document_id": "doc_1"}]],
            "distances": [[0.12]],
        }

    def delete(self, **kwargs):
        self.delete_call = kwargs


def test_add_chunks_writes_project_document_metadata(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(store_vector, "get_collection", lambda: collection)

    store_vector.add_chunks(
        project_id="project_1",
        document_id="doc_1",
        filename="notes.txt",
        chunks=[
            {
                "page": 4,
                "chunk_index": 0,
                "text": "Chunk text",
                "embedding": [0.1, 0.2],
            }
        ],
    )

    assert collection.add_call["ids"] == ["doc_1_chunk_0"]
    assert collection.add_call["documents"] == ["Chunk text"]
    assert collection.add_call["embeddings"] == [[0.1, 0.2]]
    assert collection.add_call["metadatas"] == [
        {
            "project_id": "project_1",
            "document_id": "doc_1",
            "filename": "notes.txt",
            "chunk_index": 0,
            "page": 4,
        }
    ]


def test_search_chunks_filters_by_project(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(store_vector, "get_collection", lambda: collection)

    results = store_vector.search_chunks([0.1, 0.2], project_id="project_1")

    assert collection.query_call["where"] == {"project_id": "project_1"}
    assert results[0]["id"] == "doc_1_chunk_0"
    assert results[0]["text"] == "Chunk text"


def test_search_chunks_filters_by_project_and_document_ids(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(store_vector, "get_collection", lambda: collection)

    store_vector.search_chunks([0.1], project_id="project_1", document_ids=["doc_1", "doc_2"])

    assert collection.query_call["where"] == {
        "$and": [
            {"project_id": "project_1"},
            {"document_id": {"$in": ["doc_1", "doc_2"]}},
        ]
    }


def test_delete_document_chunks_deletes_by_document_id(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(store_vector, "get_collection", lambda: collection)

    store_vector.delete_document_chunks("doc_1")

    assert collection.delete_call == {"where": {"document_id": "doc_1"}}
