"""The Expense model: one expense and its conversion to and from JSON."""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from expense_tracker.exceptions import ValidationError
from expense_tracker.domain.validation import clean_text, parse_amount, parse_stored_date, validate_amount


@dataclass
class Expense:
    """One row in the expense table.

    Validation runs in __post_init__, so an Expense object is always valid,
    whether it was built from user input or loaded from the data file.
    """

    id: int
    name: str
    category: str
    amount: Decimal
    date: datetime.date
    note: str = ""

    def __post_init__(self) -> None:
        # bool is a subclass of int, so True would otherwise pass as id 1.
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id < 1:
            raise ValidationError("Expense id must be a positive whole number.")
        if not isinstance(self.amount, Decimal):
            raise ValidationError("Amount must be a Decimal.")
        # datetime is a subclass of date; we only want plain dates.
        if isinstance(self.date, datetime.datetime) or not isinstance(self.date, datetime.date):
            raise ValidationError("Date must be a date.")

        self.name = clean_text(self.name, "Name")
        # Lowercase so "Food", "food " and "FOOD" are one category in summaries.
        self.category = clean_text(self.category, "Category").lower()
        self.note = clean_text(self.note, "Note", required=False)
        self.amount = validate_amount(self.amount)

    def to_dict(self) -> dict:
        """Convert to JSON-safe types. Amount is a string so no precision is lost."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "amount": str(self.amount),
            "date": self.date.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Build an Expense from a dict loaded from the data file."""
        if not isinstance(data, dict):
            raise ValidationError("Expense entry must be a JSON object.")
        try:
            return cls(
                id=data["id"],
                name=data["name"],
                category=data["category"],
                amount=parse_amount(data["amount"]),
                date=parse_stored_date(data["date"]),
                note=data.get("note", ""),
            )
        except KeyError as missing:
            raise ValidationError(f"Expense entry is missing the field {missing}.") from None
