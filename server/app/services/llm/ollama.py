def generate_with_ollama(llm: dict, messages: list[dict]) -> str:
    import httpx

    response = httpx.post(
        f"{llm['base_url']}/api/chat",
        json={
            "model": llm["model"],
            "messages": messages,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["message"]["content"]
