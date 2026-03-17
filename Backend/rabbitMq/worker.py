import aio_pika
import asyncio
import json
from rabbitMq.connection import RabbitMQConnection
from Controller.Scan_Controller import ScanController
from Model.scanResult import ScanResult
from mongoDB import MongoDB
from services.JSONSerializer import JSONSerializer


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        collection = MongoDB.db["scans"]
        scan_id = None
        try:
            body = json.loads(message.body.decode())
            arn = body["identifier"]
            scan_id = body["scan_id"]
            scan_controller = ScanController(arn)
            account_id = scan_controller.connect()
            print(f"Connected to AWS account {account_id} for scan {scan_id}")
            
            await collection.update_one({"scan_id": scan_id}, {"$set": {"status": "running"}})
            users = scan_controller.scan_users()
            await collection.update_one({"scan_id": scan_id}, {"$set": {"progress": 20, "resources.users": users}})
            groups = scan_controller.scan_groups()
          
            await collection.update_one({"scan_id": scan_id}, {"$set": {"progress": 40, "resources.groups": groups}})
            roles = scan_controller.scan_roles()
            await collection.update_one({"scan_id": scan_id}, {"$set": {"progress": 60, "resources.roles": roles}})
            ec2 = scan_controller.scan_ec2()
            await collection.update_one({"scan_id": scan_id}, {"$set": {"progress": 80, "resources.ec2": ec2}})
            buckets = scan_controller.scan_s3()
            await collection.update_one({"scan_id": scan_id}, {"$set": {"progress": 100, "status": "completed", "resources.buckets": buckets}})
        except Exception as e:
            print(f"Error processing message: {e}")
            if scan_id is not None:
                await collection.update_one({"scan_id": scan_id}, {"$set": {"status": "error", "errors": str(e)}})

async def main():
    MongoDB.connect()
    await RabbitMQConnection.connect()
    queue = await RabbitMQConnection.channel.declare_queue("scan_queue", durable=True)
    await queue.consume(process_message, no_ack=False)
    await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())

