from pathlib import Path
from typing import List
from pivot_track.lib.connectors import SourceConnector, OutputConnector
import yaml


def load_config(path:Path = None) -> dict:
    """This function is loads the configuration from a file and returns it."""
    if not isinstance(path, Path):
        raise AttributeError("Pivot Track configuration path only allows Path objects.")
    
    if path is None or not path.exists():
        raise FileNotFoundError()

    with open(path, 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
            return config
        except yaml.YAMLError:
            return None

# TODO reduce code duplication
def init_source_connections(config:dict) -> List[SourceConnector]:
    available_connections = list()
    for connector_config_key in config.get('connectors', dict() ).keys():
        connector_config = config.get('connectors').get(connector_config_key)
        if connector_config.get('enabled', True):
            connector = subclass_by_parent_find(SourceConnector, connector_config_key)
            if connector is not None:
                available_connections.append(connector(connector_config))
    return available_connections

# TODO reduce code duplication
def init_output_connections(config:dict, filter:str = None) -> List[OutputConnector]:
    available_connections = list()
    for connector_config_key in config.get('connectors', dict() ).keys():
        connector_config = config.get('connectors').get(connector_config_key)
        if connector_config.get('enabled', True):
            connector = subclass_by_parent_find(OutputConnector, connector_config_key)
            if connector is not None:
                available_connections.append(connector(connector_config))
    return available_connections

def subclass_by_parent_find(parent_class, search_string:str):
    """This function returns a sub class of a parent class."""
    for connector in parent_class.__subclasses__():
        connector_name = connector.__name__.lower()
        if search_string in connector_name and 'mock' not in connector_name:
            return connector 
    return None

def subclasses_by_parent(parent_class):
    """This function returns all sub classes of a given parent class."""
    return parent_class.__subclasses__()