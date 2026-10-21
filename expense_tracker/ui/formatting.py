"""Turning expenses and summaries into text for the terminal.

These functions only build strings; printing happens in ui/menu.py. That keeps
them easy to test and reuse.
"""

from decimal import Decimal

from expense_tracker.domain.expense import Expense, format_user_date
from expense_tracker.services.monthly_report import MonthlySummary

MAX_CELL_WIDTH = 30
BAR_CHAR = "#"  # plain ASCII: works in every Windows console


def format_amount(amount: Decimal) -> str:
    """12345.5 -> '12,345.50'."""
    return f"{amount:,.2f}"


def expense_table(expenses: list[Expense]) -> str:
    """A text table of expenses with a total line underneath."""
    if not expenses:
        return "No expenses found."

    headers = ["ID", "Date", "Category", "Amount", "Name", "Note"]
    rows = [
        [
            str(e.id),
            format_user_date(e.date),
            e.category,
            format_amount(e.amount),
            e.name,
            e.note,
        ]
        for e in expenses
    ]
    right_aligned = {0, 3}  # ID and Amount line up better on the right
    lines = _table(headers, rows, right_aligned)

    total = sum((e.amount for e in expenses), Decimal("0"))
    count = len(expenses)
    lines.append(f"{count} expense{'s' if count != 1 else ''}, total {format_amount(total)}")
    return "\n".join(lines)


def expense_details(expense: Expense) -> str:
    """One expense on a single readable line, e.g. for confirmations."""
    text = (
        f"#{expense.id}  {format_user_date(expense.date)}  {expense.name}"
        f"  ({expense.category})  {format_amount(expense.amount)}"
    )
    if expense.note:
        text += f"  - {expense.note}"
    return text


def summary_report(summary: MonthlySummary) -> str:
    """Total for the month plus a per-category breakdown with bars."""
    title = f"{summary.month_name}: total {format_amount(summary.total)} ({summary.count} expenses)"
    if not summary.by_category:
        return f"{title}\nNo expenses in this month."

    headers = ["Category", "Count", "Total", "%", ""]
    rows = [
        [
            row.category,
            str(row.count),
            format_amount(row.total),
            f"{row.percent}",
            BAR_CHAR * max(1, round(row.percent / 5)),  # 20 chars = 100%
        ]
        for row in summary.by_category
    ]
    lines = [title, ""] + _table(headers, rows, right_aligned={1, 2, 3})
    return "\n".join(lines)


def _table(headers: list[str], rows: list[list[str]], right_aligned: set[int]) -> list[str]:
    """Lay out rows in columns as wide as their widest cell."""
    rows = [[_shorten(cell) for cell in row] for row in rows]
    widths = [
        max([len(header)] + [len(row[i]) for row in rows])
        for i, header in enumerate(headers)
    ]

    def format_row(cells: list[str]) -> str:
        parts = [
            cell.rjust(widths[i]) if i in right_aligned else cell.ljust(widths[i])
            for i, cell in enumerate(cells)
        ]
        return "  ".join(parts).rstrip()

    separator = "  ".join("-" * width for width in widths)
    return [format_row(headers), separator] + [format_row(row) for row in rows]


def _shorten(text: str) -> str:
    """Cut long cells so one long note doesn't break the whole table."""
    if len(text) <= MAX_CELL_WIDTH:
        return text
    return text[: MAX_CELL_WIDTH - 3] + "..."
