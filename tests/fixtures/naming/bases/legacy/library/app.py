from datetime import date

from .notify import Beacon
from .repo import DB
from .services import LoanMgr, PatronService


class App:
    def __init__(self, today=date.today):
        self.today = today
        self.db = DB()
        self.beacon = Beacon()
        self.patrons = PatronService(self.db)
        self.loans = LoanMgr(self.db, self.beacon)
