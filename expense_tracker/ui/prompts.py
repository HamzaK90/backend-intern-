"""helper functions for asking the user for input, with validation and error messages."""

import datetime
from typing import Callable, TypeVar

from expense_tracker.domain.validation import clean_text, parse_amount
from expense_tracker.exceptions import ValidationError
from expense_tracker.filters.expense_filter import ExpenseFilter
from expense_tracker.filters.rules import (
    AmountRangeRule,
    CategoryRule,
    DateRangeRule,
    Rule,
    TextSearchRule,
)
from expense_tracker.ui.user_input import parse_user_date

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


def ask_filter(categories: list[str]) -> ExpenseFilter:
    """Ask for optional filters. Answering 'y' to the first question skips them all."""
    if confirm("Include all expenses?"):
        return ExpenseFilter()
    if categories:
        print(f"  Categories: {', '.join(categories)}")
    while True:
        try:
            return ExpenseFilter(_ask_rules())
        except ValidationError as err:
            # e.g. "from" date after "to" date: ask the filters again.
            print(f"  ! {err}")


def _ask_rules() -> list[Rule]:
    """Ask each optional filter and build a rule only for the ones answered."""
    rules: list[Rule] = []

    category = ask_optional("Category", text_parser("Category"))
    if category:
        rules.append(CategoryRule(category))

    start = ask_optional("From date (DD-MM-YYYY)", parse_future_ok_date)
    end = ask_optional("To date (DD-MM-YYYY)", parse_future_ok_date)
    if start or end:
        rules.append(DateRangeRule(start, end))

    search = ask_optional("Search name/note", text_parser("Search"))
    if search:
        rules.append(TextSearchRule(search))

    minimum = ask_optional("Minimum amount", parse_amount)
    maximum = ask_optional("Maximum amount", parse_amount)
    if minimum is not None or maximum is not None:
        rules.append(AmountRangeRule(minimum, maximum))

    return rules


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
