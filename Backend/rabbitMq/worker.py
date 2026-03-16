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
        try:
            body = json.loads(message.body.decode())
            arn = body["identifier"]
            scan_id = body["scan_id"]
            scan_controller = ScanController(arn)
            account_id = scan_controller.connect()
            
            await collection.update_one({"scan_id": scan_id}, {"$set": {"status": "running"}})
            users = scan_controller.scan_users()
            usersList = JSONSerializer.serialize(users)
            await collection.update_one({"scan_id": scan_id}, {"$set": {"porcentage": 20, "resources.users": usersList}})
            groups = scan_controller.scan_groups()
            groupsList = JSONSerializer.serialize(groups)
            await collection.update_one({"scan_id": scan_id}, {"$set": {"porcentage": 40, "resources.groups": groupsList}})
            roles = scan_controller.scan_roles()
            rolesList = JSONSerializer.serialize(roles)
            await collection.update_one({"scan_id": scan_id}, {"$set": {"porcentage": 60, "resources.roles": rolesList}})
            ec2 = scan_controller.scan_ec2()
            ec2List = JSONSerializer.serialize(ec2)
            await collection.update_one({"scan_id": scan_id}, {"$set": {"porcentage": 80, "resources.ec2": ec2List}})
            buckets = scan_controller.scan_s3()
            bucketsList = JSONSerializer.serialize(buckets)
            await collection.update_one({"scan_id": scan_id}, {"$set": {"porcentage": 100, "status": "completed", "resources.buckets": bucketsList}})
        except Exception as e:
            print(f"Error processing message: {e}")
            await collection.update_one({"scan_id": scan_id}, {"$set": {"status": "error", "errors": str(e)}})

async def main():
    MongoDB.connect()
    await RabbitMQConnection.connect()
    queue = await RabbitMQConnection.channel.declare_queue("scan_queue", durable=True)
    await queue.consume(process_message, no_ack=False)
    await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())

