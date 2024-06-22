import typer
from rich import print
from rich.console import Console
from datetime import datetime, timezone

from .lib import utils, query
from .lib.connectors import ShodanSourceConnector, OpenSearchConnector

app = typer.Typer(help="Pivot track helps TI analysts to pivot on IoC and to track their research.")
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.")
app.add_typer(query_app, name="query")
err_console = Console(stderr=True, style="bold red")

config = utils.load_config()

@query_app.command("host", help="This command searches for a host on a given database.")
def query_host(host: str, service:str="shodan", format="raw", output="json"):
    try:  
        host_query_result = query.host(config = config, host = host, service=service)
        _handle_result_output(query = host, query_result = host_query_result, output = output, index_name = f"{service}-host-raw")
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@query_app.command("generic", help="This command executes a \"generic\" search on a given database.")
def query_generic(service:str, search: str, format="raw", output="json"):
    try:
        generic_query_result = query.host_search(config = config, search = search, service = service)
        _handle_result_output(query = search, query_result = generic_query_result, output = output, index_name = f"{service}-generic-raw")
    except NotImplementedError:
        err_console.print("This data source does not exist. Use this command with \"--help\" for more information.")
        exit(-1)

@app.command("init-opensearch")
def init_opensearch():
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])
    for index_name, index_field_properties in ShodanSourceConnector.OPENSEARCH_FIELD_PROPERTIES.items():
        opensearch.init_pivottrack_query_index(index_name, index_field_properties)

def _handle_result_output(query:str, query_result:dict, output:str, index_name:str):
    if(output == "opensearch"):
        OpenSearchConnector(config['connectors']['opensearch']).index_query_result(query = query, query_result = query_result, index = index_name)
    elif(output == "json"):
        print(utils.printable_result(query_result))


if __name__ == "__main__":
    app()
