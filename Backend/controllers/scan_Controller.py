
from Factories.scannerFactory import ScannerFactory
from services.JSONSerializer import JSONSerializer
from Model.scanResult import ScanResult
from uuid import uuid4
import logging
logger = logging.getLogger("scanController")
class ScanController:

  def __init__(self, arn,provider):
    self.scan_service = ScannerFactory.create_scanner(provider)
    self.arn = arn
    self.account_id = None

  def connect(self):
    try:
      account_id=self.scan_service.connect(self.arn)
      self.account_id = account_id
    except Exception as e:
      logger.error(f"Error connecting to service: {str(e)}")

      raise Exception(f"Error connecting to service: {str(e)}")
    logger.info(f"Connected to service with account ID: {account_id}")
     
    return account_id

  def find_resources(self):
    try:
      resources = self.scan_service.get_resources()
      logger.info(f"Resources found: {resources}")
      return resources
    except Exception as e:
      logger.error(f"Error finding resources: {str(e)}")
      raise Exception(f"Error finding resources: {str(e)}")

  def scanByResource(self,resource):
    resources = self.scan_service.get_resources()
    if resource not in resources:
      logger.warning(f"Resource {resource} not found in available resources: {resources}")
      raise Exception(f"Resource {resource} not found in available resources: {resources}")
    result= self.scan_service.scan_resource(resource)
    result_serializado = JSONSerializer.serializeList(result)
    return result_serializado

 

    


    