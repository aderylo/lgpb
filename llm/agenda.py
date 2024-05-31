from openai import OpenAI
import json
from dataclasses import asdict
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


def get_referenced_moot_points(
    client: OpenAI, model: str, moot_points: list[str], text: str
) -> list[str]:
    response_format = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "referenced_moot_points": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "required": ["referenced_moot_points"],
            },
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"""
            You are an intelligent system that helps with detecting referenced moot points 
            in a debate text, similar to a seasoned journalist. You will be presented with 
            a speech from a debate that references one or more established moot points.
            Please output a concise list of referenced moot points. The names of these moot 
            points must be concise and match exactly with the provided list. If no moot
            points are referenced then output an empty list.
            Here is the list of established moot points: {str(moot_points)}.
            Your output format is JSON with one property field called "referenced_moot_points". 
            This property is of type list[str] or, in other words, a list of strings.
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
        return content["referenced_moot_points"]
    except:
        breakpoint()
        return []


def classify_stance_towards_moot_point(
    client: OpenAI, model: str, stances: list[str], moot_point: str, text: str
) -> str:
    response_format = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "stance": {
                    "type": "string",
                },
                "required": ["stance"],
            },
        },
    }

    messages = [
        {
            "role": "system",
            "content": f"""
            You are an intelligent system that helps classify the stance towards a specific moot point in a debate text. 
            You will be presented with a speech from a debate and a specific moot point.
            Please classify the stance towards the moot point as one of the following: {str(stances)}.
            The names of these stances must be concise and exactly match the provided list.
            Here is the specific moot point: "{moot_point}".
            Your output format is JSON with one property field called "stance". 
            This property is a string that represents the stance towards the moot point.
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
        return content["stance"]
    except:
        breakpoint()
        return ""


def annotate_transcript(
    client: OpenAI, model: str, transcript: utils.Transcript
) -> list[str]:

    moot_points = []
    for speech in transcript.speeches:

        annotations = []
        for par in speech.pars:
            t = any_new_moot_points(client, model, moot_points, par)
            if t:
                new_moot_points = get_new_moot_points(client, model, moot_points, par)
                moot_points += new_moot_points

            ref_mp = get_referenced_moot_points(client, model, moot_points, par)
            stances = {
                mp: classify_stance_towards_moot_point(
                    client, model, ["negative", "neutral", "positive"], mp, par
                )
                for mp in ref_mp
            }
            print(par)
            print(t)
            print("all moot points: ", moot_points)
            print("refed moot points : ", stances)

            annotations.append(
                utils.Annotation(
                    introduces_new_moot_point=t,
                    moot_points_so_far=moot_points,
                    stances_towards_moot_points=stances,
                )
            )

        speech.annotations = annotations

    return transcript


if __name__ == "__main__":
    client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-xxx")
    model = "gpt-4"
    transcripts = utils.load_transcripts("transcripts.json")

    annotated = annotate_transcript(client, model, transcripts[0])

    with open("transcript0_annotated.json", "w") as f:
        json.dump(asdict(annotated), f, ensure_ascii=False, indent=2)

    # small models are a bit dumb if task has multiple steps
    # make tasks small
