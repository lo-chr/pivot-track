import typer
from rich import print
from rich.console import Console
from datetime import datetime, timezone

from .lib import utils
from .lib.connectors.shodan import ShodanConnector
from .lib.connectors.opensearch import OpenSearchConnector

app = typer.Typer(help="Pivot track helps TI analysts to pivot on IoC and to track their research.")
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.")
app.add_typer(query_app, name="query")

err_console = Console(stderr=True, style="bold red")

@query_app.command("host", help="This command searches for a host on a given database.")
def query_host(host: str, service:str="shodan", format="raw", output="json"):
    config = utils.load_config()

    if(service == "shodan"):
        shodan = ShodanConnector(config['connectors']['shodan'])
        host_query_result = shodan.host_query(host, format)
    else:
        err_console.print("Not implemented yet. Use this command with \"--help\" for more information.")
        exit(-1)
   
    if(output == "opensearch"):
        opensearch = OpenSearchConnector(config['connectors']['opensearch'])
        opensearch.index_query_result(query = host, query_result = host_query_result, index = "shodan-host-raw")
    elif(output == "json"):
        print(utils.printable_result(host_query_result))

@query_app.command("generic", help="This command executes a \"generic\" search on a given database.")
def query_generic(service:str, query: str, format="raw", output="json"):
    config = utils.load_config()

    if(service == "shodan"):
        shodan = ShodanConnector(config['connectors']['shodan'])
        generic_query_result = shodan.generic_query(query, format)
    else:
        err_console.print("Not implemented yet. Use this command with \"--help\" for more information.")
        exit(-1)

    if(output == "opensearch"):
        opensearch = OpenSearchConnector(config['connectors']['opensearch'])
        opensearch.index_query_result(query = query, query_result = generic_query_result, index = "shodan-generic-raw")
    elif(output == "json"):
        print(utils.printable_result(generic_query_result))

@app.command("init-opensearch")
def init_opensearch():
    config = utils.load_config()
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])

    for index_name, index_field_properties in ShodanConnector.OPENSEARCH_FIELD_PROPERTIES.items():
        opensearch.init_pivottrack_query_index(index_name, index_field_properties)

if __name__ == "__main__":
    app()
