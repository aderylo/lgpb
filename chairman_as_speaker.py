import json
import re

def load_transcripts() -> list: 
    with open("transcripts.json") as f:
        transcripts = json.load(f)
        print(type(transcripts))
        return transcripts
    
def update_chairman(transcripts: list) -> list:
    """
    Updates "speaker" elements which are marked as chairman within each transcript. Changes case "speaker: Przewodniczacy" 
    into "speaker: Name, Surname" based on regex, if possible. 

    Missing names:
    Line 41240 - cannot obtain the right chairman / missing name
    Missing chairman names in 2 transcripts. Check "mapped_committee_chairmans.json" for more insight.
    """ 
    score = 0
    score_speaker=0
    for meetings in transcripts:
        current_chairman = meetings["chairman"]
        for speech in meetings["speeches"]:
            if "Przewodnicz" in speech["speaker"]:
                score_speaker += 1
                speech["speaker"] = current_chairman
            for par in speech["pars"]:
                pattern_Findeisen = r'\b[Pp]rzewodnictwo obrad\b.*?\b(Findeisen)\b' # Catchesz Findeisen case
                pattern = r'\b[Pp]rzewodnictwo obrad\b.*?\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*)\b.*?\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*)\b' # Catches "przewodnictwo obrad"
                pattern2 = r'\b[Oo]bradom przewodniczy\b.*?\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*)\b.*?\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*)\b' # Catches "obradom przewodniczy"
                match = re.search(pattern, par)
                match2 = re.search(pattern2, par)
                match_Findeisen = re.search(pattern_Findeisen, par)
                if match:
                    score += 1
                    first_name = match.group(1)
                    last_name = match.group(2)
                    current_chairman = first_name + " " + last_name
                    print(f"Comment{par}, current chairman {current_chairman}")
                elif match_Findeisen:
                    score += 1
                    first_name = match_Findeisen.group(1)
                    current_chairman = first_name
                    print(f"Comment{par}, current chairman {current_chairman}")
                elif match2:
                    score += 1
                    first_name = match2.group(1)
                    last_name = match2.group(2)
                    current_chairman = first_name + " " + last_name
                    print(f"Comment{par}, current chairman {current_chairman}")
    
    print(score)
    return transcripts
                    
                
if __name__ == "__main__":
    t = load_transcripts()
    t_updated = update_chairman(t)
    with open("transcripts_updated3.json", "w") as f:
        json.dump(t_updated, f, ensure_ascii=False, indent=2)
    
