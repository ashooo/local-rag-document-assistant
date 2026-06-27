import pytest

from app.services.llm.providers import get_provider


def test_get_provider_uses_default_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")

    provider = get_provider("groq", "")

    assert provider["sdk"] == "openai"
    assert provider["base_url"] == "https://api.groq.com/openai/v1"
    assert provider["model"] == "llama-3.1-8b-instant"
    assert provider["api_key"] == "fake-groq-key"


def test_get_provider_uses_model_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")

    provider = get_provider("openai", "custom-model")

    assert provider["model"] == "custom-model"
    assert provider["api_key"] == "fake-openai-key"


@pytest.mark.parametrize(
    ("provider_name", "env_name", "fake_key"),
    [
        ("openai", "OPENAI_API_KEY", "fake-openai-key"),
        ("deepseek", "DEEPSEEK_API_KEY", "fake-deepseek-key"),
        ("groq", "GROQ_API_KEY", "fake-groq-key"),
        ("gemini", "GEMINI_API_KEY", "fake-gemini-key"),
    ],
)
def test_api_providers_read_their_own_env_keys(monkeypatch, provider_name, env_name, fake_key):
    monkeypatch.setenv(env_name, fake_key)

    provider = get_provider(provider_name, "")

    assert provider["api_key"] == fake_key


def test_ollama_does_not_require_api_key():
    provider = get_provider("ollama", "")

    assert provider["sdk"] == "ollama"
    assert provider["model"] == "llama3.2"
    assert provider["api_key"] is None


def test_unknown_provider_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_provider("unknown", "")
