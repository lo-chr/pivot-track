import pytest
from pydantic import ValidationError
from pivot_track.lib.track import TrackingDefinition, TrackingQuery
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
        assert TrackingQuery.from_dict(query_dict1) in definition.query
        assert TrackingQuery.from_dict(query_dict2) in definition.query

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
        assert TrackingQuery.from_dict(query_dict1) in definition.query
    
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


