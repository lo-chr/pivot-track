import logging, time

from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

class SourceConnector(ABC):
    """Abstract class, providing shared connector capabilities"""
    
    OPENSEARCH_FIELD_PROPERTIES = None

    @abstractmethod
    def _api_throttle(self):
        '''Function to throttle API consumption (through waiting).'''
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
        '''Function for updating last_call variable for API consumption throttling.'''

        logger.debug("Update last_call timestamp for API consumption throttling")
        self.last_call = int(round(datetime.now().timestamp()) * 1000)

class HostQuery(ABC):
    """This class represents a interface for requesting host information at a source."""
    @abstractmethod
    def query_host_search(self, query:str):
        """Abstract function for performing a query for a host search."""
        raise NotImplementedError
    
    @abstractmethod
    def query_host(self, host:str):
        """Abstract function for performing a query for a specific host."""
        raise NotImplementedError

class OutputConnector(ABC):
    """This class represents a parent class for implementing certain types of outputs.
    It is optimized for printing (or storing) data, based on Query results."""
    @abstractmethod
    def query_output(self, query_result, raw=False):
        raise NotImplementedError

    @abstractmethod
    def query_result_to_com_list(self, query_result) -> list:
        result = list()
        if type(query_result) == list:
            logger.debug(f"List of QueryResult elements identified. Length is {len(query_result)}")
            
            for query_result_element in query_result:
                if query_result_element.is_collection:
                    logger.debug("query_result_element is collection.")
                    result.extend(query_result_element.com_result)
                else:
                    result.append(query_result_element.com_result)
        else:
            result = query_result.com_result if query_result.is_collection else [query_result.com_result]
        return result