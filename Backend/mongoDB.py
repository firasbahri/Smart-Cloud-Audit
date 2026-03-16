from motor.motor_asyncio import AsyncIOMotorClient

class MongoDB:
    db=None
    client=None

    @staticmethod
    def connect():
        print("Connecting to MongoDB...")
        try:
           if not MongoDB.client:
               MongoDB.client =AsyncIOMotorClient("mongodb://localhost:27017/")
               MongoDB.db = MongoDB.client["testdb"]
               print("Connected to MongoDB")
        except Exception as e:
            raise Exception(f"Error al conectar a MongoDB: {str(e)}")