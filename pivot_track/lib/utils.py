import json
from pathlib import Path

import yaml


def load_config(path:str = None):
    if(path == None):
        path = str(Path.home() / '.pivottrack' / 'config.yaml')
    
    # TODO Implement testing for correct path
    with open(path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

def printable_result(input, format:str = "json"):
    if(format == "json"):
        return print_json(input)
    else:
        return "Not implemented yet"

def print_json(input, indent=2):
    print(str(type(input)))
    if(type(input) == dict or type(input) == list):
        return json.dumps(input, indent=indent)
    else:
        try:
            loaded = json.loads(input)
            return json.dumps(loaded, indent=indent)
        except ValueError as e:
            return None