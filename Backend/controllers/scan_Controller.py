
from Factories.scannerFactory import ScannerFactory
from services.JSONSerializer import JSONSerializer
from Model.scanResult import ScanResult
from uuid import uuid4
import logging
logger = logging.getLogger("scanController")
class ScanController:
  """Capa fina entre el servicio de escaneo y el scanner concreto del proveedor: resuelve qué scanner usar
  y deja al servicio trabajar siempre con la misma interfaz, sin importar si por dentro es AWS u otro proveedor."""

  def __init__(self, arn,provider,regions):
    """Crea el scanner adecuado para el proveedor indicado, listo para conectar.

    Args:
        arn (str): identificador de la cuenta a escanear (en AWS, el ARN del rol a asumir).
        provider (str): proveedor cloud, usado por ScannerFactory para elegir la implementación.
        regions (list): regiones a recorrer al escanear EC2; puede ir vacía para autodetectarlas.
    """
    self.scan_service = ScannerFactory.create_scanner(provider)
    self.arn = arn
    self.regions = regions
    self.account_id = None

  def connect(self):
    """Abre sesión contra el proveedor y guarda el account_id devuelto en self.account_id.

    Returns:
        str: account_id de la cuenta conectada.
    """
    try:
      account_id=self.scan_service.connect(self.arn)
      self.account_id = account_id
    except Exception as e:
      logger.error(f"Error connecting to service: {str(e)}")

      raise Exception(f"Error connecting to service: {str(e)}")
    logger.info(f"Connected to service with account ID: {account_id}")

    return account_id

  def find_resources(self):
    """Tipos de recurso que el scanner conectado sabe escanear (delegado directo a get_resources())."""
    try:
      resources = self.scan_service.get_resources()
      logger.info(f"Resources found: {resources}")
      return resources
    except Exception as e:
      logger.error(f"Error finding resources: {str(e)}")
      raise Exception(f"Error finding resources: {str(e)}")

  def scanByResource(self,resource):
    """Escanea un tipo de recurso, lo serializa a JSON y, si es "ec2", actualiza self.regions con las
    regiones donde de verdad se encontró algo (para que llamadas futuras no tengan que recorrer todas otra vez).

    Args:
        resource (str): tipo de recurso a escanear, debe estar en find_resources().

    Returns:
        list: el recurso serializado, listo para guardarse en MongoDB.

    Raises:
        Exception: si resource no es uno de los tipos soportados por el scanner.
    """
    resources = self.scan_service.get_resources()
    if resource not in resources:
      logger.warning(f"Resource {resource} not found in available resources: {resources}")
      raise Exception(f"Resource {resource} not found in available resources: {resources}")
    if resource == "ec2":
       all_instances, regions_founded = self.scan_service.scan_resource(resource,self.regions)
       result_serializado = JSONSerializer.serializeList(all_instances)
       self.regions = regions_founded
    else:
      result = self.scan_service.scan_resource(resource,self.regions)
      result_serializado = JSONSerializer.serializeList(result)
    return result_serializado



