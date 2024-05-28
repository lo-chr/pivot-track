import json
import time
from datetime import datetime

from common_osint_model import Host

import shodan


class ShodanConnector():
    """Connector for Shodan"""

    shodan_client = None
    config = None
    last_call = 0

    def __init__(self, config):
        self.config = config            # Set Config data
        self.shodan_client = shodan.Shodan(self.config['api_key'])  # Start Shodan Client
        # Set Last Call Timestamp for Throtteling
        self.last_call = int(round(datetime.now().timestamp()) * 1000)

    def generic_query(self, query:str, format:str = "source"):
        self.api_throttle()
        query_result = self.shodan_client.search(query)         # Execute shodan search
        self.update_last_call()

        if(format == "raw"):     # return in source format (dict)
            return query_result
        elif(format == "com-flat"): # return in flattend common osint model format (array of dict)
            return [self.host_query(match['ip_str'], "com-flat") for match in query_result["matches"]]
            
    def host_query(self, host:str, format:str = "source"):
        self.api_throttle()
        query_result = self.shodan_client.host(host)            # Get shodan host info
        self.update_last_call()

        if(format == "raw"):     # return in source format (dict)
            return query_result
        elif(format == "com-flat"): # return in flattend common osint model format (dict)
            com_host = Host.from_shodan(query_result)
            return com_host.flattened_dict

    def api_throttle(self):
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
    
    def update_last_call(self):
        '''Update last_call var for API consumption throttling'''
        self.last_call = int(round(datetime.now().timestamp()) * 1000)
