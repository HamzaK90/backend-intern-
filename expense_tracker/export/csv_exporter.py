"""Export expenses to a CSV file that opens in Excel, LibreOffice or Google Sheets."""

import csv
from pathlib import Path

from expense_tracker.exceptions import StorageError
from expense_tracker.domain.expense import Expense

COLUMNS = ["id", "date", "name", "category", "amount", "note"]

# A cell starting with one of these is run as a formula by spreadsheet apps.
FORMULA_PREFIXES = ("=", "+", "-", "@")


def export_csv(expenses: list[Expense], path: Path) -> int:
    """Write the expenses to a CSV file and return how many rows were written.

    - Dates are ISO (YYYY-MM-DD) because every spreadsheet app reads them
      correctly; DD-MM-YYYY gets swapped to MM-DD in US-locale Excel.
    - Encoding is utf-8-sig: the extra BOM makes Excel show non-English
      text (e.g. Arabic) correctly instead of garbled characters.
    """
    path = Path(path)
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)
            for expense in expenses:
                writer.writerow([
                    expense.id,
                    expense.date.isoformat(),
                    _safe_cell(expense.name),
                    _safe_cell(expense.category),
                    str(expense.amount),
                    _safe_cell(expense.note),
                ])
    except OSError as err:
        raise StorageError(f"Could not write {path}: {err.strerror or err}") from None
    return len(expenses)


def _safe_cell(text: str) -> str:
    """Stop text like '=HYPERLINK(...)' from running as a formula when opened.

    Prefixing with an apostrophe makes the spreadsheet treat it as plain text.
    """
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text
