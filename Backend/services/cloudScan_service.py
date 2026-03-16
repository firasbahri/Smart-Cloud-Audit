from fastapi import HTTPException
from Repositories.ScanRepository import ScanRepository
from Repositories.cloudRepository import CloudRepository
from rabbitMq.producer import RabbitMQProducer
from Model.scanResult import ScanResult
from typing import Optional

class CloudScanService:
  def __init__(self):
      self.cloud_repository = CloudRepository()
      self.scan_repository = ScanRepository()



  async def start_scan(self, id: str):
      cloud= await self.cloud_repository.found_cloud_account(id)
      if not cloud:
          raise HTTPException(status_code=404, detail="Cloud account not found")
      
      #if cloud.user_id != user_id:
       #   raise HTTPException(status_code=403, detail="Forbidden: You don't have access to this cloud account")
      
      arn = cloud.identifier
      scanResult= ScanResult(
          scan_id=str(cloud.id),
          arn=arn,
      )
      scanId= await self.scan_repository.create_scan_result(scanResult)
      await RabbitMQProducer.send_message(scan_id=scanId, identifier=arn)
      
      return {"message": "Scan started successfully", "scan_id": scanId}
