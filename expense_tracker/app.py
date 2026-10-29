"""The running application (Singleton pattern).

App owns the start-up: loading the data (with the broken-file prompt), running
the menu, catching anything that reaches the top, and turning the outcome into
an exit code. Only one App can exist, so there is exactly one owner of the
data file while the program runs.
"""

import sys
from pathlib import Path

from expense_tracker.exceptions import CorruptDataError, ExpenseTrackerError
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui.menu import Menu
from expense_tracker.ui.prompts import confirm

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130


class App:
    """The application. Every App(...) call returns the same single instance."""

    _instance: "App | None" = None

    def __new__(cls, *args, **kwargs):
        # __new__ creates the object, before __init__ runs. Create it only the
        # first time; afterwards always hand back that same object.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, service: ExpenseService, menu: Menu, data_file: Path) -> None:
        # Python calls __init__ after every App(...), even when __new__ returned
        # the existing object, so only set it up the first time.
        if self._initialized:
            return
        self._service = service
        self._menu = menu
        self._data_file = data_file
        self._initialized = True

    def run(self) -> int:
        """Load the data, run the menu, and return the exit code."""
        # If the terminal can't show a character (e.g. Arabic in an old
        # console), print '?' instead of crashing.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        try:
            if not self._load_data():
                return EXIT_ERROR
            print(f"Expense Tracker - data file: {self._data_file}")
            self._menu.run()
            return EXIT_OK
        except EOFError:
            # Input was closed (Ctrl+Z on Windows, Ctrl+D elsewhere): a normal exit.
            print("\nGoodbye!")
            return EXIT_OK
        except KeyboardInterrupt:
            # Ctrl+C at the menu.
            print("\nGoodbye!")
            return EXIT_INTERRUPTED
        except ExpenseTrackerError as err:
            print(f"! {err}")
            return EXIT_ERROR
        except Exception as err:  # last-resort safety net: a bug, not a user error
            print(f"! Unexpected error: {err!r}")
            print("Everything saved before this point is safe in the data file.")
            return EXIT_ERROR

    def _load_data(self) -> bool:
        """Load the data. If it is broken, offer to back it up and start fresh.

        Returns False if the user chose to keep the broken file and exit.
        """
        try:
            self._service.load()
        except CorruptDataError as err:
            print(f"! {err}")
            if not confirm("Move the broken file aside and start with an empty one?"):
                print("Nothing was changed. Fix the file by hand, or use --file to open another one.")
                return False
            backup_path = self._service.recover_from_corrupt_data()
            print(f"The old file was saved as {backup_path}")
        return True
