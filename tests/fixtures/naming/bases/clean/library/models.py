"""Records the library keeps: members, books, loans and holds."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Member:
    id: int
    name: str
    email: str
    unpaid_fines: Decimal = Decimal("0.00")


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    copies: int
    copies_on_loan: int = 0

    @property
    def has_free_copy(self) -> bool:
        return self.copies_on_loan < self.copies


@dataclass
class Loan:
    id: int
    isbn: str
    member_id: int
    borrowed_on: date
    due_on: date
    returned_on: date | None = None

    @property
    def is_active(self) -> bool:
        return self.returned_on is None


@dataclass
class Hold:
    id: int
    isbn: str
    member_id: int
    placed_on: date
    is_active: bool = True
