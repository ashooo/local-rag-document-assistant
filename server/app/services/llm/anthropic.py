def generate_with_anthropic(llm: dict, messages: list[dict]) -> str:
    from anthropic import Anthropic

    client = Anthropic(
        api_key=llm.get("api_key"),
    )

    system_prompt = ""
    user_messages = []

    for message in messages:
        if message["role"] == "system":
            system_prompt = message["content"]
        else:
            user_messages.append(message)

    response = client.messages.create(
        model=llm["model"],
        max_tokens=1024,
        system=system_prompt,
        messages=user_messages,
    )

    return response.content[0].text
