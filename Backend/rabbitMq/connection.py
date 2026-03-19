import aio_pika
import asyncio


class RabbitMQConnection:
  connection=None
  channel=None


  @staticmethod
  async def connect():
    if RabbitMQConnection.connection is None or RabbitMQConnection.channel is None:
        try:
          print("Connecting to RabbitMQ...")
          # connectar a RabbitMQ usando aio_pika
          RabbitMQConnection.connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
          #crear un canal
          RabbitMQConnection.channel = await RabbitMQConnection.connection.channel()
          
        except Exception as e:
          print("Error connecting to RabbitMQ: ", str(e))
          raise e
    return RabbitMQConnection.channel