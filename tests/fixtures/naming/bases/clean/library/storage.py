"""In-memory storage of library records.

`get_*` raises KeyError for a missing record; `find_*` returns None.
"""

from .models import Book, Hold, Loan, Member


class Storage:
    def __init__(self) -> None:
        self._members: dict[int, Member] = {}
        self._books: dict[str, Book] = {}
        self._loans: dict[int, Loan] = {}
        self._holds: dict[int, Hold] = {}
        self._last_id = 0

    def next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def add_member(self, member: Member) -> None:
        self._members[member.id] = member

    def add_book(self, book: Book) -> None:
        self._books[book.isbn] = book

    def add_loan(self, loan: Loan) -> None:
        self._loans[loan.id] = loan

    def add_hold(self, hold: Hold) -> None:
        self._holds[hold.id] = hold

    def get_member(self, member_id: int) -> Member:
        return self._members[member_id]

    def get_book(self, isbn: str) -> Book:
        return self._books[isbn]

    def find_member(self, member_id: int) -> Member | None:
        return self._members.get(member_id)

    def find_book(self, isbn: str) -> Book | None:
        return self._books.get(isbn)

    def find_loan(self, loan_id: int) -> Loan | None:
        return self._loans.get(loan_id)

    def active_loans(self, member_id: int) -> list[Loan]:
        return [loan for loan in self._loans.values() if loan.member_id == member_id and loan.is_active]

    def hold_queue(self, isbn: str) -> list[Hold]:
        """Active holds on the book, oldest first."""
        holds = [hold for hold in self._holds.values() if hold.isbn == isbn and hold.is_active]
        return sorted(holds, key=lambda hold: (hold.placed_on, hold.id))
