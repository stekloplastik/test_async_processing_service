from abc import ABC, abstractmethod


class EventBroker(ABC):
    @abstractmethod
    async def publish(self, topic: str, payload: dict) -> None:
        pass
