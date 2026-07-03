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
from enums import AuditOrigin
from uuid import uuid4
import logging

logger= logging.getLogger(__name__)

class CloudAuditService:
    """Orquesta las auditorías (estática y con IA): recupera el scan, llama al AuditController, calcula los
    contadores por severidad y guarda el resultado como un nuevo AuditResult."""
    def __init__(self):
        self.scan_repository = ScanRepository()
        self.audit_repository = AuditRepository()
        self.auditController=AuditController()

    async def static_audit_cloud_resources(self, scan_id: str, user_id: str):
        """Ejecuta el análisis estático sobre los recursos de un scan ya completado y guarda el resultado.

        Args:
            scan_id (str): id del scan cuyos recursos se van a auditar.
            user_id (str): usuario que pide la auditoría, queda asociado al AuditResult creado.

        Returns:
            AuditResult: resultado nuevo, con id propio, origin="static" y los counts por severidad ya calculados.

        Raises:
            HTTPException: 404 si no existe un scan con ese id.
        """
        scanResult= await self.scan_repository.findById(scan_id)
        if not scanResult:
            logger.error(f"Scan with id {scan_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Scan not found")

        resources = scanResult.resources
        accountId=scanResult.cloudAccount_id

        deserializedResources=JSONDeserializer.deserialize_resources(resources)
        vulnerabilities=self.auditController.staticAudit(deserializedResources,"AWS")
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
        """Última auditoría (de cualquier tipo) guardada para una cuenta y usuario.

        Raises:
            HTTPException: 404 si esa cuenta no tiene ninguna auditoría todavía.
        """
        result= await self.audit_repository.findLastByAccountUser(account_id, user_id)
        if not result:
            logger.error(f"No audit results found for account {account_id} and user {user_id}")
            raise HTTPException(status_code=404, detail="No audit results found for this account")
        return result



    async def ai_audit_cloud_resources(self,audit_id: str, scan_id: str, user_id: str,user_context: dict):
        """Ejecuta el análisis con IA sobre los recursos del scan, usando como referencia las vulnerabilidades
        de una auditoría estática ya existente (para que el modelo no las repita), y guarda el resultado como
        una auditoría nueva e independiente (origin="ai").

        Args:
            audit_id (str): id de la auditoría estática previa cuyas vulnerabilidades se le pasan al modelo como contexto.
            scan_id (str): id del scan con los recursos a analizar.
            user_id (str): usuario que pide el análisis.
            user_context (dict): descripción de negocio y contexto de recursos aportado por el usuario.

        Returns:
            AuditResult: resultado nuevo, separado del de static_audit_cloud_resources, con origin="ai".

        Raises:
            HTTPException: 404 si no existe el scan o la auditoría estática indicada.
        """

        scanResult=await self.scan_repository.findById(scan_id)
        if audit_id:
            auditResult= await self.audit_repository.findById(audit_id)
            vulnerabilities=auditResult.vulnerabilities
        else:
            vulnerabilities=[]
        
        if not scanResult:
            logger.error(f"Scan with id {scan_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Scan not found")
  
        resources=scanResult.resources
       
        response_vulnerabilities=self.auditController.aiAudit(resources, vulnerabilities, user_context, "Gemini")
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
        """Historial completo de auditorías (estáticas e IA) de una cuenta, usado por la vista "Mis Auditorías".

        Raises:
            HTTPException: 404 si la cuenta no tiene ninguna auditoría todavía.
        """
        results=await self.audit_repository.findAuditsByAccountUser(account_id,user_id)
        if not results:
            logger.error(f"No audit results found for account {account_id} and user {user_id}")
            raise HTTPException(status_code=404, detail="No audit results found for this account")

        return results

    async def delete_audit(self,audit_id,user_id):
        """Borra una auditoría, comprobando antes que pertenece al usuario que pide el borrado.

        Raises:
            HTTPException: 404 si no existe esa auditoría, 403 si pertenece a otro usuario.
        """
        auditResult= await self.audit_repository.findById(audit_id)
        if not auditResult:
            logger.error(f"Audit result with id {audit_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Audit result not found")
        if auditResult.userID != user_id:
            logger.error(f"User {user_id} is not authorized to delete audit result with id {audit_id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this audit result")
        await self.audit_repository.delete(audit_id)


    async def generate_ai_recommendation(self, vulnerability_id:str, audit_id:str, user_id:str):
        """Pide a Gemini la recomendación y el comando CLI para una vulnerabilidad concreta de una auditoría
        ya guardada, y persiste el resultado en esa misma vulnerabilidad (para no tener que regenerarlo otra vez).

        Args:
            vulnerability_id (str): id de la vulnerabilidad dentro de la auditoría.
            audit_id (str): id de la auditoría que contiene esa vulnerabilidad.
            user_id (str): usuario que pide la recomendación, solo para logging.

        Returns:
            dict: {"recommendation": str, "cli_command": str} — lo mismo que devuelve GeminiAnalyzer.generateCLI.

        Raises:
            HTTPException: 404 si la vulnerabilidad no existe dentro de esa auditoría.
        """
        vulnerability= await self.audit_repository.findVulnerabilityById(audit_id, vulnerability_id)
        if not vulnerability:
            logger.error(f"Vulnerability with id {vulnerability_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        ai_recommendation=self.auditController.generate_recomendations(vulnerability, "Gemini")
        vulnerability.recommendation=ai_recommendation.get("recommendation", "")
        vulnerability.cli_command=ai_recommendation.get("cli_command", "")
        await self.audit_repository.updateVulnerability(audit_id, vulnerability_id, vulnerability)
        logger.info(f"Generated AI recommendation for vulnerability {vulnerability_id} in audit {audit_id} for user {user_id}")
        return ai_recommendation
