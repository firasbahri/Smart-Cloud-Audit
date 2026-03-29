from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_user_id_from_token
from services.cloudAudit_service import CloudAuditService
from Requests import cloudAuditRequest
from Responses import AuditResponse


cloudAuditService=CloudAuditService()
router=APIRouter()

@router.post("/static-audit", response_model=AuditResponse)
async def static_audit_cloud_resources(request: cloudAuditRequest, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    result= await cloudAuditService.static_audit_cloud_resources(request.scan_id, user_id)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities)


@router.post("/ai-audit", response_model=AuditResponse)
async def ai_audit_cloud_resources(request: cloudAuditRequest, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Fallback temporal: reutiliza la auditoria actual hasta implementar pipeline IA dedicado.
    result = await cloudAuditService.static_audit_cloud_resources(request.scan_id, user_id)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities)

@router.get("/last-audit-result/{account_id}", response_model=AuditResponse)
async def get_last_audit_result(account_id: str, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await cloudAuditService.get_last_audit_result(account_id, user_id)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities)