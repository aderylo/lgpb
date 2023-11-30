import os
import json
import requests

URL = "http://0.0.0.0:5555"
LOGIN_URL = URL + "/api_login"
ADD_TEXT_URL = URL + "/api/text"
QUERY_URL = URL + '/query_api/{corpus_id}/query'

CCL_DIR = "ccls"
METADATA_FILE = "processed_data.json"

COLLECTION_ID = 37
COLLECTION_NAME = "test24"

USERNAME = "ryszardtuora@gmail.com"
PASSWORD = "password1"

def login():
    login_response = requests.post(LOGIN_URL, json={"username": USERNAME,
                                                    "password": PASSWORD})

    access_token = login_response.json()["access_token"]
    authorization_header = {"Authorization": f"Bearer {access_token}"}
    return authorization_header


def index_doc(entry, authorization_header):
    doc_id = entry["id"]
    filename = doc_id + ".xml"
    filepath = os.path.join(CCL_DIR, filename)
    with open(filepath) as f:
        ccl_text = f.read()

    metadata = {f"meta_{key}":value for key, value in entry["metadata"].items()}
    text_name = metadata["meta_title"].lower().replace(" ", "_")
    text_data = {
        "collection_id": COLLECTION_ID,
        "collection_name": COLLECTION_NAME,
        "force_udpate": True,
        "text": ccl_text,
        "text_format": ".ccl",
        "text_name": text_name,
        "text_metadata": metadata,
        }

    add_text_response = requests.post(ADD_TEXT_URL, json=text_data, headers=authorization_header)
    return add_text_response


def main():
    authorization_header = login()
    with open(METADATA_FILE) as f:
        data = json.load(f)

    for entry in data:
        add_text_response = index_doc(entry, authorization_header)
        print(add_text_response)


if __name__ == "__main__":
    main()
