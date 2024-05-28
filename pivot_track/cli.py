import typer
from rich import print
from rich.console import Console

from .lib import utils
from .lib.connectors.shodan import ShodanConnector

app = typer.Typer(help="Pivot track helps TI analysts to pivot on IoC and to track their research.")
query_app = typer.Typer(help="This module helps to query different sources of OSINT platforms and databases.")
app.add_typer(query_app, name="query")

err_console = Console(stderr=True, style="bold red")

@query_app.command("host", help="This command searches for a host on a given database.")
def query_host(host: str, service:str="shodan", format="raw", printer="json"):
    config = utils.load_config()

    if(service == "shodan"):
        shodan = ShodanConnector(config['connectors']['shodan'])
        host_query_result = shodan.host_query(host, format)

        print(utils.printable_result(host_query_result))
    else:
        err_console.print("Not implemented yet. Use this command with \"--help\" for more information.")
        exit(-1)

@query_app.command("generic", help="This command executes a \"generic\" search on a given database.")
def query_generic(service:str, query: str, format="raw", printer="json"):
    config = utils.load_config()

    if(service == "shodan"):
        shodan = ShodanConnector(config['connectors']['shodan'])
        generic_query_result = shodan.generic_query(query, format)
        print(utils.printable_result(generic_query_result))
    else:
        err_console.print("Not implemented yet. Use this command with \"--help\" for more information.")
        exit(-1)

if __name__ == "__main__":
    app()
