from pathlib import Path

import yaml


def load_config(path:Path = None) -> dict:
    """This function is loads the configuration from a file and returns it."""
    if(path == None):
        path = str(Path.home() / '.pivottrack' / 'config.yaml')
    
    # TODO Implement testing for correct path
    with open(path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

# TODO Rename in find_connector_class_by_name
def find_connector_class(parent_class, name:str):
    """This function returns a sub class of a parent class."""
    for connector in parent_class.__subclasses__():
        if name in connector.__name__.lower():
            return connector 
    return None

def connector_classes_by_parent(parent_class):
    """This function returns all sub classes of a given parent class."""
    return parent_class.__subclasses__()