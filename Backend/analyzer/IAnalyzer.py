from abc import ABC, abstractmethod

class IAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, resources:list):
        pass