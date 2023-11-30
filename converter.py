import itertools
from typing import (
    List,
    Iterator
)

import lxml.etree as et

from uuid import uuid4
from dataclasses import dataclass
from spacy.tokens.doc import Doc
from spacy.tokens.token import Token
from spacy.tokens.span import Span

from io import StringIO
from pathlib import Path
from typing import Tuple, Dict

from lxml import etree as et


# noinspection PyProtectedMember
def get_ccl_chunks(ccl: et._ElementTree, el_type: str = 'chunkList') -> et._Element:
    chunk_list = ccl.xpath(f'/cesAna/{el_type}')
    chunk_list = chunk_list[0] if chunk_list else None
    return chunk_list


# noinspection PyProtectedMember
def write_ccl(ccl: et._ElementTree, out_path: Path):
    ccl.write(str(out_path), encoding='utf-8', pretty_print=True, xml_declaration=True)


def read_ccl(in_path: Path):
    return et.parse(str(in_path), et.XMLParser(remove_blank_text=True))


# noinspection PyProtectedMember
def gen_ccl_structure() -> Tuple[et._ElementTree, et._Element]:
    schema = """
    <!DOCTYPE chunkList SYSTEM "ccl.dtd">
    <cesAna>
    <chunkList>
    </chunkList>
    </cesAna>
    """
    ccl = et.parse(StringIO(schema))

    return ccl, ccl.getroot()[0]


# noinspection PyProtectedMember
def add_element(where: et._Element, tag: str, text: str = None, attributes: Dict = None):
    el = et.SubElement(where, tag)
    el.text = text
    if attributes:
        for k, v in attributes.items():
            el.set(k, v)
    return el

PROPS_NAMES = {
    "number[psor]": "number.psor",
    "gender[psor]": "gender.psor",
    "person[psor]": "person.psor",
    "number[psee]": "number.psee",
    "animacy[gram]": "animacy.gram",
    "number[psed]": "number.psed",
}

@dataclass
class AnnotationsIndices:
    annotations: int = 0
    ref_token: int = 0


# noinspection PyProtectedMember
def add_sentence_ids(ccl: et._ElementTree) -> et._ElementTree:
    simple_doc_id = uuid4()
    sentence_num = 0

    for chunk in get_ccl_chunks(ccl):
        for sentence in chunk:
            add_element(sentence, 'sentence_id', f"{simple_doc_id}_{sentence_num}")
            # add sentence_id for each token
            for tok in sentence.iterfind('tok'):
                add_element(tok, 'sentence_id', f"{simple_doc_id}_{sentence_num}")
            sentence_num += 1

    return ccl





# noinspection PyPep8Naming,PyProtectedMember
class Converter():
    props_names = PROPS_NAMES

    @classmethod
    def get_paragraphs(cls, doc: Doc, speech: Span) -> Iterator[Span]:
        speech_start, speech_end = speech.start, speech.end
        doc_paragraphs = doc.spans["pars"]
        speech_paragraphs = [par for par in doc_paragraphs if par.start >= speech_start
                                                              and par.end <= speech_end]
        return speech_paragraphs

    @classmethod
    def get_sentences(cls, par: Span) -> Iterator[Span]:
        return par.sents

    @classmethod
    def get_speeches(cls, doc: Doc) -> Iterator[Span]:
        speeches = doc.spans["speeches"]
        return speeches

    @classmethod
    def get_tokens(cls, sent: Span) -> List[Token]:
        yield from sent

    @classmethod
    def tag_mapping(cls, tag_name):
        return cls.props_names.get(tag_name, tag_name)

    @classmethod
    def has_trailing_space(cls, tok):
        if tok.whitespace_ == '':
            return False
        else:
            return True

    @classmethod
    def ann_element(
            cls,
            annotations: et._Element,
            tag: str,
            span_ids: List[int],
            ann_type: str = 'ne',
            curr_ann_tok_id: AnnotationsIndices = 0
    ):
        ann_el = add_element(
            annotations,
            'ann',
            attributes={'t': ann_type, 'st': tag}
        )
        add_element(ann_el, 'ne.len', str(len(span_ids)))
        for ind, _ in enumerate(span_ids):
            add_element(
                ann_el,
                'wref',
                attributes={'tid': str(curr_ann_tok_id.annotations)}
            )
            curr_ann_tok_id.annotations += 1

    @classmethod
    def token_mapping(cls, tok: Token,  curr_ann_tok_id: AnnotationsIndices = None) -> et._Element:
        mapping_dict = cls.token_dict(tok)
        token_elements = dict()
        ccl_token = et.Element('tok')

        for name, value in mapping_dict.items():
            token_elements[name] = add_element(ccl_token, name, value)

        morph = token_elements['morph']
        for prop, val in tok.morph.to_dict().items():
            prop = cls.tag_mapping(prop.lower())
            add_element(morph, prop, val.lower())

        cls.add_ner_reference(tok, ccl_token, curr_ann_tok_id)

        return ccl_token

    @classmethod
    def ner_annotations(
            cls,
            docs: Iterator[Doc],
            ccl: et._Element,
            curr_ann_tok_id: AnnotationsIndices = 0
    ):
        annotations = add_element(ccl, 'annotations')

        for doc in docs:
            for ent in doc.ents:
                tag = doc[ent.start].ent_type_
                span_ids = [word.i for word in ent]
                cls.ann_element(annotations, tag, span_ids, curr_ann_tok_id=curr_ann_tok_id)

    @classmethod
    def add_ner_reference(
            cls,
            tok: Token,
            ccl_token: et._Element,
            curr_ann_tok_id: AnnotationsIndices = None
    ) -> None:
        ner_tag = tok.ent_type_
        mark_type = tok.ent_iob_

        if ner_tag:
            ner_el = add_element(ccl_token, 'ner', ner_tag)
            ner_el.set('mark', mark_type)

            # add token index for reference
            ccl_token.set('id', str(curr_ann_tok_id.ref_token))
            curr_ann_tok_id.ref_token += 1

    @classmethod
    def token_dict(cls, tok, tokens=None):
        distance = tok.i - tok.head.i
        tok_map = {
            'orth': tok.orth_,
            'upos': tok.pos_,
            'xpos': tok.tag_,
            'lemma': tok.lemma_,
            'morph': '',
            'deprel': tok.dep_,
            'head.lemma': tok.head.lemma_,
            'head.distance': str(abs(distance)),
            'head.position': 'left' if distance >= 0 else 'right',
            'head.upos': tok.head.pos_
        }

        tok_map.update(
            {
                f"head.{cls.tag_mapping(prop.lower())}": val.lower()
                for prop, val in tok.head.morph.to_dict().items()
            }
        )

        return tok_map

    @classmethod
    def ccl_mapping(cls, docs: Iterator[Doc]) -> et._ElementTree:
        ccl, ccl_subtree = gen_ccl_structure()
        curr_ann_tok_id = AnnotationsIndices()  # integrate indices between paragraph
        docs_ann, docs_tokens = itertools.tee(docs, 2)
        cls.ner_annotations(docs_ann, ccl.getroot(), curr_ann_tok_id)

        for doc in docs:
            is_sentencized = doc.has_annotation("SENT_START")
            for speech in cls.get_speeches(doc):
                ccl_speech = add_element(ccl_subtree, 'speech')
                author = speech.label_
                ccl_speech.set('t', 'speaker')
                ccl_speech.set('st', author)
                for paragraph in cls.get_paragraphs(doc, speech):
                    ccl_paragraph = add_element(ccl_speech, 'chunk')
                    ccl_paragraph.set('type', 'p')
                    if is_sentencized:
                        sentences = cls.get_sentences(paragraph)
                    else:
                        sentences = [paragraph]
                    for sent in sentences:
                        ccl_sentence = add_element(ccl_paragraph, 'sentence')
                        nps = False  # no preceding space
                        for tok in cls.get_tokens(sent):
                            ccl_token = cls.token_mapping(tok, curr_ann_tok_id)
                            if nps:
                                add_element(ccl_token, 'nps', 'true')
                            ccl_sentence.append(ccl_token)

                            if not cls.has_trailing_space(tok):
                                nps = True
                                add_element(ccl_sentence, 'ns')
                            else:
                                nps = False

        ccl = add_sentence_ids(ccl)
        return ccl
