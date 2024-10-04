import yaml
from pathlib import Path
from typing import List, Dict
from pivot_track.lib.connectors import SourceConnector, OutputConnector


def load_config(path: Path = None) -> Dict[str, Dict]:
    """This function is loads the configuration from a file and returns it."""
    if not isinstance(path, Path):
        raise AttributeError("Pivot Track configuration path only allows Path objects.")

    if path is None or not path.exists():
        raise FileNotFoundError()

    with open(path, "r") as config_file:
        try:
            config = yaml.safe_load(config_file)
            return config
        except yaml.YAMLError:
            return None


def init_source_connections(config: dict, filter: str = "") -> List[SourceConnector]:
    available_connections = _init_typed_connections(
        config, SourceConnector, filter=filter
    )
    return available_connections


def init_output_connections(config: dict, filter: str = "") -> List[OutputConnector]:
    available_connections = _init_typed_connections(config, OutputConnector)
    return available_connections


def _init_typed_connections(config: dict, parent_class, filter: str = "") -> List:
    available_connections = list()
    connector_config_keys = config.get("connectors", dict()).keys()
    if not filter == "" and filter in connector_config_keys:
        connector_config_keys = [filter]
    for connector_config_key in connector_config_keys:
        connector_config = config.get("connectors").get(connector_config_key)
        if connector_config.get("enabled", True):
            connector = subclass_by_parent_find(parent_class, connector_config_key)
            if connector is not None:
                connection = connector(connector_config)
                available_connections.append(connection)
    return available_connections


def subclass_by_parent_find(parent_class, search_string: str):
    """This function returns a sub class of a parent class."""
    for connector in parent_class.__subclasses__():
        connector_name = connector.__name__.lower()
        if search_string in connector_name and "mock" not in connector_name:
            return connector
    return None


def subclasses_by_parent(parent_class):
    """This function returns all sub classes of a given parent class."""
    return parent_class.__subclasses__()
