import typer
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from datetime import datetime, timezone

from common_osint_model import Host

from .lib import utils, query
from .lib.connectors import OpenSearchConnector, SourceConnector

from .lib import output_util

app = typer.Typer(help="Pivot Track helps TI analysts to pivot on IoC and to track their research.")
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.")
app.add_typer(query_app, name="query")
err_console = Console(stderr=True, style="bold red")

# TODO Introduce Config Loading via Environment var
config = utils.load_config()

# TODO rename "raw" format to "source" format
@query_app.command("host", help="This command searches for a host on a given OSINT source.")
def query_host(service:str,
               host: str,
               raw : Annotated[bool, typer.Option()]=False,
               output: Annotated[str, typer.Option()] = "cli"):
    if(raw and output == "cli"):
        err_console.print("This combination does not work. CLI output does only work with normalized data handling.")
        exit(-1)
    try:  
        host_query_result = query.host(config = config,
                                       host = host,
                                       service=service,
                                       raw=raw)
        query.output(config = config,
                     query_result = host_query_result,
                     output_format=output,
                     query = host,
                     raw = raw,
                     service = service,
                     query_command = "host")
        
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@query_app.command("generic", help="This command executes a \"generic\" search on a given OSINT source.")
def query_generic(service:str,
                  search: str,
                  raw : Annotated[bool, typer.Option()]=False,
                  output: Annotated[str, typer.Option()] = "cli",
                  refine: Annotated[bool, typer.Option()]=False):
    if(raw and output == "cli"):
        err_console.print("This combination does not work. CLI output does only work with normalized data handling.")
        exit(-1)
    try:
        generic_query_result = query.host_search(config = config, search = search, service = service, raw=raw, refine=refine)
        query.output(config = config,
                     query_result = generic_query_result,
                     output_format=output,
                     query = search,
                     raw = raw,
                     service = service,
                     query_command = "generic")
    
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@app.command("init-opensearch", help="This command helps you initializing opensearch indicies, required for the '--output opensearch' option.")
def init_opensearch():
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])

    for connector in utils.connector_classes_by_parent(SourceConnector):
        if connector.OPENSEARCH_FIELD_PROPERTIES != None:
            for index_name, index_field_properties in connector.OPENSEARCH_FIELD_PROPERTIES.items():
                opensearch.init_pivottrack_query_index(index_name, index_field_properties)


if __name__ == "__main__":
    app()
