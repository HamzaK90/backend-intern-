"""Builds every object the app needs (Factory pattern).

This is the only module that calls the constructors of the storage, the
service, the actions and the menu. The rest of the code only receives
ready-made objects, so switching e.g. JSON to SQLite means changing one line
here and nothing else.
"""

from pathlib import Path

from expense_tracker.app import App
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.storage.base import Storage
from expense_tracker.storage.json_storage import JsonStorage
from expense_tracker.ui.actions.add_expense import AddExpenseAction
from expense_tracker.ui.actions.delete_expense import DeleteExpenseAction
from expense_tracker.ui.actions.edit_expense import EditExpenseAction
from expense_tracker.ui.actions.export_expenses import ExportExpensesAction
from expense_tracker.ui.actions.list_expenses import ListExpensesAction
from expense_tracker.ui.actions.monthly_summary import MonthlySummaryAction
from expense_tracker.ui.menu import Menu


class AppFactory:
    """Creates the app's objects and wires them together."""

    def __init__(self, data_file: Path) -> None:
        self._data_file = data_file

    def create_storage(self) -> Storage:
        """The storage strategy. Change this line to use another storage format."""
        return JsonStorage(self._data_file)

    def create_service(self, storage: Storage) -> ExpenseService:
        return ExpenseService(storage)

    def create_menu(self, service: ExpenseService) -> Menu:
        """The menu options, in the order they are shown."""
        actions = [
            AddExpenseAction(service),
            ListExpensesAction(service),
            EditExpenseAction(service),
            DeleteExpenseAction(service),
            MonthlySummaryAction(service),
            ExportExpensesAction(service),
        ]
        return Menu(actions)

    def create_app(self) -> App:
        """Build the whole object graph: storage -> service -> menu -> App."""
        service = self.create_service(self.create_storage())
        return App(service, self.create_menu(service), self._data_file)
