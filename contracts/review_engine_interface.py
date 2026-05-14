from abc import ABC, abstractmethod

class ReviewEngineInterface(ABC):
    @abstractmethod
    def evaluate(self, task: dict) -> dict:
        pass
