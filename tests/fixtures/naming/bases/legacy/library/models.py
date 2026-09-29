from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: str
    fines_amt: float = 0.0


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    copies: int
    copies_out: int = 0


@dataclass
class Loan:
    id: int
    book_isbn: str
    borrower_id: int
    start: date
    due: date
    returned: Optional[date] = None


@dataclass
class Reservation:
    id: int
    isbn: str
    patron_id: int
    created: date
    active: bool = True
