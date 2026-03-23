from Controller.Scan_Controller import ScanController
from fastapi import HTTPException
from Repositories.userRepository import UserRepository
from Repositories.cloudRepository import CloudRepository
from services.JSONSerializer import JSONSerializer
from datetime import datetime as DateTime, timezone
from Model.cloud import Cloud

class CloudAuthService:
    def __init__(self):
        self.cloud_repository = CloudRepository()
        self.user_repository = UserRepository()


    async def register_aws(self,arn: str,user_id: str,name: str, description: str,provider: str):
        user= await self.user_repository.findById(user_id)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        try:
            scan_controller = ScanController(arn,provider)
            account_id = scan_controller.connect()       
            creation_date = DateTime.now(timezone.utc).isoformat()
            cloud_data=Cloud(name,provider,arn,account_id,user_id,description,creation_date)
            id=await self.cloud_repository.create(cloud_data)
        except HTTPException :
            raise
        except Exception as e: 
            raise HTTPException(status_code=500, detail=str(e))
        
        return id
    async def get_cloud_data(self, user_id: str):

        user= await self.user_repository.findById(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        try:
            clouds_data = await self.cloud_repository.found_cloud_accounts(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        if not clouds_data:
            raise HTTPException(status_code=404, detail="Cloud data not found for the user")
        
        cloudsDataSerializado=JSONSerializer.serializeList(clouds_data)
        print("Serialized cloud data: ", cloudsDataSerializado)

        return cloudsDataSerializado

    async def update_cloud_data(self, id: str,user_id: str,name: str, description: str,):
        

        user = await self.user_repository.findById(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        existedCloud = await self.cloud_repository.findById(id)
        if not existedCloud:
            raise HTTPException(status_code=404, detail="Cloud data not found")

        if name:    
            existedCloud.name = name
        if description:
            existedCloud.description = description

        try:
            await self.cloud_repository.update(existedCloud)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return True


        
    async def delete_cloud_data(self, user_id: str,id_cloud: str):
        user= await self.user_repository.findById(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            await self.cloud_repository.delete(id_cloud)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return True


    

