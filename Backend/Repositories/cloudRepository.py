from DataBase.mongoDB import MongoDB
from Repositories.IRepository import IRepository
from Model.cloud import Cloud
from fastapi import HTTPException
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class CloudRepository(IRepository):
    def __init__(self):
        self.collection = MongoDB.db["cloud_users"]

    async def create(self, cloud: Cloud):
        cloud_dict = cloud.__dict__
        cloud_existed = await self.collection.find_one(
            {"account_id": cloud.account_id, "user_id": cloud.user_id}
        )

        if cloud_existed:
            logger.warning(
                "Cloud user already exists for account_id: %s and user_id: %s",
                cloud.account_id,
                cloud.user_id,
            )
            raise HTTPException(status_code=400, detail="Cloud user already exists")

        result = await self.collection.insert_one(cloud_dict)
        return str(result.inserted_id)

    async def found_cloud_accounts(self, user_id):
        result = self.collection.find({"user_id": user_id})

        clouds = []
        async for cloud in result:
            logger.info("Found cloud data: %s", cloud)
            clouds.append(
                Cloud(
                    cloud.get("name"),
                    cloud.get("provider"),
                    cloud.get("identifier"),
                    cloud.get("account_id"),
                    cloud.get("user_id"),
                    cloud.get("description"),
                    cloud.get("created_at"),
                    id=str(cloud.get("_id")),
                )
            )

        if clouds:
            for cloud in clouds:
                logger.info("Found cloud data: %s", cloud.__dict__)
            return clouds
        return None

    async def findById(self, cloud_id):
        cloud = await self.collection.find_one({"_id": ObjectId(cloud_id)})
        if cloud:
            object_id = cloud.get("_id")
            return Cloud(
                name=cloud.get("name"),
                provider=cloud.get("provider"),
                identifier=cloud.get("identifier"),
                account_id=cloud.get("account_id"),
                user_id=cloud.get("user_id"),
                created_at=cloud.get("created_at"),
                description=cloud.get("description"),
                id=str(object_id),
            )
        return None

    async def update(self, cloud_id, cloud: Cloud):
        cloud_dict = cloud.__dict__
        result = await self.collection.update_one(
            {"_id": ObjectId(cloud_id)}, {"$set": cloud_dict}
        )
        return result.modified_count > 0

    async def delete(self, cloud_id):
        result = await self.collection.delete_one({"_id": ObjectId(cloud_id)})
        return result.deleted_count > 0


