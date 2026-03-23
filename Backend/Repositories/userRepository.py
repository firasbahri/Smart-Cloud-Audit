
from Model.user import User
from DataBase.mongoDB import MongoDB
from Repositories.IRepository import IRepository
from bson import ObjectId


class UserRepository(IRepository):
   def __init__(self):
      self.collection = MongoDB.db["users"]

   async def create(self, user_data: User):
      userDict = {}
      for key, value in user_data.__dict__.items():
         if value is not None:
            userDict[key] = value
      result = await self.collection.insert_one(userDict)
      return str(result.inserted_id)

   async def find_user_by_username(self, username) -> bool:
      print("Finding user by username:", username)
      userResponse = await self.collection.find_one({"username": username})
      print("User response from database:", userResponse["username"] if userResponse else None)
      user = User(userResponse["username"], userResponse["password"], userResponse["email"], str(userResponse["_id"])) if userResponse else None
      return user

   async def findById(self, user_id):
      print("Finding user by id:", user_id)
      userResponse = await self.collection.find_one({"_id": ObjectId(user_id)})
      print("User response from database:", userResponse)
      user = User(userResponse["username"], userResponse["password"], userResponse["email"], str(userResponse["_id"])) if userResponse else None
      return user

   async def delete(self, user_id):
      result = await self.collection.delete_one({"_id": ObjectId(user_id)})
      return result.deleted_count > 0

   async def update(self, user_id, user_data: User):
      userDict = {}
      for key, value in user_data.__dict__.items():
         if value is not None:
            userDict[key] = value
      result = await self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": userDict})
      return result.modified_count > 0
