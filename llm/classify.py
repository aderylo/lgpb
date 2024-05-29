from openai import OpenAI
import json


def classify(client: OpenAI, model: str, labels: list[str], text: str) -> str:
    response_format = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {"classification": {"type": "string", "enum": labels}},
            "required": ["classification"],
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"""You are intelligent labeling system, 
                            which for each user prompt classifies to one of the following labels: {str(labels)}""",
        },
        {"role": "user", "content": text},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format,
        logprobs=True,
    )

    content = json.loads(response.choices[0].message.content)
    return content["classification"]


if __name__ == "__main__":
    client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-xxx")

    label = classify(
        client=client,
        model="gpt-4",
        labels=["proponent budowy", "neutralny", "przeciwnik budowy"],
        text="Nikt mi nie powie ze czarne jest czarne a biale jest biale!",
    )
    print(label)
