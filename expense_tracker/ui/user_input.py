"""User input parsing and formatting."""
import datetime

from expense_tracker.exceptions import ValidationError

# The user types and sees day-month-year with a 4-digit year.
USER_DATE_FORMAT = "%d-%m-%Y"
USER_MONTH_FORMAT = "%m-%Y"


def parse_user_date(raw: str, allow_future: bool = False) -> datetime.date:
    """Turn a date the user typed ('18-10-2026') into a date.

    '/', '.' and spaces are accepted as separators too. Future dates are
    rejected for new expenses (you can't have spent money tomorrow), but
    allowed in filters, e.g. "up to 31-12-2026". The check lives here, not in
    Expense, so an old data file never fails to load because the computer
    clock was changed.
    """
    try:
        parsed = datetime.datetime.strptime(_normalize_separators(raw), USER_DATE_FORMAT)
    except ValueError:
        raise ValidationError(
            f"'{raw}' is not a valid date. Use DD-MM-YYYY, e.g. 18-10-2026."
        ) from None

    value = parsed.date()
    if not allow_future and value > datetime.date.today():
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

