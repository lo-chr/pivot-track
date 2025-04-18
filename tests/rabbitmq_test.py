from pivot_track.lib.connectors import RabbitMQConnector

import uuid


class TestRabbitMQ:
    def test_availability_wrong_config(self):
        rabbitmq_bad_config = {
            "host": str(uuid.uuid4()),
            "port": 1234,
            "verify_certs": False,
            "user": str(uuid.uuid4()),
            "pass": str(uuid.uuid4()),
        }
        rabbitmq_conn1 = RabbitMQConnector(rabbitmq_bad_config)
        assert rabbitmq_conn1.available is False

    def test_availability_empty_config(self):
        rabbitmq_conn2 = RabbitMQConnector(dict())
        assert rabbitmq_conn2.available is False
