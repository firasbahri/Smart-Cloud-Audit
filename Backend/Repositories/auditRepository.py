from Repositories.IRepository import IRepository
from DataBase.mongoDB import MongoDB  

class AuditRepository(IRepository):
    def __init__(self):
        self.collection = MongoDB.db["audits"]

    async def create(self, audit_result):
        audit_dict = {}
        for key, value in audit_result.__dict__.items():
            if value is not None:
                audit_dict[key] = value
        result = await self.collection.insert_one(audit_dict)
        return str(result.inserted_id)

    async def findById(self, audit_id):
        pass
    
    async def update(self, audit_id, audit_result):
        pass
    
    async def delete(self, audit_id):
        pass