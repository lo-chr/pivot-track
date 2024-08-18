import typer, logging
from typing_extensions import Annotated
from rich.console import Console
from pathlib import Path

from .lib import utils, query, track
from .lib.connectors import OpenSearchConnector, SourceConnector, HostQuery

def init_application(config_path:str = None):
    # Load Config
    config = utils.load_config(config_path)

    # We have to reset logging
    logging.root.handlers = []
    logging.basicConfig(
        level=config['logging']['level'],
        handlers=[
            logging.FileHandler(Path(config['logging']['logfile'])),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(name)s %(levelname)s %(message)s'
    )

    return config

# Create Typer App
app = typer.Typer(help="Pivot Track helps TI analysts to pivot on IoC and to track their research.", pretty_exceptions_show_locals=False)
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.", pretty_exceptions_show_locals=False)
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
    
    config = init_application(config_path)
    source_connector = utils.find_connector_class(HostQuery, name=service)
    try:  
        host_query_result = query.host(config = config,
                                       host = host,
                                       source = source_connector)
        query.output(
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
    
    config = init_application(config_path)
    source_connector = utils.find_connector_class(HostQuery, name=service)
    try:
        generic_query_result, expanded_query_result = query.host_query(config = config, search = search, source = source_connector, expand=expand)
        if not expand:
            query.output(
                config = config,
                query_result = generic_query_result,
                output_format=output,
                raw=raw
            )
        else:
            query.output(
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
    interval: Annotated[int, typer.Option(envvar="PIVOTTRACK_TRACK_INTERVAL")] = 600    # Default to 10 minutes
):
    config = init_application(config_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting automatic tracking service with config file \"{config_path}\" and tracking definitions \"{definition_path}\".")
    
    track.Tracking.execute_tracker(config=config, tracking_definition_path=Path(definition_path), interval = interval)

@app.command("init-opensearch", help="This command helps you initializing opensearch indicies, required for the '--output opensearch' option.")
def init_opensearch(config_path: Annotated[str, typer.Option(envvar="PIVOTTRACK_CONFIG")] = None):
    config = init_application(config_path)
    
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])
    for connector in utils.connector_classes_by_parent(SourceConnector):
        if connector.OPENSEARCH_FIELD_PROPERTIES != None:
            for index_name, index_field_properties in connector.OPENSEARCH_FIELD_PROPERTIES.items():
                opensearch.init_pivottrack_query_index(index_name, index_field_properties)


if __name__ == "__main__":
    app()
