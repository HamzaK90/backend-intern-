"""Menu option: add a new expense."""

import datetime

from expense_tracker.domain.validation import parse_amount
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui import formatting
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask, text_parser
from expense_tracker.ui.user_input import format_user_date, parse_user_date


class AddExpenseAction(MenuAction):
    label = "Add expense"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        categories = self._service.categories()
        if categories:
            print(f"  Existing categories: {', '.join(categories)}")
        name = ask("Name", text_parser("Name"))
        category = ask("Category", text_parser("Category"))
        amount = ask("Amount", parse_amount)
        today = format_user_date(datetime.date.today())
        date = ask("Date (DD-MM-YYYY)", parse_user_date, default=today)
        note = ask("Note (optional)", text_parser("Note", required=False), default="")
        expense = self._service.add(name, category, amount, date, note)
        print(f"  Added: {formatting.expense_details(expense)}")
