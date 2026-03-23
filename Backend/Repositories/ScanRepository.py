from DataBase.mongoDB import MongoDB
from Repositories.IRepository import IRepository
from Model.scanResult import ScanResult



class ScanRepository(IRepository):
  def __init__(self):
    self.colls = MongoDB.db["scans"]


  async def create(self, scan_result: ScanResult):
    scanDict={}
    for key, value in scan_result.__dict__.items():
      if value is not None:
        scanDict[key] = value
    result = await self.colls.insert_one(scanDict)
    return str(result.inserted_id)

  async def update(self, scan_id, scanDict:dict):
    result = await self.colls.update_one({"scan_id": scan_id}, {"$set": scanDict})
    return result.modified_count > 0  
  
  async def findById(self, scan_id):
    scanResponse= await self.colls.find_one({"scan_id": scan_id})
    if scanResponse:
      scanResult = ScanResult(
          scan_id=scanResponse["scan_id"],
          arn=scanResponse["arn"],
          cloud_id=scanResponse["cloudAccount_id"],
          user_id=scanResponse["user_id"]
      )
      scanResult.resources = scanResponse.get("resources", {})
      scanResult.created_at = scanResponse.get("created_at")
      scanResult.errors = scanResponse.get("errors", [])
      scanResult.progress = scanResponse.get("progress", 0)
      scanResult.status = scanResponse.get("status", "Started")
      return scanResult
    return None
  
  async def delete(self, scan_id):
    result = await self.colls.delete_one({"scan_id": scan_id})
    return result.deleted_count > 0
  