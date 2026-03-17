from rabbitMq.connection import RabbitMQConnection
import aio_pika
import json

class RabbitMQProducer:

    @staticmethod
    async def send_message(scan_id:str,identifier:str):
        message={"scan_id": scan_id, "identifier": identifier}
        
        await RabbitMQConnection.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="scan_queue"
        )
        print("Message sent to RabbitMQ: ", message)