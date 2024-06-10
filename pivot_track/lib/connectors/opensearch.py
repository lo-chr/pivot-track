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

    def create_index(self, index_name, index_body = None ):
        logger.info(f"Creating Opensearch index {index_name}")
        if(not self.opensearch_client.indices.exists(index=index_name)):
            response = self.opensearch_client.indices.create(index = index_name, body = index_body)
            logger.debug(f"Creation of Opensearch index {index_name} sucessful.")
            return response
        else:
            logger.info(f"Opensearch index {index_name} did already exist.")
            return None
    
    def index_document(self, content:str, index:str):
        response = self.opensearch_client.index(index = index, body = content, refresh=True)
        return response