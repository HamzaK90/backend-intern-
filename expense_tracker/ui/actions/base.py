"""The interface every menu option implements."""

from abc import ABC, abstractmethod


class MenuAction(ABC):
    """One menu option: a label to show and a run() to execute."""

    label: str

    @abstractmethod
    def run(self) -> None:
        """Do the action: ask, call the service, print the result."""
