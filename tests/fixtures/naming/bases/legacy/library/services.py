from datetime import date

from .helpers import calc, calc_fine, check_limit, due_date
from .models import Loan, Reservation, User


class PatronService:
    def __init__(self, db):
        self.db = db

    def get_patron(self, uid, name="", email=""):
        u = self.db.get_user(uid)
        if u is None:
            u = User(uid, name, email)
            self.db.add_user(u)
        return u


class LoanMgr:
    def __init__(self, db, beacon):
        self.db = db
        self.beacon = beacon

    def process(self, uid, isbn, today: date, flag=False):
        u = self.db.get_user(uid)
        if u is None:
            return {"ok": False, "reason": "NO_USER"}
        data = self.db.fetch_book(isbn)
        if data is None:
            return {"ok": False, "reason": "NO_BOOK"}
        loans_list = self.db.loans_for(uid)
        err = check_limit(u, loans_list)
        if err:
            return {"ok": False, "reason": err}
        if data.copies_out >= data.copies:
            return {"ok": False, "reason": "NO_COPIES"}
        q = self.db.load_reservations(isbn)
        if q and q[0].patron_id != uid and not flag:
            return {"ok": False, "reason": "HELD"}
        tmp = Loan(self.db.next_id(), isbn, uid, today, due_date(today))
        self.db.insert(tmp)
        data.copies_out += 1
        if q and q[0].patron_id == uid:
            q[0].active = False
        return {"ok": True, "loan": tmp}

    def do_return(self, loan_id, today: date):
        l = self.db.retrieve_loan(loan_id)
        if l is None or l.returned:
            return None
        l.returned = today
        fine = calc_fine(calc(today, l.due))
        u = self.db.get_user(l.borrower_id)
        u.fines_amt += fine
        b = self.db.fetch_book(l.book_isbn)
        b.copies_out -= 1
        nxt = self.db.load_reservations(l.book_isbn)
        if nxt:
            self.beacon.ping(nxt[0].patron_id, "BOOK_READY")
        return fine

    def reserve(self, uid, isbn, today: date):
        for r in self.db.load_reservations(isbn):
            if r.patron_id == uid:
                return {"ok": False, "reason": "DUPLICATE"}
        r = Reservation(self.db.next_id(), isbn, uid, today)
        self.db.insert(r)
        return {"ok": True, "reservation": r}
