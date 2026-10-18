"""The Expense model and the rules for what counts as a valid expense."""

import datetime
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from expense_tracker.errors import ValidationError

# The file stores ISO dates: unambiguous and they sort correctly as text.
STORAGE_DATE_FORMAT = "%Y-%m-%d"
# The user types and sees day-month-year with a 4-digit year.
USER_DATE_FORMAT = "%d-%m-%Y"
USER_MONTH_FORMAT = "%m-%Y"
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("1000000000")
MAX_TEXT_LENGTH = 100


def parse_amount(raw: str) -> Decimal:
    """Turn text like '12.5' into a validated Decimal amount."""
    if not isinstance(raw, str):
        raise ValidationError("Amount must be text like 12.50.")
    try:
        amount = Decimal(raw.strip())
    except InvalidOperation:
        raise ValidationError(f"'{raw}' is not a number. Use digits like 12.50.") from None
    return validate_amount(amount)


def validate_amount(amount: Decimal) -> Decimal:
    """Check an amount is a positive, finite value with at most 2 decimals."""
    if not amount.is_finite():
        raise ValidationError("Amount must be a real number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValidationError(f"Amount cannot be more than {MAX_AMOUNT}.")
    if amount != amount.quantize(CENT):
        raise ValidationError("Amount can have at most 2 decimal places.")
    return amount.quantize(CENT)


def parse_stored_date(raw: str) -> datetime.date:
    """Turn an ISO date from the data file ('2026-10-18') into a date."""
    if not isinstance(raw, str):
        raise ValidationError("Date must be text in the form YYYY-MM-DD.")
    try:
        parsed = datetime.datetime.strptime(raw.strip(), STORAGE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(f"'{raw}' is not a valid stored date.") from None
    return parsed.date()


def parse_user_date(raw: str) -> datetime.date:
    """Turn a date the user typed ('18-10-2026') into a date.

    '/', '.' and spaces are accepted as separators too. Future dates are
    rejected here, not in Expense, so an old data file never fails to load
    just because the computer clock was changed.
    """
    try:
        parsed = datetime.datetime.strptime(_normalize_separators(raw), USER_DATE_FORMAT)
    except ValueError:
        raise ValidationError(
            f"'{raw}' is not a valid date. Use DD-MM-YYYY, e.g. 18-10-2026."
        ) from None

    value = parsed.date()
    if value > datetime.date.today():
        raise ValidationError("Date cannot be in the future.")
    return value


def parse_user_month(raw: str) -> tuple[int, int]:
    """Turn a month the user typed ('10-2026') into (year, month)."""
    try:
        parsed = datetime.datetime.strptime(_normalize_separators(raw), USER_MONTH_FORMAT)
    except ValueError:
        raise ValidationError(
            f"'{raw}' is not a valid month. Use MM-YYYY, e.g. 10-2026."
        ) from None
    return parsed.year, parsed.month


def format_user_date(value: datetime.date) -> str:
    """Show a date the way the user types it."""
    return value.strftime(USER_DATE_FORMAT)


def _normalize_separators(raw: str) -> str:
    """Let the user type '/', '.' or spaces instead of '-' in dates."""
    cleaned = raw.strip()
    for separator in ("/", ".", " "):
        cleaned = cleaned.replace(separator, "-")
    return cleaned


def clean_text(value: str, field_name: str, required: bool = True) -> str:
    """Strip whitespace and check a text field's length."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be text.")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field_name} cannot be empty.")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValidationError(f"{field_name} cannot be longer than {MAX_TEXT_LENGTH} characters.")
    return value


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
