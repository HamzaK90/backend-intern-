"""The interactive terminal menu: prompts, actions and error handling.

This is the only module that reads input or prints. Every expected error
(ExpenseTrackerError) is caught here and shown as a short message, so the
user never sees a traceback.
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import Callable, TypeVar

from expense_tracker import display
from expense_tracker.exceptions import CorruptDataError, ExpenseTrackerError, ValidationError
from expense_tracker.exporter import export_csv
from expense_tracker.models import (
    USER_MONTH_FORMAT,
    clean_text,
    format_user_date,
    parse_amount,
    parse_user_date,
    parse_user_month,
)
from expense_tracker.storage import JsonStorage
from expense_tracker.tracker import ExpenseFilter, ExpenseTracker

CLEAR_NOTE = "-"

T = TypeVar("T")


# --- Input helpers ---------------------------------------------------------

def ask(label: str, parse: Callable[[str], T], default: str | None = None) -> T:
    """Ask until the answer parses. Enter accepts the default, if there is one."""
    hint = f" [{default}]" if default else ""
    while True:
        raw = input(f"{label}{hint}: ")
        if not raw.strip() and default is not None:
            raw = default
        try:
            return parse(raw)
        except ValidationError as err:
            print(f"  ! {err}")


def ask_optional(label: str, parse: Callable[[str], T]) -> T | None:
    """Like ask(), but Enter means "skip" and returns None."""
    while True:
        raw = input(f"{label} (Enter to skip): ")
        if not raw.strip():
            return None
        try:
            return parse(raw)
        except ValidationError as err:
            print(f"  ! {err}")


def confirm(question: str) -> bool:
    """Yes/no question. Anything other than y/yes counts as no (the safe answer)."""
    return input(f"{question} [y/N]: ").strip().lower() in ("y", "yes")


def parse_id(raw: str) -> int:
    raw = raw.strip()
    if not raw.isdigit() or int(raw) < 1:
        raise ValidationError(f"'{raw}' is not a valid id. Use a positive whole number.")
    return int(raw)


def text_parser(field_name: str, required: bool = True) -> Callable[[str], str]:
    """Make a parser for a text field, e.g. text_parser("Name")."""
    return lambda raw: clean_text(raw, field_name, required)


def parse_future_ok_date(raw: str) -> datetime.date:
    return parse_user_date(raw, allow_future=True)


# --- The menu --------------------------------------------------------------

class ExpenseApp:
    """The main menu loop. Each menu entry maps to one method."""

    def __init__(self, tracker: ExpenseTracker) -> None:
        self.tracker = tracker
        self.menu = {
            "1": ("Add expense", self.add_expense),
            "2": ("List / filter expenses", self.list_expenses),
            "3": ("Edit expense", self.edit_expense),
            "4": ("Delete expense", self.delete_expense),
            "5": ("Monthly summary", self.monthly_summary),
            "6": ("Export to CSV", self.export),
            "0": ("Exit", None),
        }

    def run(self) -> None:
        while True:
            self._print_menu()
            choice = input("Choose an option: ").strip()
            if choice not in self.menu:
                print(f"  ! '{choice}' is not an option. Pick a number from the menu.")
                continue
            label, action = self.menu[choice]
            if action is None:
                print("Goodbye!")
                return
            print(f"\n== {label} ==")
            try:
                action()
            except ExpenseTrackerError as err:
                print(f"  ! {err}")
            except KeyboardInterrupt:
                # Ctrl+C inside an action cancels it; Ctrl+C at the menu exits.
                print("\n  Cancelled.")

    def _print_menu(self) -> None:
        print()
        for key, (label, _) in self.menu.items():
            print(f"  {key}. {label}")

    # --- Actions -----------------------------------------------------------

    def add_expense(self) -> None:
        categories = self.tracker.categories()
        if categories:
            print(f"  Existing categories: {', '.join(categories)}")
        name = ask("Name", text_parser("Name"))
        category = ask("Category", text_parser("Category"))
        amount = ask("Amount", parse_amount)
        date = ask("Date (DD-MM-YYYY)", parse_user_date, default=format_user_date(datetime.date.today()))
        note = ask("Note (optional)", text_parser("Note", required=False), default="")
        expense = self.tracker.add(name, category, amount, date, note)
        print(f"  Added: {display.expense_details(expense)}")

    def list_expenses(self) -> None:
        expense_filter = self._ask_filter()
        print()
        print(display.expense_table(self.tracker.list_expenses(expense_filter)))

    def edit_expense(self) -> None:
        expense = self.tracker.get(ask("Expense id", parse_id))
        print(f"  Editing: {display.expense_details(expense)}")
        print(f"  Press Enter to keep the current value. Type '{CLEAR_NOTE}' to clear the note.")
        name = ask("Name", text_parser("Name"), default=expense.name)
        category = ask("Category", text_parser("Category"), default=expense.category)
        amount = ask("Amount", parse_amount, default=str(expense.amount))
        date = ask("Date (DD-MM-YYYY)", parse_user_date, default=format_user_date(expense.date))
        note = ask("Note", text_parser("Note", required=False), default=expense.note)
        if note == CLEAR_NOTE:
            note = ""
        updated = self.tracker.update(
            expense.id, name=name, category=category, amount=amount, date=date, note=note
        )
        print(f"  Saved: {display.expense_details(updated)}")

    def delete_expense(self) -> None:
        expense = self.tracker.get(ask("Expense id", parse_id))
        print(f"  {display.expense_details(expense)}")
        if not confirm("Delete this expense?"):
            print("  Nothing deleted.")
            return
        self.tracker.delete(expense.id)
        print(f"  Deleted expense #{expense.id}.")

    def monthly_summary(self) -> None:
        this_month = datetime.date.today().strftime(USER_MONTH_FORMAT)
        year, month = ask("Month (MM-YYYY)", parse_user_month, default=this_month)
        print()
        print(display.summary_report(self.tracker.monthly_summary(year, month)))

    def export(self) -> None:
        expense_filter = self._ask_filter()
        expenses = self.tracker.list_expenses(expense_filter)
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

    def _ask_filter(self) -> ExpenseFilter:
        """Ask for optional filters. Answering 'y' to the first question skips them all."""
        if confirm("Include all expenses?"):
            return ExpenseFilter()
        categories = self.tracker.categories()
        if categories:
            print(f"  Categories: {', '.join(categories)}")
        while True:
            try:
                return ExpenseFilter(
                    category=ask_optional("Category", text_parser("Category")),
                    start_date=ask_optional("From date (DD-MM-YYYY)", parse_future_ok_date),
                    end_date=ask_optional("To date (DD-MM-YYYY)", parse_future_ok_date),
                    search=ask_optional("Search name/note", text_parser("Search")),
                    min_amount=ask_optional("Minimum amount", parse_amount),
                    max_amount=ask_optional("Maximum amount", parse_amount),
                )
            except ValidationError as err:
                # e.g. "from" date after "to" date: ask the filters again.
                print(f"  ! {err}")


# --- Startup ---------------------------------------------------------------

def load_tracker(storage: JsonStorage) -> ExpenseTracker | None:
    """Load the data file. If it is broken, offer to back it up and start fresh."""
    try:
        return ExpenseTracker(storage)
    except CorruptDataError as err:
        print(f"! {err}")
        if not confirm("Move the broken file aside and start with an empty one?"):
            print("Nothing was changed. Fix the file by hand, or use --file to open another one.")
            return None
        backup_path = storage.backup_corrupt_file()
        print(f"The old file was saved as {backup_path}")
        return ExpenseTracker(storage)


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
        tracker = load_tracker(JsonStorage(args.file))
        if tracker is None:
            return 1
        print(f"Expense Tracker - data file: {args.file}")
        ExpenseApp(tracker).run()
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
