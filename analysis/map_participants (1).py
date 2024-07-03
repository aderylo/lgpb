
import json
from dataclasses import dataclass
from typing import List
from dataclasses import field
import re

@dataclass
class Participant:
    id: str
    side: str
    spoken_text: list[str]

    def __dict__(self):
        return {"id" : self.id, "side" : self.side, "spoken_pars": self.spoken_text}
    

@dataclass
class Speech:
    speaker: str
    pars: List[str] = field(default_factory=list)

@dataclass
class Sitting:
    id: str
    participants: list[Participant]
    speeches: list[Speech]

@dataclass
class Transcript:
    committee: str
    title: str
    sitting_date: (
        str  # A date would be better, but some transcripts are from multiple dates.
    )
    chairman: str
    speeches: list[Speech] 

    def __str__(self):
        d = dict(self.__dict__)
        del d["speeches"]
        return str(d)

def read_participants(file_path: str) -> dict[Participant]:
    participants = {}
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    for participant_name in set(json_data.values()):
        participants[participant_name] = Participant(participant_name, "", [])
    return participants

def parse_document_with_sides(filename:str):
    participants = {"o":[], "r":[]}
    with open(filename, 'r') as f:
        for line in f.readlines():
            if bool(re.match(r".*opozycyjno-solidarnościowa.*", line)):
                names = re.findall(r"\S+\s\S+,|\S+\s\S+ \(przew.\),|\S+\s\S+\-\S+,", line)
                names = [name[:-1] if  not re.match(".*przew.*", name)  else name[:-10]  for name in names ]
                participants["o"].extend(names)
            elif bool(re.match(r".*koalicyjno-rządowa.*", line)):
                names = re.findall(r"\S+\s\S+,|\S+\s\S+ \(przew.\),|\S+\s\S+\-\S+,", line)
                
                names = [name[:-1] if  not re.match(".*przew.*", name)  else name[:-10]  for name in names ]
                participants["r"].extend(names)
    participants["o"] = list(set(participants["o"]))
    participants["r"] = list(set(participants["r"]))
    return participants

def load_transcripts(filename: str) -> list[Transcript]:
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




def list_particapnts_ids(transcripts: List[Transcript], filename, save_to_file = True) -> list[str]:
    participants = set()
    for transcript in transcripts:
        for speech in transcript.speeches:
            participants.add(speech.speaker)
    with open(filename, "w") as f:
        json.dump({p:"" for p in participants}, f, ensure_ascii=False, indent=2)

    return list(participants)

def map_participants_to_unique_key(json_with_all_participants: str, json_with_mapping: str) -> None:
    with open(json_with_all_participants, "r") as f:
        all_participants = json.load(f)
    with open(json_with_mapping, "r") as f: 
        mapping = json.load(f)

    with open("verified_mapping.json", "r") as f:
        verified_mapping = json.load(f)

    result ={}
    for participant in all_participants:
        if participant=="":
            continue 
        
        possiblities = [] 
        to_continue = False
        for key in mapping.keys():
            
            if key == participant:
                result[participant] = key
                to_continue = True
                break 
        if to_continue:
            continue

        count = 0
        
        for key in mapping.keys():
            if re.match(f"{participant.split()[-1]}", key.split()[-1]):
                count += 1
                possiblities.append(key)
            if any([part.replace('\\',"")==key.split()[-1] for part in participant.split()]):
                count += 1
                if key not in possiblities:
                    possiblities.append(key)
        if count == 1: 
            result[participant] = possiblities[0]
            continue
        loop_break = False
        if len(possiblities) == 1:
            result[participant] = possiblities[0]
            continue
        for p in possiblities:
            if p in verified_mapping.keys():
                result[participant] = p
                loop_break = True
                break 
        if loop_break:
            continue
        if possiblities ==[]:
            print("n",participant)
        else:
            print("m",participant, possiblities)
            
    for key in verified_mapping.keys():
        if key not in result.keys():
            result[key] = verified_mapping[key]
    with open("all_participants_mapping.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
            
def from_all_to_mapped():
    with open("all_participants_mapping.json", "r") as f:
        mapping = json.load(f)       
    with open("all_participants.json", "r") as fi:    
        all_participants = json.load(fi)
    for key in all_participants.keys():
        if key not in mapping.keys():
            mapping[key] = key
    with open("all_participants_mapping.json", "w") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

def map_speeches_to_participants(participants: dict[str:Participant], transcripts: List[Transcript], mapping_json_filname:str) -> None:
    with open(mapping_json_filname, "r") as f:
        dict_names = json.load(f)
    
    
    other: dict[str:Participant] = {}
    for transcript in transcripts:
        for speech in transcript.speeches:
            
            if speech.speaker in participants.keys():
                participants[speech.speaker].spoken_text.extend(speech.pars)

            elif speech.speaker in dict_names.keys():
                if dict_names[speech.speaker] in participants.keys():
                    participants[dict_names[speech.speaker]].spoken_text.extend(speech.pars)
                else:
                    participants[dict_names[speech.speaker]] = Participant(dict_names[speech.speaker], '', spoken_text=speech.pars)

            elif speech.speaker in other.keys():
                other[speech.speaker].spoken_text.extend(speech.pars)
                
            else:
                other[speech.speaker] = Participant(speech.speaker, '', spoken_text=speech.pars)
    participants.update(other)
    return  participants
             
def give_sides_to_participants(participants: dict[str:Participant], filename) -> None:   
    with open(filename) as f:
        data = json.load(f)
    for participant in participants.keys():
        if participant in data.keys():
            participants[participant].side = data[participant]
        elif participant in ["METACOMMENT"]:
            participants[participant].side = "m"
        elif participant in [""]:
            participants[participant].side = "i"
        elif participant in ["Przewodniczący"]:
            participants[participant].side = "p"
        else:
            participants[participant].side = "u"          
                    
def read_participants_from_json(file_path: str) -> List[Participant]:
    with open(file_path, "r") as file:
        data = json.load(file)
    participants = []
    for participant in data:
        spoken_text = participant.pop("spoken_pars")
        participants.append(Participant(**{k: v for k, v in participant.items() if k != "spoken_pars"}, spoken_text=spoken_text))

    return participants


def split_participants(participants: list[Participant]) -> tuple[list[Participant], list[Participant]]:
    return [participant for participant in participants if participant.side == "o"], [participant for participant in participants if participant.side == "r"]
    

def calc_stats(participants: List[Participant]) -> dict[str: int or str]:
    participants.__iter__()



def main():
    """
    participants = read_participants("participants.txt")
    print(participants)
    transcripts = load_transcripts("transcripts_updated3.json")
    names = get_dict_names("verified_mapping.json")
   

    participants_matched = map_speeches_to_participants(participants, transcripts, names)
    for participant in participants_matched.values():
        if participant.side == 'u':
            print(participant.id, participant.side)
    
    
   
    """
    transcripts = load_transcripts("transcripts_updated3.json")
    participants = read_participants("all_participants_mapping.json")
    participants = map_speeches_to_participants(participants, transcripts, "all_participants_mapping.json")
    give_sides_to_participants(participants, "mapping_side.json")
    """
    o_participants, r_participants = split_participants(participants.values())
    with open("o_speakers.json", "w") as f:
        json.dump([p.__dict__() for p in o_participants], f, ensure_ascii=False, indent=2)
    with open("r_speakers.json", "w") as f:
        json.dump([p.__dict__() for p in r_participants], f, ensure_ascii=False, indent=2)
    print(len(o_participants), len(r_participants))
    print(len(participants.values()))
    """
    nspeeches = {}
    for participant in participants.values():
        if participant.side in nspeeches.keys():
            nspeeches[participant.side] += len(participant.spoken_text)
        else:
            nspeeches[participant.side] = len(participant.spoken_text)
       
    print(nspeeches)
if __name__ == "__main__":
    main()        