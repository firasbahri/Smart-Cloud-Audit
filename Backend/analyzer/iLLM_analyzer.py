from abc import ABC, abstractmethod


class ILLMAnalyzer(ABC):
    @abstractmethod
    def analyze(self, resources,vulnerabilities,userContext=dict ):
        pass

    def build_analyze_prompt(self, resources, vulnerabilities, userContext):
        pass
    
    def parse_analyze_response(self, response):
        pass