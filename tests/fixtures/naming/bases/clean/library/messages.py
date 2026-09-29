"""Texts the mobile app shows to members."""

from .circulation import Refusal

REFUSAL_MESSAGES = {
    Refusal.UNKNOWN_MEMBER: "Читача не знайдено.",
    Refusal.UNKNOWN_BOOK: "Такої книжки немає в каталозі.",
    Refusal.TOO_MANY_LOANS: "У вас уже три книжки. Поверніть одну, щоб узяти нову.",
    Refusal.UNPAID_FINES: "Спершу сплатіть штраф.",
    Refusal.NO_FREE_COPY: "Усі примірники зараз видано.",
    Refusal.HELD_FOR_ANOTHER_MEMBER: "Книжку заброньовано іншим читачем.",
    Refusal.ALREADY_HELD: "Ви вже забронювали цю книжку.",
}
LOAN_NOT_FOUND = "Видачу не знайдено."
