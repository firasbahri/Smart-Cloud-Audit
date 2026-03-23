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
      print(f"Starting scan for cloud account {id} and user {user_id}")
      resources = []
      cloud= await self.cloud_repository.findById(id)
      if not cloud:
          raise HTTPException(status_code=404, detail="Cloud account not found")
      
      if cloud.user_id != user_id:
          raise HTTPException(status_code=403, detail="Forbidden: You don't have access to this cloud account")
      
      arn = cloud.identifier
      provider = cloud.provider
      print(f"Starting scan for cloud account {id} with ARN {arn} and provider {provider}")
      if provider == "AWS":
           resources={"users": [], "groups": [], "roles": [], "buckets": [], "ec2": []}
      scan_id = str(uuid4())
      scanResult= ScanResult(
          scan_id=scan_id,
          arn=arn,
          cloud_id=cloud.id,
          user_id=user_id,
          resources=resources
      )
      scanId= await self.scan_repository.create(scanResult)
      await RabbitMQProducer.send_message(scan_id=scan_id, identifier=arn, provider=provider)
      
      return {"message": "Scan started successfully", "scan_id": scan_id}


  async def get_scan_status(self, scan_id: str, user_id: str):
        scanResult=await self.scan_repository.findById(scan_id)
        if not scanResult:
            raise HTTPException(status_code=404, detail="Scan not found")
        if scanResult.status == "Started":
            return {"status": scanResult.status, "progress": scanResult.progress}
        elif scanResult.status == "running":
            return {"status": scanResult.status, "progress": scanResult.progress}
        else:
            return {"status": scanResult.status, "progress": scanResult.progress, "results": scanResult.resources, "errors": scanResult.errors}

