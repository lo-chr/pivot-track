from datetime import datetime, timezone
from opensearchpy import OpenSearch, OpenSearchException
from common_osint_model import Host, Domain

from .interface import OutputConnector

import logging
import uuid

logger = logging.getLogger(__name__)


class OpenSearchConnector(OutputConnector):
    opensearch_client = None
    config = None
    available = False

    def __init__(self, config):
        try:
            logger.info(
                f"Initializing OpenSearchConnector for connection {config['host']}:{config['port']}"
            )

            self.config = config
            self.opensearch_client = OpenSearch(
                hosts=[{"host": self.config["host"], "port": self.config["port"]}],
                http_compress=False,
                use_ssl=True,
                verify_certs=self.config["verify_certs"],
                http_auth=(self.config["user"], self.config["pass"]),
            )
            self.opensearch_client.ping()
            # Make sure, that there is some kind of index prefix, at least an empty string
            if self.config["index_prefix"] is None:
                self.config["index_prefix"] = ""
            self.available = True
        except KeyError:
            logger.error(
                "Could not initialize OpenSearchConnector with wrong configuration."
            )
        except OpenSearchException as e:
            logger.error(
                f"Failed connecting to OpenSearch instance running on {self.config['host']}:{self.config['port']}. User was {self.config['user']}. OpenSearchException message: {e}"
            )

    # TODO Create function for index settings (i.E. max_docvalue_fields_search)
    def init_pivottrack_query_index(
        self, index_name: str, index_field_properties: dict = None
    ):
        index_name = f"{self.config['index_prefix']}{index_name}"
        index_mappings = {
            "mappings": {
                "properties": {
                    "pivottrack.query_timestamp": {"type": "date"},
                    "pivottrack.query_string": {"type": "keyword"},
                }
            }
        }
        if index_field_properties is not None:
            index_mappings["mappings"]["properties"].update(index_field_properties)

        logger.info(f"Creating Opensearch index {index_name}")
        if not self.opensearch_client.indices.exists(index=index_name):
            response = self.opensearch_client.indices.create(
                index=index_name, body=index_mappings
            )
            logger.debug(f"Creation of Opensearch index {index_name} successful.")
            return response
        else:
            logger.info(f"Opensearch index {index_name} did already exist.")
            return None

    def index_document(self, document: dict, index: str):
        try:
            response = self.opensearch_client.index(
                index=index, body=document, refresh=True
            )
            logger.debug(f"Indexing of document to index {index} successful.")
            return response
        except OpenSearchException as e:
            logger.error(f"OpenSearchException while indexing document for {index}.")
            logger.debug(f"OpenSearchException message: {e}")
            return None

    def query_output(self, query_result, raw=False):
        if not isinstance(query_result, list):
            query_result = [query_result]

        for query_result_element in query_result:
            pivottrack_metadata = {
                "query_timestamp": datetime.now(timezone.utc).isoformat(),
                "query_string": query_result_element.search_term,
            }

            if raw:
                query_result_payload = query_result_element.raw_result
                if (
                    isinstance(query_result_payload, list)
                    and len(query_result_payload) > 1
                ):
                    query_result_payload = {"result": query_result_payload}
                elif (
                    isinstance(query_result_payload, list)
                    and len(query_result_payload) == 1
                ):
                    query_result_payload = query_result_payload[0]

                source = query_result_element.source.__name__.lower().removesuffix(
                    "sourceconnector"
                )
                index_name = f"{self.config['index_prefix']}{source}-{query_result_element.query_command}-raw"
                query_result_payload["pivottrack"] = pivottrack_metadata

                logger.info(
                    f"Write a query result for query {query_result_element.search_term} to index {index_name}."
                )

                self.index_document(document=query_result_payload, index=index_name)
            else:
                com_list = self.query_result_to_com_list(query_result_element)
                for com_result_element in com_list:
                    # TODO this is a little hacky right now, but otherwise it's hard to get this data into opensearch...
                    com_result_element.services = []
                    query_result_payload = com_result_element.flattened_dict
                    query_result_payload["pivottrack"] = pivottrack_metadata
                    index_name = f"{self.config['index_prefix']}com-{query_result_element.query_command}"
                    self.index_document(document=query_result_payload, index=index_name)

    def query_result_to_com_list(self, query_result) -> list:
        logger.debug('Call "_query_result_to_com_list" in parent class')
        return super().query_result_to_com_list(query_result)

    # TODO: Add tracking output interface
    def tracking_output(self, query_result, definition):
        new_elements = []
        pivottrack_metadata = {
            "tracking_timestamp": datetime.now(timezone.utc).isoformat(),
            "tracking_reference": str(uuid.uuid4()),
        }
        pivottrack_tracking_definition = {
            "title": definition.title,
            "uuid": definition.uuid,
            "status": definition.status,
            "created": definition.created.strftime("%Y/%m/%d"),
            "modified": definition.modified.strftime("%Y/%m/%d"),
            "tags": definition.tags,
        }

        com_list = self.query_result_to_com_list(query_result)
        logger.info(
                    f'Preparing OpenSearch tracking output. Got {len(com_list)} COM objects for "{str(definition.uuid)}".'
        )
        for com_result_element in com_list:
            # TODO this is a little hacky right now, but otherwise it's hard to get this data into opensearch...
            com_result_element.services = []
            tracking_result_payload = com_result_element.flattened_dict
            tracking_result_payload["pt_meta"] = pivottrack_metadata
            tracking_result_payload["pt_tracking_definition"] = (
                pivottrack_tracking_definition
            )
            index_name = f"{self.config['index_prefix']}tracking-hosts"

            new_elements.extend(
                self.tracking_get_new_elements(com_result_element, definition)
            )
            self.index_document(document=tracking_result_payload, index=index_name)
        return new_elements

    def tracking_get_new_elements(self, tracked_item, definition):
        # TODO Check for types (Host, etc.)
        new_elements = []
        index_name = f"{self.config['index_prefix']}tracking-hosts"
        if isinstance(tracked_item, Host):
            logger.debug(
                f"Tracked item is Host, searching for IP {tracked_item.ip} and definition UUID."
            )
            body = {
                "query": {
                    "bool": {
                        "filter": [
                            {"match": {"pt_tracking_definition.uuid": definition.uuid}},
                            {"match": {"ip": tracked_item.ip}},
                        ]
                    }
                }
            }
            for domain in tracked_item.domains:
                new_elements.extend(self.tracking_get_new_elements(domain, definition))
        elif isinstance(tracked_item, Domain):
            logger.debug(
                f"Tracked item is Domain, searching for IP {tracked_item.domain} and definition UUID."
            )
            body = {
                "query": {
                    "bool": {
                        "filter": [
                            {"match": {"pt_tracking_definition.uuid": definition.uuid}},
                            {"match": {"domains.domain": tracked_item.domain}},
                        ]
                    }
                }
            }
        try:
            response = self.opensearch_client.search(
                body=body, index=index_name, params={"size": 1}
            )
            logger.info(
                f"Searching {index_name} successful finished successful with {response['hits']['total']} results."
            )
            if response["hits"]["total"]["value"] > 0:
                logger.debug("Tracked item exists in Opensearch Database.")
                return new_elements
            else:
                logger.debug("Tracked item does not exist in Opensearch Database.")
                new_elements.append(tracked_item)
                return new_elements
        except OpenSearchException as e:
            logger.error(
                f"OpenSearchException while searching tracked item document in {index_name}."
            )
            logger.debug(f"OpenSearchException message: {e}")
            return new_elements
