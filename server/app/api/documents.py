from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import UPLOADS_DIR
from app.services.database import create_chat_session, create_document, create_project
from app.services.embedder import embed_chunks, embed_text
from app.services.store_vector import add_chunks, search_chunks
from app.utils.chunker import chunk_pages
from app.utils.readers import read_file, supported_extensions

router = APIRouter(
    prefix="/file",
    tags=["file"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    project_id: str | None = None
    document_ids: list[str] | None = None


@router.post("/import")
async def import_file(
    file: UploadFile = File(...),
    project_id: str = "default",
    chat_id: str | None = None,
):
    document_id = str(uuid4())
    safe_filename = Path(file.filename or "document").name
    saved_file_path = UPLOADS_DIR / f"{document_id}_{safe_filename}"
    uploaded_at = datetime.now(timezone.utc).isoformat()

    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        with open(saved_file_path, "wb") as saved_file:
            saved_file.write(await file.read())

        create_project(
            project_id=project_id,
            name=None,
            created_at=uploaded_at,
            updated_at=uploaded_at,
        )

        create_document(
            document_id=document_id,
            project_id=project_id,
            filename=safe_filename,
            content_type=file.content_type,
            file_path=str(saved_file_path),
            uploaded_at=uploaded_at,
        )

        if chat_id:
            create_chat_session(
                chat_id=chat_id,
                project_id=project_id,
                title=None,
                created_at=uploaded_at,
                updated_at=uploaded_at,
            )

        pages = read_file(str(saved_file_path), safe_filename)
        chunks = chunk_pages(pages)
        embedded = embed_chunks(chunks)
        add_chunks(project_id, document_id, safe_filename, embedded)

    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    return {
        "document_id": document_id,
        "project_id": project_id,
        "chat_id": chat_id,
        "filename": safe_filename,
        "content_type": file.content_type,
        "supported_extensions": supported_extensions(),
        "status": "indexed",
        "page_count": len(pages),
        "chunk_count": len(chunks),
    }


@router.post("/search")
async def search_file(request: SearchRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    query_embedding = embed_text(query)
    results = search_chunks(
        query_embedding=query_embedding,
        top_k=request.top_k,
        project_id=request.project_id,
        document_ids=request.document_ids,
    )

    return {
        "query": query,
        "top_k": request.top_k,
        "project_id": request.project_id,
        "document_ids": request.document_ids,
        "results": results,
    }


@router.delete("/remove")
async def remove_file():
    print("file removed")
