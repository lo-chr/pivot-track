import logging
import time

from abc import ABC, abstractmethod
from typing import List, Union
from datetime import datetime

from common_osint_model import Host, Domain

logger = logging.getLogger(__name__)


class SourceConnector(ABC):
    """Abstract class, providing shared connector capabilities"""

    @abstractmethod
    def _api_throttle(self):
        """Function to throttle API consumption (through waiting)."""
        logger.debug("Throttle API consumption.")
        # Get current timestamp
        current_timestamp = int(round(datetime.now().timestamp()) * 1000)
        # Default to 1 Sec Rate Limit if not set
        rate_limit = (
            self.config["rate_limit"] if self.config["rate_limit"] is not None else 1
        )
        # Calcuate time between calls
        time_between_calls = int(round((1000 / rate_limit)))
        # Calc Time to Wait
        time_to_wait = (
            (self.last_call + time_between_calls) - current_timestamp
        ) / 1000
        # Wait
        if time_to_wait > 0:
            logger.debug(f"Throttle API consumption. Wait {time_to_wait} Seconds.")
            time.sleep(time_to_wait)

    @abstractmethod
    def _update_last_call(self):
        """Function for updating last_call variable for API consumption throttling."""

        logger.debug("Update last_call timestamp for API consumption throttling")
        self.last_call = int(round(datetime.now().timestamp()) * 1000)

    @property
    def short_name(self):
        return self.__class__.__name__.lower().removesuffix("sourceconnector")


class HostQuery(ABC):
    """This class represents a interface for requesting host information at a source."""

    @abstractmethod
    def query_host_search(self, query: str):
        """Abstract function for performing a query for a host search."""
        raise NotImplementedError

    @abstractmethod
    def query_host(self, host: str):
        """Abstract function for performing a query for a specific host."""
        raise NotImplementedError


class OutputConnector(ABC):
    """This class represents a parent class for implementing certain types of outputs.
    It is optimized for printing (or storing) data, based on Query results."""

    @abstractmethod
    def query_output(self, query_result, raw: bool = False):
        raise NotImplementedError

    @abstractmethod
    def definition_track_output(self, query_result):
        raise NotImplementedError


class NotificationConnector(ABC):
    @abstractmethod
    def notify(definition=None, notify_items: List[Union[Host, Domain]] = None):
        raise NotImplementedError
