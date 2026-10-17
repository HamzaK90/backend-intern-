"""Exceptions raised by the app.

Every error the user can cause inherits from ExpenseTrackerError, so the
menu loop can catch that one type and show a friendly message instead of a
traceback.
"""


class ExpenseTrackerError(Exception):
    """Base class for all expected errors in the app."""


class ValidationError(ExpenseTrackerError):
    """A value (amount, date, name, ...) is not acceptable."""


class ExpenseNotFoundError(ExpenseTrackerError):
    """No expense exists with the requested id."""


class StorageError(ExpenseTrackerError):
    """The data file could not be read or written."""
