"""
Zesty OS
Base AI Provider
Version: 1.1

Mission 17
Updated Interface
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> dict:
        """
        Generate a response from the AI provider.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict:
        """
        Return provider health information.
        """
        raise NotImplementedError

    @abstractmethod
    def supports_vision(self) -> bool:
        """
        Return True if provider supports image understanding.
        """
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        """
        Return provider name.
        """
        raise NotImplementedError


if __name__ == "__main__":
    print("BaseProvider Interface Ready")