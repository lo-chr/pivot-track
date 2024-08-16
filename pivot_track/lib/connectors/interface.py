import logging, time

from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

class SourceConnector(ABC):
    """Abstract class, providing shared connector capabilities"""
    
    OPENSEARCH_FIELD_PROPERTIES = None

    @abstractmethod
    def _api_throttle(self):
        '''Throttle API consumption'''

        logger.debug("Throttle API consumption.")
        # Get current timestamp
        current_timestamp = int(round(datetime.now().timestamp()) * 1000)
        # Default to 1 Sec Rate Limit if not set
        rate_limit = self.config['rate_limit'] if self.config['rate_limit'] != None else 1
        # Calcuate time between calls
        time_between_calls = int(round((1000 / rate_limit)))
        # Calc Time to Wait
        time_to_wait = ((self.last_call + time_between_calls) - current_timestamp) / 1000
        # Wait
        if(time_to_wait > 0):
            logger.debug(f"Throttle API consumption. Wait {time_to_wait} Seconds.")
            time.sleep(time_to_wait)
    
    @abstractmethod
    def _update_last_call(self):
        '''Update last_call var for API consumption throttling'''

        logger.debug("Update last_call timestamp for API consumption throttling")
        self.last_call = int(round(datetime.now().timestamp()) * 1000)

class HostQuery(ABC):
    @abstractmethod
    def query_host_search(self, query:str):
        raise NotImplementedError
    
    def query_host(self, host:str):
        raise NotImplementedError