from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.services.database import init_db

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


app.include_router(documents_router)
app.include_router(chat_router)
