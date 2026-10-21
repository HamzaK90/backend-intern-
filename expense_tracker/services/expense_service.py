"""The operations a user can perform on their expenses."""

import dataclasses
import datetime
from dataclasses import dataclass
from decimal import Decimal

from expense_tracker.exceptions import ExpenseNotFoundError, ValidationError
from expense_tracker.domain.expense import Expense
from expense_tracker.services.monthly_report import MonthlySummary, month_range, summarize_month
from expense_tracker.storage.base import StoredData, Storage


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


class ExpenseService:
    """Holds the user's expenses in memory and saves every change to storage."""
    
    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._expenses: list[Expense] = []
        self._next_id = 1
        self._loaded = False

    def load(self) -> None:
        """Read the saved data. Must be called before anything else."""
        data = self._storage.load()
        self._expenses = data.expenses
        self._next_id = data.next_id
        self._loaded = True

    def add(
        self,
        name: str,
        category: str,
        amount: Decimal,
        date: datetime.date,
        note: str = "",
    ) -> Expense:
        """Record a new expense and return it (with its new id)."""
        expense = Expense(self._next_id, name, category, amount, date, note)
        self._commit(self._expenses + [expense], self._next_id + 1)
        return expense

    def get(self, expense_id: int) -> Expense:
        """Return the expense with this id, or raise ExpenseNotFoundError."""
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise ExpenseNotFoundError(f"No expense with id {expense_id}.")

    def update(
        self,
        expense_id: int,
        *,
        name: str | None = None,
        category: str | None = None,
        amount: Decimal | None = None,
        date: datetime.date | None = None,
        note: str | None = None,
    ) -> Expense:
        """Change some fields of an expense. Fields left as None stay the same."""
        old = self.get(expense_id)
        changes = {
            "name": name,
            "category": category,
            "amount": amount,
            "date": date,
            "note": note,
        }
        changes = {field: value for field, value in changes.items() if value is not None}
        # replace() builds a new Expense, so __post_init__ validates the changes.
        new = dataclasses.replace(old, **changes)
        updated_list = [new if e.id == expense_id else e for e in self._expenses]
        self._commit(updated_list, self._next_id)
        return new

    def delete(self, expense_id: int) -> Expense:
        """Remove an expense and return it, or raise ExpenseNotFoundError."""
        removed = self.get(expense_id)
        remaining = [e for e in self._expenses if e.id != expense_id]
        self._commit(remaining, self._next_id)
        return removed

    def list_expenses(self, expense_filter: ExpenseFilter | None = None) -> list[Expense]:
        """Return matching expenses, oldest first (like a bank statement)."""
        expense_filter = expense_filter or ExpenseFilter()
        matching = [e for e in self._expenses if expense_filter.matches(e)]
        return sorted(matching, key=lambda e: (e.date, e.id))

    def monthly_summary(self, year: int, month: int) -> MonthlySummary:
        """Total and per-category spending for one month."""
        first_day, last_day = month_range(year, month)
        month_filter = ExpenseFilter(start_date=first_day, end_date=last_day)
        return summarize_month(self.list_expenses(month_filter), year, month)

    def categories(self) -> list[str]:
        """Return every category used so far, alphabetically."""
        return sorted({e.category for e in self._expenses})

    def _commit(self, expenses: list[Expense], next_id: int) -> None:
        """Save the new state, and only keep it in memory if the save worked.

        If saving fails, StorageError propagates and memory still matches the
        file, so the user never sees an expense that wasn't actually saved.
        """
        if not self._loaded:
            raise RuntimeError("load() must be called before changing expenses.")

        self._storage.save(StoredData(expenses, next_id))
        self._expenses = expenses
        self._next_id = next_id
