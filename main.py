"""Entry point: python main.py [--file PATH]

The start-up steps below (loading the data, handling errors, exit codes) move
into the App class in the next step, leaving only argument parsing here.
"""

import argparse
import sys
from pathlib import Path

from expense_tracker.exceptions import CorruptDataError, ExpenseTrackerError
from expense_tracker.factory import AppFactory
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.storage.base import Storage
from expense_tracker.ui.prompts import confirm


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


def load_data(service: ExpenseService, storage: Storage) -> bool:
    """Load the data file. If it is broken, offer to back it up and start fresh.

    Returns False if the user chose to keep the broken file and exit.
    """
    try:
        service.load()
    except CorruptDataError as err:
        print(f"! {err}")
        if not confirm("Move the broken file aside and start with an empty one?"):
            print("Nothing was changed. Fix the file by hand, or use --file to open another one.")
            return False
        backup_path = storage.backup_corrupt_file()
        print(f"The old file was saved as {backup_path}")
        service.load()
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the app and return an exit code: 0 ok, 1 error, 130 interrupted."""
    # If the terminal can't show a character (e.g. Arabic in an old console),
    # print '?' instead of crashing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = parse_args(argv)
    factory = AppFactory(args.file)
    try:
        storage = factory.create_storage()
        service = factory.create_service(storage)
        if not load_data(service, storage):
            return 1
        print(f"Expense Tracker - data file: {args.file}")
        factory.create_menu(service).run()
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


if __name__ == "__main__":
    sys.exit(main())
