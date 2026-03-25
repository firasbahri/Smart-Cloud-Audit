import logging 

logger=logging.getLogger(__name__)


class AuditController:
    def __init__(self, audit_service):
        self.audit_service = audit_service

    
    def staticAudit(self, resources ):
        try:
            result = self.audit_service.analyze(resources)
            return result
        except Exception as e:
            logger.error(f"Error auditing cloud resources: {str(e)}")
            raise Exception(f"Error auditing cloud resources: {str(e)}")

    