import pytest
from .mocks import MockCensysSourceConnector, MockShodanSourceConnector, MockOpenSearchConnector
from pydantic import ValidationError
import pathlib
from pivot_track.lib.track import TrackingDefinition, TrackingQuery, Tracking
from uuid import uuid4

class TestTrackingDefinition:
    def test_minimal_definition_dict(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }

        query_dict2 = {
            'source' : 'censys',
            'command' : 'host',
            'query' : 'example query'
        }

        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : [query_dict1, query_dict2]
        }

        definition = TrackingDefinition.from_dict(definition = definition_dict)
        assert isinstance(definition, TrackingDefinition)
        assert str(definition.uuid) == definition_dict['uuid']
        assert TrackingQuery.from_dict(query_dict1) in definition.queries
        assert TrackingQuery.from_dict(query_dict2) in definition.queries
        assert 'censys' in definition.sources
        assert 'shodan' in definition.sources

    def test_none_uuid_definition_dict(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }
        definition_dict = {
            'query' : [query_dict1]
        }

        with pytest.raises(ValidationError) as e:
            TrackingDefinition.from_dict(definition = definition_dict)
        assert "UUID input should be a string, bytes or UUID object" in str(e.value)
    
    def test_no_query_list_definition_dict(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }
        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : query_dict1
        }

        with pytest.raises(ValidationError) as e:
            TrackingDefinition.from_dict(definition = definition_dict)
        assert "Input should be a valid list" in str(e.value)
        
    def test_none_query_definition_dict(self):
        definition_dict = {
            'uuid' : str(uuid4())
        }

        with pytest.raises(ValidationError) as e:
            TrackingDefinition.from_dict(definition = definition_dict)
        assert "Input should be a valid list" in str(e.value)

    def test_full_definition_dict(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }
        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : [query_dict1],
            'title' : 'this is an example title',
            'status' : 'testing',
            'description' : 'this is an example description',
            'author' : 'Ex Ample',
            'created' : '2024/09/29',
            'modified' : '2024/09/29',
            'tags' : ['test', 'unit', 'example'],
            'output' : 'example'
        }

        definition = TrackingDefinition.from_dict(definition = definition_dict)
        assert isinstance(definition, TrackingDefinition)
        assert str(definition.uuid) == definition_dict['uuid']
        assert str(definition.title) == definition_dict['title']
        assert str(definition.status) == definition_dict['status']
        assert str(definition.description) == definition_dict['description']
        assert str(definition.author) == definition_dict['author']
        assert definition.created.strftime("%Y/%m/%d") == definition_dict['created']
        assert definition.modified.strftime("%Y/%m/%d") == definition_dict['modified']
        assert definition.tags == definition_dict['tags']
        assert str(definition.output) == definition_dict['output']
        assert TrackingQuery.from_dict(query_dict1) in definition.queries
    
    def test_full_definition_yaml(self):
        definition_yaml = '''title: Default cobaltstrike servers
uuid: af8bda70-0714-4ecd-a275-7dcabaac2bf9
status: test
description: This query adresses searches for Cobaltstrike servers in default configuration
author: Christoph Lobmeyer
created: 2024/09/04
modified: 2024/09/04
tags:
  - tlp.white
  - cobaltstrike
query:
  - source: censys
    command: host_generic
    query: services.tls.certificate.parsed.serial_number:146473198
    expand: False
  - source: shodan
    command: host_generic
    query: ssl.cert.serial:146473198
    expand: True
output: opensearch'''
        definition = TrackingDefinition.from_yaml(definition = definition_yaml)
        assert isinstance(definition, TrackingDefinition)
        assert str(definition.uuid) == 'af8bda70-0714-4ecd-a275-7dcabaac2bf9'
        assert str(definition.title) == 'Default cobaltstrike servers'
        assert definition.created.strftime("%Y/%m/%d") == '2024/09/04'
        assert definition.modified.strftime("%Y/%m/%d") == '2024/09/04'
        assert len(definition.queries_by_source('censys')) == 1
        assert len(definition.queries_by_source('shodan')) == 1
        assert len(definition.queries_by_command('host_generic')) == 2
        assert type(definition.queries_by_source('censys')) == type(definition.queries)
        assert type(definition.queries_by_source('censys')) == type(definition.queries)
        assert len(definition.queries_by_filter(command='host_generic', source = 'censys')) == 1
        assert len(definition.queries_by_filter(command='host_generic', source = 'shodan')) == 1
        assert len(definition.queries_by_filter(command='host_generic', source = 'totalvirus')) == 0
        assert len(definition.queries_by_filter(command='host', source = 'shodan')) == 0


class TestTrackingQuery:
    def test_minimal_query_dict(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }
        tracking_query1 = TrackingQuery.from_dict(query_dict1)
        assert isinstance(tracking_query1, TrackingQuery)
        assert tracking_query1.source == query_dict1['source']
        assert tracking_query1.command == query_dict1['command']
        assert tracking_query1.query == query_dict1['query']
        assert tracking_query1.expand == False

        query_dict2 = {
            'source' : 'censys',
            'command' : 'host',
            'query' : 'example query'
        }
        tracking_query2 = TrackingQuery.from_dict(query_dict2)
        assert isinstance(tracking_query2, TrackingQuery)
        assert tracking_query2.source == query_dict2['source']
        assert tracking_query2.command == query_dict2['command']
        assert tracking_query2.query == query_dict2['query']
        assert tracking_query2.expand == False

        query_dict3 = {
            'source' : 'censys',
            'command' : 'host',
            'query' : 'example query',
            'expand' : True,
        }
        tracking_query3 = TrackingQuery.from_dict(query_dict3)
        assert isinstance(tracking_query3, TrackingQuery)
        assert tracking_query3.source == query_dict3['source']
        assert tracking_query3.command == query_dict3['command']
        assert tracking_query3.query == query_dict3['query']
        assert tracking_query3.expand == query_dict3['expand']

    def test_wrong_source_query_dict(self):
        query_dict1 = {
            'source' : 'totalvirus',
            'command' : 'host_generic',
            'query' : 'example query'
        }

        query_dict2 = {
            'source' : False,
            'command' : 'host_generic',
            'query' : 'example query'
        }
        
        with pytest.raises(ValidationError) as e:
            TrackingQuery.from_dict(query_dict1)
        assert "Input should be 'censys' or 'shodan'" in str(e.value)

        with pytest.raises(ValidationError) as e:
            TrackingQuery.from_dict(query_dict2)
        assert "Input should be 'censys' or 'shodan'" in str(e.value)
    
    def test_wrong_command_query_dict(self):
        query_dict1 = {
            'source' : 'censys',
            'command' : 'example_stuff',
            'query' : 'example query'
        }

        query_dict2 = {
            'source' : 'shodan',
            'command' : None,
            'query' : 'example query'
        }
        
        with pytest.raises(ValidationError) as e:
            TrackingQuery.from_dict(query_dict1)
        assert "Input should be 'host_generic' or 'host'" in str(e.value)

        with pytest.raises(ValidationError) as e:
            TrackingQuery.from_dict(query_dict2)
        assert "Input should be 'host_generic' or 'host'" in str(e.value)


class TestTracking:
    
    @pytest.fixture
    def yaml_load_mocker(self, mocker):
        definition_yaml = '''title: Default cobaltstrike servers
uuid: af8bda70-0714-4ecd-a275-7dcabaac2bf9
status: test
description: This query adresses searches for Cobaltstrike servers in default configuration
author: Christoph Lobmeyer
created: 2024/09/04
modified: 2024/09/04
tags:
  - tlp.white
  - cobaltstrike
query:
  - source: censys
    command: host_generic
    query: services.tls.certificate.parsed.serial_number:146473198
    expand: False
  - source: shodan
    command: host_generic
    query: ssl.cert.serial:146473198
    expand: True
output: opensearch'''
        mocked_yaml_definition = mocker.mock_open(read_data=definition_yaml)
        mocker.patch("pivot_track.lib.track.open", mocked_yaml_definition)
        mocker.patch("pathlib.Path.exists", return_value = True)
        mocker.patch("pathlib.Path.glob", return_value = [pathlib.Path("/path/to/file")])
        
    def test_load_yaml_definitions(self, yaml_load_mocker):
        definitions = Tracking.load_yaml_definition_files(pathlib.Path("."))
        assert len(definitions) == 1
    
    def test_load_yaml_definitions_wrong_path(self):
        with pytest.raises(AttributeError) as e:
            definitions = Tracking.load_yaml_definition_files(pathlib.Path(str(uuid4())))
        assert "Could not load tracking definitions." in str(e.value)
    
    def test_load_definitions_legacy(self, yaml_load_mocker):
        loaded_definitions, loaded_definition_by_source = Tracking.load_definitions(pathlib.Path("."))
        assert len(loaded_definitions) == 1
        assert not loaded_definition_by_source.get('shodan') == None
        assert not loaded_definition_by_source.get('censys') == None
        assert len(loaded_definition_by_source.get('shodan')) == 1
        assert len(loaded_definition_by_source.get('censys')) == 1
        assert loaded_definition_by_source.get('test') == None

    def test_execute_tracking_queries(self):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }

        query_dict2 = {
            'source' : 'censys',
            'command' : 'host',
            'query' : 'example query'
        }

        queries = [TrackingQuery.from_dict(query_dict1), TrackingQuery.from_dict(query_dict2)]
        mock_shodan = MockShodanSourceConnector()
        query_results = Tracking.execute_tracking_queries(queries, mock_shodan)
        assert len(query_results) == 2
    
    def test_execute_tracking_queries_opensearch(self, mocker):
        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }

        query_dict2 = {
            'source' : 'censys',
            'command' : 'host',
            'query' : 'example query'
        }

        queries = [TrackingQuery.from_dict(query_dict1), TrackingQuery.from_dict(query_dict2)]
        mock_shodan = MockShodanSourceConnector()
        mock_opensearch = MockOpenSearchConnector()
        spy = mocker.spy(mock_opensearch, 'query_output')
        query_results = Tracking.execute_tracking_queries(queries, mock_shodan, mock_opensearch)
        assert len(query_results) == 2
        assert spy.call_count == 2

    def test_track_source(self, mocker):
        definition_yaml = '''title: Default cobaltstrike servers
uuid: af8bda70-0714-4ecd-a275-7dcabaac2bf9
status: test
description: This query adresses searches for Cobaltstrike servers in default configuration
author: Christoph Lobmeyer
created: 2024/09/04
modified: 2024/09/04
tags:
  - tlp.white
  - cobaltstrike
query:
  - source: censys
    command: host_generic
    query: services.tls.certificate.parsed.serial_number:146473198
    expand: False
  - source: shodan
    command: host_generic
    query: ssl.cert.serial:146473198
    expand: True
output: opensearch'''
        definition = TrackingDefinition.from_yaml(definition_yaml)

        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host',
            'query' : 'example query'
        }

        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : [query_dict1]
        }

        definition2 = TrackingDefinition.from_dict(definition_dict)
        
        mock_shodan = MockShodanSourceConnector()
        mock_censys = MockCensysSourceConnector()
        mock_opensearch = MockOpenSearchConnector()
        spy_opensearch_query_output = mocker.spy(mock_opensearch, 'query_output')
        spy_opensearch_tracking_output = mocker.spy(mock_opensearch, 'tracking_output')
        spy_shodan = mocker.spy(mock_shodan, 'query_host_search')
        spy_censys = mocker.spy(mock_censys, 'query_host_search')
        
        Tracking.track_definitions_for_source([definition], mock_shodan, mock_opensearch)
        Tracking.track_definitions_for_source([definition, definition2], mock_censys, mock_opensearch)
        assert spy_shodan.call_count == 1
        assert spy_censys.call_count == 1
        assert spy_opensearch_query_output.call_count == 2
        assert spy_opensearch_tracking_output.call_count == 3
    
    def test_definitions_by_source(self):
        definition_yaml = '''title: Default cobaltstrike servers
uuid: af8bda70-0714-4ecd-a275-7dcabaac2bf9
status: test
description: This query adresses searches for Cobaltstrike servers in default configuration
author: Christoph Lobmeyer
created: 2024/09/04
modified: 2024/09/04
tags:
  - tlp.white
  - cobaltstrike
query:
  - source: censys
    command: host_generic
    query: services.tls.certificate.parsed.serial_number:146473198
    expand: False
  - source: shodan
    command: host_generic
    query: ssl.cert.serial:146473198
    expand: True
output: opensearch'''
        definition = TrackingDefinition.from_yaml(definition_yaml)

        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host',
            'query' : 'example query'
        }

        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : [query_dict1]
        }

        definition2 = TrackingDefinition.from_dict(definition_dict)
        definitions = [definition, definition2]
        mock_shodan = MockShodanSourceConnector()

        shodan_definitions = Tracking.definitions_by_source(definitions, mock_shodan.short_name)
        censys_definitions = Tracking.definitions_by_source(definitions, 'censys')
        wrong_definitions = Tracking.definitions_by_source(definitions, 'wrong')
        assert len(shodan_definitions) == 2
        assert len(censys_definitions) == 1
        assert len(wrong_definitions) == 0
    
    def test_track_definitions(self, mocker):
        definition_yaml = '''title: Default cobaltstrike servers
uuid: af8bda70-0714-4ecd-a275-7dcabaac2bf9
status: test
description: This query adresses searches for Cobaltstrike servers in default configuration
author: Christoph Lobmeyer
created: 2024/09/04
modified: 2024/09/04
tags:
  - tlp.white
  - cobaltstrike
query:
  - source: censys
    command: host_generic
    query: services.tls.certificate.parsed.serial_number:146473198
    expand: False
  - source: shodan
    command: host_generic
    query: ssl.cert.serial:146473198
    expand: True
output: opensearch'''
        definition = TrackingDefinition.from_yaml(definition_yaml)

        query_dict1 = {
            'source' : 'shodan',
            'command' : 'host_generic',
            'query' : 'example query'
        }

        definition_dict = {
            'uuid' : str(uuid4()),
            'query' : [query_dict1]
        }

        definition2 = TrackingDefinition.from_dict(definition_dict)
        
        mock_shodan = MockShodanSourceConnector()
        mock_censys = MockCensysSourceConnector()
        mock_opensearch = MockOpenSearchConnector()
        spy_opensearch_query_output = mocker.spy(mock_opensearch, 'query_output')
        spy_opensearch_tracking_output = mocker.spy(mock_opensearch, 'tracking_output')
        spy_shodan = mocker.spy(mock_shodan, 'query_host_search')
        spy_censys = mocker.spy(mock_censys, 'query_host_search')
        
        Tracking.track_definitions([definition, definition2], [mock_shodan, mock_censys], mock_opensearch)
        assert spy_shodan.call_count == 2
        assert spy_censys.call_count == 1
        assert spy_opensearch_query_output.call_count == 3
        assert spy_opensearch_tracking_output.call_count == 3