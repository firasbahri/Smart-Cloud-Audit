from fastapi import HTTPException
from analyzer.IAM_Analyzer import IAMAnalyzer
from analyzer.aws_analyzer import AWSAnalyzer
from Repositories.ScanRepository import ScanRepository
from Repositories.auditRepository import AuditRepository
from Model.auditResult import AuditResult
from services.JSONSerializer import JSONSerializer
from services.JSONDeserializer import JSONDeserializer
from datetime import datetime as dateTime, timezone
from controllers.auditController import AuditController
from uuid import uuid4
import logging

logger= logging.getLogger(__name__)

class CloudAuditService:
    def __init__(self):
        self.scan_repository = ScanRepository()
        self.audit_repository = AuditRepository()

    async def static_audit_cloud_resources(self, scan_id: str, user_id: str):
        scanResult= await self.scan_repository.findById(scan_id)
        if not scanResult:
            logger.error(f"Scan with id {scan_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Scan not found")

        resources = scanResult.resources
        accountId=scanResult.cloudAccount_id
        aws_analyzer=AWSAnalyzer()
        auditController=AuditController(aws_analyzer)
        deserializedResources=JSONDeserializer.deserialize_resources(resources)
        vulnerabilities=auditController.staticAudit(deserializedResources)
        auditID=str(uuid4())
        creationDate=dateTime.now(timezone.utc)
        vulnerabilities_serialized=JSONSerializer.serializeList(vulnerabilities)
        auditResult= AuditResult(id=auditID, vulnerabilities=vulnerabilities_serialized, accountID=accountId,userID=user_id,created_at=creationDate)
        await self.audit_repository.create(auditResult)
        logger.info(f"Found {len(vulnerabilities)} vulnerabilities in scan {scan_id} for user {user_id}")
        return auditResult
        
    async def get_last_audit_result(self, account_id: str, user_id: str):
        result= await self.audit_repository.findLastByAccountUser(account_id, user_id)
        if not result:
            logger.error(f"No audit results found for account {account_id} and user {user_id}")
            raise HTTPException(status_code=404, detail="No audit results found for this account")
        return result