from datetime import datetime, timezone
from opensearchpy import OpenSearch, OpenSearchException
from common_osint_model import Host

from .interface import OutputConnector

import logging

logger = logging.getLogger(__name__)

class OpenSearchConnector(OutputConnector):
    opensearch_client = None
    config = None

    def __init__(self, config):
        logger.info(f"Initializing OpenSearchConnector for connection {config['host']}:{config['port']}")
        
        self.config = config
        try:
            self.opensearch_client = OpenSearch(
                hosts = [{
                    'host' : self.config['host'],
                    'port' : self.config['port']
                }],
                http_compress = False,
                use_ssl = True,
                verify_certs = self.config['verify_certs'],
                http_auth = (self.config['user'], self.config['pass'])
            )
        except OpenSearchException as e:
            logger.error(f"Failed connecting to OpenSearch instance running on {self.config['host']}:{self.config['port']}. User was {self.config['user']}. OpenSearchException message: {e}")
        # Make sure, that there is some kind of index prefix, at least an empty string
        if(self.config['index_prefix'] == None):
            self.config['index_prefix'] = ''

    # TODO Create function for index settings (i.E. max_docvalue_fields_search)
    def init_pivottrack_query_index(self, index_name:str, index_field_properties:dict = None):
        index_name = f"{self.config['index_prefix']}{index_name}"
        index_mappings = {
            'mappings' : {
                'properties' : {
                    'pivottrack.query_timestamp' : {
                        'type' : 'date'
                    } ,
                    'pivottrack.query_string' : {
                        'type' : 'keyword'
                    }
                }
            }
        }
        if(index_field_properties != None):
            index_mappings['mappings']['properties'].update(index_field_properties)

        logger.info(f"Creating Opensearch index {index_name}")
        if(not self.opensearch_client.indices.exists(index=index_name)):
            response = self.opensearch_client.indices.create(index = index_name, body = index_mappings)
            logger.debug(f"Creation of Opensearch index {index_name} successful.")
            return response
        else:
            logger.info(f"Opensearch index {index_name} did already exist.")
            return None
    
    def index_query_result(self, query:str, query_result:dict, index:str):
        index = f"{self.config['index_prefix']}{index}"
        query_result['pivottrack'] = {
            "query_timestamp" : datetime.now(timezone.utc).isoformat(),
            "query_string": query
        }

        logger.info(f"Write a query result for query {query} to index {index} and force refresh.")
        try:
            response = self.opensearch_client.index(index = index, body = query_result, refresh=True)
            logger.debug(f"Indexing of query result for query {query} to index {index} successful.")
            return response
        except OpenSearchException as e:
            logger.error(f"OpenSearchException while indexing query {query} results to index {index}. Message: {e}")
            return None
    
    def query_output(self, query_result, raw=False):
        service = query_result.source.__name__.lower().removesuffix("sourceconnector")
        if raw:
            query_result_payload = query_result.raw_result
            if type(query_result_payload) == list and len(query_result_payload) > 1:
                query_result_payload = {
                    'result': query_result_payload
                }
            elif type(query_result_payload) == list and len(query_result_payload) == 1:
                query_result_payload = query_result_payload[0]
            self.index_query_result(query = query_result.search_term, query_result = query_result_payload, index = f"{service}-{query_result.query_command}-raw")
        else:
            com_results = query_result.com_result
            if isinstance(com_results, Host):
                com_results = [com_results]
            for element in com_results:
                # TODO this is a little hacky right now, but otherwise it's hard to get this data into opensearch...
                element.services = []
                self.index_query_result(query = query_result.search_term, query_result = element.flattened_dict, index = f"com-{query_result.query_command}")