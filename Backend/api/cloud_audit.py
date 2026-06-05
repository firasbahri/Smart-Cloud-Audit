from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_user_id_from_token
from services.cloudAudit_service import CloudAuditService
from Requests import cloudAuditRequest, CloudAIAuditRequest
from Responses import AuditResponse
from typing import List
import logging

logger= logging.getLogger(__name__)

cloudAuditService=CloudAuditService()
router=APIRouter()

@router.post("/static-audit", response_model=AuditResponse)
async def static_audit_cloud_resources(request: cloudAuditRequest, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    result= await cloudAuditService.static_audit_cloud_resources(request.scan_id, user_id)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities, created_at=result.created_at)


@router.post("/ai-audit", response_model=AuditResponse)
async def ai_audit_cloud_resources(request: CloudAIAuditRequest, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    logger.info(f"Starting AI audit for scan {request.scan_id} and audit {request.audit_id} for user {user_id}")
    result = await cloudAuditService.ai_audit_cloud_resources(request.audit_id, request.scan_id, user_id, request.user_context)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities, created_at=result.created_at, counts=result.counts, origin=result.origin)

@router.get("/last-audit-result/{account_id}", response_model=AuditResponse)
async def get_last_audit_result(account_id: str, user_id: str = Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await cloudAuditService.get_last_audit_result(account_id, user_id)
    return AuditResponse(audit_id=result.id, vulnerabilities=result.vulnerabilities, created_at=result.created_at, counts=result.counts, origin=result.origin)


@router.get("/my-audits/{account_id}", response_model=List[AuditResponse])
async def get_all_audit_results(account_id:str,user_id:str =Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    audits=[]
    logger.info(f"Fetching all audit results for account {account_id} and user {user_id}")
    results=await cloudAuditService.get_all_audit_results(account_id, user_id)
    logger.info(f"found first element in api response: {results[0].vulnerabilities if results else 'No results'} for account {account_id} and user {user_id}  ")
    audits=[AuditResponse(audit_id=a.id,vulnerabilities=a.vulnerabilities, created_at=a.created_at,counts=a.counts,origin=a.origin) for a in results]
    return audits


@router.delete("/delete-audit/{audit_id}")
async def delete_audit(audit_id:str,user_id:str=Depends(get_user_id_from_token)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    await cloudAuditService.delete_audit(audit_id, user_id)
    return {"message": "Audit deleted successfully"}
