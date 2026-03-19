from rabbitMq.connection import RabbitMQConnection
import aio_pika
import json

class RabbitMQProducer:

    @staticmethod
    async def send_message(scan_id:str,identifier:str):
        message={"scan_id": scan_id, "identifier": identifier}

        # publicar el mensaje en la cola de rabbitmq
        await RabbitMQConnection.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="scan_queue"
        )
        print("Message enviado a RabbitMQ: ", message)