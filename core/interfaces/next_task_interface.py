from abc import ABC, abstractmethod
from ...models.schemas import ReviewOutput
from ...models.orchestration import V2NextTask

class NextTaskGeneratorInterface(ABC):
    @abstractmethod
    def generate_next_task(self, review: ReviewOutput, classification: str) -> V2NextTask:
        pass
