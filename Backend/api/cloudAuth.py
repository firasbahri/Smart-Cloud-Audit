from fastapi import APIRouter, HTTPException,Header,Depends
from Requests import CloudAddRequest,CloudUpdateRequest,CloudDeleteRequest
from services.cloudAuth_service import CloudAuthService
from tokenConfigure import verify_access_token
from dependencies import get_user_id_from_token


CloudService= CloudAuthService()
router= APIRouter()

@router.post("/register_cloud")
async def cloud_auth( cloudAddRequest : CloudAddRequest,user_id: str = Depends(get_user_id_from_token)):
    
    arn = cloudAddRequest.arn
    name=cloudAddRequest.name
    provider=cloudAddRequest.provider
    description=cloudAddRequest.description    
    id=await CloudService.register_aws(arn, user_id, name, description,provider)
    print("Cloud account registered with id: ", id) 
    return{"message": "Cloud account registered successfully", "id": str(id)}

   

@router.get("/get_cloud_data")
async def getCloudData( user_id: str = Depends(get_user_id_from_token)):
    print("Received request to get cloud data for user_id: ", user_id)
    clouds_data = await CloudService.get_cloud_data(user_id)
    print("Cloud data to return: ", clouds_data)
    return clouds_data


@router.post("/update_cloud_data")
async def updateCloudData(cloudUpdateRequest : CloudUpdateRequest, user_id: str = Depends(get_user_id_from_token)):
    
    id = cloudUpdateRequest.id
    name=cloudUpdateRequest.name
    description=cloudUpdateRequest.description

    result = await CloudService.update_cloud_data(id, user_id, name, description)
    
    return result


@router.delete("/delete_cloud_data")
async def deleteCloudData(cloudDeleteRequest : CloudDeleteRequest, user_id: str = Depends(get_user_id_from_token)):
    print("Received request to delete cloud data with id: ", cloudDeleteRequest.id, " for user_id: ", user_id)
    id= cloudDeleteRequest.id
    result = await CloudService.delete_cloud_data(user_id,id)
    return result
