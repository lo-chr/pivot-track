import json

from rich.table import Table
from rich import print

from common_osint_model import Host
from .connectors import OpenSearchConnector

# TODO Include further COM types (certificates, domains, etc.)
def print_com_host_table(hosts):
    table = Table("IP", "First Seen", "Last Seen", "Source", "Domains", show_lines=True)
    if type(hosts) == Host:
        hosts = [hosts]
    for host in hosts:
        table.add_row(host.ip, str(host.first_seen), str(host.last_seen), host.source, '\n'.join([domain.domain for domain in host.domains]))
    print(table)

def print_json(input, indent=2):
    if(type(input) == dict or type(input) == list):
        if(type(input) == list and len(input) == 1):
            input = input[0]
        printable = json.dumps(input, indent=indent)
    else:
        try:
            loaded = json.loads(input)
            printable =  json.dumps(loaded, indent=indent)
        except ValueError as e:
            # TODO add Error Logging
            printable = ""
    print(printable)

# TODO Consider moving this to opensearch module?
def opensearch_output(opensearch_config:dict, query:str, query_result, index_name):
    if type(query_result) == list and len(query_result) > 1:
        query_result = {
            'result': query_result
        }
    elif type(query_result) == list and len(query_result) == 1:
        query_result = query_result[0]
    OpenSearchConnector(opensearch_config).index_query_result(query = query, query_result = query_result, index = index_name)