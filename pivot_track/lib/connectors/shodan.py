import shodan, logging

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
        logger.info(f"Query for hosts with query \"{query}\"")
        
        self._api_throttle()
        try:
            query_result = self.shodan_client.search(query)         # Execute shodan search
            self._update_last_call()
            return query_result
        except shodan.APIError as e:
            logger.error(f"Shodan APIError while searching for hosts with query \"{query}\". Message {e}")
            return None
            
    def query_host(self, host:str):
        logger.info(f"Query host \"{host}\"")
        
        self._api_throttle()
        try:
            query_result = self.shodan_client.host(host)            # Get shodan host info
            self._update_last_call()
            return query_result
        except shodan.APIError as e:
            logger.error(f"Shodan APIError while querying for host \"{host}\". Message {e}")
            return None

    def _api_throttle(self):
        logger.debug("Call \"_api_throttle()\" in parent class")
        super()._api_throttle()

    def _update_last_call(self):
        logger.debug("Call \"_update_last_call()\" in parent class")
        super()._update_last_call()