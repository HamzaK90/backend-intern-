"""A filter is a list of rules; an expense must pass all of them."""

from expense_tracker.domain.expense import Expense
from expense_tracker.filters.rules import Rule


class ExpenseFilter:
    """Combines any number of rules into one check.

    An expense matches when it passes every rule. No rules means everything
    matches, so ExpenseFilter() is "show all".
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self._rules = list(rules or [])

    def matches(self, expense: Expense) -> bool:
        return all(rule.matches(expense) for rule in self._rules)
