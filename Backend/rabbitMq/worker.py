import aio_pika
import asyncio
import json
from rabbitMq.connection import RabbitMQConnection
from Controller.Scan_Controller import ScanController
from Model.scanResult import ScanResult
from mongoDB import MongoDB
from services.JSONSerializer import JSONSerializer
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



async def process_message(message: aio_pika.IncomingMessage):
    logger.info(f"Received message: {message.body.decode()}")
    async with message.process():
        collection = MongoDB.db["scans"]
        scan_id = None
        try:
            body = json.loads(message.body.decode())
            arn = body["identifier"]
            scan_id = body["scan_id"]
            provider = body["provider"] 
            scan_controller = ScanController(arn, provider)
            account_id = scan_controller.connect()
            logger.info(f"Connected to {provider} account {account_id} for scan {scan_id}")
            resources = scan_controller.find_resources()
            total_findings = len(resources)
            logger.info(f"Found {total_findings} resources to scan for scan {scan_id}")

            for index, resource in enumerate(resources):
                results = scan_controller.scanByResource(resource)
                progress = int(((index + 1) / total_findings) * 100) if total_findings else 100
                status = "running" if progress < 100 else "completed"
                resource_key = "buckets" if resource == "s3" else resource

                await collection.update_one(
                    {"scan_id": scan_id},
                    {
                        "$set": {
                            "status": status,
                            "progress": progress,
                            f"resources.{resource_key}": results,
                        }
                    },
                )

                logger.info(f"Finished scanning resource {resource} for scan {scan_id}")
           
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if scan_id is not None:
                await collection.update_one({"scan_id": scan_id}, {"$set": {"status": "error", "errors": str(e)}})

async def main():
    MongoDB.connect()
    #connectar a rabbitMQ 
    await RabbitMQConnection.connect()
    #sacar la cola de rabbitMQ
    queue = await RabbitMQConnection.channel.declare_queue("scan_queue", durable=True)
    #consumir mensajes de la cola
    await queue.consume(process_message, no_ack=False)
    await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())

