from  pivot_track.lib.connectors import OpenSearchConnector
from pathlib import Path

import pytest
import uuid

class TestOpenSearch:
    def test_availability_wrong_config(self):
        opensearch_bad_config = {
            'host' : str(uuid.uuid4()),
            'port' : 1234,
            'verify_certs' : False,
            'user' : str(uuid.uuid4()),
            'pass' :str(uuid.uuid4())
        }
        opensearch_conn1 = OpenSearchConnector(opensearch_bad_config)
        assert opensearch_conn1.available == False

    def test_availability_empty_config(self):
        opensearch_conn2 = OpenSearchConnector(dict())
        assert opensearch_conn2.available == False