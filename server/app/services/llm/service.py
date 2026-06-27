from app.config import CONFIG
from app.services.llm.providers import get_provider


def generate_response(messages: list[dict]) -> str:
    provider = CONFIG["llm"]["provider"]
    model = CONFIG["llm"]["model"]
    
    llm = get_provider(provider, model)
    
    sdk = llm["sdk"]
    
    match sdk:
        case "openai":
            from app.services.llm.openai import generate_with_openai

            return generate_with_openai(llm, messages)
        case "anthropic":
            from app.services.llm.anthropic import generate_with_anthropic

            return generate_with_anthropic(llm, messages)
        case "ollama":
            from app.services.llm.ollama import generate_with_ollama

            return generate_with_ollama(llm, messages)
        case _:
            raise ValueError(f"SDK not supported: {sdk}")
    
