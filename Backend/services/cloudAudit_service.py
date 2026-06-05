from fastapi import HTTPException
from analyzer.IAM_Analyzer import IAMAnalyzer
from analyzer.aws_analyzer import AWSAnalyzer
from analyzer.gemini_analyzer import  GeminiAnalyzer
from Repositories.ScanRepository import ScanRepository
from Repositories.auditRepository import AuditRepository
from Model.auditResult import AuditResult
from services.JSONSerializer import JSONSerializer
from services.JSONDeserializer import JSONDeserializer
from datetime import datetime as dateTime, timezone
from controllers.auditController import AuditController
from enums import AuditOrigin
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
        vulnerabilities_serialized=JSONSerializer.serializeList(vulnerabilities)
        critical_count=sum(1 for v in vulnerabilities if v.severity.lower() == 'critical')
        high_count=sum(1 for v in vulnerabilities if v.severity.lower() == 'high')
        medium_count=sum(1 for v in vulnerabilities if v.severity.lower() == 'medium')
        low_count=sum(1 for v in vulnerabilities if v.severity.lower() == 'low')
        counts = {'critical': critical_count, 'high': high_count, 'medium': medium_count, 'low': low_count}
        auditResult= AuditResult(id=auditID, vulnerabilities=vulnerabilities_serialized, accountID=accountId,userID=user_id,resources=resources, origin=AuditOrigin.Static.value, counts=counts)
        insterdId=await self.audit_repository.create(auditResult)
        logger.info(f"Created audit result with id {insterdId} for scan {scan_id} and user {user_id}")
        return auditResult
        
    async def get_last_audit_result(self, account_id: str, user_id: str):
        result= await self.audit_repository.findLastByAccountUser(account_id, user_id)
        if not result:
            logger.error(f"No audit results found for account {account_id} and user {user_id}")
            raise HTTPException(status_code=404, detail="No audit results found for this account")
        return result
    


    async def ai_audit_cloud_resources(self,audit_id: str, scan_id: str, user_id: str,user_context: dict):

        scanResult=await self.scan_repository.findById(scan_id)
        auditResult= await self.audit_repository.findById(audit_id)
        if not scanResult:
            logger.error(f"Scan with id {scan_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Scan not found")
        if not auditResult:
            logger.error(f"Audit result with id {audit_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Audit result not found")
        resources=scanResult.resources
        vulnerabilities=auditResult.vulnerabilities
        geminiAnalyzer=GeminiAnalyzer()

        response_vulnerabilities=geminiAnalyzer.analyze(resources, vulnerabilities, user_context)
        auditID=str(uuid4())
        critical_count=sum(1 for v in response_vulnerabilities if v.severity.lower() == 'critical')
        high_count=sum(1 for v in response_vulnerabilities if v.severity.lower() == 'high')
        medium_count=sum(1 for v in response_vulnerabilities if v.severity.lower() == 'medium')
        low_count=sum(1 for v in response_vulnerabilities if v.severity.lower() == 'low')
        counts = {'critical': critical_count, 'high': high_count, 'medium': medium_count, 'low': low_count}

        auditAiResult= AuditResult(id=auditID, vulnerabilities=JSONSerializer.serializeList(response_vulnerabilities), accountID=scanResult.cloudAccount_id,userID=user_id,resources=resources,origin=AuditOrigin.AI.value, counts=counts)
        insertedId=await self.audit_repository.create(auditAiResult)
        return auditAiResult
        

    async def get_all_audit_results(self, account_id:str, user_id:str):
        results=await self.audit_repository.findAuditsByAccountUser(account_id,user_id)
        if not results:
            logger.error(f"No audit results found for account {account_id} and user {user_id}")
            raise HTTPException(status_code=404, detail="No audit results found for this account")
        
        return results
    
    async def delete_audit(self,audit_id,user_id):
        auditResult= await self.audit_repository.findById(audit_id)
        if not auditResult:
            logger.error(f"Audit result with id {audit_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Audit result not found")
        if auditResult.userID != user_id:
            logger.error(f"User {user_id} is not authorized to delete audit result with id {audit_id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this audit result")
        await self.audit_repository.delete(audit_id)