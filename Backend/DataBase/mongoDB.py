from pymongo import AsyncMongoClient
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class MongoDB:
    db=None
    client=None

    @staticmethod
    def connect():
        logger.info("Connecting to MongoDB...")
        try:
           if not MongoDB.client:
               MongoDB.client =AsyncMongoClient(os.getenv("MONGODB_URL"))
               MongoDB.db = MongoDB.client["testdb"]
               logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise Exception(f"Error al conectar a MongoDB: {str(e)}")