import os
import requests

URL = "http://0.0.0.0:5555"
LOGIN_URL = URL + "/api_login"
ADD_TEXT_URL = URL + "/api/text"
QUERY_URL = URL + '/query_api/{corpus_id}/query'

CCL_DIR = "ccls"

COLLECTION_ID = 1
COLLECTION_NAME = "KOOS"

USERNAME = "ryszardtuora@gmail.com"
PASSWORD = "password1"

def login():
    login_response = requests.post(LOGIN_URL, json={"username": USERNAME,
                                                    "password": PASSWORD})

    access_token = login_response.json()["access_token"]
    authorization_header = {"Authorization": f"Bearer {access_token}"}
    return authorization_header


def index_file(filepath, authorization_header):
    with open(filepath) as f:
        ccl_text = f.read()

    text_data = {
        "collection_id": COLLECTION_ID,
        "collection_name": COLLECTION_NAME,
        "force_udpate": True,
        "text": ccl_text,
        "text_format": ".ccl",
        "text_name": "test_api",
        "text_metadata": {},
        }

    add_text_response = requests.post(ADD_TEXT_URL, json=text_data, headers=authorization_header)
    return add_text_response


def main():
    authorization_header = login()
    for filename in os.listdir(CCL_DIR):
        filepath = os.path.join(CCL_DIR, filename)
        add_text_response = index_file(filepath, authorization_header)
        print(add_text_response)


if __name__ == "__main__":
    main()
