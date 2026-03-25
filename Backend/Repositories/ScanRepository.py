from DataBase.mongoDB import MongoDB
from Repositories.IRepository import IRepository
from Model.scanResult import ScanResult


class ScanRepository(IRepository):
    def __init__(self):
        self.colls = MongoDB.db["scans"]

    async def create(self, scan_result: ScanResult):
        cloud_id = scan_result.cloudAccount_id
        user_id = scan_result.user_id
        scan_dict = {}
        for key, value in scan_result.__dict__.items():
            if value is not None:
                scan_dict[key] = value
        result = await self.colls.replace_one(
            {"cloudAccount_id": cloud_id, "user_id": user_id},
            scan_dict,
            upsert=True,
        )
        if result.upserted_id is not None:
            return str(result.upserted_id)
        return scan_dict.get("scan_id")

    async def update(self, cloud_id, user_id, scan_dict: dict):
        result = await self.colls.update_one(
            {"cloudAccount_id": cloud_id, "user_id": user_id},
            {"$set": scan_dict}
        )
        return result.modified_count > 0

    async def findById(self, scan_id):
        scan_response = await self.colls.find_one({"scan_id": scan_id})
        if scan_response:
            scan_result = ScanResult(
                scan_id=scan_response["scan_id"],
                arn=scan_response["arn"],
                cloud_id=scan_response["cloudAccount_id"],
                user_id=scan_response["user_id"],
            )
            scan_result.resources = scan_response.get("resources", {})
            scan_result.created_at = scan_response.get("created_at")
            scan_result.errors = scan_response.get("errors", [])
            scan_result.progress = scan_response.get("progress", 0)
            scan_result.status = scan_response.get("status", "Started")
            return scan_result
        return None
    
    async def delete(self, scan_id):
        result = await self.colls.delete_one({"scan_id": scan_id})
        return result.deleted_count > 0
  