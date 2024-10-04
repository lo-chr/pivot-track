import typer
import logging
import time
from typing_extensions import Annotated
from rich.console import Console
from pathlib import Path

from pivot_track.lib import utils
from pivot_track.lib.track import Tracking
from pivot_track.lib.query import Querying
from pivot_track.lib.connectors import (
    OpenSearchConnector,
    SourceConnector,
    FileConnector,
)


def init_logging(config) -> dict:
    # We have to reset logging
    logging.root.handlers = []

    basic_config_handlers = [logging.StreamHandler()]

    logfilepath = Path(config.get("logging").get("logfile"))
    if logfilepath.exists():
        basic_config_handlers.append(logging.FileHandler(logfilepath))
    logging.basicConfig(
        level=config.get("logging").get("level"),
        handlers=basic_config_handlers,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


# Create Typer App
app = typer.Typer(
    help="Pivot Track helps TI analysts to pivot on IoC and to track their research.",
    pretty_exceptions_show_locals=False,
)
query_app = typer.Typer(
    help="This module helps to query different sources of OSINT platforms and databases.",
    pretty_exceptions_show_locals=False,
)
app.add_typer(query_app, name="query")

err_console = Console(stderr=True, style="bold red")


# TODO rename "raw" format to "source" format
@query_app.command(
    "host", help="This command searches for a host on a given OSINT source."
)
def query_host(
    service: str,
    host: str,
    raw: Annotated[bool, typer.Option()] = False,
    output: Annotated[str, typer.Option()] = "cli",
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
):
    if raw and output == "cli":
        err_console.print(
            "This combination does not work. CLI output does only work with normalized data handling."
        )
        exit(-1)

    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))

    init_logging(config)

    # Find source connection and setup for query
    source_connections = utils.init_source_connections(config, filter=service)
    if not len(source_connections) == 1:
        err_console.print(f'Source "{service}" is not available.')
        exit(-1)
    service_connection = source_connections[0]

    try:
        host_query_result = Querying.host(host=host, connection=service_connection)
        Querying.output(
            config=config, query_result=host_query_result, output_format=output, raw=raw
        )

    except NotImplementedError:
        err_console.print(
            'This data source does not exist. Use this command with "--help" for more information.'
        )
        exit(-1)


@query_app.command(
    "generic", help='This command executes a "generic" search on a given OSINT source.'
)
def query_generic(
    service: str,
    search: str,
    raw: Annotated[bool, typer.Option()] = False,
    expand: Annotated[bool, typer.Option()] = True,
    output: Annotated[str, typer.Option()] = "cli",
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
):
    if raw and output == "cli":
        err_console.print(
            "This combination does not work. CLI output does only work with normalized data handling."
        )
        exit(-1)

    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))
    init_logging(config)

    # Find source connection and setup for query
    source_connections = utils.init_source_connections(config, filter=service)
    if not len(source_connections) == 1:
        err_console.print(f'Source "{service}" is not available.')
        exit(-1)
    service_connection = source_connections[0]

    try:
        generic_query_result, expanded_query_result = Querying.host_query(
            search=search, connection=service_connection, expand=expand
        )
        if not expand:
            Querying.output(
                config=config,
                query_result=generic_query_result,
                output_format=output,
                raw=raw,
            )
        else:
            Querying.output(
                config=config,
                query_result=expanded_query_result,
                output_format=output,
                raw=raw,
            )

    except NotImplementedError:
        err_console.print(
            'This data source does not exist. Use this command with "--help" for more information.'
        )
        exit(-1)


@app.command(
    "track",
    help="This command runs Pivot Track in non-interactive mode, to execute queries automatically.",
)
def automatic_track(
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
    definition_path: Annotated[
        str, typer.Option(envvar="PIVOTTRACK_TRACK_DEFINITIONS")
    ] = None,
    run_once: Annotated[bool, typer.Option(envvar="PIVOTTRACK_TRACK_RUNONCE")] = False,
    interval: Annotated[
        int, typer.Option(envvar="PIVOTTRACK_TRACK_INTERVAL")
    ] = 600,  # Default to 10 minutes
):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))
    init_logging(config)
    logger = logging.getLogger(__name__)
    logger.info(
        f'Starting automatic tracking service with config file "{config_path}" and tracking definitions "{definition_path}".'
    )

    source_connections = utils.init_source_connections(config)
    # For now we assume, that there is just one output connection (OpenSearch), this will change soon
    output_connections = utils.init_output_connections(config)[0]
    notification_connection = FileConnector(Path(config.get("tracking_file")))

    init_opensearch(config_path)
    running = True

    while running:
        definitions = Tracking.load_yaml_definition_files(Path(definition_path))
        Tracking.track_definitions(
            definitions=definitions,
            source_connections=source_connections,
            output_connection=output_connections,
            notification_connection=notification_connection,
        )
        if not run_once:
            logger.info(
                f"Done tracking for now. Waiting {interval} seconds for next try."
            )
            time.sleep(interval)
        else:
            running = False
            logger.info("Tracking finished.")


@app.command(
    "init-opensearch",
    help="This command helps you initializing opensearch indicies, required for the '--output opensearch' option.",
)
def init_opensearch(
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))
    init_logging(config)

    opensearch = OpenSearchConnector(config["connectors"]["opensearch"])
    for connector in utils.subclasses_by_parent(SourceConnector):
        if connector.OPENSEARCH_FIELD_PROPERTIES is not None:
            for (
                index_name,
                index_field_properties,
            ) in connector.OPENSEARCH_FIELD_PROPERTIES.items():
                opensearch.init_pivottrack_query_index(
                    index_name, index_field_properties
                )
    opensearch.init_pivottrack_tracking_index()


if __name__ == "__main__":
    app()
