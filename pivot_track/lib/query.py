from .connectors import HostQuery
from . import utils

# TODO: reduce code duplication
def host(config:dict, host:str, service = "shodan"):
    connector = utils.find_connector_class(HostQuery, name=service)
    if connector == None:
        raise NotImplementedError
    connection = connector(config['connectors'][service])

    host_query_result = connection.query_host(host)
    return host_query_result

# TODO: reduce code duplication
def host_search(config:dict, search:str, service = "shodan"):
    connector = utils.find_connector_class(HostQuery, name=service)
    if connector == None:
        raise NotImplementedError
    connection = connector(config['connectors'][service])

    search_query_result = connection.query_host_search(search)
    return search_query_result