import logging
from censys.search import SearchClient, CensysHosts
from censys.common.exceptions import CensysAPIException

from .interface import SourceConnector, HostQuery

logger = logging.getLogger(__name__)

class CensysSourceConnector(SourceConnector, HostQuery):
    def __init__(self, config):
        logger.debug("Created new instance of class ShodanSourceConnector")
        self.config = config            # Set Config data
        self.censys_client = SearchClient(api_id = self.config['api_id'], api_secret = self.config['api_secret'])
        # TODO: Set Last Call Timestamp for Throtteling
        #self._update_last_call()

    def query_host(self, host: str):
        # TODO: Introduce API Throttling for Censys
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.view(document_id=host)
            return query_result
        except CensysAPIException:
            return None
    
    def query_host_search(self, query: str):
        # TODO: Introduce API Throttling for Censys
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.search(query = query)
            return query_result.view_all()
        except CensysAPIException:
            return None
    
    def _api_throttle(self):
        super()._api_throttle()
    
    def _update_last_call(self):
        super()._update_last_call()