from abc import ABC, abstractmethod

class IRepository(ABC):
    @abstractmethod
    async def create(self, *args, **kwargs):
        pass

    @abstractmethod
    async def findById(self, *args, **kwargs):
        pass

    @abstractmethod
    async def update(self, *args, **kwargs):
        pass

    @abstractmethod
    async def delete(self, *args, **kwargs):
        pass