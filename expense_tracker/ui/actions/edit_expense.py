"""Menu option: change the fields of an existing expense."""

from expense_tracker.domain.validation import parse_amount
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui import formatting
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask, parse_id, text_parser
from expense_tracker.ui.user_input import format_user_date, parse_user_date

# Typed at the note editing to remove the note (Enter keeps the current one).
CLEAR_NOTE = "-"


class EditExpenseAction(MenuAction):
    label = "Edit expense"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        expense = self._service.get(ask("Expense id", parse_id))
        print(f"  Editing: {formatting.expense_details(expense)}")
        print(f"  Press Enter to keep the current value. Type '{CLEAR_NOTE}' to clear the note.")
        name = ask("Name", text_parser("Name"), default=expense.name)
        category = ask("Category", text_parser("Category"), default=expense.category)
        amount = ask("Amount", parse_amount, default=str(expense.amount))
        date = ask("Date (DD-MM-YYYY)", parse_user_date, default=format_user_date(expense.date))
        note = ask("Note", text_parser("Note", required=False), default=expense.note)
        if note == CLEAR_NOTE:
            note = ""
        updated = self._service.update(
            expense.id, name=name, category=category, amount=amount, date=date, note=note
        )
        print(f"  Saved: {formatting.expense_details(updated)}")
