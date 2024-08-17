import json, logging

from rich.table import Table
from rich import print

from common_osint_model import Host

logger = logging.getLogger(__name__)

# TODO Include further COM types (certificates, domains, etc.)
def com_host_table(hosts):
    logger.debug("Printing Host Table")

    table = Table("IP", "First Seen", "Last Seen", "Source", "Domains", show_lines=True)
    if type(hosts) == Host:
        hosts = [hosts]
    for host in hosts:
        table.add_row(host.ip, str(host.first_seen), str(host.last_seen), host.source, '\n'.join([domain.domain for domain in host.domains]))
    print(table)

def json(input, indent=2):
    logger.debug("Printing JSON Output")

    if isinstance(input, list) and len(input) == 1:
        input = input[0]
    
    if isinstance(input, Host):
        printable = json.dumps(input.flattened_dict, indent=indent)
    elif isinstance(input, list) and isinstance(input[0], Host):
        printable = json.dumps([element.flattened_dict for element in input], indent=indent)
    elif(type(input) == dict or type(input) == list):
        printable = json.dumps(input, indent=indent)
    else:
        try:
            loaded = json.loads(input)
            printable =  json.dumps(loaded, indent=indent)
        except ValueError as e:
            # TODO add Error Logging
            printable = ""
    print(printable)