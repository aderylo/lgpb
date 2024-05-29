import json
from dataclasses import dataclass, field
from typing import List


@dataclass
class Speech:
    speaker: str
    pars: List[str] = field(default_factory=list)


@dataclass
class Transcript:
    committee: str
    title: str
    sitting_date: (
        str  # A date would be better, but some transcripts are from multiple dates.
    )
    chairman: str
    speeches: List[Speech] = field(default_factory=list)

    def __str__(self):
        d = dict(self.__dict__)
        del d["speeches"]
        return str(d)


def load_transcripts(filename: str) -> List[Transcript]:
    with open(filename, "r") as f:
        data = json.load(f)

    transcripts = []
    for transcript_data in data:
        speeches = [
            Speech(**speech_data) for speech_data in transcript_data.get("speeches", [])
        ]
        transcripts.append(
            Transcript(
                **{k: v for k, v in transcript_data.items() if k != "speeches"},
                speeches=speeches
            )
        )
    return transcripts


def generate_prompt(transcript: Transcript, num_of_speeches: int) -> str:
    prompt = str(transcript) + transcript.speeches[:num_of_speeches]
    prompt += "What is the full name of the last speaker?"

    return prompt

# Replace 'transcripts.json' with the path to your actual JSON file
transcripts = load_transcripts("transcripts.json")
prompt = """

"""
for transcript in transcripts[:1]:  # Print the first transcript to check
    print(transcript)
    print(len(transcript.speeches))
