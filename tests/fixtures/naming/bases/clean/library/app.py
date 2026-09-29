"""Composition root: wires storage, mail and circulation for the HTTP API."""

from collections.abc import Callable
from datetime import date

from .circulation import Circulation
from .mail import Mailer
from .storage import Storage


class App:
    def __init__(self, today: Callable[[], date] = date.today) -> None:
        self.today = today
        self.storage = Storage()
        self.mailer = Mailer()
        self.circulation = Circulation(self.storage, self.mailer)
