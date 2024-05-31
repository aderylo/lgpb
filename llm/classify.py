from openai import OpenAI
import json
import numpy as np


def all_labels_represented(labels: list[str], tokens: list[str]):
    count = 0
    for label in labels:
        for token in tokens:
            if label.startswith(token):
                count += 1
                break

    return count == len(labels)


def longest_prefix_in_dict(s, dict):
    longest = ""
    for i in range(1, len(s) + 1):
        prefix = s[:i]
        if prefix in dict:
            longest = prefix

    return longest


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
        top_logprobs=3,
    )

    label_probs = {label: 0 for label in labels}
    for logprobs in response.choices[0].logprobs.top_logprobs:

        if all_labels_represented(labels, logprobs.keys()):
            for label in labels:
                prefix = longest_prefix_in_dict(label, logprobs)
                label_probs[label] = np.exp(logprobs[prefix])

    content = json.loads(response.choices[0].message.content)
    return content["classification"], label_probs


if __name__ == "__main__":
    client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-xxx")

    label, label_prob = classify(
        client=client,
        model="gpt-4",
        labels=["proponent budowy", "neutralny", "przeciwnik budowy"],
        text="Nikt mi nie powie ze czarne jest czarne a biale jest biale!",
    )
    print(label)
    print(label_prob)
