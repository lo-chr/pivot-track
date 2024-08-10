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
    if(type(input) == dict or type(input) == list):
        return json.dumps(input, indent=indent)
    else:
        try:
            loaded = json.loads(input)
            return json.dumps(loaded, indent=indent)
        except ValueError as e:
            return None

# TODO Rename in find_connector_class_by_name
def find_connector_class(parent_class, name:str):
    for connector in parent_class.__subclasses__():
        if name in connector.__name__.lower():
            return connector 
    return None

def connector_classes_by_parent(parent_class):
    return parent_class.__subclasses__()