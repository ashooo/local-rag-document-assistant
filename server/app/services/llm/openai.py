def generate_with_openai(llm: dict, messages: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=llm.get("api_key"),
        base_url=llm["base_url"],
    )

    response = client.chat.completions.create(
        model=llm["model"],
        messages=messages,
    )

    return response.choices[0].message.content or ""
