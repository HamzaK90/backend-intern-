"""Filter rules: each class checks one condition on an expense.

Every rule has the same interface, matches(expense) -> bool, so ExpenseFilter
can run any mix of them without knowing which kinds it holds. A new kind of
filter is a new Rule subclass; nothing else has to change.
"""

import datetime
from abc import ABC, abstractmethod
from decimal import Decimal

from expense_tracker.domain.expense import Expense
from expense_tracker.exceptions import ValidationError


class Rule(ABC):
    """One condition an expense must pass."""

    @abstractmethod
    def matches(self, expense: Expense) -> bool:
        """Return True if the expense passes this condition."""


class CategoryRule(Rule):
    """The expense is in exactly this category (not case-sensitive)."""

    def __init__(self, category: str) -> None:
        # Match the way Expense stores categories (stripped, lowercase).
        self._category = category.strip().lower()

    def matches(self, expense: Expense) -> bool:
        return expense.category == self._category


class DateRangeRule(Rule):
    """The expense date is on or between the given dates. None leaves that side open."""

    def __init__(self, start: datetime.date | None = None, end: datetime.date | None = None) -> None:
        if start is not None and end is not None and start > end:
            raise ValidationError("Start date must be before end date.")
        self._start = start
        self._end = end

    def matches(self, expense: Expense) -> bool:
        if self._start is not None and expense.date < self._start:
            return False
        if self._end is not None and expense.date > self._end:
            return False
        return True


class AmountRangeRule(Rule):
    """The amount is between the given limits (inclusive). None leaves that side open."""

    def __init__(self, minimum: Decimal | None = None, maximum: Decimal | None = None) -> None:
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError("Minimum amount must be less than maximum amount.")
        self._minimum = minimum
        self._maximum = maximum

    def matches(self, expense: Expense) -> bool:
        if self._minimum is not None and expense.amount < self._minimum:
            return False
        if self._maximum is not None and expense.amount > self._maximum:
            return False
        return True


class TextSearchRule(Rule):
    """The name or the note contains the text (not case-sensitive)."""

    def __init__(self, text: str) -> None:
        self._text = text.strip().lower()

    def matches(self, expense: Expense) -> bool:
        return self._text in f"{expense.name} {expense.note}".lower()
