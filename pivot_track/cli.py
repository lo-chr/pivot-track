import typer
import logging
import time
from typing_extensions import Annotated
from rich.console import Console
from pathlib import Path

from .lib import utils, query, track
from .lib.connectors import OpenSearchConnector, SourceConnector, HostQuery

def init_application(config_path:Path = None) -> dict:
    # We do need a configuration file for now
    # TODO: Rework configuration, so that it also works with ENVIRONMENT Variables
    if config_path is None:
        return None
    # Load Config
    config = utils.load_config(config_path)

    # We have to reset logging
    logging.root.handlers = []

    basic_config_handlers = [logging.StreamHandler()]

    logfilepath = Path(config.get('logging').get('logfile'))
    if logfilepath.exists():
        basic_config_handlers.append(logging.FileHandler(logfilepath))
    logging.basicConfig(
        level=config.get('logging').get('level'),
        handlers=basic_config_handlers,
        format='%(asctime)s %(name)s %(levelname)s %(message)s'
    )

    return config

# Create Typer App
#app = typer.Typer(help="Pivot Track helps TI analysts to pivot on IoC and to track their research.", pretty_exceptions_show_locals=False)
#query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.", pretty_exceptions_show_locals=False)
app = typer.Typer(help="Pivot Track helps TI analysts to pivot on IoC and to track their research.", pretty_exceptions_show_locals=True)
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.", pretty_exceptions_show_locals=True)
app.add_typer(query_app, name="query")

err_console = Console(stderr=True, style="bold red")

# TODO rename "raw" format to "source" format
@query_app.command("host", help="This command searches for a host on a given OSINT source.")
def query_host(service:str,
               host: str,
               raw : Annotated[bool, typer.Option()]=False,
               output: Annotated[str, typer.Option()] = "cli",
               config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None):
    if(raw and output == "cli"):
        err_console.print("This combination does not work. CLI output does only work with normalized data handling.")
        exit(-1)
    
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = init_application(Path(config_path))
    # TODO use util.init_source_connection()
    source_connector = utils.subclass_by_parent_find(HostQuery, search_string=service)
    connection_config = config['connectors'][source_connector.__name__.lower().removesuffix("sourceconnector")]
    try:  
        host_query_result = query.Querying.host(host = host,
                                                connection = source_connector(connection_config))
        query.Querying.output(
            config = config,
            query_result = host_query_result,
            output_format = output,
            raw = raw
        )
        
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@query_app.command("generic", help="This command executes a \"generic\" search on a given OSINT source.")
def query_generic(service:str,
                  search: str,
                  raw : Annotated[bool, typer.Option()]=False,
                  expand : Annotated[bool, typer.Option()]=True,
                  output: Annotated[str, typer.Option()] = "cli",
                  config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None
                  ):
    if(raw and output == "cli"):
        err_console.print("This combination does not work. CLI output does only work with normalized data handling.")
        exit(-1)
    
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = init_application(Path(config_path))
    source_connector = utils.subclass_by_parent_find(HostQuery, search_string=service)
    connection_config = config['connectors'][source_connector.__name__.lower().removesuffix("sourceconnector")]
    try:
        generic_query_result, expanded_query_result = query.Querying.host_query(search = search, connection = source_connector(connection_config), expand=expand)
        if not expand:
            query.Querying.output(
                config = config,
                query_result = generic_query_result,
                output_format=output,
                raw=raw
            )
        else:
            query.Querying.output(
                config = config,
                query_result = expanded_query_result,
                output_format=output,
                raw = raw
            )
    
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@app.command("track", help="This command runs pivottrack in non-interactive mode, to execute queries automatically.")
def automatic_track(
    config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None,
    definition_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_TRACK_DEFINITIONS")] = None,
    run_once: Annotated[bool, typer.Option(envvar="PIVOTTRACK_TRACK_RUNONCE")] = False,
    interval: Annotated[int, typer.Option(envvar="PIVOTTRACK_TRACK_INTERVAL")] = 600    # Default to 10 minutes
):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = init_application(Path(config_path))
    logger = logging.getLogger(__name__)
    logger.info(f"Starting automatic tracking service with config file \"{config_path}\" and tracking definitions \"{definition_path}\".")
    
    source_connections = utils.init_source_connections(config)
    # For now we assume, that there is just one output connection (OpenSearch), this will change soon
    output_connections = utils.init_output_connections(config)[0]

    running = True
    
    while running:
        definitions = track.Tracking.load_yaml_definition_files(Path(definition_path))
        track.Tracking.track_definitions(definitions=definitions, source_connections=source_connections, output_connection=output_connections)
        if not run_once:
            logger.info(f"Done tracking for now. Waiting {interval} seconds for next try.")
            time.sleep(interval)
        else:
            running = False
            logger.info("Tracking finished.")


@app.command("init-opensearch", help="This command helps you initializing opensearch indicies, required for the '--output opensearch' option.")
def init_opensearch(config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None):
    if config_path is None:
        err_console.print("Configuration file must not be None.")
        exit(-1)

    config = init_application(Path(config_path))
    
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])
    for connector in utils.subclasses_by_parent(SourceConnector):
        if connector.OPENSEARCH_FIELD_PROPERTIES is not None:
            for index_name, index_field_properties in connector.OPENSEARCH_FIELD_PROPERTIES.items():
                opensearch.init_pivottrack_query_index(index_name, index_field_properties)


if __name__ == "__main__":
    app()
