from datetime import date, timedelta


def calc(d1: date, d2: date) -> int:
    x = (d1 - d2).days
    return x if x > 0 else 0


def calc_fine(days: int) -> float:
    f = days * 0.25
    if f > 10:
        f = 10.0
    return f


def due_date(start: date) -> date:
    return start + timedelta(days=14)


def check_limit(user, loans):
    if len(loans) >= 3:
        return "LIMIT"
    if user.fines_amt > 5:
        return "FINES"
    return None
