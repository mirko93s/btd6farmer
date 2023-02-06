import json
from pathlib import Path

def load_from_file(path):
    return parse_json(path)

def load_from_url(url):
    # Check if the content is valid 
    # valid zip -> setup and instructions

    pass

def parse_json(path):
    """
        Will read the @path as a json file load into a dictionary.
    """
    data = {}
    try:
        with path.open('r', encoding="utf-8") as f:
            data = json.load(f)
    
        return data
    except json.decoder.JSONDecodeError as e:
        raise Exception("Invalid json file", e)