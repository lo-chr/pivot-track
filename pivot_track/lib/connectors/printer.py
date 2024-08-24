import json, logging

from rich.table import Table
from rich import print
from common_osint_model import Host

from .interface import OutputConnector

logger = logging.getLogger(__name__)

class CLIPrinter(OutputConnector):
    """This class is a CLI printer, and resposbile for printint query results to the command line interface."""
    def query_output(self, query_result, raw=False):
        """This method handles generic output requests for query results."""
        if not raw:
            com_results = self.query_result_to_com_list(query_result)
            self.com_host_table(com_results)
        else:
            raise NotImplementedError

    # TODO Include further COM types (certificates, domains, etc.)
    def com_host_table(self, hosts:list):
        """This method translates a list of Common OSINT Model results to a rich framework table."""
        table = Table("IP", "First Seen", "Last Seen", "Source", "Domains", show_lines=True)
        if type(hosts) == Host:
            hosts = [hosts]
        logger.debug(f"Printing Host Table with {len(hosts)} elements.")
        for host in hosts:
            table.add_row(host.ip, str(host.first_seen), str(host.last_seen), host.source, '\n'.join([domain.domain for domain in host.domains]))
        print(table)

    def query_result_to_com_list(self, query_result) -> list:
        """This methdo translates a list of query results to a list of Common OSINT Model items."""
        logger.debug("Call \"_query_result_to_com_list\" in parent class")
        return super().query_result_to_com_list(query_result)

class JSONPrinter(OutputConnector):
    """This class is responsbile for handling JSON output of query results."""
    def query_output(self, query_result, raw=False):
        if not raw:
            com_results = self.query_result_to_com_list(query_result)
            self.json(com_results)
        else:
            if not type(query_result) == list: query_result = [query_result]
            for query_result_element in query_result:
                self.json(query_result_element.raw_result, indent=None)
    
    def json(self, input, indent=2):
        """This method creates JSON-items, based on raw data and Common OSINT Model data """
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
    
    def query_result_to_com_list(self, query_result) -> list:
        """This methdo translates a list of query results to a list of Common OSINT Model items."""
        logger.debug("Call \"_query_result_to_com_list\" in parent class")
        return super().query_result_to_com_list(query_result)