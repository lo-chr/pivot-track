import logging
import json

from censys.search import SearchClient, CensysHosts
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
        self._api_throttle()

        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.view(document_id=host)
            self._update_last_call()
            return query_result
        except CensysAPIException:
            return None
    
    def query_host_search(self, query: str):
        self._api_throttle()

        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.search(query = query)()
            self._update_last_call()
            return query_result
        except CensysAPIException:
            return None
    
    def _api_throttle(self):
        super()._api_throttle()
    
    def _update_last_call(self):
        super()._update_last_call()