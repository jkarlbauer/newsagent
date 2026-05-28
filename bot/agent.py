import json
from openai import OpenAI
from config import config

_client = OpenAI(
    api_key=config["deepseek_api_key"],
    base_url="https://api.deepseek.com",
)
_MODEL = config["deepseek_model"]

with open("prompts/topics.md") as f:
    _SYSTEM_PROMPT = f.read()


def generate_topics(interests: str) -> list[str]:
    print(f"[agent] generating topics for: {interests!r}")
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": interests},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()
    print(f"[agent] raw response: {raw}")
    parsed = json.loads(raw)
    if parsed.get("error") == "invalid_input":
        print("[agent] rejected: invalid or injected input")
        return None
    topics = parsed.get("topics", [])[:10]
    print(f"[agent] parsed topics: {topics}")
    return topics
