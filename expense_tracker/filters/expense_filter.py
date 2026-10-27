"""Conditions for narrowing down the expense list."""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from expense_tracker.domain.expense import Expense
from expense_tracker.exceptions import ValidationError


@dataclass
class ExpenseFilter:
    """Conditions for narrowing down the expense list.

    Every field is optional; None means "don't filter on this".
    """

    category: str | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    search: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None

    def __post_init__(self) -> None:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Start date must be before end date.")
        has_both_amounts = self.min_amount is not None and self.max_amount is not None
        if has_both_amounts and self.min_amount > self.max_amount:
            raise ValidationError("Minimum amount must be less than maximum amount.")
        # Match the way Expense stores categories (stripped, lowercase).
        if self.category:
            self.category = self.category.strip().lower()

    def matches(self, expense: Expense) -> bool:
        """Return True if the expense passes every condition that is set."""
        if self.category and expense.category != self.category:
            return False
        if self.start_date and expense.date < self.start_date:
            return False
        if self.end_date and expense.date > self.end_date:
            return False
        if self.min_amount is not None and expense.amount < self.min_amount:
            return False
        if self.max_amount is not None and expense.amount > self.max_amount:
            return False
        if self.search:
            text = f"{expense.name} {expense.note}".lower()
            if self.search.strip().lower() not in text:
                return False
        return True
