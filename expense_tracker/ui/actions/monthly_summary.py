"""Menu option: total and per-category spending for one month."""

import datetime

from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.ui import formatting
from expense_tracker.ui.actions.base import MenuAction
from expense_tracker.ui.prompts import ask
from expense_tracker.ui.user_input import USER_MONTH_FORMAT, parse_user_month


class MonthlySummaryAction(MenuAction):
    label = "Monthly summary"

    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    def run(self) -> None:
        this_month = datetime.date.today().strftime(USER_MONTH_FORMAT)
        year, month = ask("Month (MM-YYYY)", parse_user_month, default=this_month)
        summary = self._service.monthly_summary(year, month)
        print()
        print(formatting.summary_report(summary))
