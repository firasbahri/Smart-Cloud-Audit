
from Model.user import User
from DataBase.mongoDB import MongoDB
from Repositories.IRepository import IRepository
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class UserRepository(IRepository):
   def __init__(self):
      self.collection = MongoDB.db["users"]

   async def create(self, user_data: User):
      user_dict = {}
      for key, value in user_data.__dict__.items():
         if value is not None:
            user_dict[key] = value
      result = await self.collection.insert_one(user_dict)
      return str(result.inserted_id)

   async def find_user_by_username(self, username) -> bool:
      user_response = await self.collection.find_one({"username": username})
      logger.info("for username %s , user_id es %s", username, user_response.get("id") if user_response else None)
      user = (
         User(
            user_response["username"],
            user_response["password"],
            user_response["email"],
            user_response["isVerified"],
            None,
            user_response.get("id"),
         )
         if user_response
         else None
      )
      return user

   async def findById(self, user_id):
      user_response = await self.collection.find_one({"_id": ObjectId(user_id)})
      user = (
         User(
            user_response["username"],
            user_response["password"],
            user_response["email"],
            user_response["isVerified"],
            str(user_response["_id"]),
         )
         if user_response
         else None
      )
      return user

   async def delete(self, user_id):
      result = await self.collection.delete_one({"_id": ObjectId(user_id)})
      return result.deleted_count > 0

   async def update(self, user_id, user_data: User):
      user_dict = {}
      logger.info("Updating user with id: %s and data: %s", user_id, user_data.__dict__)
      for key, value in user_data.__dict__.items():
         if value is not None:
            user_dict[key] = value
      result = await self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
      return result.modified_count > 0

   async def find_user_by_token(self, token) -> User:
      user_response = await self.collection.find_one({"VerificationToken": token})
      if user_response:
         object_id = str(user_response.get("_id"))
         user = User(
            user_response["username"],
            user_response["password"],
            user_response["email"],
            user_response["isVerified"],
            user_response["VerificationToken"],
            object_id,
         )
         logger.info("User found by token: %s with id: %s", user.username, object_id)
         logger.info("id user found by token: %s", user.id)
         return user
      return None