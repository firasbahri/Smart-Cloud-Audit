from pymongo import AsyncMongoClient
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    db=None
    client=None

    @staticmethod
    def connect():
        logger.info("Connecting to MongoDB...")
        try:
           if not MongoDB.client:
               MongoDB.client =AsyncMongoClient("mongodb://localhost:27017/")
               MongoDB.db = MongoDB.client["testdb"]
               logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise Exception(f"Error al conectar a MongoDB: {str(e)}")