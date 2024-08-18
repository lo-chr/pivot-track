import logging

from censys.search import SearchClient
from censys.common.exceptions import CensysAPIException

from .interface import SourceConnector, HostQuery

logger = logging.getLogger(__name__)

class CensysSourceConnector(SourceConnector, HostQuery):

    OPENSEARCH_FIELD_PROPERTIES = {
        "censys-host-raw": {   
            'services.certificate' : {
                'type' : 'keyword'
            } ,
            'services.source_ip' : {
                'type' : 'ip'
            } ,
            'ip' : {
                'type' : 'ip'
            } ,
            'services.port' : {
                'type' : 'integer'
            } ,
            'autonomous_system.asn' : {
                'type' : 'integer'
            } , 
            'last_updated_at' : {
                'type' : 'date_nanos'
            }
        } ,
        "censys-generic-raw": {
            'result.ip' : {
                'type' : 'ip'
            } , 
            'result.last_updated_at' : {
                'type' : 'date_nanos'
            } , 
            'result.services.certificate' : {
                'type' : 'keyword'
            } , 
            'result.services.port' : {
                'type' : 'integer'
            }
        }
    }

    def __init__(self, config):
        logger.debug("Created new instance of class CensysSourceConnector")
        self.config = config            # Set Config data
        self.censys_client = SearchClient(api_id = self.config['api_id'], api_secret = self.config['api_secret'])
        # Set Last Call Timestamp for Throttling
        self._update_last_call()

    def query_host(self, host: str):
        logger.info(f"Query host \"{host}\"")
        
        self._api_throttle()
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.view(document_id=host)
            self._update_last_call()
            return query_result
        except CensysAPIException as e:
            logger.error(f"CensysAPIException while querying for host \"{host}\". Message {e}")
            return None
    
    def query_host_search(self, query: str):
        logger.info(f"Query for hosts with query \"{query}\"")
        
        self._api_throttle()
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.search(query = query)()
            self._update_last_call()
            return query_result
        except CensysAPIException as e:
            logger.error(f"CensysAPIException while searching for hosts with query \"{query}\". Message {e}")
            return None
    
    def _api_throttle(self):
        logger.debug("Call \"_api_throttle()\" in parent class")
        super()._api_throttle()
    
    def _update_last_call(self):
        logger.debug("Call \"_update_last_call()\" in parent class")
        super()._update_last_call()