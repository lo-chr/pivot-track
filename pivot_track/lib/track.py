import logging
import yaml
import pika
import pika.channel
import json
from datetime import datetime, date, timezone
from pathlib import Path
from pydantic import BaseModel, ValidationError, computed_field
from typing import Optional, List, Literal
from uuid import UUID, uuid4

from pivot_track.lib import utils
from pivot_track.lib.query import Querying, QueryResult
from pivot_track.lib.connectors import (
    SourceConnector,
    OutputConnector,
    RabbitMQConnector,
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
    query: List[TrackingQuery]
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
        for query_item in self.query:
            sources.add(query_item.source)
        return sources

    @property
    def commands(self):
        commands = set()
        for query_item in self.query:
            commands.add(query_item.command)
        return commands

    def queries_by_source(self, source: str):
        queries = list()
        for query_item in self.query:
            if query_item.source == source:
                queries.append(query_item)
        return queries

    def queries_by_command(self, command: str):
        queries = list()
        for query_item in self.query:
            if query_item.command == command:
                queries.append(query_item)
        return queries

    def queries_by_filter(self, command: str = None, source: str = None):
        if command is None and source is None:
            return self.query
        elif command is None and isinstance(source, str):
            return self.queries_by_source(source)
        elif isinstance(command, str) and source is None:
            return self.queries_by_command(command)
        else:
            queries = list()
            for query_item in self.query:
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

        modified = definition.get("modified")

        tags = [tag for tag in definition.get("tags", list())]
        output = definition.get("output")
        return TrackingDefinition(
            uuid=uuid,
            query=queries,
            title=title,
            status=status,
            description=description,
            author=author,
            created=created,
            modified=modified,
            tags=tags,
            output=output,
        )


class TrackingResult(BaseModel):
    uuid: UUID = uuid4()
    timestamp: datetime = datetime.now(timezone.utc)
    definition: TrackingDefinition
    query_results: Optional[List[QueryResult]] = None

    @computed_field
    @property
    def com_query_results(self) -> List:
        result = list()
        for query_result_element in self.query_results:
            if query_result_element.is_collection:
                logger.debug("query_result_element is collection.")
                result.extend(query_result_element.com_result)
            else:
                result.append(query_result_element.com_result)
        return result

    @computed_field
    @property
    def raw_query_results(self) -> list:
        return [result.raw_query_result for result in self.query_results]


class TrackingService:
    config: dict = None
    queue_connector: RabbitMQConnector = None

    def __init__(self, config: dict):
        self.config = config
        self.queue_connector = RabbitMQConnector(config["connectors"]["rabbitmq"])
        self.queue_connector.connect()
        # Ensure Make sure that task queue exists
        queue_channel = self.queue_connector.rabbitmq_client.channel()
        queue_channel.queue_declare("pivottrack-definition-tasks", durable=True)
        queue_channel.close()
        self.queue_connector.close()

    def publish_tasks(self, definition_path: Path):
        logger.info(f"Searching for tasks at {str(definition_path)}")
        definitions = Tracking.load_yaml_definition_files(definition_path)
        self.queue_connector.connect()
        queue_channel = self.queue_connector.rabbitmq_client.channel()
        logger.info(f"Producing {len(definitions)} tasks.")
        for definition in definitions:
            logger.debug(f"Producing task for definition {definition.uuid}")
            queue_channel.basic_publish(
                exchange="",
                routing_key="pivottrack-definition-tasks",
                body=definition.model_dump_json(),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
            )
        logger.info(
            f"Done publishing {len(definitions)} tracking tasks for now. Waiting until next run."
        )
        queue_channel.close()
        self.queue_connector.close()

    def subscribe_tasks(self):
        source_connections = utils.init_source_connections(self.config)
        logger.info(f"Available SourceConnections are {','.join([source_connection.short_name for source_connection in source_connections])}")
        output_connections = RabbitMQConnector(self.config["connectors"]["rabbitmq"])
        output_connections.setup_result_channel()

        def callback(channel, method, properties, body):
            logger.debug("Received message in task queue.")
            body_dict = json.loads(body)
            next_definition = TrackingDefinition.from_dict(body_dict)
            Tracking.run_definition(
                definition=next_definition,
                source_connections=source_connections,
                output_connection=output_connections,
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)

        self.queue_connector.connect()
        queue_channel = self.queue_connector.rabbitmq_client.channel()
        queue_channel.basic_qos(prefetch_count=1)
        queue_channel.basic_consume(
            queue="pivottrack-definition-tasks", on_message_callback=callback
        )

        logger.info("Start consuming, waiting for message in task queue.")
        queue_channel.start_consuming()


class Tracking:
    """The `Tracking` class is responsbile for the tracking feature within Pivot Track. Tracking means,
    the automatic execution and storing of queries against several sources, storing the results
    and providing notifications for newly found items."""

    def run_definitions(
        definitions: List[TrackingDefinition],
        source_connections: List[SourceConnector],
        output_connection: OutputConnector,
    ):
        """The function executes all definitions via the provided connections to sources. The results will be stored via the provided output connector."""
        for source_connection in source_connections:
            definitions_for_source = Tracking.definitions_by_source(
                definitions, source_connection.short_name
            )
            logger.info(
                f'{len(definitions_for_source)} tracking definition(s) available for source "{source_connection.short_name}".'
            )
            Tracking.run_definitions_for_source(
                source_connection=source_connection,
                definitions=definitions_for_source,
                output_connection=output_connection,
            )

    def run_definition(
        definition: TrackingDefinition,
        source_connections: List[SourceConnector],
        output_connection: OutputConnector,
    ):
        """The function executes all definitions via the provided connections to sources. The results will be stored via the provided output connector."""
        for source_connection in source_connections:
            Tracking.run_task_for_source(
                definition=definition,
                source_connection=source_connection,
                output_connection=output_connection,
            )

    def run_definitions_for_source(
        definitions: List[TrackingDefinition],
        source_connection: SourceConnector,
        output_connection: OutputConnector,
    ) -> None:
        """The function executes all queries for one specific source (i.E. Shodan or Censys)."""
        if output_connection.available:
            source_string = source_connection.short_name
            logger.debug(
                f'Start tracking {len(definitions)} definition(s) in source "{source_string}"'
            )
            for definition in definitions:
                Tracking.run_task_for_source(
                    definition=definition,
                    source_connection=source_connection,
                    output_connection=output_connection,
                )
        else:
            logger.error("OutputConnection is not available. This is required.")

    def run_task_for_source(
        definition: TrackingDefinition,
        source_connection: SourceConnector,
        output_connection: OutputConnector,
    ) -> TrackingResult:
        source_string = source_connection.short_name
        logger.info(
            f'Start tracking with source "{source_string}" for definition "{str(definition.uuid)}".'
        )
        # TODO: Fix manual definition of command to be executed
        host_searches = definition.queries_by_filter(
            command="host_generic", source=source_string
        )

        tracking_result = TrackingResult(definition=definition)
        # TODO: Rework to async logic
        tracking_result.query_results = Tracking.execute_tracking_queries(
            host_searches, source_connection
        )
        total_element_count = sum([query_result.element_count for query_result in tracking_result.query_results])
        logger.info(
            f'Got {total_element_count} for definition {str(tracking_result.definition.uuid)}.'
        )
        output_connection.definition_track_output(tracking_result)
        return TrackingResult

    def execute_tracking_queries(
        queries: List[TrackingQuery], source_connection: SourceConnector
    ) -> List[QueryResult]:
        """The function is responsible for executing a given TrackingQuery on a given source_connection."""
        collected_results: List[QueryResult] = list()
        for query_element in queries:
            query_result, expanded_query_result = Querying.host_query(
                search=query_element.query,
                connection=source_connection,
                expand=query_element.expand,
            )
            if query_result is not None:
                if not query_element.expand:
                    collected_results.append(query_result)
                else:
                    logger.debug(
                        f"Length of expanded query result is {len(expanded_query_result)}."
                    )
                    collected_results.extend(expanded_query_result)
                # TODO: At some point include per query raw output to RabbitMQ
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
        logger.debug(
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
        logger.debug(f"Loaded {len(loaded_definitions)} tracking definition(s).")
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
        return result_definitions
