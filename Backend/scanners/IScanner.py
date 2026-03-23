from abc import ABC, abstractmethod

class IScanner(ABC):
    def __init__(self, name):
        self.name = name
   
    def get_name(self):
        return self.name

    
    @abstractmethod
    def get_resources(self) -> list:
        pass
    
    @abstractmethod
    def connect(self,identifier):
        pass
    @abstractmethod
    def scan_resource(self, resource):
        pass
    

