import unittest
from datetime import date

from library.app import App
from library.web import dispatch

DAY = [date(2026, 3, 2)]


def mk():
    DAY[0] = date(2026, 3, 2)
    a = App(today=lambda: DAY[0])
    dispatch(a, "POST", "/books", {"isbn": "111", "title": "Кобзар", "author": "Тарас Шевченко"})
    dispatch(a, "POST", "/books", {"isbn": "222", "title": "Лісова пісня", "author": "Леся Українка", "copies": 3})
    for uid, name in ((1, "Оля"), (2, "Петро"), (3, "Ірина")):
        dispatch(a, "POST", "/members", {"user_id": uid, "name": name, "email": f"{uid}@example.com"})
    return a


class T(unittest.TestCase):
    def test_1(self):
        a = mk()
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        self.assertEqual(code, 201)
        self.assertEqual(body["due"], "2026-03-16")

    def test_2(self):
        a = mk()
        dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        code, body = dispatch(a, "POST", "/loans", {"user_id": 2, "isbn": "111"})
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "Усі примірники зараз видано.")

    def test_limit(self):
        a = mk()
        dispatch(a, "POST", "/books", {"isbn": "333", "title": "Тигролови", "author": "Іван Багряний"})
        dispatch(a, "POST", "/books", {"isbn": "444", "title": "Місто", "author": "Валер'ян Підмогильний"})
        for isbn in ("222", "333", "444"):
            dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": isbn})
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "У вас уже три книжки. Поверніть одну, щоб узяти нову.")

    def test_fine(self):
        a = mk()
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        DAY[0] = date(2026, 3, 26)
        code, body = dispatch(a, "POST", "/returns", {"loan_id": body["loan_id"]})
        self.assertEqual(code, 200)
        self.assertEqual(body["fine"], "2.50")

    def test_fine2(self):
        a = mk()
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        DAY[0] = date(2026, 6, 1)
        code, body = dispatch(a, "POST", "/returns", {"loan_id": body["loan_id"]})
        self.assertEqual(body["fine"], "10.00")
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "222"})
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "Спершу сплатіть штраф.")

    def test_hold(self):
        a = mk()
        code, body = dispatch(a, "POST", "/loans", {"user_id": 1, "isbn": "111"})
        dispatch(a, "POST", "/holds", {"user_id": 2, "isbn": "111"})
        dispatch(a, "POST", "/returns", {"loan_id": body["loan_id"]})
        self.assertEqual(a.beacon.outbox, [(2, "BOOK_READY")])
        code, body = dispatch(a, "POST", "/loans", {"user_id": 3, "isbn": "111"})
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "Книжку заброньовано іншим читачем.")
        code, _ = dispatch(a, "POST", "/loans", {"user_id": 2, "isbn": "111"})
        self.assertEqual(code, 201)

    def test_staff(self):
        a = mk()
        dispatch(a, "POST", "/holds", {"user_id": 2, "isbn": "111"})
        code, _ = dispatch(a, "POST", "/loans", {"user_id": 3, "isbn": "111", "staff": True})
        self.assertEqual(code, 201)

    def test_dup(self):
        a = mk()
        dispatch(a, "POST", "/holds", {"user_id": 2, "isbn": "111"})
        code, body = dispatch(a, "POST", "/holds", {"user_id": 2, "isbn": "111"})
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "Ви вже забронювали цю книжку.")

    def test_it_works(self):
        a = mk()
        code, body = dispatch(a, "POST", "/members", {"user_id": 1})
        self.assertEqual(body, {"user_id": 1, "fines": "0.00"})

    def test_404(self):
        a = mk()
        code, _ = dispatch(a, "POST", "/returns", {"loan_id": 99})
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
