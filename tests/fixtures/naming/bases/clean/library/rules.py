"""Lending rules from the library's regulations."""

from datetime import date, timedelta
from decimal import Decimal

LOAN_PERIOD = timedelta(days=14)
MAX_ACTIVE_LOANS = 3
MAX_UNPAID_FINES = Decimal("5.00")
FINE_PER_OVERDUE_DAY = Decimal("0.25")
MAX_FINE_PER_LOAN = Decimal("10.00")


def due_date(borrowed_on: date) -> date:
    return borrowed_on + LOAN_PERIOD


def overdue_fine(due_on: date, returned_on: date) -> Decimal:
    days_overdue = max((returned_on - due_on).days, 0)
    return min(days_overdue * FINE_PER_OVERDUE_DAY, MAX_FINE_PER_LOAN)
