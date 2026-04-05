from fastapi import HTTPException
from Repositories.ScanRepository import ScanRepository
from Repositories.cloudRepository import CloudRepository
from celery_worker.tasks import scan_cloud_account
from Model.scanResult import ScanResult
from datetime import datetime as DateTime, timezone
from typing import Optional
from uuid import uuid4
import logging  

logger=logging.getLogger(__name__)

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
      if provider == "AWS":
           resources={"users": [], "groups": [], "roles": [], "buckets": [], "ec2": []}
      scan_id = str(uuid4())
      creation_date=DateTime.now(timezone.utc).isoformat()
      scanResult= ScanResult(
          scan_id=scan_id,
          arn=arn,
          cloud_id=cloud.id,
          user_id=user_id,
           creation_at=creation_date,
          resources=resources
         
      )

      scanId= await self.scan_repository.create(scanResult)
      scan_cloud_account.delay(scan_id, arn, provider)
      return scanResult


  async def get_scan_status(self, scan_id: str, user_id: str):
        scanResult=await self.scan_repository.findById(scan_id)
        if not scanResult:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scanResult


  async def get_scan_result(self, accountID: str, user_id: str):
      logger.info("finding scan for userID {user_id} and account {accountID}")
      scanResult=await self.scan_repository.findByAccountUser(accountID, user_id)
      if not scanResult:
          raise HTTPException(status_code=404,detail="scan not found")

      return scanResult