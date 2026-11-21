from abc import ABC, abstractmethod
from typing import Union


class Backend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def generate(self, cir) -> Union[str, dict]:
        pass
