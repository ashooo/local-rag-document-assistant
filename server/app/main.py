from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.services.database import init_db

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


app.include_router(documents_router)
