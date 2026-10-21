"""The storage interface: what any way of saving expenses must provide."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from expense_tracker.domain.expense import Expense


@dataclass
class StoredData:
    """Everything a storage keeps: the expenses and the next id to hand out."""

    expenses: list[Expense] = field(default_factory=list)
    next_id: int = 1


class Storage(ABC):
    """Base class for storage strategies (JSON today, SQLite tomorrow)."""

    @abstractmethod
    def load(self) -> StoredData:
        """Return all saved data. Missing data means an empty StoredData."""

    @abstractmethod
    def save(self, data: StoredData) -> None:
        """Replace the saved data with this data."""

    @abstractmethod
    def backup_corrupt_file(self) -> Path:
        """Move broken saved data aside and return where it went."""
