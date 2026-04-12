import logging
from celery_worker.celery_app import celery_app
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from controllers.scan_Controller import ScanController


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(filename)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  


mongo_client = MongoClient(os.getenv("MONGODB_URL"),tls=True,tlsAllowInvalidCertificates=True)
db = mongo_client["testdb"]

@celery_app.task(name="scan_cloud_account")
def scan_cloud_account(scan_id,arn,provider):
    logger.info(f"starting scan for scan_id:{scan_id}")
    scanController= ScanController(arn,provider)
    collection = db["scans"]
    try:
        scanController.connect()
        resources=scanController.find_resources()
        total_resources = len(resources)
        logger.info(f"Total resources found: {total_resources}")
        for i,resource in enumerate(resources):
            logger.info(f"Scanning resource {i+1}/{total_resources}: {resource}")
            results=scanController.scanByResource(resource)
            progress = (i + 1) / total_resources * 100  
            logger.info(f"Scan progress: {progress:.2f}%")
            status="running" if progress < 100 else "completed"
            resource_key="buckets" if resource=="s3" else resource
            collection.update_one({"scan_id":scan_id},{"$set":{"progress":progress,"status":status,f"resources.{resource_key}":results}})

    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        collection.update_one({"scan_id":scan_id},{"$set":{"status":"failed","errors":str(e)}})
