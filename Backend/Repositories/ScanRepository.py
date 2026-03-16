from mongoDB import MongoDB
from Model.scanResult import ScanResult



class ScanRepository:
  def __init__(self):
    self.colls = MongoDB.db["scans"]


  async def create_scan_result(self, scan_result: ScanResult):
    scanDict={}
    for key, value in scan_result.__dict__.items():
      if value is not None:
        scanDict[key] = value
    result = await self.colls.insert_one(scanDict)
    return str(result.inserted_id)

  async def update_scan_result(self, scan_id, scanDict:dict):
    result = await self.colls.update_one({"scan_id": scan_id}, {"$set": scanDict})
    return result.modified_count > 0  
  
  async def get_scan_result(self, scan_id):
    scanResponse= await self.colls.find_one({"scan_id": scan_id})
    if scanResponse:
      scanResult=ScanResult(scanResponse["scan_id"],scanResponse["account_id"])
      scanResult.resources=scanResponse["resources"]
      scanResult.created_at=scanResponse["created_at"]
      scanResult.errors=scanResponse["errors"]
      scanResult.porcentage=scanResponse["porcentage"]
      scanResult.status=scanResponse["status"]
      return scanResult
    return None
  
  async def delete_scan_result(self, scan_id):
    result = await self.colls.delete_one({"scan_id": scan_id})
    return result.deleted_count > 0
  