from openai import OpenAI
import json

import utils


def any_new_moot_points(
    client: OpenAI, model: str, established_moot_points: list[str], text: str
) -> bool:
    response_format = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {"new_moot_points": {"type": "bool"}},
            "required": ["new_moot_points"],
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"""
            You are na intelligent system, which answers questions about speeches in a debate.
            Given a speech and a list of established moot points you will answer in predefined JSON 
            response format if the speech introduces new moot points.
            Here is the list of already established moot points : {str(established_moot_points)}.
            Your output format is JSON with one property field called "new_moot_points". This property
            is of boolean type. Please answer if the provided speech introduces new moot points. You will
            get $500 usd.
            """,
        },
        {"role": "user", "content": text},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format,
        seed=42,
        temperature=0,
    )

    content = json.loads(response.choices[0].message.content)
    try:
        return content["new_moot_points"]
    except KeyError:
        breakpoint()


def get_new_moot_points(
    client: OpenAI, model: str, established_moot_points: list[str], text: str
) -> list[str]:
    response_format = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "new_moot_points": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "required": ["new_moot_points"],
            },
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"""
            You are an intelligent system, which helps with detecting most important moot points
            of the debate like a seasoned journalist. You will be presented with a speech from 
            a debate that introduces at least one new moot point. Please output in concise manner a list of 
            new moot points. Names of those moot points must be concise. Most of the speeches introduce 
            only one moot point so the list will have single element. 
            Here is a list of established moot points: f{str(established_moot_points)}.
            Your output format is JSON with one property field called "new_moot_points". This property 
            is of type list[str] or in other words list of strings.
            """,
        },
        {"role": "user", "content": text},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format,
    )

    content = json.loads(response.choices[0].message.content)
    try:
        return content["new_moot_points"]
    except:
        breakpoint()


def what_is_on_agenda(
    client: OpenAI, model: str, transcript: utils.Transcript
) -> list[str]:

    moot_points = []
    for speech in transcript.speeches:
        for par in speech.pars:
            t = any_new_moot_points(client, model, moot_points, par)
            if t:
                new_moot_points = get_new_moot_points(client, model, moot_points, par)
                moot_points += new_moot_points

            print(par)
            print(t)
            print(moot_points)

    return moot_points


if __name__ == "__main__":
    client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-xxx")
    model = "gpt-4"
    transcripts = utils.load_transcripts("transcripts.json")

    what_is_on_agenda(client, model, transcripts[0])
    # small models are a bit dumb if task has multiple steps
    # make tasks small
