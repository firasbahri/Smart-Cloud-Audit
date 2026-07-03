from fastapi import HTTPException
from Repositories.ScanRepository import ScanRepository
from Repositories.cloudRepository import CloudRepository
from celery_worker.tasks import scan_cloud_account
from Model.scanResult import ScanResult
from Requests import ContextRequest
from datetime import datetime as DateTime, timezone
from typing import Optional
from uuid import uuid4
import logging

logger=logging.getLogger(__name__)

class CloudScanService:
  """Gestiona el ciclo de vida de un escaneo: crea el registro inicial en Mongo, dispara el trabajo de Celery
  que hace el escaneo real en segundo plano, y expone consultas sobre su progreso/resultado."""
  def __init__(self):
      self.cloud_repository = CloudRepository()
      self.scan_repository = ScanRepository()



  async def start_scan(self, id: str, user_id: str):
      """Valida que la cuenta cloud exista y pertenezca al usuario, crea el documento de scan vacío (status
      inicial) y delega el trabajo pesado a la tarea de Celery scan_cloud_account, que lo va completando en
      segundo plano mientras el usuario sigue el progreso por SSE.

      Args:
          id (str): id de la cuenta cloud (Cloud) a escanear, no el id del scan.
          user_id (str): usuario que pide el escaneo, debe ser el propietario de la cuenta.

      Returns:
          ScanResult: el documento de scan recién creado, con status="Started" y progress=0 — el contenido
          real de resources se va rellenando de forma asíncrona por el worker.

      Raises:
          HTTPException: 404 si la cuenta cloud no existe, 403 si no pertenece a user_id.
      """
      print(f"Starting scan for cloud account {id} and user {user_id}")
      resources = []
      cloud= await self.cloud_repository.findById(id)
      if not cloud:
          raise HTTPException(status_code=404, detail="Cloud account not found")

      if cloud.user_id != user_id:
          raise HTTPException(status_code=403, detail="Forbidden: You don't have access to this cloud account")

      arn = cloud.identifier
      provider = cloud.provider
      if provider == "AWS":
           resources={"users": [], "groups": [], "roles": [], "buckets": [], "ec2": []}
      scan_id = str(uuid4())
      creation_date=DateTime.now(timezone.utc).isoformat()
      scanResult= ScanResult(
          scan_id=scan_id,
          arn=arn,
          cloud_id=cloud.id,
          user_id=user_id,
          creation_at=creation_date,
          resources=resources

      )

      scanId= await self.scan_repository.create(scanResult)
      scan_cloud_account.delay(scan_id, arn, provider, cloud.regions)
      return scanResult


  async def get_scan_status(self, scan_id: str, user_id: str):
        """Estado actual de un scan (progress, status, resources parciales) tal como lo va dejando el worker en Mongo.

        Raises:
            HTTPException: 404 si no existe un scan con ese id.
        """
        scanResult=await self.scan_repository.findById(scan_id)
        if not scanResult:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scanResult


  async def get_scan_result(self, accountID: str, user_id: str):
      """Último scan guardado para una cuenta y usuario concretos.

      Raises:
          HTTPException: 404 si esa cuenta no tiene ningún scan todavía.
      """
      logger.info("finding scan for userID {user_id} and account {accountID}")
      scanResult=await self.scan_repository.findByAccountUser(accountID, user_id)
      if not scanResult:
          raise HTTPException(status_code=404,detail="scan not found")

      return scanResult

  async def update_scan_context(self, scan_id:str, contextRequest:ContextRequest, user_id:str):
        """Guarda la descripción de negocio que el usuario escribe para un recurso concreto del Inventario
        (el "Contexto IA" de InventoryView), para que luego el análisis con IA lo tenga en cuenta.

        Args:
            scan_id (str): scan al que pertenece el recurso.
            contextRequest (ContextRequest): trae resource_id y el texto de contexto a guardar.
            user_id (str): usuario que edita el contexto, debe ser el propietario del scan.

        Returns:
            bool: resultado de la actualización en Mongo (True si se modificó algún documento).

        Raises:
            HTTPException: 404 si el scan no existe, 403 si no pertenece a user_id.
        """
        scanResult=await self.scan_repository.findById(scan_id)
        if not scanResult:
            raise HTTPException(status_code=404, detail="Scan not found")

        if scanResult.user_id != user_id:
            raise HTTPException(status_code=403, detail="no tiene permisos para modificar este scan")

        scanResult.userContext[contextRequest.resource_id]=contextRequest.context
        result= await self.scan_repository.update(scan_id, {"userContext": scanResult.userContext})
        return result


