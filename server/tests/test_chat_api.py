from app.api import chat
from app.api.chat import CreateChatRequest, SendMessageRequest


def test_create_chat_creates_project_and_session(monkeypatch):
    calls = {}

    monkeypatch.setattr(chat, "uuid4", lambda: "chat_1")
    monkeypatch.setattr(chat, "datetime", type("FakeDateTime", (), {
        "now": staticmethod(lambda timezone: type("FakeNow", (), {
            "isoformat": staticmethod(lambda: "2026-06-27T00:00:00+00:00")
        })())
    }))
    monkeypatch.setattr(chat, "create_project", lambda **kwargs: calls.setdefault("project", kwargs))
    monkeypatch.setattr(chat, "create_chat_session", lambda **kwargs: calls.setdefault("chat", kwargs))

    response = chat.create_chat(CreateChatRequest(project_id="project_1", title="Research"))

    assert response["chat_id"] == "chat_1"
    assert response["project_id"] == "project_1"
    assert calls["project"]["project_id"] == "project_1"
    assert calls["chat"]["chat_id"] == "chat_1"
    assert calls["chat"]["project_id"] == "project_1"


def test_list_chats_returns_project_sessions(monkeypatch):
    monkeypatch.setattr(
        chat,
        "list_project_chat_sessions",
        lambda project_id: [
            {
                "id": "chat_1",
                "project_id": project_id,
                "title": "Research",
                "created_at": "2026-06-27T00:00:00+00:00",
                "updated_at": "2026-06-27T00:00:00+00:00",
            }
        ],
    )

    response = chat.list_chats("project_1")

    assert response == {
        "project_id": "project_1",
        "chats": [
            {
                "chat_id": "chat_1",
                "project_id": "project_1",
                "title": "Research",
                "created_at": "2026-06-27T00:00:00+00:00",
                "updated_at": "2026-06-27T00:00:00+00:00",
            }
        ],
    }


def test_send_message_returns_not_found_for_missing_chat(monkeypatch):
    monkeypatch.setattr(chat, "get_chat_session", lambda chat_id: None)

    response = chat.send_message("chat_1", SendMessageRequest(content="Hello"))

    assert response == {
        "chat_id": "chat_1",
        "answer": "Chat session not found.",
        "sources": [],
    }


def test_send_message_searches_project_and_generates_answer(monkeypatch):
    monkeypatch.setattr(chat, "get_chat_session", lambda chat_id: {"id": chat_id, "project_id": "project_1"})
    monkeypatch.setattr(chat, "embed_text", lambda text: [0.1, 0.2])
    monkeypatch.setattr(
        chat.vector_store,
        "search_chunks",
        lambda query_embedding, top_k, project_id: [
            {
                "id": "doc_1_chunk_0",
                "text": "The answer is in this chunk.",
                "metadata": {"project_id": project_id, "document_id": "doc_1"},
                "distance": 0.2,
            }
        ],
    )
    monkeypatch.setattr(chat, "generate_message", lambda messages: "Generated answer")

    response = chat.send_message("chat_1", SendMessageRequest(content="What is the answer?", top_k=3))

    assert response["chat_id"] == "chat_1"
    assert response["project_id"] == "project_1"
    assert response["answer"] == "Generated answer"
    assert response["sources"] == [
        {
            "id": "doc_1_chunk_0",
            "text": "The answer is in this chunk.",
            "metadata": {"project_id": "project_1", "document_id": "doc_1"},
            "distance": 0.2,
        }
    ]


def test_send_message_adds_front_matter_for_title_author_questions(monkeypatch):
    captured = {}

    monkeypatch.setattr(chat, "get_chat_session", lambda chat_id: {"id": chat_id, "project_id": "project_1"})
    monkeypatch.setattr(chat, "embed_text", lambda text: [0.1, 0.2])
    monkeypatch.setattr(
        chat.vector_store,
        "get_front_matter_chunks",
        lambda project_id: [
            {
                "id": "doc_1_chunk_0",
                "text": "Study Title\nAda Lovelace, Grace Hopper",
                "metadata": {
                    "project_id": project_id,
                    "document_id": "doc_1",
                    "filename": "study.pdf",
                    "page": 1,
                    "chunk_index": 0,
                },
                "distance": None,
            }
        ],
    )
    monkeypatch.setattr(
        chat.vector_store,
        "search_chunks",
        lambda query_embedding, top_k, project_id: [
            {
                "id": "doc_1_chunk_2",
                "text": "A later chunk about methods.",
                "metadata": {"project_id": project_id, "document_id": "doc_1"},
                "distance": 0.2,
            }
        ],
    )

    def fake_generate_message(messages):
        captured["content"] = messages[0]["content"]
        return "The study title is Study Title. The authors are Ada Lovelace and Grace Hopper."

    monkeypatch.setattr(chat, "generate_message", fake_generate_message)

    response = chat.send_message(
        "chat_1",
        SendMessageRequest(content="what is the studies title and who are the authors"),
    )

    assert "Study Title\nAda Lovelace, Grace Hopper" in captured["content"]
    assert "A later chunk about methods." in captured["content"]
    assert response["sources"][0]["id"] == "doc_1_chunk_0"
