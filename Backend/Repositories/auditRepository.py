from Repositories.IRepository import IRepository
from DataBase.mongoDB import MongoDB  
from Model.auditResult import AuditResult

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
    
    async def findLastByAccountUser(self, account_id, user_id):
        result = await self.collection.find_one({"accountID": account_id, "userID": user_id}, sort=[("created_at", -1)])
        if not result:
            return None

        auditResult = AuditResult(
            id=result.get("id") or str(result.get("_id")),
            vulnerabilities=result.get("vulnerabilities", []),
            accountID=result.get("accountID"),
            userID=result.get("userID"),
        )
        created_at = result.get("created_at")
        auditResult.created_at = created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at
        return auditResult

    async def findById(self, audit_id):
        result = await self.collection.find_one({"id": audit_id})
        if not result:
            return None
        
        auditResult = AuditResult(
            id=str(result.get("id")),
            vulnerabilities=result.get("vulnerabilities", []),
            accountID=result.get("accountID"),
            userID=result.get("userID"),
        )
        creaed_at = result.get("created_at")
        auditResult.created_at = creaed_at.isoformat() if hasattr(creaed_at, 'isoformat') else creaed_at
        return auditResult
    
    async def update(self, audit_id, audit_result):
        pass
    
    async def delete(self, audit_id):
        result= await self.collection.delete_one({"_id": audit_id})
        return result.deleted_count > 0
    
    async def deleteByAccountUser(self, accountID, userID):
        result = await self.collection.delete_one({"accountID": accountID, "userID": userID})
        return result.deleted_count > 0