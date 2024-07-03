from nltk.text import Text
from map_participants import Participant, Transcript, Speech, load_transcripts, read_participants_from_json
import json 
import plotly.graph_objects as go
from collections import OrderedDict, Counter
import spacy
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
from collocater import collocater
from spacy import displacy
from llama_cpp import Llama

def get_spacy_pipeline():

    nlp = spacy.load("pl_core_news_md")
    lemmatizer = nlp.get_pipe("lemmatizer")
    nlp.max_length = 1000000000

    return nlp, lemmatizer


def get_unique_commitees(transcripts: list[Transcript]):
    commitee_nspeaches = {}
    for transcript in transcripts:
        if transcript.committee in commitee_nspeaches.keys():
            commitee_nspeaches[transcript.committee] += 1
        else:
            commitee_nspeaches[transcript.committee] = 1
    return commitee_nspeaches

def get_dict_names(json_file_path:str)->dict[str, str]:
    with open(json_file_path, 'r') as j:
        names = json.loads(j.read())
    return names

def get_speaches_per_participant( transcripts: list[Transcript]) -> None:
    participants = {}
    names = get_dict_names("verified_mapping.json")
    with open("participants.txt", 'r') as file:
        for line in file.readlines():
            participants[" ".join(line.split()[:-1])] = [0,line.split()[-1]]
   
    for transcript in transcripts:
        for speech in transcript.speeches:
                if speech.speaker in participants.keys():
                    participants[speech.speaker][0] += 1
                else:
                    if speech.speaker in names.keys():
                        speaker = names[speech.speaker]
                        if speaker in participants.keys():
                            participants[speaker][0] += 1
                        else:
                            participants[names[speech.speaker]] = [1, 'u']
                    else:
                        participants[speech.speaker] = [1, 'u']
    return participants   
        
def plot_speaches_per_participant(participants: dict[str, list[int, str]]) -> None:
    participants = get_speaches_per_participant(transcripts)
    participants = sorted(participants.items(), key=lambda x: x[1][0], reverse=True)
    participants = OrderedDict(participants)
    for participant in participants:
        if participants[participant][1] == 'u':
            print(participant, participants[participant][0])
   
    encode_list = ['Nie Dotyczy', 'Rządowa' , 'Opozycyjna', 'Nieznana', 'Kościół']
    encode = lambda x: encode_list[['u', 'r', 'o', 'i','k'].index(x.lower())] if x.lower() in ['u', 'r', 'o', 'i','k'] else x

    fig = go.Figure(data=[go.Table(
    header=dict(values=['Mówca', 'Liczba wypowiedzi', 'Strona'],
                line_color='darkslategray',
                fill_color='lightskyblue',
                align='left'),
    cells=dict(values=[list(participants.keys()), # 1st column
                       [el[0] for el in participants.values()], # 2nd column
                       [encode(el[1])  for el in participants.values()]], # 3rd column
               line_color='darkslategray',
               fill_color='lightcyan',
               align='left'))
])

    fig.update_layout(width=700, height=1000)
    fig.show()
    print(participants)

def plot_speaches_per_commitee(data: OrderedDict[dict]) -> None:
    fig = go.Figure(data=[go.Table(
    header=dict(values=['Komitet', 'Liczba posiedzeń'],
                line_color='darkslategray',
                fill_color='lightskyblue',
                align='left'),
    cells=dict(values=[list(data.keys()), # 1st column
                       [el for el in data.values()]], # 2nd column
                       
               line_color='darkslategray',
               fill_color='lightcyan',
               align='left'))
])

    fig.update_layout(width=800, height=1000)
    fig.show()

def parse_with_pipe(nlp ,title, speakers: list[Participant],  exlude_stopwords =True ):
    i = 0
    lst = []
    for participant in speakers: 
        for par in participant.spoken_text:
            
            #print(par)
                #print(pars)
            
            tokens = nlp(par)
            #print(tokens)
            lst.append(tokens)
            i+=1
            if i>=5:
                print("writing to file")
                with open(title, 'a') as file:
                    for tokens in lst:
                            file.write(str([[token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
            token.shape_, token.is_alpha, token.is_stop] for token in tokens])+'\n')
                i = 0
                lst = []
    

    
def calc_most_frequent_words(file, types: list[str]) -> dict:
    data = []
    with open(file, 'r') as f:
        for line in f.readlines():
            data.append(eval(line))
    data = [el for sublist in data for el in sublist]
    words = [token[1]  for token in data if token[2] in types]
            

    
    
    # five most common tokens
    word_freq = Counter(words)
    common_words = word_freq.most_common(2000)
    return common_words
   
def keyword_clustering(keywords) -> None:

# Load spaCy model
    nlp = spacy.load('pl_core_news_md')



    # Extract keywords from DataFrame


    # Process keywords and obtain document vectors
    documents = list(nlp.pipe(keywords))
    document_vectors = [doc.vector for doc in documents]

    # Group keywords by similarity
    groups = {}
    for i, keyword in enumerate(keywords):
        cluster_found = False
        for cluster, cluster_keywords in groups.items():
            for key in cluster_keywords:
                similarity = nlp(keyword).similarity(nlp(key))
                if similarity > 0.8:
                    groups[cluster].append(keyword)
                    cluster_found = True
                    break
            if cluster_found:
                break

        if not cluster_found:
            groups[i] = [keyword]

    # Identify the pillar page keyword for each cluster
    pillar_keywords = []
    for cluster, keywords in groups.items():
        pillar_keyword = max(keywords, key=lambda x: nlp(x).similarity(nlp(x)))
        pillar_keywords.append(pillar_keyword)

    # Print the clusters along with pillar page keywords
    for cluster, keywords in groups.items():
        if cluster < len(pillar_keywords):
            pillar_keyword = pillar_keywords[cluster]
        else:
            pillar_keyword = "No pillar keyword found"
        print(f"Cluster {cluster}: {keywords} (Pillar Page: {pillar_keyword})")

    # Create a new DataFrame for the clusters and pillar page keywords
    cluster_df = pd.DataFrame({'Cluster': [f'Cluster {cluster}' for cluster in groups.keys()],
                            'Keywords': [', '.join(keywords) for keywords in groups.values()],
                            'Pillar Page': pillar_keywords})

    # Write the DataFrame to a new sheet in the same Excel file
    cluster_df.to_csv('R_clusters.csv')

def extract_text_with_keywords(file, keywords: list[str]) -> None:
    data = {k: [] for k in keywords}
    
    with open(file, 'r') as f:
            for line in f.readlines():
                line = eval(line)
                for token in line: 
                    if token[1] in keywords:
                        text = " ".join([t[0] for t in line])
                        data[token[1]].append(text)
                        break
     
    return data

def label_texts(data: dict[str, list[str]], nlp):
    key_data = {k:{ } for k in data.keys()}
    for key in data.keys():
        for text in data[key]:
            doc = nlp(text)
            for token in doc:
                if token.lemma_ == key:
                    if  token.dep_ not in key_data[key]:
                        key_data[key][token.dep_] = 1
                    else:
                        key_data[key][token.dep_] +=1
                    print(token.text, token.dep_, token.pos_, token.head.text, token.head.pos_,
                    [child for child in token.children])
    return key_data


def get_money_related_words() -> None:
    for doc in nlp.pipe(TEXTS):
        for token in doc:
            if token.ent_type_ == "MONEY":
                # We have an attribute and direct object, so check for subject
                if token.dep_ in ("attr", "dobj"):
                    subj = [w for w in token.head.lefts if w.dep_ == "nsubj"]
                    if subj:
                        print(subj[0], "-->", token)
                # We have a prepositional object with a preposition
                elif token.dep_ == "pobj" and token.head.dep_ == "prep":
                    print(token.head.head, "-->", token)
        
def main():  
    """                 
    transcripts = load_transcripts("transcripts_updated3.json")
    commitee_nspeaches = get_unique_commitees(transcripts)
    commitee_nspeaches = sorted(commitee_nspeaches.items(), key=lambda x: x[1], reverse=   True)
    commitee_nspeaches = OrderedDict(commitee_nspeaches)
    print(commitee_nspeaches)
    participants_o = read_participants_from_json("o_speakers.json")
    participants_r = read_participants_from_json("r_speakers.json")
    nlp, lemmatizer = get_spacy_pipeline()
    '''
    print("most_frequent_r: \n", calc_most_frequent_words(nlp, participants_r, 100))
    print("most_frequent_o : \n ",calc_most_frequent_words(nlp, participants_o, 100))
    '''
    parse_with_pipe(nlp, "r_words.txt", participants_r)
    parse_with_pipe(nlp, "o_words.txt", participants_o)
    r_mf_words = calc_most_frequent_words("r_words.txt")
    o_mf_words = calc_most_frequent_words("o_words.txt")
    print("R most frequent words: ", r_mf_words)
    print("O most frequent words: ", o_mf_words)
    """

    '''
    nlp = spacy.load("pl_core_news_md")
    doc1 = nlp("Proszę państwa, wydaje mi się, że popełniamy tutaj duży błąd, tutaj, w toku dyskusji i w rozumowaniu. Nie możemy zamazywać odpowiedzialności za skażenie środowiska na Śląsku i wszystko uważać, że da się załatwić we własnym gronie, na Śląsku, bez pomocy z zewnątrz, a niektóre wypowiedzi państwa po prostu bulwersują. Odnoszę wrażenie, że ma tu miejsce jakieś dziwne zamazywanie sytuacji, które później wychodzi ni stąd, ni zowąd przy „okrągłym stole”, przy naszym stoliku ekologicznym.")

    doc2 = nlp("Reprezentuję Polskę Zjednoczoną Partię Robotniczą. Ponieważ jest to czas, w którym wszyscy wykonujemy gwałtownych zmian także w sobie,")


    # Similarity of two documents
    print(doc1, "<->", doc2, doc1.similarity(doc2))
    # Similarity of tokens and spans
    french_fries = doc1
    burgers = doc2
    print(french_fries, "<->", burgers, french_fries.similarity(burgers))
    '''
    """
    with open("r_mf_words.json", 'r') as f:
        r_mf_words_n = json.load(f)
    with open("o_mf_words.json", 'r') as f: 
        o_mf_words_n = json.load(f)

  

    r_num_occurances =0
    for word in r_mf_words_n:
        r_num_occurances += word[1]
    o_num_occurances = 0    
    for word in o_mf_words_n:
        o_num_occurances += word[1]
    
    for i in range(len(r_mf_words_n)):
        for j in range(len(o_mf_words_n)):
            if r_mf_words_n[i][0] == o_mf_words_n[j][0] and i!=j:
                print(r_mf_words_n[i][0],f"r_word_index {i} ", r_mf_words_n[i][1]/r_num_occurances, o_mf_words_n[j][1]/o_num_occurances, f" o_word_index {j}")
    """       
    """
    words = {"prawo":[19,11], "gospodarka":[32,66], "cena":[39,60], "samorząd":[48,38], "reforma":[71, 49], "sąd":[73,33], "węgiel":[113,206]}
    w_freq_diff = {}
    for word in words.keys():
        for i in range(len(r_mf_words_n)):
            for j in range(len(o_mf_words_n)):
                if r_mf_words_n[i][0] == o_mf_words_n[j][0]  and i!=j and r_mf_words_n[i][0] == word:
                    w_freq_diff[word] = [(r_mf_words_n[i][1]/r_num_occurances)/ (o_mf_words_n[j][1]/o_num_occurances)]
    print(w_freq_diff)
    colors = ['tab:red' if v[0] > 1 else 'tab:green' for v in w_freq_diff.values()]
    plt.bar(list(w_freq_diff.keys()), list((v[0] for v in  w_freq_diff.values())), color = colors)
    plt.show()
    """
    """
    nlp = spacy.load("pl_core_news_md")
    r_side = (extract_text_with_keywords
        ( "r_words.txt", [ "samorząd", "węgiel"]))
    o_side = (extract_text_with_keywords
        ( "o_words.txt", [ "samorząd", "węgiel"]))
    
    key_r = label_texts(r_side, nlp)
    key_o = label_texts(o_side, nlp)
    print(key_r)
    print(key_o)
    """
    """
    key_r = {'samorząd': {'conj': 199, 'nmod': 380, 'nmod:arg': 334, 'nsubj': 355, 'obj': 155, 'ROOT': 17, 'obl:arg': 71, 'obl': 81, 'acl:relcl': 8, 'iobj': 42, 'obl:agent': 20, 'nsubj:pass': 11, 'dep': 6, 'ccomp': 8, 'inne': 17}, 'węgiel': {'conj': 60, 'obj': 239, 'nmod': 178, 'nmod:arg': 305, 'nsubj': 57,  'iobj': 17, 'nmod:flat': 56, 'obl:arg': 19, 'ROOT': 9, 'obl': 14, 'inne':4}}
    key_o = {'samorząd': {'nmod:arg': 336, 'nmod': 305, 'iobj': 56, 'nsubj': 283, 'obl:arg': 80, 'conj': 100, 'obj': 157, 'nmod:flat': 6, 'obl': 40, 'ROOT': 16, 'nsubj:pass': 6, 'obl:agent': 13, 'ccomp': 7, 'inne':10}, 'węgiel': {'nmod': 79, 'obl:arg': 13, 'obj': 65, 'iobj': 5, 'nsubj': 22, 'nmod:flat': 29, 'nmod:arg': 147, 'conj': 27, 'inne':4}}
    all_r = sum([v for v in key_r['samorząd'].values()])
    all_o = sum([v for v in key_o['samorząd'].values()])
    for key in key_r.keys():
        for dep in key_r[key].keys():
            key_r[key][dep] = key_r[key][dep]/all_r
    for key in key_o.keys():
        for dep in key_o[key].keys():
            key_o[key][dep] = key_o[key][dep]/all_o
    print(key_r)
    print(key_o)
    
    fig, ax = plt.subplots(1, 2, figsize=(20, 20))
    ax[0].pie(key_r['samorząd'].values(), labels=key_r['samorząd'].keys())
    ax[0].set_title("samorząd rządowa")
    ax[1].pie(key_o['samorząd'].values(), labels=key_o['samorząd'].keys())
    ax[1].set_title("samorząd opozycyjna")
    plt.show()

    fig, ax = plt.subplots(1, 2, figsize=(20, 20))
    ax[0].pie(key_r['węgiel'].values(), labels=key_r['węgiel'].keys())
    ax[0].set_title("węgiel rządowa")
    ax[1].pie(key_o['węgiel'].values(), labels=key_o['węgiel'].keys())
    ax[1].set_title("węgiel opozycyjna")
    plt.show()
    """
    llm = Llama(
      model_path="/Users/mich/Downloads/codellama-7b.Q4_K_M.gguf",
      chat_format="llama-2")
    output = llm("Q:Jesteś ocenijącym wydźwięk w zdaniach wypowiedzianych przez polityków Czy następujące zdanie wyraza pozytywne:P czy negatywne:N nastawienie do węgla:       No, jest pewne, naturalnie jest faktem bezsprzecznym, że węgiel nie wzbogacany w tym zakresie posyłany do elektrowni powoduje zwiększenie pylenia w tej elektrowni. Ja już pomijam wszystkie technologiczne tam same procesy, bo się trzymam tutaj tematu ochrony środowiska. I w związku z powyższym ma to również wpływ negatywny wszędzie tam, gdzie taki węgiel użytkuje się. Odpowiedz tylko jedną literą. Za dobrą odpowiedź dostaniesz 1 punkt.",
max_tokens=3)
    print(output)

   

            

if __name__=="__main__":
    main()

