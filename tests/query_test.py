import pytest
from .mocks import *
from pivot_track.lib.query import QueryResult, Querying
from pivot_track.lib.connectors import CensysSourceConnector, ShodanSourceConnector, OpenSearchConnector

class TestQueryResult:
    def test_censys_host_source(self):
        query_result = QueryResult(raw_query_result=CENSYS_HOST_JSON, query_command="host", search_term=CENSYS_TEST_HOST)
        assert query_result.source is CensysSourceConnector
    
    def test_censys_host_collection(self):
        query_result = QueryResult(raw_query_result=CENSYS_HOST_JSON, query_command="host", search_term=CENSYS_TEST_HOST)
        assert not query_result.is_collection
    
    def test_censys_host_comresult(self):
        query_result = QueryResult(raw_query_result=CENSYS_HOST_JSON, query_command="host", search_term=CENSYS_TEST_HOST)
        assert query_result.com_result.ip == CENSYS_TEST_HOST
    
    def test_censys_host_elementcount(self):
        query_result = QueryResult(raw_query_result=CENSYS_HOST_JSON, query_command="host", search_term=CENSYS_TEST_HOST)
        assert query_result.element_count == 1
    
    def test_censys_search_source(self):
        query_result = QueryResult(raw_query_result=CENSYS_SEARCH_JSON, query_command="generic", search_term=CENSYS_TEST_SEARCH_QUERY)
        assert query_result.source is CensysSourceConnector
    
    def test_censys_search_collection(self):
        query_result = QueryResult(raw_query_result=CENSYS_SEARCH_JSON, query_command="generic", search_term=CENSYS_TEST_SEARCH_QUERY)
        assert query_result.is_collection
    
    def test_censys_search_comresult(self):
        query_result = QueryResult(raw_query_result=CENSYS_SEARCH_JSON, query_command="generic", search_term=CENSYS_TEST_SEARCH_QUERY)
        ips = {"1.0.0.0", "1.0.0.1"}
        for result in query_result.com_result:
            ips.remove(result.ip)
        assert len(ips) == 0

    def test_censys_search_elementcount(self):
        query_result = QueryResult(raw_query_result=CENSYS_SEARCH_JSON, query_command="generic", search_term=CENSYS_TEST_SEARCH_QUERY)
        assert query_result.element_count == 2
    
    def test_shodan_host_source(self):
        query_result = QueryResult(raw_query_result=SHODAN_HOST_JSON, query_command="host", search_term=SHODAN_TEST_HOST)
        assert query_result.source is ShodanSourceConnector
    
    def test_shodan_host_collection(self):
        query_result = QueryResult(raw_query_result=SHODAN_HOST_JSON, query_command="host", search_term=SHODAN_TEST_HOST)
        assert not query_result.is_collection
    
    def test_shodan_host_comresult(self):
        query_result = QueryResult(raw_query_result=SHODAN_HOST_JSON, query_command="host", search_term=SHODAN_TEST_HOST)
        assert query_result.com_result.ip == SHODAN_TEST_HOST
    
    def test_shodan_host_elementcount(self):
        query_result = QueryResult(raw_query_result=SHODAN_HOST_JSON, query_command="host", search_term=SHODAN_TEST_HOST)
        assert query_result.element_count == 1
    
    def test_shodan_search_source(self):
        query_result = QueryResult(raw_query_result=SHODAN_SEARCH_JSON, query_command="generic", search_term=SHODAN_TEST_SEARCH_QUERY)
        assert query_result.source is ShodanSourceConnector
    
    def test_shodan_search_collection(self):
        query_result = QueryResult(raw_query_result=SHODAN_SEARCH_JSON, query_command="generic", search_term=SHODAN_TEST_SEARCH_QUERY)
        assert query_result.is_collection
    
    def test_shodan_search_comresult(self):
        query_result = QueryResult(raw_query_result=SHODAN_SEARCH_JSON, query_command="generic", search_term=SHODAN_TEST_SEARCH_QUERY)
        ips = {"185.11.246.51", "96.93.212.27"}
        for result in query_result.com_result:
            ips.remove(result.ip)
        assert len(ips) == 0

    def test_shodan_search_elementcount(self):
        query_result = QueryResult(raw_query_result=SHODAN_SEARCH_JSON, query_command="generic", search_term=SHODAN_TEST_SEARCH_QUERY)
        assert query_result.element_count == 2

class TestQuerying:
    def test_host_none_connector(self):
        with pytest.raises(NotImplementedError) as e:
            Querying.host(host = "1.2.4.4", connection = None)
        assert str(e.value) == "Did not find HostQuery connector."
    
    def test_host_wrong_connector_class(self):
        with pytest.raises(NotImplementedError) as e:
            Querying.host(host = "1.2.4.4", connection = OpenSearchConnector)
        assert str(e.value) == "Did not find HostQuery connector."

    def test_host_search_none_connector(self):
        with pytest.raises(NotImplementedError) as e:
            Querying.host_query(search = "blakeks", connection = None)
        assert str(e.value) == "Did not find HostQuery connector."
    
    def test_host__search_wrong_connector_class(self):
        with pytest.raises(NotImplementedError) as e:
            Querying.host_query(search = "blakeks", connection = OpenSearchConnector)
        assert str(e.value) == "Did not find HostQuery connector."
    
    def test_host_shodan(self):
        mock_shodan = MockShodanSourceConnector()
        query_result = Querying.host(host = SHODAN_TEST_HOST, connection = mock_shodan)
        assert type(query_result) == QueryResult
        assert type(query_result.source == ShodanSourceConnector)
        assert query_result.element_count == 1
        assert query_result.com_result.ip == SHODAN_TEST_HOST

    def test_host_search_shodan(self):
        mock_shodan = MockShodanSourceConnector()
        query_result_pt1, query_result_pt2 = Querying.host_query(search = SHODAN_TEST_SEARCH_QUERY, connection = mock_shodan)
        assert type(query_result_pt1) == QueryResult
        assert query_result_pt2 == None
        assert type(query_result_pt1.source == ShodanSourceConnector)
        assert query_result_pt1.element_count == 2
    
    def test_host_censys(self):
        mock_censys = MockCensysSourceConnector()
        query_result_pt1, query_result_pt2 = Querying.host_query(search = CENSYS_TEST_SEARCH_QUERY, connection = mock_censys)
        assert type(query_result_pt1) == QueryResult
        assert query_result_pt2 == None
        assert type(query_result_pt1.source == CensysSourceConnector)
        assert query_result_pt1.element_count == 2