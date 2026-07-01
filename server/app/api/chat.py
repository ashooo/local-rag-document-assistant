from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import CHROMA_DIR
from app.services.embedder import embed_text
from app.services.database import (
    create_chat_session,
    create_project,
    get_chat_session,
    list_project_chat_sessions,
)
from app.services.store_vector import VectorStore
from app.services.llm import generate_message

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)
vector_store = VectorStore(CHROMA_DIR)


class CreateChatRequest(BaseModel):
    project_id: str = "default"
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


FRONT_MATTER_TERMS = (
    "author",
    "authors",
    "study title",
    "title",
    "paper title",
    "article title",
    "research title",
    "publication",
)


@router.post("")
def create_chat(request: CreateChatRequest):
    chat_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    create_project(
        project_id=request.project_id,
        name=None,
        created_at=created_at,
        updated_at=created_at,
    )
    create_chat_session(
        chat_id=chat_id,
        project_id=request.project_id,
        title=request.title,
        created_at=created_at,
        updated_at=created_at,
    )

    return {
        "chat_id": chat_id,
        "project_id": request.project_id,
        "title": request.title,
        "created_at": created_at,
    }


@router.get("")
def list_chats(project_id: str = "default"):
    chat_sessions = list_project_chat_sessions(project_id)

    return {
        "project_id": project_id,
        "chats": [
            {
                "chat_id": chat_session["id"],
                "project_id": chat_session["project_id"],
                "title": chat_session["title"],
                "created_at": chat_session["created_at"],
                "updated_at": chat_session["updated_at"],
            }
            for chat_session in chat_sessions
        ],
    }


@router.post("/{chat_id}/messages")
def send_message(chat_id: str, request: SendMessageRequest):
    user_message = request.content.strip()

    if not user_message:
        return {
            "chat_id": chat_id,
            "answer": "Please enter a message.",
            "sources": [],
        }

    chat_session = get_chat_session(chat_id)

    if not chat_session:
        return {
            "chat_id": chat_id,
            "answer": "Chat session not found.",
            "sources": [],
        }

    project_id = chat_session["project_id"]
    query_embedding = embed_text(user_message)
    results = vector_store.search_chunks(
        query_embedding=query_embedding,
        top_k=request.top_k,
        project_id=project_id,
    )
    if _needs_front_matter(user_message):
        results = _merge_chunks(
            vector_store.get_front_matter_chunks(project_id=project_id),
            results,
        )

    if not results:
        return {
            "chat_id": chat_id,
            "project_id": project_id,
            "answer": "No relevant document context was found for this project.",
            "sources": [],
        }

    context = "\n\n".join(
        f"Source {index + 1}: {result['text']}"
        for index, result in enumerate(results)
    )
    messages = [
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{user_message}",
        },
    ]
    answer = generate_message(messages)

    return {
        "chat_id": chat_id,
        "project_id": project_id,
        "answer": answer,
        "sources": [
            {
                "id": result["id"],
                "text": result["text"],
                "metadata": result["metadata"],
                "distance": result["distance"],
            }
            for result in results
        ],
    }


def _needs_front_matter(message: str) -> bool:
    normalized = message.casefold()
    return any(term in normalized for term in FRONT_MATTER_TERMS)


def _merge_chunks(*chunk_groups: list[dict]) -> list[dict]:
    merged = []
    seen_ids = set()

    for group in chunk_groups:
        for chunk in group:
            chunk_id = chunk["id"]

            if chunk_id in seen_ids:
                continue

            merged.append(chunk)
            seen_ids.add(chunk_id)

    return merged
