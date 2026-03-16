from mongoDB import MongoDB
from Model.cloud import Cloud
from fastapi import HTTPException
from bson import ObjectId

class CloudRepository:
  def __init__(self):
    self.collection = MongoDB.db["cloud_users"]


  async def create_cloud_user(self,cloud : Cloud):
   cloud_dict= cloud.__dict__
   cloudExisted= await self.collection.find_one({"account_id": cloud.account_id, "user_id": cloud.user_id})

   if cloudExisted:
      raise HTTPException(status_code=400, detail="Cloud user already exists")

   result= await self.collection.insert_one(cloud_dict)
   print("Inserted cloud data with id: ", result.inserted_id)
   return str(result.inserted_id)



  async def found_cloud_accounts(self,user_id):
    print("REPOSITORY: Finding cloud data for user_id: ", user_id)
    result= self.collection.find({"user_id": user_id})
   
    clouds= []
    async for cloud in result:
      print("cloud name: ", cloud.get("name"))
      print("cloud provider: ", cloud.get("provider"))
      print("cloud account_id: ", cloud.get("account_id"))
      print("cloud user_id: ", cloud.get("user_id"))
      id= cloud.get("_id")
      print("cloud id: ", id)
      clouds.append(Cloud(
        cloud.get("name"),
        cloud.get("provider"),
        cloud.get("identifier"),
        cloud.get("account_id"),
        cloud.get("user_id"),
        cloud.get("description"),
        cloud.get("created_at"),
        id=str(cloud.get("_id"))
        )
      )
      
    if clouds:
        for cloud in clouds:
            print("Found cloud data: ", cloud.__dict__)
        return clouds
    return None

  async def found_cloud_account(self,id):
    cloud= await self.collection.find_one({"_id": ObjectId(id)})
    if cloud:
        id= cloud.get("_id")
        return Cloud(
            name=cloud.get("name"),
            provider=cloud.get("provider"),
            identifier=cloud.get("identifier"),
            account_id=cloud.get("account_id"),
            user_id=cloud.get("user_id"),
            created_at=cloud.get("created_at"),
            description=cloud.get("description"),
            id=str(id)
        )
    return None

  async def update_cloud_user(self,cloud : Cloud):
     cloudDict= cloud.__dict__
     result= await self.collection.update_one({"_id": ObjectId(cloud.id)}, {"$set": cloudDict})
     if result.modified_count > 0:
        return True
     return False
  
  async def delete_cloud_user(self,cloud_id):
     result= await self.collection.delete_one({"_id": ObjectId(cloud_id)}) 
     if result.deleted_count > 0:
        return True
     return False


