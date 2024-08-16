import logging

from .connectors import HostQuery
from . import output_util, utils

from common_osint_model import Host

logger = logging.getLogger(__name__)

# TODO: reduce code duplication for connection

def host(config:dict, host:str, service:str, raw:bool = False):
    logger.info(f"Query for \"{host}\" with service {service}. Raw Output {"activated" if raw else "deactivated"}.")
    
    connector = utils.find_connector_class(HostQuery, name=service)
    if connector == None:
        logger.warn(f"Did not find connector for service {service}. Raising NotImplementedError Exception.")
        raise NotImplementedError
    connection = connector(config['connectors'][service])

    host_query_result = connection.query_host(host)
    if not raw:
        logger.info("Convert raw data to Common OSINT Model.")
        if service == "shodan":
            logger.debug("Trying to convert raw Shodan result to Common OSINT Model.")
            return [Host.from_shodan(host_query_result)]
        elif service == "censys":
            logger.debug("Trying to convert raw Censys result to Common OSINT Model")
            return [Host.from_censys(host_query_result)]
        else:
            logger.warn(f"No Common OSINT Model translation available for service {service}. Raising NotImplementedError Exception.")
            raise NotImplementedError
    else:
        logger.info("Raw output required. Returning raw data.")
        return [host_query_result]

def host_search(config:dict, search:str, service:str, raw:bool = False, refine:bool=False):
    logger.info(f"Search for \"{search}\" with service {service}. Raw Output {"activated" if raw else "deactivated"}. Refine {"activated" if refine else "deactivated"}")
    
    connector = utils.find_connector_class(HostQuery, name=service)
    if connector == None:
        logger.warn(f"Did not find connector for service {service}. Raising NotImplementedError Exception.")
        raise NotImplementedError
    connection = connector(config['connectors'][service])
    
    raw_search_query_result = connection.query_host_search(search)
    if not raw:
        logger.debug("Convert raw data to Common OSINT Model.")
        if type(raw_search_query_result) == dict:     # If True -> Shodan
            query_matches = raw_search_query_result['matches']
        else:
            query_matches = raw_search_query_result
        logger.debug(f"Query had {len(query_matches)} matches.")

        result_set = list()
        for query_match in query_matches:
            if service == "shodan":
                logger.debug("Trying to convert raw Shodan result to Common OSINT Model.")
                entry_host = Host.from_shodan(query_match)
            elif service == "censys":
                logger.debug("Trying to convert raw Censys result to Common OSINT Model")
                entry_host = Host.from_censys(query_match)
            else:
                logger.warn(f"No Common OSINT Model translation available for service {service}. Raising NotImplementedError Exception.")
                raise NotImplementedError
            
            if refine:
                logger.debug(f"Refining dataset for host \"{entry_host.ip}\".")
                entry_host = host(config = config, host = entry_host.ip, service = service)[0]
            result_set.append(entry_host)
        return result_set
    else:
        logger.info("Raw output required. Returning raw data.")
        return raw_search_query_result

def output(config:dict, query_result, output_format:str, query_command:str, query:str, raw = False, service:str = ""):
    if output_format == "cli":
        output_util.print_com_host_table(query_result)
    elif output_format == "json":
        if not raw:
            if type(query_result) == list:
                output_util.print_json([entry.flattened_dict for entry in query_result])
            else:
                output_util.print_json(query_result.flattened_dict)
        else:
            output_util.print_json(query_result)
    elif output_format == "opensearch":
        if raw:
            index_name = f"{service}-{query_command}-raw"
            output_util.opensearch_output(opensearch_config = config['connectors']['opensearch'], query=query, query_result=query_result, index_name=index_name)
        else:
            index_name = f"com-{query_command}"
            if type(query_result) == Host:
                query_result = [query_result]
            
            for element in query_result:
                # TODO this is a little hacky right now, but otherwise it's hard to get this data into opensearch...
                element.services = []
                output_util.opensearch_output(opensearch_config = config['connectors']['opensearch'], query=query, query_result=element.flattened_dict, index_name=index_name)