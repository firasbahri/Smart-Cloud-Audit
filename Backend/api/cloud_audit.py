from fastapi import APIRouter, Depends
from dependencies import get_user_id_from_token
from services.cloudAudit_service import CloudAuditService
from Requests import cloudAuditRequest


cloudAuditService=CloudAuditService()
router=APIRouter()

@router.post("/static-audit")
async def static_audit_cloud_resources(request: cloudAuditRequest, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    result= await cloudAuditService.static_audit_cloud_resources(request.scan_id, user_id)
    return result