import os
import json
import uuid
import spacy
from tqdm import tqdm

from converter import Converter, write_ccl

CCL_OUTPATH = "ccls"

nlp = spacy.load("pl_nask")


def process_speech(speech):
    par_texts = [str(par) for par in speech.pars]
    par_docs = list(nlp.pipe(par_texts))
    for doc in par_docs:
        doc.spans["pars"] = [spacy.tokens.Span(doc, 0, len(doc))]
    merged = spacy.tokens.Doc.from_docs(par_docs)
    speech_span = spacy.tokens.Span(merged, 0, len(merged))
    speech_span.label_ = speech.speaker
    merged.spans["speeches"] = [speech_span]
    return merged


def process_doc(doc):
    speeches = doc.pop("speeches")
    metadata = {k:v for k,v in doc.items()}
    processed_speeches = []
    for speech in tqdm(speeches[:10]):
        pars = speech["pars"]
        if pars:
            #filtering out empty speeches
            par_docs = list(nlp.pipe(pars))
            for par_doc in par_docs:
                par_span = spacy.tokens.Span(par_doc, 0, len(par_doc))
                par_doc.spans["pars"] = [par_span]

            speech_doc = spacy.tokens.Doc.from_docs(par_docs)
            speaker = speech["speaker"]
            speech_span = spacy.tokens.Span(speech_doc, 0, len(speech_doc))
            speech_span.label_ = speaker
            speech_doc.spans["speeches"] = [speech_span]
            processed_speeches.append(speech_doc)
    transcript_doc = spacy.tokens.Doc.from_docs(processed_speeches)
    transcript_doc.user_data["metadata"] = metadata
    return transcript_doc


def main():
    with open("transcripts.json") as f:
        transcripts = json.load(f)

    out_data = []

    for doc in transcripts:
        processed_doc = process_doc(doc)
        ccl = Converter.ccl_mapping([processed_doc])
        doc_id = str(uuid.uuid4())
        processed_datapoint = {"id": doc_id,
                               "metadata": processed_doc.user_data["metadata"],
                               }
        out_data.append(processed_datapoint)
        ccl_path = os.path.join(CCL_OUTPATH, doc_id + ".xml")
        write_ccl(ccl, ccl_path)

    with open("processed_data.json", "w") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    main()
