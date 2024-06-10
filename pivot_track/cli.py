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
        host_query_result['pivottrack'] = {
            "query_timestamp" : datetime.now(timezone.utc).isoformat(),
            "query_string": host
        }
        opensearch.index_document(host_query_result, f"{config['connectors']['opensearch']['shodan_prefix']}-host-raw")
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
        generic_query_result['pivottrack'] = {
            "query_timestamp" : datetime.now(timezone.utc).isoformat(),
            "query_string": query
        }
        opensearch.index_document(generic_query_result, f"{config['connectors']['opensearch']['shodan_prefix']}-generic-raw")
    elif(output == "json"):
        print(utils.printable_result(generic_query_result))

@app.command("init-opensearch")
def init_opensearch():
    config = utils.load_config()
    
    opensearch = OpenSearchConnector(config['connectors']['opensearch'])

    # Setup Shodan Host Raw Index
    shodan_host_raw_index = f"{config['connectors']['opensearch']['shodan_prefix']}-host-raw"
    shodan_host_raw_index_mappings = {
        'mappings' : {
            'properties' : {
                'data.ssl.cert.serial' : {
                    'type' : 'keyword'
                } ,
                'data.ip_str' : {
                    'type' : 'ip'
                } ,
                'ip_str' : {
                    'type' : 'ip'
                } ,
                'pivottrack.query_timestamp' : {
                    'type' : 'date'
                } ,
                'pivottrack.query_string' : {
                    'type' : 'keyword'
                }
            }
        }
    }
    opensearch.create_index(shodan_host_raw_index, shodan_host_raw_index_mappings)

    # Setup Shodan Generic Raw Index
    shodan_generic_raw_index = f"{config['connectors']['opensearch']['shodan_prefix']}-generic-raw"
    shodan_generic_raw_index_mappings = {
        'mappings' : {
            'properties' : {
                'matches.ip_str' : {
                    'type' : 'ip'
                } ,
                'pivottrack.query_timestamp' : {
                    'type' : 'date'
                } ,
                'pivottrack.query_string' : {
                    'type' : 'keyword'
                }
            }
        }
    }
    opensearch.create_index(shodan_generic_raw_index, shodan_generic_raw_index_mappings)

if __name__ == "__main__":
    app()
