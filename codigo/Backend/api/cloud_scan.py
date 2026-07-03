from fastapi import HTTPException, APIRouter, Depends,websockets,WebSocketDisconnect,Header,Query
from fastapi.responses import  StreamingResponse
from Requests import CloudDeleteRequest, ContextRequest
from dependencies import get_user_id_from_token, get_user_id_from_query_token
from services.cloudScan_service import CloudScanService
from Responses import ScanStatusResponse, ScanResultResponse, StartScanResponse
import asyncio
import json
import logging

cloud_scan_service = CloudScanService()
router = APIRouter()
logger=logging.getLogger(__name__)


@router.post("/start_scan", response_model=StartScanResponse)
async def scan_cloud(cloudDeleteRequest: CloudDeleteRequest, user_id: str = Depends(get_user_id_from_token)):
        id = cloudDeleteRequest.id
        result = await cloud_scan_service.start_scan(id, user_id)
        return StartScanResponse(scan_id=result.scan_id)


@router.get("/scan_status/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str, user_id: str = Depends(get_user_id_from_token)):
    logger.info(f"Getting scan status for scan_id: {scan_id} and user_id: {user_id}") 
    result = await cloud_scan_service.get_scan_status(scan_id, user_id)
    return ScanStatusResponse(
        status=str(result.status),
        progress=int(result.progress or 0),
        created_at=result.created_at,
        results=result.resources,
        errors=result.errors
    )


@router.get("/get_scan_result/{accountID}", response_model=ScanResultResponse)
async def get_scan_result(accountID: str, user_id: str = Depends(get_user_id_from_token)):
   result = await cloud_scan_service.get_scan_result(accountID, user_id)
   return ScanResultResponse(
       scan_id=result.scan_id,
       results=result.resources,
       created_at=result.created_at,
       errors=result.errors,
       context=result.userContext
       
   )

@router.put("/update_context/{scan_id}")
async def update_scan_context(scan_id:str,contextRequest:ContextRequest,user_id:str = Depends(get_user_id_from_token)):
    result= await cloud_scan_service.update_scan_context(scan_id, contextRequest, user_id)
    return result

@router.get('/context_scan/{scan_id}')
async def get_context_scan(scan_id: str, user_id: str = Depends(get_user_id_from_token)):
    result = await cloud_scan_service.get_context_scan(scan_id, user_id)
    return result

@router.get("/scan_progress_sse/{scan_id}")
async def scan_progress_sse(scan_id: str, user_id: str = Depends(get_user_id_from_query_token)):
    logger.info(f"Getting scan progress for scan_id: {scan_id} and user_id: {user_id}")
    async def event_generator():
        while True:
            try:
                result = await cloud_scan_service.get_scan_status(scan_id, user_id)
            except HTTPException as e:
                yield f"data: {json.dumps({'error': e.detail, 'status': 'failed'})}\n\n"
                break
            data=json.dumps({
                "status": str(result.status),
                "progress": int(result.progress or 0),
                "results": result.resources,
                "created_at": result.created_at,
                "errors": result.errors
            })
            yield f"data: {data}\n\n"
            if result.status in ["completed", "failed"]:
                break
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})