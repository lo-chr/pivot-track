import logging, yaml, time
from pathlib import Path

from . import query, utils
from .connectors import SourceConnector, OpenSearchConnector

logger = logging.getLogger(__name__)

from common_osint_model import Domain, Host

class Tracking:
    def execute_tracker(
            config:dict = None,
            tracking_definition_path:Path = None,
            interval:int = 600
        ):
        if config == None:
            logger.error("No configuration set. Raising AttributeError.")
            raise AttributeError("No configuration set.")
        
        while True:
            loaded_definitions, definition_by_source = Tracking.load_definitions(tracking_definition_path)
            logger.info(f"{len(loaded_definitions)} tracking definition(s) available in total.")
            for source in definition_by_source.keys():
                logger.info(f"{len(definition_by_source[source])} tracking definition(s) available for source \"{source}\".")
                connector = utils.find_connector_class(SourceConnector, source)
                logger.info(f"Identified connector \"{connector.__name__}\" for source \"{source}\".")
                Tracking.track_source(source = connector, definitions = definition_by_source[source], config = config)
            logger.info(f"Done tracking for now. Waiting {interval} seconds for next try.")
            time.sleep(interval)

    def track_source(source:SourceConnector = None, definitions:list = None, config:dict = None):
        logger.info(f"Start tracking {len(definitions)} definition(s) in source \"{source.__name__}\"")
        
        source_string = source.__name__.lower().removesuffix("sourceconnector")
        for definition in definitions:
            logger.info(f"Start tracking with source \"{source.__name__}\" for definition \"{definition['uuid']}\".")

            collected_results = list()
            for host_search in definition['query']['source'][source_string]['host_generic']:
                query_result, expanded_query_result = query.host_query(
                    config = config,
                    search = host_search,
                    source = source,
                    expand = definition['query']['source'][source_string]['expand']
                )
                if not definition['query']['source'][source_string]['expand']:
                    collected_results.extend(query_result)
                    query.output(
                        config = config,
                        query_result = query_result,
                        output_format=definition['output'],
                    ) 
                else:
                    logger.debug(f"Length of expanded query result is {len(expanded_query_result)}.")
                    collected_results.extend(expanded_query_result)
                    query.output(
                        config = config,
                        query_result = expanded_query_result,
                        output_format=definition['output'],
                    )
            new_items = OpenSearchConnector(config['connectors']['opensearch']).tracking_output(query_result=collected_results, definition=definition)
            logger.debug(f"Got {len(new_items)} for last run of  \"{definition['uuid']}\".")
            if len(new_items) > 0:
                logger.info(f"Appending notification for {len(new_items)} items.")
                notification = f"🚨🚨🚨 Tracking Results for \"{definition['title']}\" ({definition['uuid']}) on {source_string.capitalize()}:\n{'\n'.join([notify_string for notify_string in Tracking.create_notify_strings(new_items)])}"
                Tracking.notify_for_new_elements(notification, config)
                
    
    def load_definitions(tracking_definition_path:Path = None) -> tuple[list, dict]:
        if tracking_definition_path == None or not tracking_definition_path.exists():
            logger.error("Could not load tracking definitions. Raising AttributeError.")
            raise AttributeError("Could not load tracking definitions.")
        
        definition_files_path = [definition_path for definition_path in tracking_definition_path.glob("**/*.yml")]
        logger.info(f"Found {len(definition_files_path)} definition file(s) in \"{str(tracking_definition_path)}\".")
        
        loaded_definitions = list()
        loaded_definition_by_source = dict()

        for definition_file_path in definition_files_path:
            with open(definition_file_path, 'r') as file:
                # TODO: Validate schema of yaml file
                definition = yaml.safe_load(file)
                loaded_definitions.append(definition)
                logger.debug(f"Loaded definition file \"{str(definition_file_path)}\" with UUID \"{definition['uuid']}\".")
                for source in definition['query']['source'].keys():
                    if source not in loaded_definition_by_source:
                        loaded_definition_by_source[source] = []
                        logger.debug(f"Created new source category \"{source}\" in loaded_definitions_by_source.")

                    loaded_definition_by_source[source].append(definition)
                    logger.debug(f"Added rule \"{definition['uuid']}\" for source {source}.")
        
        return loaded_definitions, loaded_definition_by_source
    
    def create_notify_strings(new_elements:list):
        notify_strings = list()
        for element in new_elements:
            if isinstance(element, Host):
                notify_strings.append(element.ip)
            elif isinstance(element, Domain):
                notify_strings.append(element.domain)
        return notify_strings
    
    def notify_for_new_elements(notification:str, config:dict):
        tracking_file_path = Path(config['tracking_file'])
        try:
            with open(tracking_file_path, 'a') as out_file:
                out_file.write(f"{notification}\n\n")
        except FileNotFoundError as e:
            logger.error(f"Could not find notification output: {tracking_file_path.absolute().as_posix()}")
