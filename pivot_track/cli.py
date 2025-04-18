import typer
import logging
import time
from typing_extensions import Annotated
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from pivot_track.lib import utils
from pivot_track.lib.track import TrackingService
from pivot_track.lib.query import Querying


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
service_app = typer.Typer(
    help="For the service",
    pretty_exceptions_show_locals=False,
)
app.add_typer(query_app, name="query")
app.add_typer(service_app, name="service")

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


@service_app.command(
    "publish-definitions",
    help="Publish definitions to Task Queue.",
)
def publish_definitions(
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
    definition_path: Annotated[
        str, typer.Option(envvar="PIVOTTRACK_TRACK_DEFINITIONS")
    ] = None,
    run_once: Annotated[bool, typer.Option(envvar="PIVOTTRACK_TRACK_RUNONCE")] = True,
    interval: Annotated[
        int, typer.Option(envvar="PIVOTTRACK_TRACK_INTERVAL")
    ] = 600,  # Default to 10 minutes
):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))
    init_logging(config)
    tracking_service = TrackingService(config=config)

    running = True
    while running:
        tracking_service.publish_tasks(Path(definition_path))
        if not run_once:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description=f"Waiting for {interval} seconds before next load.",
                    total=None,
                )
                time.sleep(interval)
        else:
            running = False


@service_app.command(
    "subscribe-definitions",
    help="Consume tracking definitions from RabbitMQ task queue and execute them.",
)
def subscribe_definitions(
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = utils.load_config(Path(config_path))
    init_logging(config)
    tracking_service = TrackingService(config)
    tracking_service.subscribe_tasks()


if __name__ == "__main__":
    app()
