import os
import pandas
import re
import json
from collections import Counter
from dataclasses import dataclass, asdict
from lxml import html
from typing import List
from tqdm import tqdm


name_cleaner = re.compile(r"^(Kol\.|Obywatel(ka)?\b|Ob\.|P\.|Pani?\b|Red\.|Dyr\.|Dyrektor\b|Prezes\b|Mec\.|Mecenas\b|Prokurator\b|Inż\.|Mgr\b|Dr\b|Doc\.|Prof\.|Generał\b|Gen\.|Poseł\b|Min\.|Minister\b|Premier\b|Wicepremier\b)", flags=re.IGNORECASE)
chairman_switch = re.compile(r"(?:(przewodnictwo|obrad) (ob|prz)ejmuje)|(?:przewodniczy)", flags=re.IGNORECASE)


METACOMMENT = "METACOMMENT"

@dataclass
class Transcript():
    committee: str
    title: str
    sitting_date: str #a date would be better but some transcripts are from multiple dates
    chairman: str
    speeches: List[str]

@dataclass
class Speech(): #includes also metacomments
    speaker: str
    #text: str 
    pars: List[str]


#TODO how to handle interruptions? do we divide the interrupted speech into two?
#Handle multiple chairmen
#handle "przewodnicząca"

with open("verified_mapping.json") as f:
    name_mapping = json.load(f)

def tag_is_meta(tag):
    children = tag.getchildren()
    is_meta = tag.text is None and len(children) == 1 and children[0].tag == "em"
    return is_meta


def tag_is_comment(tag):
    content = tag.text_content()
    if content:
        return content[0] == "/" and content[-1] == "/"
    return False


def get_meta_content(tag):
    emphasis = tag.find("em")
    return emphasis.text


def name_to_person(name):
    #re.IGNORECASE
    name = name.replace(":", "")
    name = name.strip()
    name = name_cleaner.sub("", name).strip()
    name = name_cleaner.sub("", name).strip()#double application, sometimes is necessary
    if not name.startswith("Przewodniczący - ") and " - " in name:
        name = name.split(" - ", 1)[0]
    name = name.strip(". ")
    if name in name_mapping:
        name = name_mapping[name]
    return name


def parse_header(header_pars):
    header_texts = [hp.text_content() for hp in header_pars]
    metadata = {}
    #metadata["filename"] = filename
    metadata["corpus_name"] = header_texts[0]
    metadata["committee_name"] = header_texts[1].split("=")[1].strip(" ")
    metadata["title"] = header_texts[2].split("=")[1].strip(" ")
    metadata["date"] = header_texts[3].split("=")[1].strip(" .")
    metadata["signature"] = header_texts[4]
    metadata["inv"] = header_texts[5]
    main_chair = header_texts[8]
    main_chair = main_chair.replace("Obradom przewodniczyli", "").replace("Obradom przewodniczy", "").strip(r"./ ")
    main_chair = name_to_person(main_chair)
    metadata["main_chair"] = main_chair
    transcript = Transcript(committee=metadata["committee_name"],
                            title=metadata["title"],
                            sitting_date=metadata["date"],
                            chairman=metadata["main_chair"],
                            speeches=[]
                            )
    return metadata, transcript


HTML_DIR = "htmls"

def main():
    html_files = [fil for fil in os.listdir(HTML_DIR) if fil.endswith(".html")]
    doc_metadatas = []
    transcripts = []
    for filename in tqdm(html_files):
        filepath = os.path.join(HTML_DIR, filename)
        with open(filepath) as f:
            root = html.parse(f).getroot()
        body = root.find("body")
        all_pars = body.getchildren()
        header_pars = all_pars[:9]
        metadata, transcript = parse_header(header_pars)
        doc_metadatas.append(metadata)
        content_pars = all_pars[9:]
        current_chairman = metadata["main_chair"]
        first_speaker_name = get_meta_content(content_pars[0])
        current_speaker = name_to_person(first_speaker_name)
        current_speech_pars = []
        for child in content_pars[1:]:
            child_content = child.text_content()
            if tag_is_meta(child):
                #speaker change
                #add old speech
                speech = Speech(current_speaker, current_speech_pars)
                transcript.speeches.append(speech)

                #get new speech
                name = get_meta_content(child)
                current_speaker = name_to_person(name)
                current_speech_pars = []
            elif tag_is_comment(child):
                #metacomment/interruption
                speech = Speech(current_speaker, current_speech_pars)
                transcript.speeches.append(speech)
                comment_speech = Speech(METACOMMENT, [child_content])
                transcript.speeches.append(comment_speech)
                current_speech_pars = []
                if chairman_switch.search(child_content):
                    split_string = chairman_switch.sub("<SP>", child_content).split("<SP>") # hack
                    current_chairman = name_to_person(split_string[1].strip(r" ./"))
            else:
                if child_content:
                    current_speech_pars.append(child.text_content())
        speech = Speech(current_speaker, current_speech_pars)
        transcript.speeches.append(speech)
        transcripts.append(transcript)

    metadata_df = pandas.DataFrame(doc_metadatas)
    metadata_df.to_csv("metadata.csv")

    dictionarized_transcripts = [asdict(transcript) for transcript in transcripts]
    with open("transcripts.json", "w") as f:
        json.dump(dictionarized_transcripts, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    main()


#TODO kierownictwo przekazuję, przedwodnictwo obejmuje itd.
# wygenerować doci spacy
# otagować doci spacy mowami
# zapisać pliki
# skopiować pliki do kontenera
# przekonwertować pliki w ccle
# zaindeksować ccle
#TODO add metacomments
#TODO merging docs and annotating them with metadata
#TODO po przerwie as speaker name
#TODO look for empty speeches
