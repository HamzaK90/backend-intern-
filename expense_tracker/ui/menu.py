"""The interactive terminal menu.

Menu only shows the options and runs the chosen one; what each option does
lives in ui/actions/. Every expected error (ExpenseTrackerError) raised by an
action is caught here and shown as a short message, so the user never sees a
traceback and goes back to the menu.
"""

from expense_tracker.exceptions import ExpenseTrackerError
from expense_tracker.ui.actions.base import MenuAction

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
