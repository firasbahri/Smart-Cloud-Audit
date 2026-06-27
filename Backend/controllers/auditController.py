from Factories.analyzerFactory import AnalyzerFactory
from Factories.AIAnalyzerFactory import AIAnalyzerFactory
import logging 

logger=logging.getLogger(__name__)


class AuditController:

    def staticAudit(self, resources,provider):
        try:
            analyzer = AnalyzerFactory.create_analyzer(provider)
            result = analyzer.analyze(resources)
            return result
        except Exception as e:
            logger.error(f"Error auditing cloud resources: {str(e)}")
            raise Exception(f"Error auditing cloud resources: {str(e)}")
        

    def aiAudit(self, resources, vulnerabilities, user_context, modelo):
        try:
            ai_analyzer = AIAnalyzerFactory.create_analyzer(modelo)
            result = ai_analyzer.analyze(resources, vulnerabilities, user_context)
            return result
        except Exception as e:
            logger.error(f"Error auditing cloud resources with AI: {str(e)}")
            raise Exception(f"Error auditing cloud resources with AI: {str(e)}")

    