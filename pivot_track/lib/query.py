import logging

from .connectors import (
    HostQuery,
    ShodanSourceConnector,
    CensysSourceConnector,
    SourceConnector,
    OpenSearchConnector,
    CLIPrinter,
    JSONPrinter,
)
from common_osint_model import Host

logger = logging.getLogger(__name__)


class QueryResult:
    def __init__(
        self, raw_query_result=None, query_command: str = "", search_term: str = ""
    ):
        self.raw_result = raw_query_result
        self.query_command = query_command
        self.search_term = search_term

    @property
    def com_result(self) -> Host | list[Host]:
        logger.info("Convert raw data to Common OSINT Model.")
        if self.source is ShodanSourceConnector:
            logger.debug("Trying to convert raw Shodan result to Common OSINT Model.")
            return (
                Host.from_shodan(self.raw_result)
                if not self.is_collection
                else [
                    Host.from_shodan(element) for element in self.raw_result["matches"]
                ]
            )
        elif self.source is CensysSourceConnector:
            logger.debug("Trying to convert raw Censys result to Common OSINT Model")
            return (
                Host.from_censys(self.raw_result)
                if not self.is_collection
                else [Host.from_censys(element) for element in self.raw_result]
            )
        else:
            logger.warn(
                f"No Common OSINT Model translation available for {self.source.__name__}. Raising NotImplementedError Exception."
            )
            raise NotImplementedError

    @property
    def source(self) -> SourceConnector:
        # Cases for single host query
        if isinstance(self.raw_result, dict):
            if (
                "data" in self.raw_result.keys()
                and len(self.raw_result["data"]) > 0
                and "_shodan" in self.raw_result["data"][0].keys()
            ):
                return ShodanSourceConnector
            elif (
                "services" in self.raw_result.keys()
                and "last_updated_at" in self.raw_result.keys()
            ):
                return CensysSourceConnector
            # Cases for generic host query
            elif (
                "matches" in self.raw_result.keys()
                and "total" in self.raw_result.keys()
            ):
                return ShodanSourceConnector
            else:
                logger.warn("Could not determine SourceConnector type.")
                print(self.raw_result)
                return None
        elif isinstance(self.raw_result, list):
            return CensysSourceConnector

    @property
    def is_collection(self) -> bool:
        if (
            isinstance(self.raw_result, dict)
            and "matches" in self.raw_result.keys()
            and "total" in self.raw_result.keys()
        ) or isinstance(self.raw_result, list):
            return True
        else:
            return False

    @property
    def element_count(self) -> int:
        if self.is_collection and self.source is ShodanSourceConnector:
            return len(self.raw_result["matches"])
        elif self.is_collection and self.source is CensysSourceConnector:
            return len(self.raw_result)
        elif not self.is_collection:
            return 1  # Case for only one element (no collection)


class Querying:
    def host(host: str, connection: HostQuery) -> QueryResult:
        if (
            connection is not None
            and isinstance(connection, HostQuery)
            and isinstance(host, str)
        ):
            logger.info(
                f'Query for "{host}" with service {connection.__class__.__name__}.'
            )
            return QueryResult(
                connection.query_host(host), query_command="host", search_term=host
            )
        else:
            logger.warn(
                "Did not find connector. Raising NotImplementedError Exception."
            )
            raise NotImplementedError("Did not find HostQuery connector.")

    def host_query(
        search: str, connection: HostQuery, expand=False
    ) -> QueryResult | tuple[QueryResult, QueryResult]:
        if (
            connection is not None
            and isinstance(connection, HostQuery)
            and isinstance(search, str)
        ):
            logger.info(
                f'Search for "{search}" with service {connection.__class__.__name__}.'
            )
            conn_result = connection.query_host_search(search)
            if conn_result is not None:
                query_result = QueryResult(
                    conn_result, query_command="generic", search_term=search
                )
                if not expand:
                    return (query_result, None)
                else:
                    com_elements = (
                        query_result.com_result
                        if query_result.is_collection
                        else [query_result.com_result]
                    )
                    return (
                        query_result,
                        [
                            Querying.host(host=com_element.ip, connection=connection)
                            for com_element in com_elements
                        ],
                    )
            else:
                return (None, None)
        else:
            logger.warn(
                "Did not find connector. Raising NotImplementedError Exception."
            )
            raise NotImplementedError("Did not find HostQuery connector.")

    def output(
        config: dict, query_result: QueryResult, output_format: str = "cli", raw=False
    ):
        if output_format == "cli":
            CLIPrinter().query_output(query_result)

        if output_format == "json":
            JSONPrinter().query_output(query_result, raw=raw)

        if output_format == "opensearch":
            OpenSearchConnector(config["connectors"]["opensearch"]).query_output(
                query_result=query_result, raw=raw
            )
