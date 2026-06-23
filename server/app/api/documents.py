from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, File, HTTPException, UploadFile

from utils.chunker import chunk_pages
from utils.readers import read_file, supported_extensions

from app.config import DATA_DIR, UPLOADS_DIR, CHROMA_DIR, DB_PATH

router = APIRouter(
    prefix="/file", 
    tags=["file"]
    )

@router.post("/import")
async def import_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix
    temp_path = None

    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())

        pages = read_file(temp_path, file.filename)
        chunks = chunk_pages(pages)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "supported_extensions": supported_extensions(),
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "pages": pages,
        "chunks": chunks,
    }

@router.delete("/remove")
async def remove_file():
     print("file removed")
