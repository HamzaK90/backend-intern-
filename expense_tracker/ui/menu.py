"""The interactive terminal menu and the app's start-up.

Menu only shows the options and runs the chosen one; what each option does
lives in ui/actions/. Every expected error (ExpenseTrackerError) is caught here
and shown as a short message, so the user never sees a traceback.

The start-up functions below (load_service, parse_args, main) move to app.py
and main.py in a later step.
"""

import argparse
import sys
from pathlib import Path

from expense_tracker.exceptions import CorruptDataError, ExpenseTrackerError
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.storage.json_storage import JsonStorage
from expense_tracker.ui.actions.add_expense import AddExpenseAction
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.actions.delete_expense import DeleteExpenseAction
from expense_tracker.ui.actions.edit_expense import EditExpenseAction
from expense_tracker.ui.actions.export_expenses import ExportExpensesAction
from expense_tracker.ui.actions.list_expenses import ListExpensesAction
from expense_tracker.ui.actions.monthly_summary import MonthlySummaryAction
from expense_tracker.ui.prompts import confirm

EXIT_CHOICE = "0"


class Menu:
    """Shows the options and runs the chosen one. Knows nothing about what they do."""

    def __init__(self, actions: list[MenuAction]) -> None:
        self._actions = actions

    def run(self) -> None:
        """Loop until the user picks Exit. Errors in an action return to the menu."""
        while True:
            self._print_options()
            choice = input("Choose an option: ").strip()
            if choice == EXIT_CHOICE:
                print("Goodbye!")
                return
            action = self._find(choice)
            if action is None:
                print(f"  ! '{choice}' is not an option. Pick a number from the menu.")
                continue
            print(f"\n== {action.label} ==")
            try:
                action.run()
            except ExpenseTrackerError as err:
                print(f"  ! {err}")
            except KeyboardInterrupt:
                # Ctrl+C inside an action cancels it; Ctrl+C at the menu exits.
                print("\n  Cancelled.")

    def _print_options(self) -> None:
        """Number the options by their position in the list, starting at 1."""
        print()
        for number, action in enumerate(self._actions, start=1):
            print(f"  {number}. {action.label}")
        print(f"  {EXIT_CHOICE}. Exit")

    def _find(self, choice: str) -> MenuAction | None:
        """Return the action for a typed number, or None if there is none."""
        if choice.isdigit() and 1 <= int(choice) <= len(self._actions):
            return self._actions[int(choice) - 1]
        return None


# --- Start-up (moves to app.py / main.py later) ------------------------------

def load_service(storage: JsonStorage) -> ExpenseService | None:
    """Load the data file. If it is broken, offer to back it up and start fresh."""
    service = ExpenseService(storage)
    try:
        service.load()
    except CorruptDataError as err:
        print(f"! {err}")
        if not confirm("Move the broken file aside and start with an empty one?"):
            print("Nothing was changed. Fix the file by hand, or use --file to open another one.")
            return None
        backup_path = storage.backup_corrupt_file()
        print(f"The old file was saved as {backup_path}")
        service.load()
    return service


def default_data_file() -> Path:
    """~/.expense_tracker/expenses.json, so the same file is used from any folder.

    Falls back to the current folder if the home folder can't be found.
    """
    try:
        home = Path.home()
    except RuntimeError:
        home = Path.cwd()
    return home / ".expense_tracker" / "expenses.json"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    default_file = default_data_file()
    parser = argparse.ArgumentParser(
        prog="expense_tracker",
        description="Track your personal expenses from the terminal.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=default_file,
        help=f"data file to use (default: {default_file})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the app and return an exit code: 0 ok, 1 error, 130 interrupted."""
    # If the terminal can't show a character (e.g. Arabic in an old console),
    # print '?' instead of crashing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = parse_args(argv)
    try:
        service = load_service(JsonStorage(args.file))
        if service is None:
            return 1
        print(f"Expense Tracker - data file: {args.file}")
        # The order of this list is the order of the menu options.
        actions = [
            AddExpenseAction(service),
            ListExpensesAction(service),
            EditExpenseAction(service),
            DeleteExpenseAction(service),
            MonthlySummaryAction(service),
            ExportExpensesAction(service),
        ]
        Menu(actions).run()
        return 0
    except EOFError:
        # Input was closed (Ctrl+Z on Windows, Ctrl+D elsewhere): a normal exit.
        print("\nGoodbye!")
        return 0
    except KeyboardInterrupt:
        # Ctrl+C at the menu.
        print("\nGoodbye!")
        return 130
    except ExpenseTrackerError as err:
        print(f"! {err}")
        return 1
    except Exception as err:  # last-resort safety net: a bug, not a user error
        print(f"! Unexpected error: {err!r}")
        print("Everything saved before this point is safe in the data file.")
        return 1
