from app.config import CONFIG
from app.services.llm.providers import get_provider

from app.services.llm.openai import generate_with_openai
from app.services.llm.anthropic import generate_with_anthropic
from app.services.llm.ollama import generate_with_ollama

SYSTEM_PROMPT = """
You are a helpful RAG document assistant.

Answer the user's question using only the provided document context.

Rules:
- If the answer is in the context, answer clearly and directly.
- If the answer is not in the context, say: "I cannot find that in the provided document."
- Do not invent facts, names, dates, numbers, citations, or conclusions.
- If the context is incomplete or unclear, say what is missing.
- Cite sources using the provided labels, such as [Source 1] or [Source 2].
- Keep the answer concise unless the user asks for a detailed explanation.
"""

def generate_message(messages: list[dict]) -> str:
    message = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.strip(),  
        },
        *messages,
    ]
    
    return generate_response(message)

def generate_response(messages: list[dict]) -> str:
    provider = CONFIG["llm"]["provider"]
    model = CONFIG["llm"]["model"]
    
    llm = get_provider(provider, model)
    
    sdk = llm["sdk"]
    
    match sdk:
        case "openai":
            return generate_with_openai(llm, messages)
        case "anthropic":
            return generate_with_anthropic(llm, messages)
        case "ollama":
            return generate_with_ollama(llm, messages)
        case _:
            raise ValueError(f"SDK not supported: {sdk}")
    