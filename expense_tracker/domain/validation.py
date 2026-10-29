"""Validation functions for the Expense Tracker domain."""
import datetime
from decimal import Decimal, InvalidOperation

from expense_tracker.exceptions import ValidationError


# The file stores ISO dates: unambiguous and they sort correctly as text.
STORAGE_DATE_FORMAT = "%Y-%m-%d"
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
