"""Menu option: list expenses, optionally filtered."""

from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui import formatting
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask_filter


class ListExpensesAction(MenuAction):
    label = "List / filter expenses"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        expense_filter = ask_filter(self._service.categories())
        expenses = self._service.list_expenses(expense_filter)
        print()
        print(formatting.expense_table(expenses))
