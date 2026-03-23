from rabbitMq.connection import RabbitMQConnection
import aio_pika
import json
import logging

logger = logging.getLogger(__name__)

class RabbitMQProducer:

    @staticmethod
    async def send_message(scan_id:str,identifier:str,provider:str):
        message={"scan_id": scan_id, "identifier": identifier, "provider": provider}

        # publicar el mensaje en la cola de rabbitmq
        await RabbitMQConnection.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="scan_queue"
        )
        logger.info(f"Message sent to RabbitMQ: {message}")