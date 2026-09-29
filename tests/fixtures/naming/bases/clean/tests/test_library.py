"""Lending, returns and holds through the HTTP API of the mobile app."""

import unittest
from datetime import date

from library.app import App
from library.web import dispatch

KOBZAR = "111"
FOREST_SONG = "222"
OLIA, PETRO, IRYNA = 1, 2, 3


class Calendar:
    """Today's date that a test moves forward."""

    def __init__(self, today: date) -> None:
        self.today = today

    def __call__(self) -> date:
        return self.today


def open_library(calendar: Calendar) -> App:
    """A library with one copy of Kobzar, three copies of Forest Song and three members."""
    app = App(today=calendar)
    dispatch(app, "POST", "/books", {"isbn": KOBZAR, "title": "Кобзар", "author": "Тарас Шевченко"})
    dispatch(
        app, "POST", "/books",
        {"isbn": FOREST_SONG, "title": "Лісова пісня", "author": "Леся Українка", "copies": 3},
    )
    for member_id, name in ((OLIA, "Оля"), (PETRO, "Петро"), (IRYNA, "Ірина")):
        dispatch(app, "POST", "/members", {"user_id": member_id, "name": name, "email": f"{member_id}@example.com"})
    return app


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.calendar = Calendar(date(2026, 3, 2))
        self.app = open_library(self.calendar)

    def post(self, path: str, body: dict) -> tuple[int, dict]:
        return dispatch(self.app, "POST", path, body)

    def lend(self, member_id: int, isbn: str) -> int:
        status, body = self.post("/loans", {"user_id": member_id, "isbn": isbn})
        self.assertEqual(status, 201)
        return body["loan_id"]

    def test_member_borrows_book_for_fourteen_days(self):
        status, body = self.post("/loans", {"user_id": OLIA, "isbn": KOBZAR})
        self.assertEqual(status, 201)
        self.assertEqual(body["due"], "2026-03-16")

    def test_book_without_free_copy_is_refused(self):
        self.lend(OLIA, KOBZAR)
        status, body = self.post("/loans", {"user_id": PETRO, "isbn": KOBZAR})
        self.assertEqual((status, body["error"]), (409, "Усі примірники зараз видано."))

    def test_member_with_three_loans_cannot_borrow_more(self):
        self.post("/books", {"isbn": "333", "title": "Тигролови", "author": "Іван Багряний"})
        self.post("/books", {"isbn": "444", "title": "Місто", "author": "Валер'ян Підмогильний"})
        for isbn in (FOREST_SONG, "333", "444"):
            self.lend(OLIA, isbn)
        status, body = self.post("/loans", {"user_id": OLIA, "isbn": KOBZAR})
        self.assertEqual((status, body["error"]), (409, "У вас уже три книжки. Поверніть одну, щоб узяти нову."))

    def test_late_return_is_fined_per_overdue_day(self):
        loan_id = self.lend(OLIA, KOBZAR)
        self.calendar.today = date(2026, 3, 26)
        status, body = self.post("/returns", {"loan_id": loan_id})
        self.assertEqual((status, body["fine"]), (200, "2.50"))

    def test_capped_fine_blocks_borrowing(self):
        loan_id = self.lend(OLIA, KOBZAR)
        self.calendar.today = date(2026, 6, 1)
        status, body = self.post("/returns", {"loan_id": loan_id})
        self.assertEqual(body["fine"], "10.00")
        status, body = self.post("/loans", {"user_id": OLIA, "isbn": FOREST_SONG})
        self.assertEqual((status, body["error"]), (409, "Спершу сплатіть штраф."))

    def test_returned_book_waits_for_first_member_in_hold_queue(self):
        loan_id = self.lend(OLIA, KOBZAR)
        self.post("/holds", {"user_id": PETRO, "isbn": KOBZAR})
        self.post("/returns", {"loan_id": loan_id})
        self.assertEqual(self.app.mailer.outbox, [("hold_ready", PETRO, KOBZAR)])
        status, body = self.post("/loans", {"user_id": IRYNA, "isbn": KOBZAR})
        self.assertEqual((status, body["error"]), (409, "Книжку заброньовано іншим читачем."))
        self.lend(PETRO, KOBZAR)

    def test_librarian_lends_held_book_out_of_turn(self):
        self.post("/holds", {"user_id": PETRO, "isbn": KOBZAR})
        status, _ = self.post("/loans", {"user_id": IRYNA, "isbn": KOBZAR, "staff": True})
        self.assertEqual(status, 201)

    def test_member_cannot_hold_same_book_twice(self):
        self.post("/holds", {"user_id": PETRO, "isbn": KOBZAR})
        status, body = self.post("/holds", {"user_id": PETRO, "isbn": KOBZAR})
        self.assertEqual((status, body["error"]), (409, "Ви вже забронювали цю книжку."))

    def test_registering_existing_member_returns_stored_record(self):
        status, body = self.post("/members", {"user_id": OLIA})
        self.assertEqual((status, body), (200, {"user_id": OLIA, "fines": "0.00"}))

    def test_returning_unknown_loan_is_not_found(self):
        status, _ = self.post("/returns", {"loan_id": 99})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
