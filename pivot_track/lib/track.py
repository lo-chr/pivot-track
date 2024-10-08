import logging
import yaml
from datetime import datetime, date
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Literal
from uuid import UUID

from pivot_track.lib.query import Querying, QueryResult
from pivot_track.lib.connectors import (
    SourceConnector,
    OpenSearchConnector,
    OutputConnector,
    NotificationConnector,
)

logger = logging.getLogger(__name__)


class TrackingQuery(BaseModel):
    source: Literal["censys", "shodan"]
    command: Literal["host_generic", "host"]
    query: str
    expand: Optional[bool] = False

    @classmethod
    def from_dict(cls, query_dict: dict):
        source = query_dict.get("source")
        command = query_dict.get("command")
        expand = query_dict.get("expand", False)
        query = query_dict.get("query")

        return TrackingQuery(source=source, command=command, query=query, expand=expand)


class TrackingDefinition(BaseModel):
    uuid: UUID
    queries: List[TrackingQuery]
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created: Optional[date] = None
    modified: Optional[date] = None
    tags: Optional[List[str]] = list()
    output: Optional[str] = None

    @property
    def sources(self):
        sources = set()
        for query_item in self.queries:
            sources.add(query_item.source)
        return sources

    @property
    def commands(self):
        commands = set()
        for query_item in self.queries:
            commands.add(query_item.command)
        return commands

    def queries_by_source(self, source: str):
        queries = list()
        for query_item in self.queries:
            if query_item.source == source:
                queries.append(query_item)
        return queries

    def queries_by_command(self, command: str):
        queries = list()
        for query_item in self.queries:
            if query_item.command == command:
                queries.append(query_item)
        return queries

    def queries_by_filter(self, command: str = None, source: str = None):
        if command is None and source is None:
            return self.queries()
        elif command is None and isinstance(source, str):
            return self.queries_by_source(source)
        elif isinstance(command, str) and source is None:
            return self.queries_by_command
        else:
            queries = list()
            for query_item in self.queries:
                if query_item.command == command and query_item.source == source:
                    queries.append(query_item)
            return queries

    @classmethod
    def from_yaml(cls, definition: str):
        parsed_definition = yaml.safe_load(definition)
        return cls.from_dict(parsed_definition)

    @classmethod
    def from_dict(cls, definition: dict):
        uuid = definition.get("uuid")
        if uuid is not None:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise ValidationError

        # This needs to be replaced with a proper typed TrackingDefinitionQuery (or similar)
        queries = definition.get("query")
        if queries is None or len(queries) == 0 or not isinstance(queries, list):
            queries = None
        else:
            queries = [
                TrackingQuery.from_dict(query_element) for query_element in queries
            ]

        title = definition.get("title")
        status = definition.get("status")
        description = definition.get("description")
        author = definition.get("author")
        created = definition.get("created")
        if created is not None:
            try:
                created = datetime.strptime(created, "%Y/%m/%d").date()
            except ValueError:
                raise ValidationError

        modified = definition.get("modified")
        if modified is not None:
            try:
                modified = datetime.strptime(modified, "%Y/%m/%d").date()
            except ValueError:
                raise ValidationError

        tags = [tag for tag in definition.get("tags", list())]
        output = definition.get("output")
        return TrackingDefinition(
            uuid=uuid,
            queries=queries,
            title=title,
            status=status,
            description=description,
            author=author,
            created=created,
            modified=modified,
            tags=tags,
            output=output,
        )


class Tracking:
    """The `Tracking` class is responsbile for the tracking feature within Pivot Track. Tracking means,
    the automatic execution and storing of queries against several sources, storing the results
    and providing notifications for newly found items."""

    def track_definitions(
        definitions: List[TrackingDefinition],
        source_connections: List[SourceConnector],
        output_connection: OutputConnector,
        notification_connection: NotificationConnector = None,
    ):
        """The function executes all definitions via the provided connections to sources. The results will be  stored via the provided output connector."""
        for source_connection in source_connections:
            definitions_for_source = Tracking.definitions_by_source(
                definitions, source_connection.short_name
            )
            logger.info(
                f'{len(definitions_for_source)} tracking definition(s) available for source "{source_connection.short_name}".'
            )
            Tracking.track_definitions_for_source(
                source_connection=source_connection,
                definitions=definitions_for_source,
                output_connection=output_connection,
                notification_connection=notification_connection,
            )

    def track_definitions_for_source(
        definitions: List[TrackingDefinition],
        source_connection: SourceConnector,
        output_connection: OutputConnector,
        notification_connection: NotificationConnector = None,
    ):
        """The function executes all queries for one specific source (i.E. Shodan or Censys)."""
        opensearch_connection = output_connection
        if opensearch_connection.available:
            source_string = source_connection.short_name
            logger.info(
                f'Start tracking {len(definitions)} definition(s) in source "{source_string}"'
            )
            for definition in definitions:
                logger.info(
                    f'Start tracking with source "{source_string}" for definition "{str(definition.uuid)}".'
                )
                # TODO Fix manual definition of command to be executed
                host_searches = definition.queries_by_filter(
                    command="host_generic", source=source_string
                )
                collected_results = Tracking.execute_tracking_queries(
                    host_searches, source_connection, opensearch_connection
                )
                logger.info(
                    f'Got {len(collected_results)} for definition "{str(definition.uuid)}".'
                )
                new_items = opensearch_connection.tracking_output(
                    query_result=collected_results, definition=definition
                )
                if notification_connection is not None:
                    notification_connection.notify(
                        definition=definition, notify_items=new_items
                    )
        else:
            logger.error(
                "OpenSearchConnector is not available. OpenSearch is required for this feature."
            )

    def execute_tracking_queries(
        queries: List[TrackingQuery],
        source_connection: SourceConnector,
        output_connection: OpenSearchConnector = None,
    ) -> List[QueryResult]:
        """The function is responible for executing a given TrackingQuery on a given source_connection."""
        collected_results = list()
        for query_element in queries:
            query_result, expanded_query_result = Querying.host_query(
                search=query_element.query,
                connection=source_connection,
                expand=query_element.expand,
            )
            if query_result is not None:
                if not query_element.expand:
                    collected_results.append(query_result)
                    output_result = query_result
                else:
                    logger.debug(
                        f"Length of expanded query result is {len(expanded_query_result)}."
                    )
                    collected_results.extend(expanded_query_result)
                    output_result = expanded_query_result
                if output_connection is not None:
                    output_connection.query_output(query_result=output_result)
        return collected_results

    def load_yaml_definition_files(
        definition_yaml_path: Path,
    ) -> List[TrackingDefinition]:
        """The function is loads TrackingDefinitions (in their YAML-representation) from a given path."""
        if definition_yaml_path is None or not definition_yaml_path.exists():
            logger.error("Could not load tracking definitions. Raising AttributeError.")
            raise AttributeError("Could not load tracking definitions.")

        definition_files_path = [
            definition_path for definition_path in definition_yaml_path.glob("**/*.yml")
        ]
        logger.info(
            f'Found {len(definition_files_path)} definition file(s) in "{str(definition_yaml_path)}".'
        )

        loaded_definitions = list()
        for definition_file_path in definition_files_path:
            with open(definition_file_path, "r") as file:
                definition = TrackingDefinition.from_yaml(file)
                loaded_definitions.append(definition)
                logger.debug(
                    f'Loaded definition file "{str(definition_file_path)}" with UUID "{definition.uuid}".'
                )
        logger.info(f"Loaded {len(loaded_definitions)} tracking definition(s).")
        return loaded_definitions

    def load_definitions(tracking_definition_path: Path = None) -> tuple[list, dict]:
        """This legacy function is responsible for loading all tracking definitions at a given path.
        It returns a tuple, containing a list with all loaded definitinons. Additionally it
        returns a dictionary where the key is a given data source and the value the tracking
        definition."""

        loaded_definitions_by_source = dict()
        loaded_definitions = Tracking.load_yaml_definition_files(
            tracking_definition_path
        )
        loaded_definitions_by_source["censys"] = Tracking.definitions_by_source(
            loaded_definitions, "censys"
        )
        loaded_definitions_by_source["shodan"] = Tracking.definitions_by_source(
            loaded_definitions, "shodan"
        )
        return loaded_definitions, loaded_definitions_by_source

    def definitions_by_source(
        definitions: List[TrackingDefinition], source: str
    ) -> List[TrackingDefinition]:
        """This function returns all definitions, that are applicable to a specific source."""
        if not isinstance(source, str):
            raise TypeError("'source' has to be of type 'str'.")
        result_definitions = list()
        for definition in definitions:
            if source in definition.sources:
                result_definitions.append(definition)
                logger.debug(f'Added rule "{definition.uuid}" for source {source}.')
        logger.info(
            f'{len(result_definitions)} tracking definition(s) available for source "{source}".'
        )
        return result_definitions
