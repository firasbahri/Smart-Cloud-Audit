from abc import ABC, abstractmethod

class IRepository(ABC):
    @abstractmethod
    def create(self, item):
        pass

    @abstractmethod
    def findById(self, item_id):
        pass

    @abstractmethod
    def update(self, item_id, item):
        pass

    @abstractmethod
    def delete(self, item_id):
        pass