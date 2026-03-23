from fastapi import HTTPException, APIRouter, Depends
from Requests import CloudDeleteRequest
from dependencies import get_user_id_from_token
from services.cloudScan_service import CloudScanService
cloud_scan_service = CloudScanService()
router = APIRouter()




@router.post("/start_scan")
async def scan_cloud(cloudDeleteRequest : CloudDeleteRequest,user_id: str= Depends(get_user_id_from_token)):
  id = cloudDeleteRequest.id
  result = await cloud_scan_service.start_scan(id, user_id )
  return result


@router.get("/scan_status/{scan_id}")
async def get_scan_status(scan_id: str, user_id: str = Depends(get_user_id_from_token)):
    result = await cloud_scan_service.get_scan_status(scan_id, user_id)
    return result