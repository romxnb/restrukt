from .models import Book, Loan, Reservation, User


class DB:
    def __init__(self):
        self.users = {}
        self.books = {}
        self.loans = {}
        self.res = {}
        self._seq = 0

    def next_id(self):
        self._seq += 1
        return self._seq

    def add_user(self, u: User):
        self.users[u.id] = u

    def add_book(self, b: Book):
        self.books[b.isbn] = b

    def get_user(self, uid):
        return self.users.get(uid)

    def fetch_book(self, isbn):
        return self.books.get(isbn)

    def retrieve_loan(self, loan_id):
        return self.loans.get(loan_id)

    def loans_for(self, uid):
        return [l for l in self.loans.values() if l.borrower_id == uid and l.returned is None]

    def load_reservations(self, isbn):
        lst = [r for r in self.res.values() if r.isbn == isbn and r.active]
        return sorted(lst, key=lambda r: (r.created, r.id))

    def insert(self, obj):
        if isinstance(obj, Loan):
            self.loans[obj.id] = obj
        elif isinstance(obj, Reservation):
            self.res[obj.id] = obj
        else:
            raise TypeError(f"cannot insert {obj!r}")
