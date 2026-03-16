
from Model.user import User
from mongoDB import MongoDB
from bson import ObjectId


class UserRepository:
 def __init__(self):
    self.collection = MongoDB.db["users"]

 async def create_user( self,user_data: User):
    userDict={}
    for key, value in user_data.__dict__.items():
      if value is not None:
        userDict[key] = value
    result = await self.collection.insert_one(userDict)
    return str(result.inserted_id)
  
 async def find_user_by_username( self, username) -> bool:
    print("Finding user by username:", username)
    userResponse= await self.collection.find_one({"username": username})
    print("User response from database:", userResponse["username"] if userResponse else None)
    user=User(userResponse["username"],userResponse["password"],userResponse["email"],str(userResponse["_id"])) if userResponse else None
    return user
 
 async def find_user_by_id( self, user_id):
    print("Finding user by id:", user_id)
    userResponse= await self.collection.find_one({"_id": ObjectId(user_id)})
    print("User response from database:", userResponse)
    user=User(userResponse["username"],userResponse["password"],userResponse["email"],str(userResponse["_id"])) if userResponse else None
    return user

