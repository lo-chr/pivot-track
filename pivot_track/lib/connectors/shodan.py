import shodan
import logging

from .interface import SourceConnector, HostQuery

logger = logging.getLogger(__name__)

class ShodanSourceConnector(SourceConnector, HostQuery):
    """Connector for Shodan"""
    OPENSEARCH_FIELD_PROPERTIES = {
        "shodan-host-raw": {   
            'data.ssl.cert.serial' : {
                'type' : 'keyword'
            } ,
            'data.ip_str' : {
                'type' : 'ip'
            } ,
            'ip_str' : {
                'type' : 'ip'
            }
        } ,
        "shodan-generic-raw": {
            'matches.ip_str' : {
                'type' : 'ip'
            }
        }
    }

    def __init__(self, config):
        logger.debug("Created new instance of class ShodanSourceConnector")
        self.config = config            # Set Config data
        self.shodan_client = shodan.Shodan(self.config['api_key'])  # Start Shodan Client
        # Set Last Call Timestamp for Throtteling
        self._update_last_call()

    def query_host_search(self, query:str):
        self._api_throttle()

        try:
            query_result = self.shodan_client.search(query)         # Execute shodan search
            self._update_last_call()
            return query_result
        except shodan.APIError:
            return None
            
    def query_host(self, host:str):
        self._api_throttle()

        try:
            query_result = self.shodan_client.host(host)            # Get shodan host info
            self._update_last_call()
            return query_result
        except shodan.APIError:
            return None

    def _api_throttle(self):
        super()

    def _update_last_call(self):
        super()