from abc import ABC, abstractmethod


class ILLMAnalyzer(ABC):
    @abstractmethod
    def analyze(self, resources,vulnerabilities,userContext=dict ):
        pass

    def build_prompt(self, resources, vulnerabilities, userContext):
        pass
    
    def parse_response(self, response):
        pass