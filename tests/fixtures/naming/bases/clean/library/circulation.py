"""Circulation: lending books, taking them back and queuing holds."""

from datetime import date
from decimal import Decimal
from enum import Enum

from .mail import Mailer
from .models import Hold, Loan
from .rules import MAX_ACTIVE_LOANS, MAX_UNPAID_FINES, due_date, overdue_fine
from .storage import Storage


class Refusal(Enum):
    UNKNOWN_MEMBER = "unknown_member"
    UNKNOWN_BOOK = "unknown_book"
    TOO_MANY_LOANS = "too_many_loans"
    UNPAID_FINES = "unpaid_fines"
    NO_FREE_COPY = "no_free_copy"
    HELD_FOR_ANOTHER_MEMBER = "held_for_another_member"
    ALREADY_HELD = "already_held"


class RefusalError(Exception):
    """The library rules forbid the requested operation."""

    def __init__(self, reason: Refusal) -> None:
        super().__init__(reason.value)
        self.reason = reason


class Circulation:
    def __init__(self, storage: Storage, mailer: Mailer) -> None:
        self._storage = storage
        self._mailer = mailer

    def lend(self, member_id: int, isbn: str, today: date, *, ignore_holds: bool = False) -> Loan:
        """Lend the book to the member or raise RefusalError.

        Librarians pass ignore_holds to lend a held book out of turn.
        """
        member = self._storage.find_member(member_id)
        if member is None:
            raise RefusalError(Refusal.UNKNOWN_MEMBER)
        book = self._storage.find_book(isbn)
        if book is None:
            raise RefusalError(Refusal.UNKNOWN_BOOK)
        if len(self._storage.active_loans(member_id)) >= MAX_ACTIVE_LOANS:
            raise RefusalError(Refusal.TOO_MANY_LOANS)
        if member.unpaid_fines > MAX_UNPAID_FINES:
            raise RefusalError(Refusal.UNPAID_FINES)
        if not book.has_free_copy:
            raise RefusalError(Refusal.NO_FREE_COPY)
        first_hold = next(iter(self._storage.hold_queue(isbn)), None)
        if first_hold and first_hold.member_id != member_id and not ignore_holds:
            raise RefusalError(Refusal.HELD_FOR_ANOTHER_MEMBER)

        loan = Loan(self._storage.next_id(), isbn, member_id, borrowed_on=today, due_on=due_date(today))
        self._storage.add_loan(loan)
        book.copies_on_loan += 1
        if first_hold and first_hold.member_id == member_id:
            first_hold.is_active = False
        return loan

    def return_book(self, loan_id: int, today: date) -> Decimal | None:
        """Close the loan, charge the overdue fine and tell the next member in the hold queue.

        Return the charged fine, or None when there is no active loan with this id.
        """
        loan = self._storage.find_loan(loan_id)
        if loan is None or not loan.is_active:
            return None
        loan.returned_on = today
        fine = overdue_fine(loan.due_on, returned_on=today)
        self._storage.get_member(loan.member_id).unpaid_fines += fine
        self._storage.get_book(loan.isbn).copies_on_loan -= 1
        next_hold = next(iter(self._storage.hold_queue(loan.isbn)), None)
        if next_hold:
            self._mailer.send_hold_ready(next_hold.member_id, loan.isbn)
        return fine

    def place_hold(self, member_id: int, isbn: str, today: date) -> Hold:
        """Queue the member for the book or raise RefusalError when the member already waits for it."""
        if any(hold.member_id == member_id for hold in self._storage.hold_queue(isbn)):
            raise RefusalError(Refusal.ALREADY_HELD)
        hold = Hold(self._storage.next_id(), isbn, member_id, placed_on=today)
        self._storage.add_hold(hold)
        return hold
