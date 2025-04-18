import logging

from censys.search import SearchClient
from censys.common.exceptions import CensysAPIException

from .interface import SourceConnector, HostQuery

logger = logging.getLogger(__name__)


class CensysSourceConnector(SourceConnector, HostQuery):
    def __init__(self, config):
        logger.debug("Created new instance of class CensysSourceConnector")
        self.config = config  # Set Config data
        self.censys_client = SearchClient(
            api_id=self.config["api_id"], api_secret=self.config["api_secret"]
        )
        # Set Last Call Timestamp for Throttling
        self._update_last_call()

    def query_host(self, host: str):
        logger.debug(f'Query host "{host}"')

        self._api_throttle()
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.view(document_id=host)
            self._update_last_call()
            return query_result
        except CensysAPIException as e:
            logger.error(
                f'CensysAPIException while querying for host "{host}". Message {e}'
            )
            return None

    def query_host_search(self, query: str):
        logger.debug(f'Query for hosts with query "{query}"')

        self._api_throttle()
        try:
            hosts = self.censys_client.v2.hosts
            query_result = hosts.search(query=query)()
            self._update_last_call()
            return query_result
        except CensysAPIException as e:
            logger.error(
                f'CensysAPIException while searching for hosts with query "{query}". Message {e}'
            )
            return None

    def _api_throttle(self):
        logger.debug('Call "_api_throttle()" in parent class')
        super()._api_throttle()

    def _update_last_call(self):
        logger.debug('Call "_update_last_call()" in parent class')
        super()._update_last_call()
