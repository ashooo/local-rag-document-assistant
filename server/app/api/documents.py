from fastapi import APIRouter, UploadFile, File

router = APIRouter(
    prefix="/file", 
    tags=["file"]
    )

@router.post("/import")
async def import_file(file: UploadFile = File(...)):
     return {
        "filename": file.filename,
        "content_type": file.content_type,
    }

@router.delete("/remove")
async def remove_file():
     print("file removed")