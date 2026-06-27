import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

PROVIDERS = {
    "openai": {
        "sdk": "openai",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "sdk": "openai",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "groq": {
        "sdk": "openai",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
        "api_key_env": "GROQ_API_KEY",
    },
    "ollama": {
        "sdk": "ollama",
        "base_url": "http://localhost:11434",
        "default_model": "llama3.2",
    },
}

def get_provider(provider: str, model: str) -> dict:
    try:
        provider_config = PROVIDERS[provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported LLM provider: {provider}") from exc
    
    selected_model = model or provider_config["default_model"]
    
    api_key = None
    api_key_env = provider_config.get("api_key_env")
    
    if api_key_env:
        api_key = os.getenv(api_key_env)
    
    return {
        **provider_config,
        "model": selected_model,
        "api_key": api_key,
    }
    
