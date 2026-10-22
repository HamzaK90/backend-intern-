"""Menu option: delete an expense after confirmation."""

from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui import formatting
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask, confirm, parse_id


class DeleteExpenseAction(MenuAction):
    label = "Delete expense"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        expense = self._service.get(ask("Expense id", parse_id))
        print(f"  {formatting.expense_details(expense)}")
        if not confirm("Delete this expense?"):
            print("  Nothing deleted.")
            return
        self._service.delete(expense.id)
        print(f"  Deleted expense #{expense.id}.")
