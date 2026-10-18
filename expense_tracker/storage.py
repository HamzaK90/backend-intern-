"""Saving and loading expenses as a JSON file."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from expense_tracker.errors import CorruptDataError, StorageError, ValidationError
from expense_tracker.models import Expense

FILE_VERSION = 1


@dataclass
class StoredData:
    """Everything kept in the data file."""

    expenses: list[Expense] = field(default_factory=list)
    next_id: int = 1


class JsonStorage:
    """Reads and writes the expense file.

    File layout:
        {"version": 1, "next_id": 4, "expenses": [{...}, {...}]}
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> StoredData:
        """Load the file. A missing or empty file means no expenses yet."""
        if not self.path.exists():
            return StoredData()

        text = self._read_text()
        if not text.strip():
            return StoredData()

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as err:
            raise self._corrupt(f"not valid JSON (line {err.lineno}, column {err.colno})")
        return self._parse(raw)

    def save(self, data: StoredData) -> None:
        """Write all data to the file safely.

        We write to a temporary file first and then swap it in with
        os.replace, which is atomic: if the program dies mid-write, the old
        file is still intact instead of half-written.
        """
        content = {
            "version": FILE_VERSION,
            "next_id": data.next_id,
            "expenses": [expense.to_dict() for expense in data.expenses],
        }
        temp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(content, file, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.path)
        except OSError as err:
            self._remove_quietly(temp_path)
            raise StorageError(f"Could not save to {self.path}: {err.strerror or err}") from None

    def backup_corrupt_file(self) -> Path:
        """Move a broken data file aside so the user can start fresh without losing it."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.path.with_name(f"{self.path.stem}.corrupt-{timestamp}{self.path.suffix}")
        try:
            os.replace(self.path, backup_path)
        except OSError as err:
            raise StorageError(f"Could not back up {self.path}: {err.strerror or err}") from None
        return backup_path

    def _read_text(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise self._corrupt("not readable UTF-8 text") from None
        except OSError as err:
            raise StorageError(f"Could not read {self.path}: {err.strerror or err}") from None

    def _parse(self, raw: object) -> StoredData:
        """Turn the loaded JSON into Expense objects, rejecting anything broken.

        A single bad row makes the whole file count as corrupt. Skipping it
        would silently delete that row on the next save.
        """
        if not isinstance(raw, dict) or not isinstance(raw.get("expenses"), list):
            raise self._corrupt("expected an object with an 'expenses' list")

        version = raw.get("version", FILE_VERSION)
        if version != FILE_VERSION:
            raise self._corrupt(f"unsupported file version {version!r}")

        expenses = []
        used_ids = set()
        for position, entry in enumerate(raw["expenses"], start=1):
            try:
                expense = Expense.from_dict(entry)
            except ValidationError as err:
                raise self._corrupt(f"entry #{position}: {err}") from None
            if expense.id in used_ids:
                raise self._corrupt(f"entry #{position}: id {expense.id} is used twice")
            used_ids.add(expense.id)
            expenses.append(expense)

        next_id = self._safe_next_id(raw.get("next_id"), used_ids)
        return StoredData(expenses, next_id)

    @staticmethod
    def _safe_next_id(stored: object, used_ids: set[int]) -> int:
        """Return a next_id that cannot collide with an existing id.

        Unlike expense rows, next_id can always be repaired without losing
        anything, so a missing or wrong value is fixed instead of rejected.
        """
        lowest_safe = max(used_ids, default=0) + 1
        is_valid_int = isinstance(stored, int) and not isinstance(stored, bool)
        if is_valid_int and stored >= lowest_safe:
            return stored
        return lowest_safe

    def _corrupt(self, reason: str) -> CorruptDataError:
        return CorruptDataError(f"The data file {self.path} is broken: {reason.rstrip('.')}.")

    @staticmethod
    def _remove_quietly(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
