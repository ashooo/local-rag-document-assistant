import pytest

from app.services.llm import service


def test_generate_message_adds_system_prompt(monkeypatch):
    captured = {}

    def fake_generate_response(messages):
        captured["messages"] = messages
        return "answer"

    monkeypatch.setattr(service, "generate_response", fake_generate_response)

    answer = service.generate_message([{"role": "user", "content": "Question?"}])

    assert answer == "answer"
    assert captured["messages"][0]["role"] == "system"
    assert "RAG document assistant" in captured["messages"][0]["content"]
    assert captured["messages"][1] == {"role": "user", "content": "Question?"}


def test_generate_response_dispatches_openai(monkeypatch):
    monkeypatch.setitem(service.CONFIG, "llm", {"provider": "openai", "model": "test-model"})
    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider, model: {"sdk": "openai", "model": model, "base_url": "url", "api_key": "key"},
    )
    monkeypatch.setattr(service, "generate_with_openai", lambda llm, messages: "openai answer")

    assert service.generate_response([{"role": "user", "content": "Hi"}]) == "openai answer"


def test_generate_response_dispatches_anthropic(monkeypatch):
    monkeypatch.setitem(service.CONFIG, "llm", {"provider": "anthropic", "model": "test-model"})
    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider, model: {"sdk": "anthropic", "model": model, "api_key": "key"},
    )
    monkeypatch.setattr(service, "generate_with_anthropic", lambda llm, messages: "anthropic answer")

    assert service.generate_response([{"role": "user", "content": "Hi"}]) == "anthropic answer"


def test_generate_response_dispatches_ollama(monkeypatch):
    monkeypatch.setitem(service.CONFIG, "llm", {"provider": "ollama", "model": "llama3.2"})
    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider, model: {"sdk": "ollama", "model": model, "base_url": "http://localhost:11434"},
    )
    monkeypatch.setattr(service, "generate_with_ollama", lambda llm, messages: "ollama answer")

    assert service.generate_response([{"role": "user", "content": "Hi"}]) == "ollama answer"


def test_generate_response_rejects_unknown_sdk(monkeypatch):
    monkeypatch.setitem(service.CONFIG, "llm", {"provider": "bad", "model": "test-model"})
    monkeypatch.setattr(service, "get_provider", lambda provider, model: {"sdk": "bad"})

    with pytest.raises(ValueError, match="SDK not supported: bad"):
        service.generate_response([{"role": "user", "content": "Hi"}])
