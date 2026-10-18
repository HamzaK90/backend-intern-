"""Monthly spending summaries.

These are plain functions over a list of expenses: they never touch the
file, which makes them easy to test and reuse.
"""

import calendar
import datetime
from dataclasses import dataclass
from decimal import Decimal

from expense_tracker.models import Expense

ZERO = Decimal("0.00")


@dataclass
class CategoryTotal:
    """How much was spent in one category."""

    category: str
    total: Decimal
    count: int
    percent: Decimal


@dataclass
class MonthlySummary:
    """Answers "How much did I spend this month, and on what?"."""

    year: int
    month: int
    total: Decimal
    count: int
    by_category: list[CategoryTotal]

    @property
    def month_name(self) -> str:
        return f"{calendar.month_name[self.month]} {self.year}"


def month_range(year: int, month: int) -> tuple[datetime.date, datetime.date]:
    """Return the first and last day of a month."""
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, 1), datetime.date(year, month, last_day)


def summarize_month(expenses: list[Expense], year: int, month: int) -> MonthlySummary:
    """Group one month's expenses by category, biggest spending first.

    The caller passes only that month's expenses (ExpenseTracker does the
    filtering).
    """
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for expense in expenses:
        totals[expense.category] = totals.get(expense.category, ZERO) + expense.amount
        counts[expense.category] = counts.get(expense.category, 0) + 1

    grand_total = sum(totals.values(), ZERO)
    by_category = [
        CategoryTotal(
            category=category,
            total=total,
            count=counts[category],
            percent=_percent(total, grand_total),
        )
        for category, total in totals.items()
    ]
    # Biggest spending first; ties sorted alphabetically.
    by_category.sort(key=lambda row: (-row.total, row.category))

    return MonthlySummary(year, month, grand_total, len(expenses), by_category)


def _percent(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO:
        return ZERO
    return (part / whole * 100).quantize(Decimal("0.1"))
