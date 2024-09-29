import logging, yaml, time
from datetime import datetime, UTC, date
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Literal
from uuid import UUID

from . import query, utils
from .connectors import SourceConnector, OpenSearchConnector

logger = logging.getLogger(__name__)

from common_osint_model import Domain, Host

class TrackingQuery(BaseModel):
    source:Literal['censys', 'shodan']
    command:Literal['host_generic', 'host']
    query:str
    expand:Optional[bool] = False

    @classmethod
    def from_dict(cls, query_dict:dict):
        source = query_dict.get('source')
        command = query_dict.get('command')
        expand = query_dict.get('expand', False)
        query = query_dict.get('query')

        return TrackingQuery(source=source, command=command, query=query, expand=expand)


class TrackingDefinition(BaseModel):
    uuid:UUID
    query:List[TrackingQuery]
    title:Optional[str] = None
    status:Optional[str] = None
    description:Optional[str] = None
    author:Optional[str] = None
    created:Optional[date] = None
    modified:Optional[date] = None
    tags:Optional[List[str]] = list()
    output:Optional[str] = None

    @classmethod
    def from_yaml(cls, definition:str):
        parsed_definition = yaml.safe_load(definition)
        return cls.from_dict(parsed_definition)

    @classmethod
    def from_dict(cls, definition:dict):
        uuid = definition.get('uuid')
        if uuid is not None:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise ValidationError
        
        # This needs to be replaced with a proper typed TrackingDefinitionQuery (or similar)
        query = definition.get('query')
        if query is None or len(query) == 0 or not type(query) == list:
            query = None
        else:
            query = [TrackingQuery.from_dict(query_element) for query_element in query]
        
        title = definition.get('title')
        status = definition.get('status')
        description = definition.get('description')
        author = definition.get('author')
        created = definition.get('created')
        if created is not None:
            try:
                created = datetime.strptime(created, "%Y/%m/%d").date()
            except ValueError:
                raise ValidationError

        modified = definition.get('modified')
        if modified is not None:
            try:
                modified = datetime.strptime(modified, "%Y/%m/%d").date()
            except ValueError:
                raise ValidationError
        
        tags = [tag for tag in definition.get('tags', list())]
        output = definition.get('output')
        return TrackingDefinition(uuid=uuid,
                                  query=query,
                                  title=title,
                                  status=status,
                                  description=description,
                                  author=author,
                                  created=created,
                                  modified=modified,
                                  tags=tags,
                                  output=output)


class Tracking:
    """The `Tracking` class is responsbile for the tracking feature within Pivot Track. Tracking means,
    the automatic execution and storing of queries against several sources, storing the results
    and providing notifications for newly found items. """
    def execute_tracker(
            config:dict = None,
            tracking_definition_path:Path = None,
            interval:int = 600
        ):
        """This function is responsbile for executing searches defined by a set of tracking definitions.
        It retries the searches after a given period of time."""
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
        """The function executes all queries for one source (i.E. Shodan or Censys)."""
        opensearch_connector = OpenSearchConnector(config['connectors']['opensearch'])
        if opensearch_connector.available:
            logger.info(f"Start tracking {len(definitions)} definition(s) in source \"{source.__name__}\"")
            
            source_string = source.__name__.lower().removesuffix("sourceconnector")
            for definition in definitions:
                logger.info(f"Start tracking with source \"{source.__name__}\" for definition \"{definition['uuid']}\".")
                connection = source(config['connectors'][source.__name__.lower().removesuffix("sourceconnector")])

                collected_results = list()
                host_searches = definition['query']['source'][source_string]['host_generic'] if definition['query']['source'][source_string]['host_generic'] != None else []
                for host_search in host_searches:
                    query_result, expanded_query_result = query.Querying.host_query(
                        search = host_search,
                        connection = connection,
                        expand = definition['query']['source'][source_string]['expand']
                    )
                    if not definition['query']['source'][source_string]['expand']:
                        collected_results.append(query_result)
                        query.Querying.output(
                            config = config,
                            query_result = query_result,
                            output_format=definition['output'],
                        ) 
                    else:
                        logger.debug(f"Length of expanded query result is {len(expanded_query_result)}.")
                        collected_results.extend(expanded_query_result)
                        query.Querying.output(
                            config = config,
                            query_result = expanded_query_result,
                            output_format=definition['output'],
                        )
                
                    new_items = opensearch_connector.tracking_output(query_result=collected_results, definition=definition)
                    logger.debug(f"Got {len(new_items)} for last run of  \"{definition['uuid']}\".")
                    if len(new_items) > 0:
                        logger.info(f"Appending notification for {len(new_items)} items.")
                        notification = f"🚨🚨🚨 Tracking Results for \"{definition['title']}\" ({definition['uuid']}) on {source_string.capitalize()}:\n{'\n'.join([notify_string for notify_string in Tracking.create_notify_strings(new_items)])}"
                        Tracking.notify_for_new_elements(notification, config)
        else:
            logger.error("OpenSearchConnector is not available. OpenSearch is required for this feature.")
            return
                
    
    def load_definitions(tracking_definition_path:Path = None) -> tuple[list, dict]:
        """This function is responsible for loading all tracking definitions at a given path.
        It returns a tuple, containing a list with all loaded definitinons. Additionally it
        returns a dictionary where the key is a given data source and the value the tracking
        definition."""
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
    
    def create_notify_strings(new_elements:list) -> list:
        """This function transfers a set of Common OSINT Model items to a list of identifiable strings (hostnames and IPs for now)."""
        notify_strings = list()
        for element in new_elements:
            if isinstance(element, Host):
                notify_strings.append(element.ip)
            elif isinstance(element, Domain):
                notify_strings.append(element.domain)
        return notify_strings
    
    def notify_for_new_elements(notification:str, config:dict):
        """This function handles the notification for new events. For now it just stores them in a given file."""
        tracking_file_path = Path(config['tracking_file'])
        try:
            with open(tracking_file_path, 'a') as out_file:
                out_file.write(f"{notification}\n\n")
        except FileNotFoundError as e:
            logger.error(f"Could not find notification output: {tracking_file_path.absolute().as_posix()}")
