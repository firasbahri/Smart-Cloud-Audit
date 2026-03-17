from fastapi import HTTPException
from Repositories.ScanRepository import ScanRepository
from Repositories.cloudRepository import CloudRepository
from rabbitMq.producer import RabbitMQProducer
from Model.scanResult import ScanResult
from typing import Optional
from uuid import uuid4

class CloudScanService:
  def __init__(self):
      self.cloud_repository = CloudRepository()
      self.scan_repository = ScanRepository()



  async def start_scan(self, id: str, user_id: str):
      cloud= await self.cloud_repository.found_cloud_account(id)
      if not cloud:
          raise HTTPException(status_code=404, detail="Cloud account not found")
      
      if cloud.user_id != user_id:
          raise HTTPException(status_code=403, detail="Forbidden: You don't have access to this cloud account")
      
      arn = cloud.identifier
      scan_id = str(uuid4())
      scanResult= ScanResult(
          scan_id=scan_id,
          arn=arn,
          cloud_id=cloud.id,
          user_id=user_id
      )
      scanId= await self.scan_repository.create_scan_result(scanResult)
      await RabbitMQProducer.send_message(scan_id=scan_id, identifier=arn)
      
      return {"message": "Scan started successfully", "scan_id": scan_id}


  async def get_scan_status(self, scan_id: str, user_id: str):
        scanResult=await self.scan_repository.get_scan_result(scan_id, user_id)
        if not scanResult:
            raise HTTPException(status_code=404, detail="Scan not found")
        if scanResult.status == "Started":
            return {"status": scanResult.status, "progress": scanResult.progress}
        elif scanResult.status == "running":
            return {"status": scanResult.status, "progress": scanResult.progress}
        else:
            return {"status": scanResult.status, "progress": scanResult.progress, "results": scanResult.resources, "errors": scanResult.errors}

