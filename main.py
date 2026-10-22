"""Entry point: python main.py [--file PATH]

Reads the command-line arguments, asks the factory for the app, and runs it.
Everything else (loading, the menu, error handling) lives in expense_tracker.
"""

import argparse
import sys
from pathlib import Path

from expense_tracker.factory import AppFactory


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
    """Build the app and run it. Returns the exit code."""
    args = parse_args(argv)
    app = AppFactory(args.file).create_app()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
