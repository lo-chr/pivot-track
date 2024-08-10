from datetime import datetime, timezone
from opensearchpy import OpenSearch

import logging

logger = logging.getLogger(__name__)

class OpenSearchConnector():
    opensearch_client = None
    config = None

    def __init__(self, config):
        self.config = config
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
            logger.debug(f"Creation of Opensearch index {index_name} sucessful.")
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
        response = self.opensearch_client.index(index = index, body = query_result, refresh=True)
        return response