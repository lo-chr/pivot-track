import pika.exceptions
from .interface import OutputConnector

import logging
import pika

logger = logging.getLogger(__name__)


class RabbitMQConnector(OutputConnector):
    rabbitmq_client = None
    config = None

    def __init__(self, config):
        logger.debug("Initializing RabbitMQ for connection")
        self.config = config
        # Test connection
        self.connect()
        self.close()

    def connect(self):
        try:
            # Setup RabbitMQ Client
            credentials = pika.PlainCredentials(
                self.config["username"], self.config["password"]
            )
            parameters = pika.ConnectionParameters(
                self.config["host"],
                self.config["port"],
                self.config["virtual_host"],
                credentials,
            )
            self.rabbitmq_client = pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            logger.error("Error during RabbitMQ connection setup.")

    def close(self):
        logger.debug("Closing RabbitMQ connection")
        self.rabbitmq_client.close()

    @property
    def available(self) -> bool:
        return self.rabbitmq_client.is_open

    def setup_result_channel(self):
        self.connect()
        # Setup RabbitMQ channel
        setup_channel = self.rabbitmq_client.channel()
        setup_channel.exchange_declare(
            exchange=self.config["results_exchange"],
            exchange_type="topic",
            durable=True,
        )
        # Making sure that RabbitMQ queue exists
        setup_channel.queue_declare("pivottrack-results-hosts", durable=True)
        setup_channel.close()
        self.close()

    def query_output(self, query_result, raw: bool = False):
        # Not implemented yet
        return super().query_output(query_result, raw)

    def _definition_track_output(self, tracking_result):
        # TODO: Making this more flexible (do not use hardcoded routing keys)
        logger.info(
            f"Sending results for run {tracking_result.uuid} and definition {tracking_result.definition.uuid} to RabbitMQ"
        )
        result_channel = self.rabbitmq_client.channel()
        result_channel.queue_bind(
            exchange=self.config["results_exchange"],
            queue="pivottrack-results-hosts",
            routing_key="hosts",
        )
        result_channel.basic_publish(
            exchange="pivottrack-results",
            routing_key="hosts",
            body=tracking_result.model_dump_json(
                exclude={"raw_query_results", "query_results"}
            ),
        )
        result_channel.close()

    def definition_track_output(self, tracking_result):
        if not self.available:
            self.connect()
        try:
            self._definition_track_output(tracking_result=tracking_result)
        except pika.exceptions.ConnectionClosed:
            logging.info("Connection was closed, trying to reconnect")
            self.connect()
            self._definition_track_output(tracking_result=tracking_result)
        self.close()
