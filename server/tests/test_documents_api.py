import asyncio

from app.api import documents


def test_list_files_returns_project_documents(monkeypatch):
    monkeypatch.setattr(
        documents,
        "list_project_documents",
        lambda project_id: [
            {
                "id": "doc_1",
                "project_id": project_id,
                "filename": "notes.pdf",
                "content_type": "application/pdf",
                "uploaded_at": "2026-06-27T00:00:00+00:00",
                "status": "indexed",
                "page_count": 2,
                "chunk_count": 8,
            }
        ],
    )
    monkeypatch.setattr(documents, "supported_extensions", lambda: (".pdf", ".txt"))

    response = asyncio.run(documents.list_files("project_1"))

    assert response == {
        "project_id": "project_1",
        "documents": [
            {
                "document_id": "doc_1",
                "project_id": "project_1",
                "filename": "notes.pdf",
                "content_type": "application/pdf",
                "uploaded_at": "2026-06-27T00:00:00+00:00",
                "status": "indexed",
                "page_count": 2,
                "chunk_count": 8,
            }
        ],
        "supported_extensions": (".pdf", ".txt"),
    }
