from abc import ABC, abstractmethod
from datetime import datetime
import time

class SourceConnector(ABC):
    """Abstract class, providing shared connector capabilities"""
    
    OPENSEARCH_FIELD_PROPERTIES = None

    @abstractmethod
    def _api_throttle(self):
        '''Throttle API consumption'''
        # Get current timestamp
        current_timestamp = int(round(datetime.now().timestamp()) * 1000)
        # Calcuate time between calls
        time_between_calls = int(round((1000 / self.config['rate_limit'])))
        # Calc Time to Wait
        time_to_wait = ((self.last_call + time_between_calls) - current_timestamp) / 1000
        # Wait
        if(time_to_wait > 0):
            time.sleep(time_to_wait)
    
    @abstractmethod
    def _update_last_call(self):
        '''Update last_call var for API consumption throttling'''
        self.last_call = int(round(datetime.now().timestamp()) * 1000)

class HostQuery(ABC):
    @abstractmethod
    def query_host_search(self, query:str):
        raise NotImplementedError
    
    def query_host(self, host:str):
        raise NotImplementedError