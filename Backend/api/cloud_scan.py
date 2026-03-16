from fastapi import HTTPException, APIRouter, Depends
from Requests import CloudDeleteRequest
from dependencies import get_user_id_from_token
from services.cloudScan_service import CloudScanService

cloud_scan_service = CloudScanService()
router = APIRouter()




@router.post("/scan_cloud")
async def scan_cloud(cloudDeleteRequest : CloudDeleteRequest):
  id = cloudDeleteRequest.id
  result = await cloud_scan_service.start_scan(id)
  return result