"""Menu option: export all or filtered expenses to a CSV file."""

import datetime
from pathlib import Path

from expense_tracker.export.csv_exporter import export_csv
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask, ask_filter, confirm


class ExportExpensesAction(MenuAction):
    label = "Export to CSV"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        expense_filter = ask_filter(self._service.categories())
        expenses = self._service.list_expenses(expense_filter)
        if not expenses:
            print("  No expenses to export.")
            return
        default_name = f"expenses-{datetime.date.today().isoformat()}.csv"
        path = ask("File name", lambda raw: Path(raw.strip()), default=default_name)
        if path.exists() and not confirm(f"{path} already exists. Overwrite it?"):
            print("  Export cancelled.")
            return
        count = export_csv(expenses, path)
        print(f"  Exported {count} expenses to {path.resolve()}")
